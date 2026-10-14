from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

class Recipient(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        stripped = v.strip()
        if len(stripped) < 2:
            raise ValueError("Recipient name must have at least 2 non-whitespace characters")
        return stripped

class GenerationRequest(BaseModel):
    event_name: str = Field(min_length=2, max_length=200)
    date: str = Field(min_length=1, max_length=50)
    recipients: List[Recipient] = Field(min_length=1)

    @field_validator("event_name", "date")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Field cannot be empty or only whitespace")
        return stripped

class CertificateResponse(BaseModel):
    id: int
    recipient_name: str
    email: str
    status: str
    error: Optional[str] = None
    download_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobResponse(BaseModel):
    job_id: int
    status: str
    total: int
    successful: int
    failed: int
    event_name: Optional[str] = None
    event_date: Optional[str] = None
    created_at: Optional[datetime] = None
    certificates: Optional[List[CertificateResponse]] = None

