import json
import urllib.request

def test_api():
    print("Testing POST /api/jobs/analyze-requirements:")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/jobs/analyze-requirements",
        data=json.dumps({"target_role": "ML Engineer", "target_company": "Google"}).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"Status: {resp.status}")
        print("Target role:", data["target_role"])
        print("Matched job count:", data["matched_job_count"])
        print(f"Required skills count: {len(data['required_skills'])}")
        print("Sample skills:", data["required_skills"][:10])

test_api()
