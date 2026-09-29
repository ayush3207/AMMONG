import io
import json
import urllib.request
import urllib.parse
from urllib.error import HTTPError

BASE_URL = "http://127.0.0.1:8000"

def get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def post_json(path, payload):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def post_multipart(path, fields, files):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = bytearray()

    for k, v in fields.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        body.extend(f"{v}\r\n".encode())

    for k, (filename, content, content_type) in files.items():
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(f'Content-Disposition: form-data; name="{k}"; filename="{filename}"\r\n'.encode())
        body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
        body.extend(content)
        body.extend(b"\r\n")

    body.extend(f"--{boundary}--\r\n".encode())

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def run_tests():
    print("========================================")
    print("      AMMONG BACKEND ENDPOINT TESTS     ")
    print("========================================")

    # 1. Health check
    status, res = get("/api/health")
    assert status == 200, f"Expected 200, got {status}"
    assert res.get("status") == "ok", f"Expected ok, got {res}"
    print(f"[PASS] GET /api/health -> {res}")

    # 2. Stats check
    status, res = get("/api/jobs/stats")
    assert status == 200
    assert res.get("total_jobs") == 1167, f"Expected 1167, got {res.get('total_jobs')}"
    assert res.get("successfully_loaded") is True
    print(f"[PASS] GET /api/jobs/stats -> total={res.get('total_jobs')}, categories={len(res.get('categories', {}))}")

    # 3. Jobs listing with pagination & category
    status, res = get("/api/jobs?category=INFORMATION-TECHNOLOGY&page=1&page_size=5")
    assert status == 200
    assert res.get("total") == 240, f"Expected 240 IT jobs, got {res.get('total')}"
    assert len(res.get("jobs")) == 5
    print(f"[PASS] GET /api/jobs (filter) -> total={res.get('total')}, page={res.get('page')}, returned={len(res.get('jobs'))}")

    # 4. Search jobs
    status, res = get("/api/jobs?search=python&page=1&page_size=3")
    assert status == 200
    print(f"[PASS] GET /api/jobs (search) -> total matching 'python': {res.get('total')}")

    # 5. Get single job by ID
    sample_job_id = res["jobs"][0]["job_id"]
    status, res = get(f"/api/jobs/{sample_job_id}")
    assert status == 200
    assert res.get("job_id") == sample_job_id
    assert "job_title" in res
    assert "job_description" in res
    assert "job_skill_set" in res
    print(f"[PASS] GET /api/jobs/{sample_job_id} -> title='{res.get('job_title')}' (preserved fields intact)")

    # 6. JSON placement analysis
    sample_resume = """
    Jane Smith
    Email: jane.smith@example.com
    Summary: Final year Computer Science student seeking Backend Developer roles.
    
    Technical Skills:
    Languages: Python, Java, SQL, TypeScript
    Frameworks & Tools: FastAPI, Spring Boot, Docker, Git, REST APIs, PostgreSQL
    
    Projects:
    - Distributed Task Queue: Implemented asynchronous worker system using Python, Redis and PostgreSQL.
    - Cloud Microservices App: Containerized multi-tier web service using Docker and deployed on AWS.
    """
    status, res = post_json("/api/analyze/json", {
        "company": "Google",
        "role": "Backend Developer",
        "resume_text": sample_resume
    })
    assert status == 200
    assert "match_score" in res
    assert "what_you_have" in res
    assert "skill_gaps" in res
    assert "weaknesses" in res
    assert "improvement_plan" in res
    print(f"[PASS] POST /api/analyze/json -> Match Score: {res.get('match_score')}%")
    print(f"       Extracted Skills: {res.get('student_extracted_skills')}")
    print(f"       Skill Gaps: {[g['skill'] for g in res.get('skill_gaps', [])]}")
    print(f"       Weaknesses: {len(res.get('weaknesses', []))} items")
    print(f"       Plan: {len(res.get('improvement_plan', []))} priority actions")

    # 7. Multipart File Upload analysis (simulating PDF / text upload)
    file_content = sample_resume.encode("utf-8")
    status, res = post_multipart(
        "/api/analyze",
        fields={"company": "Microsoft", "role": "Software Engineer"},
        files={"file": ("resume.txt", file_content, "text/plain")}
    )
    assert status == 200
    assert "match_score" in res
    print(f"[PASS] POST /api/analyze (multipart upload) -> Match Score: {res.get('match_score')}% for {res.get('target_company')} - {res.get('target_role')}")

    print("\nALL BACKEND API TESTS PASSED PERFECTLY!")

if __name__ == "__main__":
    run_tests()
