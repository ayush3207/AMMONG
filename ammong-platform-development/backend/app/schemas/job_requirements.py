from typing import List, Optional
from pydantic import BaseModel, Field


class SourceJobItem(BaseModel):
    """A single job posting that contributed to the aggregated requirements."""
    job_id: int
    job_title: str
    category: str
    relevance_score: float = Field(
        description="0-100 relevance score against the target role"
    )


class JobRequirementsRequest(BaseModel):
    target_company: str = Field(..., description="Student's target company (preserved as-is)")
    target_role: str = Field(..., description="Target job role used for retrieval")


class JobRequirementsResponse(BaseModel):
    """
    Aggregated job requirements retrieved from the dataset.

    IMPORTANT DATA LIMITATION:
    The dataset does NOT contain a company field.
    source_type is always 'role_level_job_postings' — these are role-level
    requirements derived from matching job postings, NOT company-specific data.
    """
    target_company: str
    target_role: str
    source_type: str = Field(
        default="role_level_job_postings",
        description=(
            "Always 'role_level_job_postings'. The dataset has no company column, "
            "so requirements come from role-level job postings, not company-specific data."
        ),
    )
    matched_job_count: int = Field(description="Number of relevant job postings found")
    required_skills: List[str] = Field(
        default_factory=list,
        description="Deduplicated, normalized skills aggregated from matched postings",
    )
    source_jobs: List[SourceJobItem] = Field(
        default_factory=list,
        description="Job postings used as sources, ordered by relevance",
    )
