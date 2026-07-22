"""
Pydantic schemas for service requests and status logs.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.service_request import RequestStatus, RequestPriority
from app.schemas.category import CategoryOut  # Import from category schema


class ServiceRequestCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    description: str = Field(..., min_length=10)
    location: str = Field(..., min_length=2, max_length=150)
    category_id: int
    priority: RequestPriority = RequestPriority.MEDIUM


class ServiceRequestUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    priority: Optional[RequestPriority] = None


class StatusChangeRequest(BaseModel):
    new_status: RequestStatus
    comment: Optional[str] = None


class SubmitterOut(BaseModel):
    id: int
    full_name: str
    email: str

    class Config:
        from_attributes = True


class ServiceRequestOut(BaseModel):
    id: int
    title: str
    description: str
    location: str
    priority: RequestPriority
    status: RequestStatus
    evidence_file_path: Optional[str]
    category: CategoryOut  # Uses CategoryOut from category schema
    submitted_by: SubmitterOut
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StatusLogOut(BaseModel):
    id: int
    previous_status: Optional[str]
    new_status: str
    comment: Optional[str]
    changed_by: SubmitterOut
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedServiceRequests(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ServiceRequestOut]
