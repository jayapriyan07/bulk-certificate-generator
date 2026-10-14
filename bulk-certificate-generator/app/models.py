from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

def get_utc_now():
    return datetime.now(timezone.utc)

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String, nullable=False)
    event_date = Column(String, nullable=False)
    status = Column(String, default="processing")
    total = Column(Integer, default=0)
    successful = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_utc_now)

    certificates = relationship("Certificate", back_populates="job", cascade="all, delete-orphan")

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    recipient_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    status = Column(String, nullable=False)
    file_path = Column(String, nullable=True)
    error = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    job = relationship("Job", back_populates="certificates")

