from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.core.logging import logger
from app.schemas.job import JobResponse, JobsListResponse, JobStatsResponse
from app.schemas.job_requirements import JobRequirementsRequest, JobRequirementsResponse
from app.services.dataset_service import dataset_service
from app.services.job_retriever import job_retriever

router = APIRouter(prefix="/jobs", tags=["Jobs Knowledge Base"])

@router.get(
    "/stats",
    response_model=JobStatsResponse,
    summary="Get dataset statistics",
    description="Returns total job count, category distribution, and dataset loading status.",
)
async def get_job_stats():
    """Returns dataset summary information."""
    return dataset_service.get_stats()

@router.get(
    "",
    response_model=JobsListResponse,
    summary="Search and list job postings",
    description="Query jobs with free-text search, category filter, job title filter, and pagination.",
)
async def get_jobs(
    search: Optional[str] = Query(None, description="Search term for title, description, or skills"),
    category: Optional[str] = Query(None, description="Filter by category (e.g. INFORMATION-TECHNOLOGY)"),
    job_title: Optional[str] = Query(None, description="Filter by job title"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
):
    try:
        return dataset_service.get_jobs(
            search=search,
            category=category,
            job_title=job_title,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        logger.error(f"Error querying jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve jobs from knowledge base.",
        )

@router.get(
    "/{job_id}",
    response_model=JobResponse,
    summary="Get single job by ID",
    description="Returns exact original dataset fields: job_id, category, job_title, job_description, job_skill_set.",
)
async def get_job(job_id: int):
    job = dataset_service.get_job_by_id(job_id)
    if not job:
        logger.warning(f"Job with id {job_id} not found.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job posting with ID {job_id} was not found.",
        )
    return job


@router.post(
    "/analyze-requirements",
    response_model=JobRequirementsResponse,
    summary="Retrieve aggregated job requirements for a target role",
    description=(
        "Searches the job postings dataset by target_role, ranks relevant postings, "
        "aggregates their skills, normalizes duplicates, and returns structured role-level "
        "requirements. NOTE: The dataset has no company column — requirements are role-level, "
        "not company-specific."
    ),
)
async def analyze_requirements(payload: JobRequirementsRequest):
    if not payload.target_role or len(payload.target_role.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_role must be at least 2 characters.",
        )

    if not dataset_service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Job requirements dataset is not loaded. Please try again later.",
        )

    try:
        result = job_retriever.retrieve_requirements(
            target_company=payload.target_company.strip(),
            target_role=payload.target_role.strip(),
        )
        return result
    except Exception as e:
        logger.error(f"Error retrieving job requirements: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve job requirements: {str(e)}",
        )
