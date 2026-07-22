"""
Service request endpoints: submission, tracking, filtering/search with
pagination, status updates, and evidence file upload.
"""

import os
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.core.permissions import require_officer, require_any_authenticated
from app.models.user import User
from app.models.service_request import RequestPriority, RequestStatus
from app.crud.service_request import create_request, get_request, search_requests, change_status
from app.schemas.service_request import (
    ServiceRequestOut,
    ServiceRequestCreate,
    StatusChangeRequest,
    PaginatedServiceRequests,
    StatusLogOut,
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/requests", tags=["Service Requests"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def _save_evidence_file(file: UploadFile) -> str:
    """Save uploaded evidence file and return file path."""
    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: jpg, jpeg, png, pdf",
        )

    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 5MB limit"
        )

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(contents)

    return file_path


@router.post("", response_model=ServiceRequestOut, status_code=status.HTTP_201_CREATED)
def submit_request(
    title: str = Form(...),
    description: str = Form(...),
    location: str = Form(...),
    category_id: int = Form(...),
    priority: RequestPriority = Form(RequestPriority.MEDIUM),
    evidence: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """
    Submit a new service request.

    Any authenticated user (student, staff, officer, admin) can submit a request.
    """
    try:
        logger.info(
            f"User {current_user.id} ({current_user.role.name}) submitting request")
        logger.info(
            f"Title: {title}, Category: {category_id}, Priority: {priority}")

        # Handle evidence file
        evidence_path = None
        if evidence:
            logger.info(f"Saving evidence file: {evidence.filename}")
            evidence_path = _save_evidence_file(evidence)
            logger.info(f"Evidence saved to: {evidence_path}")

        # Create request
        request_in = ServiceRequestCreate(
            title=title,
            description=description,
            location=location,
            category_id=category_id,
            priority=priority
        )

        result = create_request(db, request_in, current_user.id, evidence_path)
        logger.info(f"✅ Request created successfully with ID: {result.id}")
        return result

    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating request: {str(e)}"
        )


@router.get("", response_model=PaginatedServiceRequests)
def list_requests(
    status_filter: RequestStatus | None = None,
    category_id: int | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List service requests with filtering and pagination.

    - STUDENT/STAFF: See only their own requests
    - MAINTENANCE_OFFICER: See requests assigned to them
    - ADMIN: See all requests
    """
    submitted_by_id = None
    officer_id = None

    if current_user.role.name in ("STUDENT", "STAFF"):
        submitted_by_id = current_user.id
    elif current_user.role.name == "MAINTENANCE_OFFICER":
        officer_id = current_user.id
    # ADMIN sees all (no filters applied)

    total, items = search_requests(
        db,
        status_filter=status_filter.value if status_filter else None,
        category_id=category_id,
        search_text=search,
        submitted_by_id=submitted_by_id,
        officer_id=officer_id,
        page=page,
        page_size=page_size,
    )
    return PaginatedServiceRequests(total=total, page=page, page_size=page_size, items=items)


@router.get("/{request_id}", response_model=ServiceRequestOut)
def get_request_detail(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get details of a specific service request."""
    service_request = get_request(db, request_id)
    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    is_owner = service_request.submitted_by_id == current_user.id
    is_privileged = current_user.role.name in ("MAINTENANCE_OFFICER", "ADMIN")
    if not (is_owner or is_privileged):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this request"
        )

    return service_request


@router.get("/{request_id}/logs", response_model=list[StatusLogOut])
def get_request_logs(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status change logs for a service request."""
    service_request = get_request(db, request_id)
    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    # Check authorization
    is_owner = service_request.submitted_by_id == current_user.id
    is_privileged = current_user.role.name in ("MAINTENANCE_OFFICER", "ADMIN")
    if not (is_owner or is_privileged):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view logs"
        )

    return service_request.status_logs


@router.patch("/{request_id}/status", response_model=ServiceRequestOut)
def update_request_status(
    request_id: int,
    payload: StatusChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_officer),
):
    """Update request status (Maintenance Officers and Admins only)."""
    service_request = get_request(db, request_id)
    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    return change_status(db, service_request, payload.new_status, current_user.id, payload.comment)
