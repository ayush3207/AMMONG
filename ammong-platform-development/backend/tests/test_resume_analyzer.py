"""
AMMONG Resume Analysis Layer — Comprehensive Test Suite

Tests:
  1. Valid PDF upload → structured extraction verified
  2. Invalid file type (.png, .txt) → 400 Bad Request
  3. Empty resume (0-byte, whitespace-only) → 400/422
  4. Malformed LLM response → graceful fallback recovery
  5. Missing fields (no education/experience/certs) → null/empty arrays returned
"""

import io
import json
import sys
import urllib.request
from urllib.error import HTTPError

BASE_URL = "http://127.0.0.1:8000"

# ────────────────────────────────────────────────
#  Helpers
# ────────────────────────────────────────────────

def make_pdf_bytes(text_content):
    """Build a minimal valid PDF containing the given text string."""
    # Escape parentheses for PDF text object
    safe = text_content.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 10 Tf 50 700 Td ({safe}) Tj ET"
    slen = len(stream)
    raw = (
        "%PDF-1.4\n"
        "1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        "2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        "3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Contents 4 0 R /Resources <</Font <</F1 5 0 R>>>>>> endobj\n"
        f"4 0 obj <</Length {slen}>> stream\n{stream}\nendstream endobj\n"
        "5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        "xref\n0 6\n"
        "0000000000 65535 f \n"
        "0000000010 00000 n \n"
        "0000000060 00000 n \n"
        "0000000117 00000 n \n"
        "0000000300 00000 n \n"
        "0000000400 00000 n \n"
        "trailer <</Size 6 /Root 1 0 R>>\n"
        "startxref\n450\n%%EOF"
    )
    return raw.encode("latin-1")


def post_multipart(path, fields, files):
    """Send a multipart/form-data POST request to the backend."""
    boundary = "----AMMONGTestBoundary9876"
    body = bytearray()

    for key, val in fields.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
        body += f"{val}\r\n".encode()

    for key, (fname, content, ctype) in files.items():
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{key}"; filename="{fname}"\r\n'.encode()
        body += f"Content-Type: {ctype}\r\n\r\n".encode()
        body += content
        body += b"\r\n"

    body += f"--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=bytes(body),
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode())
    except HTTPError as e:
        err_body = e.read().decode()
        try:
            return e.code, json.loads(err_body)
        except Exception:
            return e.code, {"detail": err_body}


# ────────────────────────────────────────────────
#  Test 1 — Valid PDF
# ────────────────────────────────────────────────

def test_valid_pdf():
    resume_text = (
        "John Doe  "
        "Bachelor of Technology in Computer Science, XYZ University, 2025  "
        "Technical Skills: Python, Java, SQL, Docker, FastAPI, React, Git  "
        "Projects:  "
        "E-Commerce Platform: Built microservices backend using FastAPI and PostgreSQL. "
        "Handled 500 concurrent users.  "
        "Chat Application: Real-time messaging with WebSockets deployed on AWS.  "
        "Experience:  "
        "Software Intern at Acme Corp, Jan-Jun 2024. Built internal REST APIs."
    )
    pdf = make_pdf_bytes(resume_text)

    code, data = post_multipart(
        "/api/analyze/resume",
        fields={"target_company": "Google", "target_role": "Backend Developer"},
        files={"file": ("john_doe_resume.pdf", pdf, "application/pdf")},
    )

    assert code == 200, f"Expected 200, got {code}: {data}"

    # ---- Schema structure checks ----
    sp = data.get("student_profile", {})
    assert sp is not None, "student_profile missing"
    assert isinstance(sp.get("education"), list)
    assert isinstance(sp.get("experience"), list)

    assert isinstance(data.get("technical_skills"), list)
    assert len(data["technical_skills"]) > 0, "Expected at least one technical skill"
    assert isinstance(data.get("skills"), list)
    assert isinstance(data.get("projects"), list)
    assert isinstance(data.get("skill_evidence"), list)
    assert isinstance(data.get("resume_strengths"), list)
    assert isinstance(data.get("resume_weaknesses"), list)
    assert len(data["resume_weaknesses"]) > 0

    # ---- Project item structure ----
    if data["projects"]:
        p = data["projects"][0]
        assert "project_name" in p
        assert "description" in p
        assert "technologies" in p

    # ---- Skill evidence item structure ----
    if data["skill_evidence"]:
        e = data["skill_evidence"][0]
        assert "skill" in e
        assert "evidence_source" in e
        assert "evidence_text" in e
        assert e.get("confidence") in ("high", "medium", "low")

    print("[PASS] Test 1: Valid PDF — structured extraction with correct schema.")


# ────────────────────────────────────────────────
#  Test 2 — Invalid file type
# ────────────────────────────────────────────────

def test_invalid_file():
    # .png upload
    code, data = post_multipart(
        "/api/analyze/resume",
        fields={"target_company": "Google", "target_role": "SDE"},
        files={"file": ("photo.png", b"\x89PNG\r\n\x1a\n", "image/png")},
    )
    assert code == 400, f"Expected 400 for .png, got {code}"
    assert "Only PDF" in data.get("detail", "")

    # .txt upload
    code2, data2 = post_multipart(
        "/api/analyze/resume",
        fields={"target_company": "Microsoft", "target_role": "SWE"},
        files={"file": ("resume.txt", b"plain text resume", "text/plain")},
    )
    assert code2 == 400, f"Expected 400 for .txt, got {code2}"
    assert "Only PDF" in data2.get("detail", "")

    # .exe upload
    code3, data3 = post_multipart(
        "/api/analyze/resume",
        fields={"target_company": "TCS", "target_role": "Dev"},
        files={"file": ("virus.exe", b"MZ\x00\x00", "application/octet-stream")},
    )
    assert code3 == 400, f"Expected 400 for .exe, got {code3}"

    print("[PASS] Test 2: Invalid file types (.png, .txt, .exe) correctly rejected with 400.")


# ────────────────────────────────────────────────
#  Test 3 — Empty resume
# ────────────────────────────────────────────────

def test_empty_resume():
    # 0-byte file
    code, data = post_multipart(
        "/api/analyze/resume",
        fields={"target_company": "Google", "target_role": "SDE"},
        files={"file": ("empty.pdf", b"", "application/pdf")},
    )
    assert code == 400, f"Expected 400 for empty PDF, got {code}"
    assert "empty" in data.get("detail", "").lower()

    # PDF with extremely short text (< 20 chars)
    tiny = make_pdf_bytes("Hi")
    code2, data2 = post_multipart(
        "/api/analyze/resume",
        fields={"target_company": "Google", "target_role": "SDE"},
        files={"file": ("tiny.pdf", tiny, "application/pdf")},
    )
    assert code2 == 422, f"Expected 422 for tiny PDF, got {code2}"
    assert "extract" in data2.get("detail", "").lower() or "readable" in data2.get("detail", "").lower()

    print("[PASS] Test 3: Empty / unextractable PDFs rejected with 400/422.")


# ────────────────────────────────────────────────
#  Test 4 — Malformed LLM response (service unit test)
# ────────────────────────────────────────────────

def test_malformed_llm_response():
    """
    Verify the ResumeAnalyzer falls back to deterministic extraction
    when the LLM returns non-JSON garbage. We test the service directly.
    """
    import asyncio
    from unittest.mock import AsyncMock

    # Add backend to path so we can import the service
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    from app.services.resume_analyzer import ResumeAnalyzer
    from app.schemas.resume_analysis import ResumeAnalysisResponse

    analyzer = ResumeAnalyzer()

    # Simulate an LLM client that returns non-JSON text
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_choice.message.content = "This is NOT valid JSON at all {{{broken"
    mock_response.choices = [mock_choice]

    analyzer.client = AsyncMock()
    analyzer.client.chat = AsyncMock()
    analyzer.client.chat.completions = AsyncMock()
    analyzer.client.chat.completions.create = AsyncMock(return_value=mock_response)

    resume = (
        "Alice Smith\n"
        "Skills: Python, Java, SQL, Git\n"
        "Projects:\n"
        "- Library System: Built CRUD app with Python and PostgreSQL\n"
    )

    # Patch LLM_API_KEY so the service tries the LLM path first
    import app.core.config as cfg
    original_key = cfg.settings.LLM_API_KEY
    cfg.settings.LLM_API_KEY = "fake-key-for-test"

    try:
        result = asyncio.run(analyzer.analyze_resume(resume, "Amazon", "Software Engineer"))
    finally:
        cfg.settings.LLM_API_KEY = original_key

    assert isinstance(result, ResumeAnalysisResponse)
    assert len(result.technical_skills) > 0, "Fallback should still detect skills"
    assert len(result.resume_weaknesses) > 0
    assert result.target_company == "Amazon"
    assert result.target_role == "Software Engineer"

    print("[PASS] Test 4: Malformed LLM response handled — fell back to deterministic extraction.")


# ────────────────────────────────────────────────
#  Test 5 — Missing fields in resume
# ────────────────────────────────────────────────

def test_missing_fields():
    """
    A resume with ONLY skills and one project line.
    Verify education, experience, certifications, achievements return empty.
    """
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    from app.services.resume_analyzer import ResumeAnalyzer

    analyzer = ResumeAnalyzer()

    sparse_resume = (
        "Skills: Python, Git\n"
        "Projects:\n"
        "- Calculator App: Built simple arithmetic calculator in Python\n"
    )
    data = analyzer._deterministic_extract(sparse_resume, "TCS", "Developer")
    result = analyzer._build_pydantic_response(data, "TCS", "Developer")

    # Missing sections → empty lists, not fabricated data
    assert result.student_profile.education == [], f"Expected empty education, got {result.student_profile.education}"
    assert result.student_profile.experience == [], f"Expected empty experience, got {result.student_profile.experience}"
    assert result.certifications == []
    assert result.achievements == []
    # Skills and weaknesses should still be present
    assert isinstance(result.skills, list)
    assert isinstance(result.resume_weaknesses, list)
    assert len(result.resume_weaknesses) > 0

    print("[PASS] Test 5: Missing fields correctly returned as null/empty arrays — no hallucination.")


# ────────────────────────────────────────────────
#  Runner
# ────────────────────────────────────────────────

def main():
    print("=" * 56)
    print("  AMMONG RESUME ANALYSIS LAYER — TEST SUITE")
    print("=" * 56)

    test_valid_pdf()
    test_invalid_file()
    test_empty_resume()
    test_malformed_llm_response()
    test_missing_fields()

    print()
    print("=" * 56)
    print("  ALL 5 TESTS PASSED SUCCESSFULLY")
    print("=" * 56)


if __name__ == "__main__":
    main()
