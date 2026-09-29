from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class EducationItem(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None

class ExperienceItem(BaseModel):
    role: Optional[str] = None
    organization: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None

class ProjectItem(BaseModel):
    project_name: str
    description: str
    technologies: List[str] = Field(default_factory=list)
    role: Optional[str] = None
    evidence: Optional[str] = None

class SkillEvidenceItem(BaseModel):
    skill: str
    evidence_source: str = Field(
        description="Source where skill is evidenced, e.g. project title, experience, or education"
    )
    evidence_text: str = Field(
        description="Direct or derived excerpt demonstrating the skill application"
    )
    confidence: str = Field(
        default="medium",
        description="'high', 'medium', or 'low'"
    )

class StudentProfile(BaseModel):
    name: Optional[str] = None
    education: List[EducationItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)

class ResumeAnalysisResponse(BaseModel):
    """
    Complete structured resume analysis output.
    All fields return null or empty lists when not found in the resume (no hallucinations).
    """
    student_profile: StudentProfile
    student_name: Optional[str] = None
    technical_skills: List[str] = Field(default_factory=list)
    soft_skills: List[str] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)
    skill_evidence: List[SkillEvidenceItem] = Field(default_factory=list)
    resume_strengths: List[str] = Field(default_factory=list)
    resume_weaknesses: List[str] = Field(default_factory=list)

    # Context metadata
    target_company: Optional[str] = None
    target_role: Optional[str] = None

    model_config = {
        "extra": "ignore"
    }
