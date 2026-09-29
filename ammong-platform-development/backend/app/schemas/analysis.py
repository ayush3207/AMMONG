from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.job import JobResponse

class SkillMatchItem(BaseModel):
    skill: str
    status: str = Field(description="'match' or 'partial'")

class SkillGapItem(BaseModel):
    skill: str
    priority: int

class WeaknessItem(BaseModel):
    title: str
    problem: str
    suggestion: str

class PlanItem(BaseModel):
    priority: int
    skill: str
    why: str
    action: str

class AnalysisRequest(BaseModel):
    company: str = Field(..., description="Target company, e.g. Google")
    role: str = Field(..., description="Target job role, e.g. Backend Developer")
    resume_text: Optional[str] = Field(None, description="Direct resume text if not uploading file")

class AnalysisResponse(BaseModel):
    """
    Structured placement intelligence analysis response.
    Supports both snake_case and camelCase field access for frontend convenience.
    """
    match_score: int
    target_company: str
    target_role: str
    matched_job: Optional[JobResponse] = None
    
    # Core placement intelligence
    what_you_have: List[SkillMatchItem]
    what_job_requires: List[str]
    skill_gaps: List[SkillGapItem]
    strong_matches: List[str]
    weaknesses: List[WeaknessItem]
    improvement_plan: List[PlanItem]
    resume_improvements: List[str]
    
    # Evidence extracted from resume
    student_extracted_skills: List[str]
    project_evidence: List[str]

    # CamelCase aliases for seamless frontend compatibility
    whatYouHave: Optional[List[SkillMatchItem]] = None
    whatJobRequires: Optional[List[str]] = None
    skillGaps: Optional[List[SkillGapItem]] = None
    strongMatches: Optional[List[str]] = None
    improvementPlan: Optional[List[PlanItem]] = None
    resumeImprovements: Optional[List[str]] = None
