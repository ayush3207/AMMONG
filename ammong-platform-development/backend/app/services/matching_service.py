from typing import Any, Dict, List, Optional
from app.core.logging import logger
from app.schemas.analysis import (
    AnalysisResponse,
    PlanItem,
    SkillGapItem,
    SkillMatchItem,
    WeaknessItem,
)
from app.schemas.job import JobResponse
from app.services.dataset_service import dataset_service
from app.services.llm_service import llm_service
from app.utils.text_normalizer import skills_match

class MatchingService:
    """
    Core Placement Intelligence Matching Engine.
    Compares extracted student skills & evidence with ground truth
    job requirements from all_job_post.csv.
    """
    async def analyze_placement(
        self,
        resume_text: str,
        company: str,
        role: str,
    ) -> AnalysisResponse:
        logger.info(f"Running placement analysis for company='{company}', role='{role}'")

        # Step 1: Extract student profile skills & project evidence
        extracted_data = await llm_service.extract_student_profile(resume_text, role)
        student_skills = extracted_data.get("skills", [])
        project_evidence = extracted_data.get("projects", [])
        weaknesses_raw = extracted_data.get("weaknesses", [])

        # Step 2: Find reference job postings from the knowledge base
        matching_jobs = dataset_service.find_matching_jobs(role=role, company=company, limit=3)
        
        primary_job = matching_jobs[0] if matching_jobs else None
        matched_job_response = None
        if primary_job:
            matched_job_response = JobResponse(
                job_id=primary_job["job_id"],
                category=primary_job["category"],
                job_title=primary_job["job_title"],
                job_description=primary_job["job_description"],
                job_skill_set=primary_job["job_skill_set"],
            )

        # Step 3: Aggregate target job requirements from dataset
        required_skills: List[str] = []
        if primary_job and primary_job.get("parsed_skills"):
            required_skills.extend(primary_job["parsed_skills"])
        
        # Supplement from other top matched jobs if primary has very few
        if len(required_skills) < 5 and len(matching_jobs) > 1:
            for extra_job in matching_jobs[1:]:
                for s in extra_job.get("parsed_skills", []):
                    if s not in required_skills:
                        required_skills.append(s)
                if len(required_skills) >= 8:
                    break

        # If no skills found in dataset for this role, provide default common role skills
        if not required_skills:
            required_skills = ["Java", "SQL", "Git", "REST APIs", "Docker", "AWS", "System Design"]

        # Step 4: Compare Student Skills vs Job Requirements
        what_you_have: List[SkillMatchItem] = []
        strong_matches: List[str] = []
        skill_gaps: List[SkillGapItem] = []
        matched_req_skills: set = set()

        # For each student skill, see how it aligns with requirements
        for s_skill in student_skills:
            best_status = "none"
            matched_req = None
            for req in required_skills:
                match_res = skills_match(s_skill, req)
                if match_res == "match":
                    best_status = "match"
                    matched_req = req
                    break
                elif match_res == "partial" and best_status != "match":
                    best_status = "partial"
                    matched_req = req

            if best_status in ["match", "partial"]:
                what_you_have.append(SkillMatchItem(skill=s_skill, status=best_status))
                if best_status == "match":
                    strong_matches.append(s_skill)
                if matched_req:
                    matched_req_skills.add(matched_req)
            elif len(what_you_have) < 8:
                # Include relevant demonstrated skill as match/partial
                what_you_have.append(SkillMatchItem(skill=s_skill, status="match"))

        # Identify missing skills (Skill Gaps)
        missing_skills = [req for req in required_skills if req not in matched_req_skills]

        for i, missing in enumerate(missing_skills[:5], 1):
            skill_gaps.append(SkillGapItem(skill=missing, priority=i))

        # Calculate Placement Readiness Match Score
        total_reqs = max(len(required_skills), 1)
        matched_count = len(matched_req_skills)
        if total_reqs > 0:
            raw_score = (matched_count / total_reqs) * 100
            # Scale sensibly based on skills found
            bonus = min(len(student_skills) * 2, 20)
            final_score = int(min(max(raw_score + bonus, 45 if len(student_skills) > 3 else 25), 94))
        else:
            final_score = 65

        # Format Weaknesses
        weaknesses: List[WeaknessItem] = []
        for w in weaknesses_raw:
            weaknesses.append(WeaknessItem(
                title=w.get("title", "Profile Weakness"),
                problem=w.get("problem", "Improvement needed"),
                suggestion=w.get("suggestion", "Add more details")
            ))

        # Build Prioritized Improvement Plan
        improvement_plan: List[PlanItem] = []
        for gap in skill_gaps[:3]:
            skill_name = gap.skill
            why = f"Required by verified {role} job requirements and not currently demonstrated."
            action = f"Learn {skill_name} core concepts and build a targeted project demonstrating it."
            improvement_plan.append(PlanItem(
                priority=gap.priority,
                skill=skill_name,
                why=why,
                action=action,
            ))

        resume_improvements = [
            "Strengthen project descriptions with clear business or technical outcomes",
            "Add measurable achievements and performance metrics to work bullets",
            "Highlight target role keywords and frameworks prominently in your skills list",
            "Include links to live deployed applications and GitHub repositories",
            "Demonstrate containerization or cloud deployment experience",
        ]

        response = AnalysisResponse(
            match_score=final_score,
            target_company=company,
            target_role=role,
            matched_job=matched_job_response,
            what_you_have=what_you_have,
            what_job_requires=required_skills,
            skill_gaps=skill_gaps,
            strong_matches=strong_matches[:5],
            weaknesses=weaknesses,
            improvement_plan=improvement_plan,
            resume_improvements=resume_improvements,
            student_extracted_skills=student_skills,
            project_evidence=project_evidence,
            # CamelCase aliases
            whatYouHave=what_you_have,
            whatJobRequires=required_skills,
            skillGaps=skill_gaps,
            strongMatches=strong_matches[:5],
            improvementPlan=improvement_plan,
            resumeImprovements=resume_improvements,
        )

        return response

matching_service = MatchingService()
