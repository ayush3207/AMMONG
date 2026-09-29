"""
AMMONG MVP — Pydantic schemas for the core analysis response.

One simple response that answers:
"How well do my current skills match what the target job requires,
and what skills am I missing?"
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SkillRoadmapItem(BaseModel):
    """Practical learning roadmap for a weak or missing skill."""

    skill: str
    status: str = Field(
        description="'Missing' for complete gaps or 'Needs Improvement' for partial skills.",
    )
    priority: str = Field(
        description="Suggested learning priority: 'High', 'Medium', or 'Low'.",
    )
    why_required: str = Field(
        description="Why this skill is required for the target role.",
    )
    learning_steps: List[str] = Field(
        default_factory=list,
        description="Step-by-step learning progression from beginner to job-ready.",
    )
    steps: List[str] = Field(
        default_factory=list,
        description="Alias for learning_steps for backwards compatibility.",
    )
    topics: List[str] = Field(
        default_factory=list,
        description="Key recommended topics to study.",
    )
    practice_project: str = Field(
        description="A practical, hands-on mini project to solidify the skill.",
    )
    estimated_duration: str = Field(
        description="Estimated duration to reach job readiness (e.g. '5-7 days', '2 weeks').",
    )


class AmmongAnalysisResponse(BaseModel):
    """
    The single AMMONG analysis result.

    match_score is a profile-to-job-requirement match, NOT a hiring probability.
    """

    target_role: str

    match_score: int = Field(
        description="Profile-to-requirement match percentage (0-100). NOT a hiring probability."
    )

    student_skills: List[str] = Field(
        default_factory=list,
        description="Skills identified in the student's resume.",
    )

    required_skills: List[str] = Field(
        default_factory=list,
        description="Skills required by relevant job postings for the target role.",
    )

    matching_skills: List[str] = Field(
        default_factory=list,
        description="Skills clearly present in both the resume and job requirements.",
    )

    partial_skills: List[str] = Field(
        default_factory=list,
        description="Required skills with related evidence in the resume but not an exact match.",
    )

    skill_gaps: List[str] = Field(
        default_factory=list,
        description="Required skills NOT found in the resume.",
    )

    skill_roadmap: List[SkillRoadmapItem] = Field(
        default_factory=list,
        description="Practical learning roadmap for identified skill gaps and partial skills.",
    )

    source_job_count: int = Field(
        default=0,
        description="Number of relevant job postings used to derive requirements.",
    )

    summary: str = Field(
        default="",
        description="Short AI-generated explanation of the analysis result.",
    )

    model_config = {"extra": "ignore"}

