import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from app.core.config import settings
from app.core.logging import logger
from app.schemas.job import JobResponse, JobsListResponse, JobStatsResponse
from app.utils.text_normalizer import parse_skill_list

REQUIRED_COLUMNS = ["job_id", "category", "job_title", "job_description", "job_skill_set"]

class DatasetService:
    """
    Job Requirements Knowledge Base Service.
    Loads, cleans, indexes and queries all_job_post.csv (1,167 postings).
    Preserves exact original dataset fields.
    """
    def __init__(self):
        self.df: Optional[pd.DataFrame] = None
        self.jobs_by_id: Dict[int, Dict[str, Any]] = {}
        self.categories: Dict[str, int] = {}
        self.is_loaded: bool = False
        self.total_jobs: int = 0

    def load_dataset(self, csv_path: Optional[str] = None) -> bool:
        """
        Load CSV, validate columns, clean null values, normalize and index records.
        """
        path = Path(csv_path or settings.DATASET_PATH)
        if not path.exists():
            logger.error(f"Dataset CSV not found at: {path}")
            self.is_loaded = False
            return False

        try:
            logger.info(f"Loading dataset from: {path}")
            df = pd.read_csv(path)

            # Validate columns
            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                logger.error(f"Dataset is missing required columns: {missing_cols}")
                self.is_loaded = False
                return False

            # Keep only required columns and preserve original names
            df = df[REQUIRED_COLUMNS].copy()

            # Clean null values and normalize types
            df["job_id"] = pd.to_numeric(df["job_id"], errors="coerce").fillna(0).astype(int)
            df["category"] = df["category"].fillna("UNCATEGORIZED").astype(str).str.strip()
            df["job_title"] = df["job_title"].fillna("Untitled Position").astype(str).str.strip()
            df["job_description"] = df["job_description"].fillna("").astype(str).str.strip()
            df["job_skill_set"] = df["job_skill_set"].fillna("[]").astype(str).str.strip()

            # Remove invalid rows where job_id is 0
            df = df[df["job_id"] > 0].reset_index(drop=True)

            self.df = df
            self.total_jobs = len(df)
            self.categories = df["category"].value_counts().to_dict()

            # Build fast in-memory dictionary index
            self.jobs_by_id.clear()
            for _, row in df.iterrows():
                job_id = int(row["job_id"])
                # Parse skill list for convenient querying while preserving original fields
                parsed_skills = parse_skill_list(row["job_skill_set"])
                self.jobs_by_id[job_id] = {
                    "job_id": job_id,
                    "category": row["category"],
                    "job_title": row["job_title"],
                    "job_description": row["job_description"],
                    "job_skill_set": parsed_skills if parsed_skills else row["job_skill_set"],
                    "raw_skill_set": row["job_skill_set"],
                    "parsed_skills": parsed_skills,
                }

            self.is_loaded = True
            logger.info(
                f"Successfully loaded {self.total_jobs} job postings across "
                f"{len(self.categories)} categories."
            )
            return True

        except Exception as e:
            logger.error(f"Error loading job dataset: {e}", exc_info=True)
            self.is_loaded = False
            return False

    def get_stats(self) -> JobStatsResponse:
        """Returns summary statistics of the loaded dataset."""
        return JobStatsResponse(
            total_jobs=self.total_jobs,
            categories=self.categories,
            successfully_loaded=self.is_loaded,
        )

    def get_job_by_id(self, job_id: int) -> Optional[JobResponse]:
        """Fetch a single job posting by job_id."""
        if job_id not in self.jobs_by_id:
            return None
        job_data = self.jobs_by_id[job_id]
        return JobResponse(
            job_id=job_data["job_id"],
            category=job_data["category"],
            job_title=job_data["job_title"],
            job_description=job_data["job_description"],
            job_skill_set=job_data["job_skill_set"],
        )

    def get_jobs(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        job_title: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> JobsListResponse:
        """
        Query jobs with filtering, full-text search, and pagination.
        """
        if not self.is_loaded or self.df is None:
            return JobsListResponse(total=0, page=page, page_size=page_size, total_pages=0, jobs=[])

        filtered_df = self.df

        # Filter by category (case-insensitive)
        if category:
            filtered_df = filtered_df[
                filtered_df["category"].str.contains(category, case=False, na=False)
            ]

        # Filter by job title (case-insensitive)
        if job_title:
            filtered_df = filtered_df[
                filtered_df["job_title"].str.contains(job_title, case=False, na=False)
            ]

        # Search across title, description, skills
        if search:
            search_term = search.strip()
            mask = (
                filtered_df["job_title"].str.contains(search_term, case=False, na=False)
                | filtered_df["job_description"].str.contains(search_term, case=False, na=False)
                | filtered_df["job_skill_set"].str.contains(search_term, case=False, na=False)
            )
            filtered_df = filtered_df[mask]

        total = len(filtered_df)
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        page = max(1, min(page, total_pages if total_pages > 0 else 1))

        start = (page - 1) * page_size
        end = start + page_size
        page_slice = filtered_df.iloc[start:end]

        jobs: List[JobResponse] = []
        for _, row in page_slice.iterrows():
            jid = int(row["job_id"])
            if jid in self.jobs_by_id:
                job_data = self.jobs_by_id[jid]
                jobs.append(
                    JobResponse(
                        job_id=job_data["job_id"],
                        category=job_data["category"],
                        job_title=job_data["job_title"],
                        job_description=job_data["job_description"],
                        job_skill_set=job_data["job_skill_set"],
                    )
                )

        return JobsListResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            jobs=jobs,
        )

    def find_matching_jobs(self, role: str, company: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find top reference job postings from knowledge base matching target role.
        Used by placement intelligence comparison.
        """
        if not self.is_loaded or self.df is None:
            return []

        role_clean = role.lower().strip()
        role_tokens = [w for w in re.split(r"\W+", role_clean) if len(w) > 2]

        scored_jobs = []
        for job_id, job in self.jobs_by_id.items():
            title = job["job_title"].lower()
            desc = job["job_description"].lower()
            score = 0

            # Direct title match
            if role_clean in title:
                score += 100
            for token in role_tokens:
                if token in title:
                    score += 25
                elif token in desc:
                    score += 5

            if score > 0:
                scored_jobs.append((score, job))

        # Sort by score descending
        scored_jobs.sort(key=lambda x: x[0], reverse=True)

        if not scored_jobs:
            # Fallback: if role is IT/Software related, default to IT jobs
            it_jobs = [j for j in self.jobs_by_id.values() if "TECHNOLOGY" in j["category"]]
            return it_jobs[:limit] if it_jobs else list(self.jobs_by_id.values())[:limit]

        return [j for _, j in scored_jobs[:limit]]

dataset_service = DatasetService()
