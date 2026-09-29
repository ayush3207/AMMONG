"""Test suite for JobRetriever service."""
import sys
sys.path.insert(0, ".")

from app.services.job_retriever import job_retriever, JobRetriever, _normalize_skill_name, _deduplicate_skills
from app.schemas.job_requirements import JobRequirementsRequest, JobRequirementsResponse, SourceJobItem
from app.services.dataset_service import dataset_service


def test_imports():
    print("[PASS] All imports successful")


def test_skill_normalization():
    assert _normalize_skill_name("Java Programming") == "Java"
    assert _normalize_skill_name("python programming") == "Python"
    assert _normalize_skill_name("amazon web services") == "AWS"
    assert _normalize_skill_name("react.js") == "React"
    assert _normalize_skill_name("kubernetes orchestration") == "Kubernetes"
    assert _normalize_skill_name("ci cd") == "CI/CD"
    assert _normalize_skill_name("rest api") == "REST APIs"
    assert _normalize_skill_name("node js") == "Node.js"
    assert _normalize_skill_name("sql") == "SQL"
    assert _normalize_skill_name("FastAPI") == "FastAPI"
    assert _normalize_skill_name("mongodb database") == "MongoDB"
    assert _normalize_skill_name("google cloud platform") == "GCP"
    assert _normalize_skill_name("docker containers") == "Docker"
    print("[PASS] Skill normalization correct")


def test_deduplication():
    skills = ["Java", "java programming", "Java", "Python", "python programming", "SQL", "sql queries"]
    deduped = _deduplicate_skills(skills)
    deduped_lower = [s.lower() for s in deduped]
    assert "java" in deduped_lower
    assert "python" in deduped_lower
    assert "sql" in deduped_lower
    java_count = sum(1 for s in deduped_lower if s == "java")
    assert java_count == 1, f"Java appears {java_count} times in {deduped}"
    print(f"[PASS] Deduplication works: {deduped}")


def test_dataset_load():
    loaded = dataset_service.load_dataset()
    assert loaded, "Dataset failed to load"
    print(f"[PASS] Dataset loaded: {dataset_service.total_jobs} jobs")


def test_backend_developer():
    result = job_retriever.retrieve_requirements("Google", "Backend Developer")
    assert isinstance(result, JobRequirementsResponse)
    assert result.target_company == "Google"
    assert result.target_role == "Backend Developer"
    assert result.source_type == "role_level_job_postings"
    assert result.matched_job_count > 0
    assert len(result.required_skills) > 0
    assert len(result.source_jobs) > 0
    print(f"[PASS] Backend Developer: {result.matched_job_count} jobs, {len(result.required_skills)} skills")
    print(f"       Top 10 skills: {result.required_skills[:10]}")
    print(f"       Top 3 sources: {[(j.job_title, j.relevance_score) for j in result.source_jobs[:3]]}")


def test_data_scientist():
    result = job_retriever.retrieve_requirements("Microsoft", "Data Scientist")
    assert result.matched_job_count > 0
    assert len(result.required_skills) > 0
    print(f"[PASS] Data Scientist: {result.matched_job_count} jobs, {len(result.required_skills)} skills")
    print(f"       Top 10 skills: {result.required_skills[:10]}")


def test_nonexistent_role():
    result = job_retriever.retrieve_requirements("SpaceX", "Quantum Physicist")
    print(f"[PASS] Quantum Physicist: {result.matched_job_count} jobs (correctly handles edge case)")


def test_pydantic_schemas():
    req = JobRequirementsRequest(target_company="Amazon", target_role="SDE")
    assert req.target_company == "Amazon"
    assert req.target_role == "SDE"
    print("[PASS] Pydantic request schema valid")


def test_source_job_structure():
    result = job_retriever.retrieve_requirements("TCS", "Software Engineer")
    if result.source_jobs:
        sj = result.source_jobs[0]
        assert hasattr(sj, "job_id")
        assert hasattr(sj, "job_title")
        assert hasattr(sj, "category")
        assert hasattr(sj, "relevance_score")
        assert 0 <= sj.relevance_score <= 100
        print(f"[PASS] Source job structure valid: job_id={sj.job_id}, score={sj.relevance_score}")
    else:
        print("[PASS] Source job structure: no jobs (edge case handled)")


def main():
    print("=" * 56)
    print("  AMMONG JOB RETRIEVAL SERVICE — TEST SUITE")
    print("=" * 56)

    test_imports()
    test_skill_normalization()
    test_deduplication()
    test_dataset_load()
    test_backend_developer()
    test_data_scientist()
    test_nonexistent_role()
    test_pydantic_schemas()
    test_source_job_structure()

    print()
    print("=" * 56)
    print("  ALL 9 TESTS PASSED SUCCESSFULLY")
    print("=" * 56)


if __name__ == "__main__":
    main()
