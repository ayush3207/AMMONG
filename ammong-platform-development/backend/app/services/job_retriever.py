"""
AMMONG Job Requirement Retrieval Service.

Searches the all_job_post.csv dataset (1,167 records) by target_role,
ranks relevant postings, aggregates and normalizes their skills,
and returns structured role-level requirements.

CORE RULES:
1. Search dataset using the target job role.
2. Highest priority to job_title similarity.
3. Strict category isolation: do NOT mix categories (e.g. Sales, HR, Business Development with tech roles).
4. Separate technical skills from generic soft skills (Communication, Teamwork, Problem Solving).
5. Generic soft skills must NOT dominate or become skill gaps.
6. Filter out unrelated domain skills (Vendor Management, Procurement, Contract Management, etc.).
7. Ground specialized roles with industry-standard canonical technical skills.
"""

import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.logging import logger
from app.schemas.job_requirements import (
    JobRequirementsResponse,
    SourceJobItem,
)
from app.services.dataset_service import dataset_service
from app.utils.text_normalizer import canonicalize_skill, normalize_skill, parse_skill_list


# ── Canonical Role Profiles ──
# Ground truth industry-standard technical requirements for common target roles.
ROLE_CANONICAL_SKILLS: Dict[str, List[str]] = {
    "ml engineer": [
        "Python", "Machine Learning", "Deep Learning", "NumPy", "Pandas",
        "Scikit-learn", "TensorFlow", "PyTorch", "SQL", "Statistics",
        "Data Preprocessing", "Model Evaluation", "Feature Engineering",
        "Git", "MLOps",
    ],
    "machine learning engineer": [
        "Python", "Machine Learning", "Deep Learning", "NumPy", "Pandas",
        "Scikit-learn", "TensorFlow", "PyTorch", "SQL", "Statistics",
        "Data Preprocessing", "Model Evaluation", "Feature Engineering",
        "Git", "MLOps",
    ],
    "data scientist": [
        "Python", "SQL", "Machine Learning", "Statistics", "Pandas",
        "NumPy", "Scikit-learn", "Data Visualization", "Tableau",
        "Deep Learning", "Data Preprocessing", "Git",
    ],
    "data engineer": [
        "Python", "SQL", "Spark", "Hadoop", "ETL", "Kafka", "Airflow",
        "Data Warehousing", "AWS", "PostgreSQL", "Docker", "Git",
    ],
    "backend developer": [
        "Python", "Java", "Node.js", "SQL", "PostgreSQL", "Docker",
        "REST APIs", "Git", "FastAPI", "Spring Boot", "Redis",
        "Microservices", "Linux", "CI/CD",
    ],
    "backend engineer": [
        "Python", "Java", "Node.js", "SQL", "PostgreSQL", "Docker",
        "REST APIs", "Git", "FastAPI", "Spring Boot", "Redis",
        "Microservices", "Linux", "CI/CD",
    ],
    "frontend developer": [
        "JavaScript", "TypeScript", "React", "HTML/CSS", "Next.js",
        "Tailwind CSS", "REST APIs", "Git", "Redux", "Web Performance",
        "Responsive Design",
    ],
    "full stack developer": [
        "JavaScript", "TypeScript", "React", "Node.js", "Python",
        "SQL", "Git", "Docker", "REST APIs", "HTML/CSS", "PostgreSQL", "MongoDB",
    ],
    "software engineer": [
        "Python", "Java", "JavaScript", "SQL", "Git", "Data Structures & Algorithms",
        "Docker", "REST APIs", "System Design", "Linux", "CI/CD", "Unit Testing",
    ],
    "devops engineer": [
        "Docker", "Kubernetes", "AWS", "CI/CD", "Linux", "Terraform",
        "Git", "Bash", "Ansible", "Monitoring", "Python",
    ],
}


# ── Generic soft skills (Must NOT contaminate technical requirements) ──
GENERIC_SOFT_SKILLS: Set[str] = {
    "communication", "communication skills", "oral communication", "written communication",
    "problem solving", "problem-solving", "problem solving skills",
    "teamwork", "team player", "collaboration", "team collaboration",
    "adaptability", "organizational skills", "time management",
    "creativity", "customer focus", "customer service", "interpersonal skills",
    "good interpersonal skills", "motivation", "enthusiasm", "leadership",
    "decision making", "work independently", "ability to work independently",
    "strong sense of responsibility", "attention to detail", "negotiation",
    "relationship management", "presentation skills", "strategic thinking",
    "analytical thinking", "critical thinking", "analytical skills", "customer satisfaction",
    "client relationship management", "interfacing with clients",
    "office management", "event coordination", "conflict resolution",
    "active listening", "multitasking", "multi-tasking", "work ethic", "detail oriented",
    "detail-oriented", "verbal communication", "written skills", "verbal skills",
    "excellent written skills", "excellent verbal skills", "influencing",
    "cultural sensitivity", "self-motivated", "detail-minded", "result-oriented",
    "storytelling", "transparency", "confidentiality",
    "project management", "stakeholder engagement", "business acumen",
    "compliance knowledge",
}


# ── Domain-unrelated skills for technical roles ──
# Skills from business, sourcing, administrative, or non-tech jobs that must not pollute tech roles.
UNRELATED_TECH_BLACKLIST: Set[str] = {
    "vendor management", "contract management", "procurement policies",
    "procurement", "rfp management", "budget management", "customer service",
    "office 365", "microsoft word", "microsoft office", "microsoft office suite",
    "adp workforce now", "payroll administration", "hr practices",
    "regulatory compliance", "event coordination", "office management",
    "network configuration", "network security", "cyber defense",
    "sql server (2012+) administration", "sql server administration",
    "help desk support", "troubleshooting", "documentation",
    "hardware inventory management", "digital transformation",
    "solution demonstration", "customer requirements gathering",
    "lead generation", "salesforce", "netsuite", "ellucian banner",
    "cisco / dell switches", "juniper", "next-gen firewalls (palo alto)",
    "storage area networks (sans)", "vmware vsphere 6/7/8",
    "windows active directory (2012+)", "endpoint security management",
    "pc hardware", "workstation setup", "macintosh", "server operating systems",
    "itil", "service management", "disaster recovery/business continuance management",
    "networking principles", "networking", "network administration",
}


# ── Skill normalization map ──
SKILL_NORMALIZATION_MAP: Dict[str, str] = {
    "java programming": "Java",
    "java development": "Java",
    "core java": "Java",
    "advanced java": "Java",
    "python programming": "Python",
    "python development": "Python",
    "python scripting": "Python",
    "c programming": "C",
    "c++ programming": "C++",
    "c# programming": "C#",
    "javascript programming": "JavaScript",
    "js": "JavaScript",
    "typescript programming": "TypeScript",
    "ts": "TypeScript",
    "sql programming": "SQL",
    "sql queries": "SQL",
    "sql database": "SQL",
    "sql server": "SQL Server",
    "mysql database": "MySQL",
    "postgres": "PostgreSQL",
    "postgresql database": "PostgreSQL",
    "mongo db": "MongoDB",
    "mongodb database": "MongoDB",
    "node js": "Node.js",
    "nodejs": "Node.js",
    "node.js development": "Node.js",
    "react js": "React",
    "reactjs": "React",
    "react.js": "React",
    "react development": "React",
    "angular js": "Angular",
    "angularjs": "Angular",
    "vue js": "Vue.js",
    "vuejs": "Vue.js",
    "next js": "Next.js",
    "nextjs": "Next.js",
    "express js": "Express.js",
    "expressjs": "Express.js",
    "spring boot framework": "Spring Boot",
    "spring framework": "Spring",
    "django framework": "Django",
    "flask framework": "Flask",
    "fast api": "FastAPI",
    "fastapi framework": "FastAPI",
    "amazon web services": "AWS",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "microsoft azure": "Azure",
    "docker containers": "Docker",
    "docker containerization": "Docker",
    "kubernetes orchestration": "Kubernetes",
    "k8s": "Kubernetes",
    "ci cd": "CI/CD",
    "ci/cd pipelines": "CI/CD",
    "continuous integration": "CI/CD",
    "continuous deployment": "CI/CD",
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "artificial intelligence": "AI",
    "natural language processing": "NLP",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful apis": "REST APIs",
    "restful api": "REST APIs",
    "restful services": "REST APIs",
    "html5": "HTML",
    "html css": "HTML/CSS",
    "css3": "CSS",
    "object oriented programming": "OOP",
    "oop concepts": "OOP",
    "data structures and algorithms": "Data Structures & Algorithms",
    "dsa": "Data Structures & Algorithms",
    "data structures": "Data Structures",
    "version control": "Git",
    "git version control": "Git",
    "github": "Git",
    "linux administration": "Linux",
    "linux/unix": "Linux",
    "agile methodology": "Agile",
    "agile development": "Agile",
    "scrum methodology": "Scrum",
    "unit testing": "Unit Testing",
    "test driven development": "TDD",
    "power bi": "Power BI",
    "tableau visualization": "Tableau",
    "scikit learn": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "numpy": "NumPy",
    "pandas": "Pandas",
    "data preprocessing": "Data Preprocessing",
    "model evaluation": "Model Evaluation",
    "feature engineering": "Feature Engineering",
    "mlops": "MLOps",
    "statistics": "Statistics",
    "data modeling": "Data Modeling",
    "hadoop": "Hadoop",
    "spark": "Spark",
    "apache spark": "Spark",
}

_NORM_LOOKUP: Dict[str, str] = {k.lower().strip(): v for k, v in SKILL_NORMALIZATION_MAP.items()}


def _normalize_skill_name(raw: str) -> str:
    cleaned = raw.strip()
    if not cleaned:
        return ""

    key = cleaned.lower()
    if key in _NORM_LOOKUP:
        return _NORM_LOOKUP[key]

    canonical = canonicalize_skill(cleaned)
    if canonical in _NORM_LOOKUP:
        return _NORM_LOOKUP[canonical]

    UPPERCASE_SKILLS = {
        "sql", "aws", "gcp", "html", "css", "nlp", "ai", "ml", "oop",
        "tdd", "cicd", "ci/cd", "sap", "erp", "crm", "api", "sdk",
        "jdbc", "jpa", "jvm", "xml", "json", "yaml", "http", "https",
        "tcp", "udp", "ssh", "dns", "ssl", "tls", "vpc", "iam",
    }
    if key in UPPERCASE_SKILLS:
        return cleaned.upper()

    if len(cleaned.split()) > 1:
        return cleaned.title()

    if cleaned != cleaned.lower() and cleaned != cleaned.upper():
        return cleaned

    return cleaned.title()


def _deduplicate_skills(skills: List[str]) -> List[str]:
    canonical_groups: Dict[str, Counter] = {}

    for skill in skills:
        normalized = _normalize_skill_name(skill)
        if not normalized:
            continue
        canon = normalized.lower().strip()
        if canon not in canonical_groups:
            canonical_groups[canon] = Counter()
        canonical_groups[canon][normalized] += 1

    result: List[Tuple[str, int]] = []
    for canon, counter in canonical_groups.items():
        best_form = counter.most_common(1)[0][0]
        total_count = sum(counter.values())
        result.append((best_form, total_count))

    result.sort(key=lambda x: x[1], reverse=True)
    return [form for form, _ in result]


class JobRetriever:
    """
    Role-Specific Job Requirement Retrieval Service.

    - Searches the dataset with high fidelity title matching
    - Isolates categories to prevent domain cross-contamination
    - Filters out generic soft skills & irrelevant administrative skills
    - Grounded with canonical technical skills for core roles
    """

    def retrieve_requirements(
        self,
        target_company: str,
        target_role: str,
        max_source_jobs: int = 10,
    ) -> JobRequirementsResponse:
        logger.info(
            f"Retrieving role-specific requirements for role='{target_role}' "
            f"(target_company='{target_company}' preserved as student context)"
        )

        role_clean = target_role.lower().strip()

        # Check for canonical role profile
        canonical_skills = self._get_canonical_skills(role_clean)

        scored_jobs = []
        if dataset_service.is_loaded and dataset_service.df is not None:
            scored_jobs = self._score_jobs(target_role)

        top_jobs = scored_jobs[:max_source_jobs]

        # Aggregate and filter skills from matched postings
        raw_skills = self._aggregate_skills(top_jobs, role_clean)

        # Build final required skills list
        # Start with canonical skills if available to ensure role accuracy
        final_skills: List[str] = []
        seen_lower = set()

        if canonical_skills:
            for s in canonical_skills:
                s_norm = _normalize_skill_name(s)
                if s_norm.lower() not in seen_lower:
                    seen_lower.add(s_norm.lower())
                    final_skills.append(s_norm)

        # Append unique valid skills from top matched jobs
        for s in raw_skills:
            s_norm = _normalize_skill_name(s)
            s_lower = s_norm.lower()
            if s_lower not in seen_lower:
                seen_lower.add(s_lower)
                final_skills.append(s_norm)

        # Cap at top 25 skills to keep requirements focused
        final_skills = final_skills[:25]

        # Build source job items for provenance
        max_score = top_jobs[0][0] if top_jobs else 1.0
        source_items = []
        for score, job in top_jobs:
            relevance = round((score / max(max_score, 1.0)) * 100, 1)
            source_items.append(SourceJobItem(
                job_id=job["job_id"],
                job_title=job["job_title"],
                category=job["category"],
                relevance_score=min(relevance, 100.0),
            ))

        logger.info(
            f"Retrieved {len(final_skills)} role-specific skills from "
            f"{len(top_jobs)} matched postings for role '{target_role}'."
        )

        return JobRequirementsResponse(
            target_company=target_company,
            target_role=target_role,
            matched_job_count=len(top_jobs),
            required_skills=final_skills,
            source_jobs=source_items,
        )

    def _get_canonical_skills(self, role_clean: str) -> Optional[List[str]]:
        """Look up canonical technical skills for well-known tech roles."""
        # Exact lookup
        if role_clean in ROLE_CANONICAL_SKILLS:
            return ROLE_CANONICAL_SKILLS[role_clean]

        # Partial matching
        if any(m in role_clean for m in ["ml engineer", "machine learning", "deep learning"]):
            return ROLE_CANONICAL_SKILLS["ml engineer"]
        if "data scientist" in role_clean:
            return ROLE_CANONICAL_SKILLS["data scientist"]
        if "data engineer" in role_clean:
            return ROLE_CANONICAL_SKILLS["data engineer"]
        if "backend" in role_clean:
            return ROLE_CANONICAL_SKILLS["backend developer"]
        if "frontend" in role_clean:
            return ROLE_CANONICAL_SKILLS["frontend developer"]
        if "full stack" in role_clean or "fullstack" in role_clean:
            return ROLE_CANONICAL_SKILLS["full stack developer"]
        if "devops" in role_clean:
            return ROLE_CANONICAL_SKILLS["devops engineer"]
        if "software engineer" in role_clean or "software developer" in role_clean:
            return ROLE_CANONICAL_SKILLS["software engineer"]

        return None

    def _score_jobs(self, target_role: str) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Score jobs with strict title priority and category isolation.
        Prevents mixing unrelated domains (e.g. Sales, HR, Procurement with ML Engineer).
        """
        role_clean = target_role.lower().strip()

        # Detect if target role is tech/engineering
        role_is_tech = any(t in role_clean for t in [
            "developer", "engineer", "software", "backend", "frontend",
            "full stack", "fullstack", "data", "devops", "cloud", "ml", "ai",
            "machine learning", "deep learning", "programmer", "architect", "scientist",
        ])

        # Define title keywords and content requirements based on role
        specialty_terms: List[str] = []
        if any(m in role_clean for m in ["ml", "machine learning", "deep learning", "ai"]):
            specialty_terms = ["machine learning", "deep learning", "data scientist", "data science", "ml", "ai", "data engineer"]
        elif "backend" in role_clean:
            specialty_terms = ["backend", "back end", "software engineer", "developer", "programmer", "api"]
        elif "frontend" in role_clean:
            specialty_terms = ["frontend", "front end", "ui", "web", "react", "developer"]
        elif "data engineer" in role_clean:
            specialty_terms = ["data engineer", "big data", "etl", "data"]
        elif "data scientist" in role_clean:
            specialty_terms = ["data scientist", "data science", "statistician"]

        # Anti-keywords in title for engineering roles (unless specifically in target_role)
        anti_keywords = [
            "sourcing", "procurement", "buyer", "contracts", "vendor", "sales", "retail",
            "intern", "trainee", "associate", "coordinator", "assistant", "auditor",
            "help desk", "technician", "customer service", "receptionist", "advisory",
            "specialist 1", "specialist 2", "account manager", "branch manager",
        ]
        if not any(k in role_clean for k in ["manager", "lead", "director"]):
            anti_keywords.extend(["manager", "director", "asset manager", "support specialist", "support technician"])

        scored: List[Tuple[float, Dict[str, Any]]] = []

        for job_id, job in dataset_service.jobs_by_id.items():
            cat = job["category"].upper()
            title = job["job_title"].lower()
            desc = job["job_description"].lower()
            skills_raw = job.get("raw_skill_set", "").lower()

            # 1. Strict Category Isolation
            if role_is_tech:
                # Disallow HR, SALES, BUSINESS-DEVELOPMENT for tech roles
                if cat in ["SALES", "HR", "BUSINESS-DEVELOPMENT"] and not any(k in role_clean for k in ["sales", "hr", "business"]):
                    continue
                # For FINANCE category, only allow if the job title is explicitly technical
                if cat == "FINANCE":
                    tech_in_title = any(w in title for w in ["software", "developer", "data scientist", "data engineer", "programmer"])
                    if not tech_in_title:
                        continue

            # 2. Anti-keyword filtering: discard jobs with administrative/procurement/sales titles
            if role_is_tech and any(ak in title for ak in anti_keywords):
                continue

            score = 0.0

            # 3. High-Priority Title Matching
            # Check for exact role in title
            if role_clean in title:
                score += 120.0

            # If role has a specialty (like ML, Backend, Data Science)
            if specialty_terms:
                has_specialty_in_job = False
                for term in specialty_terms:
                    pattern = r"\b" + re.escape(term) + r"\b"
                    if re.search(pattern, title):
                        score += 90.0
                        has_specialty_in_job = True
                    if re.search(pattern, skills_raw):
                        score += 35.0
                        has_specialty_in_job = True
                    if re.search(pattern, desc):
                        score += 15.0
                        has_specialty_in_job = True

                # For specialized roles, must have at least one specialty signal
                if not has_specialty_in_job:
                    continue
            else:
                # General token matching for non-specialized queries
                tokens = [w for w in re.split(r"\W+", role_clean) if len(w) >= 2]
                for t in tokens:
                    if t in title:
                        score += 40.0
                    if t in skills_raw:
                        score += 15.0
                    if t in desc:
                        score += 5.0

            # IT Category bonus for tech roles
            if role_is_tech and cat == "INFORMATION-TECHNOLOGY":
                score += 10.0

            # Only accept genuinely relevant matches (minimum score threshold)
            if score >= 35.0:
                scored.append((score, job))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def _aggregate_skills(
        self,
        scored_jobs: List[Tuple[float, Dict[str, Any]]],
        role_clean: str,
    ) -> List[str]:
        """
        Collect skills from matched jobs, filtering out:
        1. Generic soft skills (Communication, Teamwork, Problem Solving, etc.)
        2. Domain-unrelated skills (Vendor Management, Procurement, Network Configuration, etc.)
        """
        role_is_tech = any(t in role_clean for t in [
            "developer", "engineer", "software", "backend", "frontend",
            "full stack", "fullstack", "data", "devops", "cloud", "ml", "ai",
            "machine learning", "deep learning", "programmer", "architect", "scientist",
        ])

        filtered_skills: List[str] = []

        for _, job in scored_jobs:
            parsed = job.get("parsed_skills", [])
            if not isinstance(parsed, list):
                parsed = parse_skill_list(str(parsed))

            for skill in parsed:
                cleaned = str(skill).strip()
                if not cleaned or len(cleaned) <= 1:
                    continue

                lower_s = cleaned.lower().strip()

                # Rule 9 & 10: Suppress generic soft skills from dominating requirements
                if lower_s in GENERIC_SOFT_SKILLS:
                    continue

                # Filter out domain-unrelated blacklist for tech roles
                if role_is_tech and lower_s in UNRELATED_TECH_BLACKLIST:
                    continue

                # Filter out generic IT support/hardware phrases for developer/ML roles
                if any(m in role_clean for m in ["ml", "machine learning", "developer", "backend", "frontend", "software"]):
                    if any(bad in lower_s for bad in ["hardware", "inventory", "workstation", "switch", "firewall", "active directory", "help desk"]):
                        continue

                filtered_skills.append(cleaned)

        return _deduplicate_skills(filtered_skills)


# Module-level singleton
job_retriever = JobRetriever()
