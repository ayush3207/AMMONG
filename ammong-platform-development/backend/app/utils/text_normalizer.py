import ast
import json
import re
from typing import List, Set

def parse_skill_list(skill_raw: str) -> List[str]:
    """
    Parse string representation of skills list (e.g. "['python', 'sql']" or comma separated)
    into a clean list of individual skills.
    """
    if not skill_raw or not isinstance(skill_raw, str):
        return []

    cleaned = skill_raw.strip()
    
    # Check if it looks like a Python list or JSON array
    if cleaned.startswith("[") and cleaned.endswith("]"):
        try:
            parsed = ast.literal_eval(cleaned)
            if isinstance(parsed, list):
                return [str(s).strip() for s in parsed if str(s).strip()]
        except Exception:
            pass
        try:
            parsed = json.loads(cleaned.replace("'", '"'))
            if isinstance(parsed, list):
                return [str(s).strip() for s in parsed if str(s).strip()]
        except Exception:
            pass
        # Fallback regex extraction between quotes
        matches = re.findall(r"['\"](.*?)['\"]", cleaned)
        if matches:
            return [m.strip() for m in matches if m.strip()]

    # Fallback to comma separation
    parts = re.split(r"[,;|]\s*", cleaned)
    return [p.strip() for p in parts if p.strip()]

def normalize_skill(skill: str) -> str:
    """Normalize skill name for robust matching."""
    if not skill:
        return ""
    normalized = skill.lower().strip()
    # Remove common extra punct
    normalized = re.sub(r"[^\w\s\+\#\.\-]", "", normalized)
    return normalized

COMMON_SYNONYMS = {
    "js": "javascript",
    "ts": "typescript",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node.js",
    "node": "node.js",
    "postgres": "postgresql",
    "psql": "postgresql",
    "k8s": "kubernetes",
    "amazon web services": "aws",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "rest api": "rest apis",
    "restful apis": "rest apis",
    "restful api": "rest apis",
    "ml": "machine learning",
    "machine learning": "machine learning",
    "ai": "artificial intelligence",
    "deep learning": "deep learning",
    "dl": "deep learning",
    "ci/cd": "cicd",
    "ci cd": "cicd",
    "golang": "go",
    "c++": "cpp",
    "c#": "csharp",
    "python programming": "python",
    "python development": "python",
    "python scripting": "python",
    "sql database": "sql",
    "sql queries": "sql",
    "sql programming": "sql",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "tf": "tensorflow",
    "torch": "pytorch",
    "data preprocessing": "data preprocessing",
    "model evaluation": "model evaluation",
    "feature engineering": "feature engineering",
    "mlops": "mlops",
    "statistics": "statistics",
    "git version control": "git",
    "github": "git",
}

def canonicalize_skill(skill: str) -> str:
    norm = normalize_skill(skill)
    return COMMON_SYNONYMS.get(norm, norm)

def skills_match(student_skill: str, job_skill: str) -> str:
    """
    Returns 'match', 'partial', or 'none'.
    """
    s1 = canonicalize_skill(student_skill)
    s2 = canonicalize_skill(job_skill)

    if not s1 or not s2:
        return "none"

    if s1 == s2:
        return "match"

    # Exact token containment (e.g. 'spring' and 'spring boot', 'react' and 'react native')
    tokens1 = set(re.findall(r"\w+", s1))
    tokens2 = set(re.findall(r"\w+", s2))

    if s1 in s2 or s2 in s1:
        return "partial"

    if tokens1 and tokens2 and (tokens1.issubset(tokens2) or tokens2.issubset(tokens1)):
        return "partial"

    return "none"
