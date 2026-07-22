"""
Pydantic schemas for assigning service requests to maintenance officers.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from app.schemas.service_request import SubmitterOut


class AssignmentCreate(BaseModel):
    service_request_id: int
    officer_id: int
    notes: str | None = Field(default=None, max_length=500)


class AssignmentOut(BaseModel):
    id: int
    service_request_id: int
    officer: SubmitterOut  # ✅ This should include full_name
    notes: str | None
    assigned_at: datetime

    class Config:
        from_attributes = True
