from datetime import datetime
from sqlalchemy import BigInteger, Column, DateTime, Integer, String, Text
from app.core.database import Base

class AnalysisRecord(Base):
    """
    Student Placement Analysis Session Record.
    Stores placement intelligence run for audit and review.
    """
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    target_company = Column(String(150), nullable=False)
    target_role = Column(String(150), nullable=False)
    matched_job_id = Column(BigInteger, nullable=True, index=True)
    match_score = Column(Integer, nullable=False)
    
    # JSON serializations of structured placement intelligence
    student_skills = Column(Text, nullable=False)
    skill_gaps = Column(Text, nullable=False)
    resume_weaknesses = Column(Text, nullable=False)
    improvement_plan = Column(Text, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
