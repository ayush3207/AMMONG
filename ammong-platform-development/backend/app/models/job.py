from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, String, Text
from app.core.database import Base

class Job(Base):
    """
    Job Requirement knowledge base model.
    Preserves original Kaggle dataset fields:
    - job_id
    - category
    - job_title
    - job_description
    - job_skill_set
    """
    __tablename__ = "jobs"

    job_id = Column(BigInteger, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    job_title = Column(String(255), nullable=False, index=True)
    job_description = Column(Text, nullable=False)
    job_skill_set = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
