import io
import re
from typing import Optional
from pypdf import PdfReader
from docx import Document
from app.core.logging import logger

def parse_resume_bytes(file_bytes: bytes, filename: str) -> str:
    """
    Extract readable text from uploaded resume bytes (PDF, DOCX, TXT).
    """
    ext = filename.lower().split(".")[-1] if "." in filename else "txt"
    text = ""

    try:
        if ext == "pdf":
            reader = PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    pages_text.append(extracted)
            text = "\n".join(pages_text)

        elif ext in ["docx", "doc"]:
            doc = Document(io.BytesIO(file_bytes))
            paras = [p.text for p in doc.paragraphs if p.text]
            for table in doc.tables:
                for row in table.rows:
                    paras.extend([cell.text.strip() for cell in row.cells if cell.text.strip()])
            text = "\n".join(paras)

        else:
            # Plain text fallback
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = file_bytes.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
    except Exception as e:
        logger.error(f"Error parsing resume file '{filename}': {e}")
        # Try fallback decode
        try:
            text = file_bytes.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

    return clean_extracted_text(text)

def clean_extracted_text(text: str) -> str:
    """Normalize whitespace and remove non-printable characters."""
    if not text:
        return ""
    # Normalize multiple newlines and spaces
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
