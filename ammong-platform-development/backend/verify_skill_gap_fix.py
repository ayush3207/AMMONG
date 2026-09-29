import asyncio
import sys
sys.path.insert(0, '.')

from app.services.dataset_service import dataset_service
from app.services.job_retriever import job_retriever
from app.services.llm_service import llm_service
from app.utils.text_normalizer import skills_match

dataset_service.load_dataset()

# Test 1: Requirements for ML Engineer
req_res = job_retriever.retrieve_requirements("", "ML Engineer")
req_skills = req_res.required_skills
print("==================================================")
print("TEST 1: ML Engineer Required Skills")
print("==================================================")
print(f"Total skills: {len(req_skills)}")
for s in req_skills:
    print(f" - {s}")

# Unwanted skills check
unwanted = [
    "Vendor Management", "Contract Management", "Procurement Policies",
    "RFP Management", "Budget Management", "Customer Service",
    "SQL Server Administration", "Network Configuration", "Cyber Defense",
    "Communication", "Problem Solving", "Teamwork"
]
found_unwanted = [u for u in unwanted if any(u.lower() == s.lower() for s in req_skills)]
print(f"\nUnwanted skills found: {found_unwanted}")
assert len(found_unwanted) == 0, f"Found unwanted skills: {found_unwanted}"

# Expected skills check
expected = [
    "Python", "Machine Learning", "Deep Learning", "NumPy", "Pandas",
    "Scikit-learn", "TensorFlow", "PyTorch", "SQL", "Statistics",
    "Data Preprocessing", "Model Evaluation", "Feature Engineering", "Git", "MLOps"
]
found_expected = [e for e in expected if any(e.lower() == s.lower() for s in req_skills)]
print(f"Found {len(found_expected)}/{len(expected)} expected core ML skills: {found_expected}")
assert len(found_expected) >= 12, "Core ML skills missing!"

# Test 2: Comparison with sample resume
print("\n==================================================")
print("TEST 2: Comparison & Skill Gaps")
print("==================================================")
student_skills = ["Python", "SQL", "Git", "Machine Learning", "Pandas", "NumPy"]
print(f"Student Skills: {student_skills}")

matching_skills = []
partial_skills = []
skill_gaps = []

for req_skill in req_skills:
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

print(f"Matching Skills ({len(matching_skills)}): {matching_skills}")
print(f"Partial Skills ({len(partial_skills)}): {partial_skills}")
print(f"Skill Gaps ({len(skill_gaps)}): {skill_gaps}")

# Verify no unwanted skills in gaps
gaps_unwanted = [u for u in unwanted if any(u.lower() == g.lower() for g in skill_gaps)]
assert len(gaps_unwanted) == 0, f"Unwanted skills in gaps: {gaps_unwanted}"

# Test 3: Skill Roadmap Generation
print("\n==================================================")
print("TEST 3: Skill Roadmap Generation")
print("==================================================")
async def test_roadmap():
    roadmap = await llm_service.generate_skill_roadmap(
        skill_gaps=skill_gaps,
        partial_skills=partial_skills,
        target_role="ML Engineer"
    )
    print(f"Generated {len(roadmap)} roadmap items.")
    for item in roadmap[:3]:
        print(f"\nSkill: {item['skill']}")
        print(f"Status: {item['status']}")
        print(f"Priority: {item['priority']}")
        print(f"Why: {item['why_required']}")
        print(f"Steps count: {len(item.get('learning_steps', []))}")
        print(f"Practice Project: {item['practice_project']}")
        print(f"Duration: {item['estimated_duration']}")

        assert item["status"] in ["Missing", "Needs Improvement"]
        assert item["priority"] in ["High", "Medium", "Low"]
        assert len(item.get("learning_steps", [])) >= 3
        assert len(item.get("steps", [])) >= 3
        assert len(item.get("topics", [])) >= 3
        assert item["practice_project"]
        assert item["estimated_duration"]

asyncio.run(test_roadmap())
print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")
