"""
AMMONG MVP — Core Analysis Endpoint.

POST /api/analyze

Accepts a resume PDF and target_role.
Returns a single structured response showing:
  - Student skills extracted from the resume
  - Required skills from matching job postings
  - Skill comparison (match / partial / gap)
  - Profile-to-requirement match score
  - Short AI-generated summary
"""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.logging import logger
from app.schemas.ammong import AmmongAnalysisResponse
from app.services.dataset_service import dataset_service
from app.services.job_retriever import job_retriever
from app.services.llm_service import llm_service
from app.utils.resume_parser import parse_resume_bytes
from app.utils.text_normalizer import skills_match

router = APIRouter(tags=["AMMONG Analysis"])


@router.post(
    "/analyze",
    response_model=AmmongAnalysisResponse,
    summary="Analyze resume against target role requirements",
    description=(
        "Upload a resume PDF and specify a target role. "
        "AMMONG extracts your skills, finds relevant job requirements, "
        "compares them, and returns a clear match report."
    ),
)
async def analyze(
    file: UploadFile = File(..., description="Resume PDF file"),
    target_role: str = Form(..., description="Target job role, e.g. Backend Developer"),
):
    # ── 1. Validate file ──
    if not file or not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A resume PDF file must be uploaded.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.filename}'. Only PDF files are accepted.",
        )

    target_role = target_role.strip()
    if len(target_role) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="target_role must be at least 2 characters.",
        )

    # ── 2. Read file bytes ──
    try:
        file_bytes = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read the uploaded file.",
        )

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF file is empty.",
        )

    # ── 3. Extract text from PDF ──
    try:
        resume_text = parse_resume_bytes(file_bytes, file.filename)
    except Exception as e:
        logger.error(f"Error parsing PDF '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not read the PDF: {str(e)}",
        )

    if not resume_text or len(resume_text.strip()) < 20:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not extract readable text from the PDF. Ensure it contains selectable text.",
        )

    # ── 4. Extract student skills from resume (LLM with deterministic fallback) ──
    try:
        extracted = await llm_service.extract_student_profile(resume_text, target_role)
        student_skills = extracted.get("skills", [])
        projects = extracted.get("projects", [])
    except Exception as e:
        logger.error(f"Skill extraction failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract skills from the resume.",
        )

    # ── 5. Retrieve required skills from job dataset ──
    if not dataset_service.is_loaded:
        logger.warning("Job dataset not loaded — using empty requirements.")
        required_skills = []
        source_job_count = 0
    else:
        job_result = job_retriever.retrieve_requirements(
            target_company="",  # Dataset has no company field
            target_role=target_role,
            max_source_jobs=10,
        )
        required_skills = job_result.required_skills
        source_job_count = job_result.matched_job_count

    # ── 6. Compare: student skills vs required skills ──
    matching_skills = []
    partial_skills = []
    skill_gaps = []

    for req_skill in required_skills:
        best_match = "none"
        for s_skill in student_skills:
            result = skills_match(s_skill, req_skill)
            if result == "match":
                best_match = "match"
                break
            elif result == "partial" and best_match != "match":
                best_match = "partial"

        if best_match == "match":
            matching_skills.append(req_skill)
        elif best_match == "partial":
            partial_skills.append(req_skill)
        else:
            skill_gaps.append(req_skill)

    # ── 7. Calculate match score ──
    # MATCH = 1, PARTIAL = 0.5, GAP = 0
    total_required = len(required_skills)
    if total_required > 0:
        score_sum = len(matching_skills) * 1.0 + len(partial_skills) * 0.5
        match_score = int(round((score_sum / total_required) * 100))
        match_score = max(0, min(match_score, 100))
    else:
        match_score = 0

    # ── 8. Generate skill roadmap for gaps and partial skills ──
    try:
        roadmap_data = await llm_service.generate_skill_roadmap(
            skill_gaps=skill_gaps,
            partial_skills=partial_skills,
            target_role=target_role,
        )
    except Exception as e:
        logger.error(f"Roadmap generation failed: {e}", exc_info=True)
        roadmap_data = []

    # ── 9. Generate summary ──
    summary = _build_summary(
        target_role=target_role,
        match_score=match_score,
        matching_skills=matching_skills,
        partial_skills=partial_skills,
        skill_gaps=skill_gaps,
    )

    return AmmongAnalysisResponse(
        target_role=target_role,
        match_score=match_score,
        student_skills=student_skills,
        required_skills=required_skills,
        matching_skills=matching_skills,
        partial_skills=partial_skills,
        skill_gaps=skill_gaps,
        skill_roadmap=roadmap_data,
        source_job_count=source_job_count,
        summary=summary,
    )


def _build_summary(
    target_role: str,
    match_score: int,
    matching_skills: list,
    partial_skills: list,
    skill_gaps: list,
) -> str:
    """Generate a concise, honest summary of the analysis."""
    parts = []

    if matching_skills:
        top = matching_skills[:4]
        joined = ", ".join(top)
        if len(matching_skills) > 4:
            joined += f" and {len(matching_skills) - 4} more"
        parts.append(f"Your profile demonstrates clear strength in {joined}.")

    if partial_skills:
        parts.append(
            f"You show related experience in {', '.join(partial_skills[:3])}, "
            f"but these skills could be demonstrated more clearly."
        )

    if skill_gaps:
        top_gaps = skill_gaps[:3]
        parts.append(
            f"The main gaps identified for {target_role} are {', '.join(top_gaps)}."
        )

    if match_score >= 80:
        parts.append("Your profile aligns well with the target role requirements.")
    elif match_score >= 50:
        parts.append("You have a solid foundation — focus on filling the identified gaps.")
    elif match_score > 0:
        parts.append("There are significant gaps to address for this target role.")
    else:
        parts.append("No matching job requirements were found for this role in the dataset.")

    return " ".join(parts)
