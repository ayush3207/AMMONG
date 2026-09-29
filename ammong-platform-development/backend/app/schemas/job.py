from typing import Dict, List, Union
from pydantic import BaseModel, Field

class JobResponse(BaseModel):
    """
    Schema matching exact Kaggle dataset fields:
    - job_id
    - category
    - job_title
    - job_description
    - job_skill_set
    """
    job_id: int
    category: str
    job_title: str
    job_description: str
    job_skill_set: Union[List[str], str]

    model_config = {
        "from_attributes": True
    }

class JobsListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    jobs: List[JobResponse]

class JobStatsResponse(BaseModel):
    total_jobs: int
    categories: Dict[str, int]
    successfully_loaded: bool
