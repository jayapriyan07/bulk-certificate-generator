from pydantic import BaseModel, EmailStr, Field
from typing import List

class Recipient(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr

class GenerationRequest(BaseModel):
    event_name: str = Field(min_length=2, max_length=200)
    date: str
    recipients: List[Recipient] = Field(min_length=1)

class JobResponse(BaseModel):
    job_id: int
    status: str
    total: int
    successful: int
    failed: int
