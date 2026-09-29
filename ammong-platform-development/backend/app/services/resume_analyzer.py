import json
import re
from typing import Any, Dict, List, Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import logger
from app.schemas.resume_analysis import (
    EducationItem,
    ExperienceItem,
    ProjectItem,
    ResumeAnalysisResponse,
    SkillEvidenceItem,
    StudentProfile,
)
from app.services.llm_service import SKILL_TAXONOMY

RESUME_ANALYSIS_PROMPT = """You are AMMONG, an AI Student Placement Intelligence System.
Analyze this student resume for the target role: "{target_role}" at target company: "{target_company}".

CRITICAL ACCURACY RULES:
1. Extract facts strictly present in the resume text.
2. Do NOT invent, assume, or fabricate any information.
3. If any field or section is not mentioned in the resume, return an empty list [] or null.
4. For resume_weaknesses, evaluate practical student placement issues such as:
   - Vague project descriptions without business or technical context
   - Missing measurable outcomes or metrics (e.g., latency, throughput, users, percentages)
   - Weak role alignment with {target_role}
   - Unsupported skill claims (skills listed without project or coursework evidence)
   - Missing deployment, version control, or production evidence
5. For skill_evidence: link each identified skill to its concrete mention in projects, experience, or education.

Respond ONLY with valid JSON in this exact structure:
{{
  "student_name": "Student Full Name or null",
  "education": [
    {{
      "institution": "University/College Name",
      "degree": "Degree (e.g. B.Tech, B.S.) or null",
      "field_of_study": "Field (e.g. Computer Science) or null",
      "graduation_year": "Year or null",
      "gpa": "GPA/Percentage or null"
    }}
  ],
  "experience": [
    {{
      "role": "Job/Internship Title",
      "organization": "Company/Org Name",
      "duration": "Duration/Dates or null",
      "description": "Responsibilities and accomplishments"
    }}
  ],
  "technical_skills": ["Skill1", "Skill2", ...],
  "soft_skills": ["Skill1", ...],
  "projects": [
    {{
      "project_name": "Project Name",
      "description": "Detailed project description",
      "technologies": ["Tech1", "Tech2"],
      "role": "Role in project or null",
      "evidence": "Concrete outcome, feature, or metric demonstrated"
    }}
  ],
  "certifications": ["Cert1", ...],
  "achievements": ["Achievement1", ...],
  "skill_evidence": [
    {{
      "skill": "Skill name",
      "evidence_source": "Project or Experience name",
      "evidence_text": "Sentence showing how this skill was applied",
      "confidence": "high, medium, or low"
    }}
  ],
  "resume_strengths": [
    "Identified strength 1",
    "Identified strength 2"
  ],
  "resume_weaknesses": [
    "Practical weakness 1 (e.g., missing metrics)",
    "Practical weakness 2 (e.g., vague technical description)"
  ]
}}

RESUME TEXT:
{resume_text}
"""

class ResumeAnalyzer:
    """
    Dedicated Resume Analysis Service.
    Extracts structured student profiles, projects, evidence, and practical weaknesses.
    Keeps extraction logic isolated from job matching and route handlers.
    """
    def __init__(self):
        self.client: Optional[AsyncOpenAI] = None
        if settings.LLM_API_KEY:
            client_kwargs = {"api_key": settings.LLM_API_KEY}
            if settings.LLM_BASE_URL:
                client_kwargs["base_url"] = settings.LLM_BASE_URL
            self.client = AsyncOpenAI(**client_kwargs)

    async def analyze_resume(
        self,
        resume_text: str,
        target_company: str,
        target_role: str,
    ) -> ResumeAnalysisResponse:
        """
        Main entrypoint for structured resume analysis.
        Extracts, validates with Pydantic, and returns ResumeAnalysisResponse.
        """
        logger.info(f"Analyzing resume for target: '{target_role}' at '{target_company}'")

        if self.client and settings.LLM_API_KEY:
            try:
                raw_result = await self._call_llm(resume_text, target_company, target_role)
                validated = self._validate_and_build_response(raw_result, target_company, target_role)
                if validated:
                    return validated
                logger.warning("LLM response validation failed. Falling back to deterministic analysis.")
            except Exception as e:
                logger.warning(f"LLM resume analysis failed: {e}. Falling back to deterministic analysis.")

        # Fallback to deterministic NLP extraction
        fallback_data = self._deterministic_extract(resume_text, target_company, target_role)
        return self._build_pydantic_response(fallback_data, target_company, target_role)

    async def _call_llm(
        self,
        resume_text: str,
        target_company: str,
        target_role: str,
    ) -> Dict[str, Any]:
        """Calls the LLM with strict JSON schema instructions."""
        prompt = RESUME_ANALYSIS_PROMPT.format(
            target_company=target_company,
            target_role=target_role,
            resume_text=resume_text[:6000],
        )

        response = await self.client.chat.completions.create(
            model=settings.LLM_MODEL or "gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are AMMONG Placement Intelligence. Extract structured resume information "
                        "strictly based on the provided text. Never hallucinate facts. Return valid JSON only."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response received from LLM.")

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}. Content preview: {content[:100]}")
            raise

    def _validate_and_build_response(
        self,
        data: Dict[str, Any],
        target_company: str,
        target_role: str,
    ) -> Optional[ResumeAnalysisResponse]:
        """Validates raw dictionary with Pydantic and returns structured response."""
        try:
            return self._build_pydantic_response(data, target_company, target_role)
        except Exception as e:
            logger.error(f"Pydantic validation error: {e}", exc_info=True)
            return None

    def _build_pydantic_response(
        self,
        data: Dict[str, Any],
        target_company: str,
        target_role: str,
    ) -> ResumeAnalysisResponse:
        """Converts dictionary into strongly-typed ResumeAnalysisResponse."""
        student_name = data.get("student_name")
        if student_name and str(student_name).lower() in ["null", "none", "not found", "n/a"]:
            student_name = None

        # Build Education Items
        education_items = []
        for edu in data.get("education", []):
            if isinstance(edu, dict):
                education_items.append(EducationItem(
                    institution=edu.get("institution"),
                    degree=edu.get("degree"),
                    field_of_study=edu.get("field_of_study"),
                    graduation_year=str(edu.get("graduation_year")) if edu.get("graduation_year") else None,
                    gpa=str(edu.get("gpa")) if edu.get("gpa") else None,
                ))
            elif isinstance(edu, str):
                education_items.append(EducationItem(institution=edu))

        # Build Experience Items
        experience_items = []
        for exp in data.get("experience", []):
            if isinstance(exp, dict):
                experience_items.append(ExperienceItem(
                    role=exp.get("role"),
                    organization=exp.get("organization"),
                    duration=exp.get("duration"),
                    description=exp.get("description"),
                ))
            elif isinstance(exp, str):
                experience_items.append(ExperienceItem(description=exp))

        # Build Project Items
        project_items = []
        for proj in data.get("projects", []):
            if isinstance(proj, dict):
                project_items.append(ProjectItem(
                    project_name=proj.get("project_name") or "Project",
                    description=proj.get("description") or "",
                    technologies=proj.get("technologies") or [],
                    role=proj.get("role"),
                    evidence=proj.get("evidence"),
                ))
            elif isinstance(proj, str):
                project_items.append(ProjectItem(
                    project_name="Project",
                    description=proj,
                ))

        # Build Skill Evidence Items
        evidence_items = []
        for ev in data.get("skill_evidence", []):
            if isinstance(ev, dict) and ev.get("skill"):
                evidence_items.append(SkillEvidenceItem(
                    skill=ev.get("skill", ""),
                    evidence_source=ev.get("evidence_source", "Resume"),
                    evidence_text=ev.get("evidence_text", ""),
                    confidence=ev.get("confidence", "medium"),
                ))

        tech_skills = data.get("technical_skills") or []
        soft_skills = data.get("soft_skills") or []
        all_skills = data.get("skills") or list(set(tech_skills + soft_skills))

        # Combine into student profile
        student_profile = StudentProfile(
            name=student_name,
            education=education_items,
            experience=experience_items,
        )

        return ResumeAnalysisResponse(
            student_profile=student_profile,
            student_name=student_name,
            technical_skills=tech_skills,
            soft_skills=soft_skills,
            skills=all_skills,
            projects=project_items,
            certifications=data.get("certifications") or [],
            achievements=data.get("achievements") or [],
            skill_evidence=evidence_items,
            resume_strengths=data.get("resume_strengths") or [],
            resume_weaknesses=data.get("resume_weaknesses") or [],
            target_company=target_company,
            target_role=target_role,
        )

    def _deterministic_extract(
        self,
        resume_text: str,
        target_company: str,
        target_role: str,
    ) -> Dict[str, Any]:
        """
        Deterministic NLP extractor scanning for skills, projects, education,
        and evidence without inventing synthetic facts.
        """
        text_lower = resume_text.lower()
        lines = [l.strip() for l in resume_text.split("\n") if l.strip()]

        # 1. Extract Name (typically first non-empty line if short)
        student_name = None
        for line in lines[:4]:
            cleaned_line = re.sub(r"[^\w\s\.\-]", "", line).strip()
            # Ignore headers like "Resume", "Curriculum Vitae"
            if cleaned_line.lower() in ["resume", "curriculum vitae", "cv", "portfolio"]:
                continue
            words = cleaned_line.split()
            if 1 < len(words) <= 4 and not any(ch.isdigit() for ch in cleaned_line) and "@" not in line:
                student_name = cleaned_line.title()
                break

        # 2. Extract Technical Skills
        detected_tech = set()
        for skill in SKILL_TAXONOMY:
            pattern = r"(?:\b|_)" + re.escape(skill) + r"(?:\b|_)"
            if re.search(pattern, text_lower):
                if skill in ["sql", "aws", "gcp", "ci/cd", "cicd", "html", "css", "nlp", "ai", "ml", "oop"]:
                    detected_tech.add(skill.upper())
                elif skill in ["react.js", "next.js", "node.js", "express.js"]:
                    detected_tech.add(skill.capitalize())
                elif skill == "fastapi":
                    detected_tech.add("FastAPI")
                elif skill == "mongodb":
                    detected_tech.add("MongoDB")
                elif skill == "postgresql":
                    detected_tech.add("PostgreSQL")
                elif skill == "docker":
                    detected_tech.add("Docker")
                elif skill == "kubernetes":
                    detected_tech.add("Kubernetes")
                elif skill == "spring boot":
                    detected_tech.add("Spring Boot")
                else:
                    detected_tech.add(skill.title())

        # 3. Soft Skills
        detected_soft = []
        for soft in ["communication", "teamwork", "leadership", "problem solving", "adaptability", "critical thinking", "collaboration"]:
            if soft in text_lower:
                detected_soft.append(soft.title())

        # 4. Education Extraction
        education_list = []
        edu_keywords = ["bachelor", "master", "b.tech", "b.e.", "b.s.", "m.tech", "degree", "university", "institute", "college"]
        for line in lines:
            line_low = line.lower()
            if any(k in line_low for k in edu_keywords) and len(line) < 120:
                year_match = re.search(r"\b(20\d\d)\b", line)
                year = year_match.group(1) if year_match else None
                education_list.append({
                    "institution": line,
                    "degree": "Bachelor of Technology" if "b.tech" in line_low or "bachelor" in line_low else None,
                    "field_of_study": "Computer Science" if "computer" in line_low else None,
                    "graduation_year": year,
                    "gpa": None,
                })
                if len(education_list) >= 2:
                    break

        # 5. Projects Extraction
        projects_list = []
        in_proj = False
        current_proj_name = None
        current_proj_desc = []

        for line in lines:
            line_low = line.lower()
            if any(h in line_low for h in ["projects", "personal projects", "academic projects", "key projects"]):
                in_proj = True
                continue
            if in_proj:
                if any(h in line_low for h in ["education", "experience", "certifications", "skills", "awards", "hobbies"]) and len(line) < 25:
                    in_proj = False
                    if current_proj_name:
                        projects_list.append({
                            "project_name": current_proj_name,
                            "description": " ".join(current_proj_desc),
                            "technologies": [s for s in detected_tech if s.lower() in " ".join(current_proj_desc).lower()][:4],
                            "role": "Developer",
                            "evidence": "Implemented functional project demonstrated in resume.",
                        })
                    break

                if (line.startswith("-") or line.startswith("•") or line.startswith("*") or ":" in line) and len(line) > 15:
                    if not current_proj_name or len(current_proj_desc) >= 2:
                        if current_proj_name:
                            projects_list.append({
                                "project_name": current_proj_name,
                                "description": " ".join(current_proj_desc),
                                "technologies": [s for s in detected_tech if s.lower() in " ".join(current_proj_desc).lower()][:4],
                                "role": "Developer",
                                "evidence": "Demonstrated technical implementation in resume.",
                            })
                        current_proj_name = line.split(":")[0].replace("-", "").replace("•", "").strip()
                        current_proj_desc = [line]
                    else:
                        current_proj_desc.append(line)

        if current_proj_name and not any(p["project_name"] == current_proj_name for p in projects_list):
            projects_list.append({
                "project_name": current_proj_name,
                "description": " ".join(current_proj_desc),
                "technologies": [s for s in detected_tech if s.lower() in " ".join(current_proj_desc).lower()][:4],
                "role": "Developer",
                "evidence": "Demonstrated technical implementation in resume.",
            })

        # 6. Skill Evidence
        skill_evidence = []
        for s in list(detected_tech)[:6]:
            for p in projects_list:
                if s.lower() in p["description"].lower() or s in p.get("technologies", []):
                    skill_evidence.append({
                        "skill": s,
                        "evidence_source": p["project_name"],
                        "evidence_text": p["description"][:120],
                        "confidence": "high",
                    })
                    break
            else:
                skill_evidence.append({
                    "skill": s,
                    "evidence_source": "Technical Skills Section",
                    "evidence_text": f"Candidate listed {s} in their skills inventory.",
                    "confidence": "medium",
                })

        # 7. Strengths
        strengths = []
        if len(detected_tech) >= 5:
            strengths.append(f"Solid foundational technical stack covering {len(detected_tech)} relevant technologies.")
        if projects_list:
            strengths.append(f"Contains {len(projects_list)} practical projects demonstrating applied skills.")
        if education_list:
            strengths.append("Clear academic background listed.")

        # 8. Practical Weaknesses (Real placement issues without asserting perfect AI judgment)
        weaknesses = []
        has_metrics = bool(re.search(r"\b\d+%\b|\b\d+x\b|\bincreased\b|\breduced\b|\bimproved\b", text_lower))
        if not has_metrics:
            weaknesses.append("Missing measurable outcomes: Project descriptions lack quantifiable metrics (e.g. % performance increase, latency reduction, user scale).")

        has_deploy = any(w in text_lower for w in ["deployed", "aws", "docker", "gcp", "azure", "kubernetes", "ci/cd", "production"])
        if not has_deploy:
            weaknesses.append(f"Missing deployment/cloud evidence: No containerization or cloud deployment experience cited for {target_role}.")

        if len(projects_list) < 2:
            weaknesses.append("Limited project depth: Adding another production-style project would strongly reinforce target role alignment.")

        weaknesses.append("Unsupported skill claims: Some listed skills lack specific project bullet points demonstrating how they were applied.")
        weaknesses.append(f"Role alignment: Highlight competencies specifically sought by {target_company} for {target_role} higher on the first page.")

        return {
            "student_name": student_name,
            "education": education_list,
            "experience": [],
            "technical_skills": sorted(list(detected_tech)),
            "soft_skills": detected_soft,
            "skills": sorted(list(detected_tech.union(detected_soft))),
            "projects": projects_list[:4],
            "certifications": [],
            "achievements": [],
            "skill_evidence": skill_evidence,
            "resume_strengths": strengths,
            "resume_weaknesses": weaknesses,
        }

resume_analyzer = ResumeAnalyzer()
