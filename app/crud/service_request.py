"""
Database access functions for service requests, filtering, pagination,
and status transitions with audit logging.
"""

import logging
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.models.service_request import ServiceRequest, RequestStatus
from app.models.status_log import StatusLog
from app.models.assignment import Assignment
from app.models.request_category import RequestCategory
from app.schemas.service_request import ServiceRequestCreate

logger = logging.getLogger(__name__)


def create_request(
    db: Session, request_in: ServiceRequestCreate, submitted_by_id: int, evidence_path: str | None
) -> ServiceRequest:
    """
    Create a new service request.

    Args:
        db: Database session
        request_in: Request data
        submitted_by_id: ID of the user submitting
        evidence_path: Optional path to evidence file

    Returns:
        ServiceRequest: The created request

    Raises:
        ValueError: If category doesn't exist
        IntegrityError: If foreign key constraint fails
    """
    # Verify category exists
    category = db.query(RequestCategory).filter(
        RequestCategory.id == request_in.category_id
    ).first()

    if not category:
        logger.error(f"Category with ID {request_in.category_id} not found")
        raise ValueError(
            f"Category with ID {request_in.category_id} does not exist. Available categories: Electrical(1), Plumbing(2), Furniture(3), Internet/Network(4), Classroom Equipment(5), Hostel Maintenance(6)")

    logger.info(
        f"Creating request with category: {category.name} (ID: {category.id})")

    try:
        # Create the service request
        service_request = ServiceRequest(
            title=request_in.title,
            description=request_in.description,
            location=request_in.location,
            category_id=request_in.category_id,
            priority=request_in.priority,
            submitted_by_id=submitted_by_id,
            evidence_file_path=evidence_path,
            status=RequestStatus.PENDING,
        )
        db.add(service_request)
        db.commit()
        db.refresh(service_request)
        logger.info(f"Created service request with ID: {service_request.id}")

        # Log the initial status change
        _log_status_change(
            db,
            service_request.id,
            submitted_by_id,
            None,
            RequestStatus.PENDING,
            "Request submitted"
        )

        # Refresh again to get the updated object with relationships
        db.refresh(service_request)
        return service_request

    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError creating request: {e}")
        raise ValueError(f"Database error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating request: {e}")
        raise


def get_request(db: Session, request_id: int) -> ServiceRequest | None:
    """Get a service request by ID with relationships loaded."""
    return db.query(ServiceRequest).filter(ServiceRequest.id == request_id).first()


def search_requests(
    db: Session,
    status_filter: str | None = None,
    category_id: int | None = None,
    search_text: str | None = None,
    submitted_by_id: int | None = None,
    officer_id: int | None = None,
    page: int = 1,
    page_size: int = 10,
):
    """
    Search and filter service requests with pagination.

    Args:
        db: Database session
        status_filter: Filter by status
        category_id: Filter by category
        search_text: Search in title/description
        submitted_by_id: Filter by submitter
        officer_id: Filter by assigned officer
        page: Page number (1-indexed)
        page_size: Items per page

    Returns:
        tuple: (total_count, list_of_requests)
    """
    # Start with the base query
    query = db.query(ServiceRequest)

    # Apply filters
    if status_filter:
        query = query.filter(ServiceRequest.status == status_filter)
    if category_id:
        query = query.filter(ServiceRequest.category_id == category_id)
    if submitted_by_id:
        query = query.filter(ServiceRequest.submitted_by_id == submitted_by_id)
    if search_text:
        pattern = f"%{search_text}%"
        query = query.filter(
            or_(
                ServiceRequest.title.ilike(pattern),
                ServiceRequest.description.ilike(pattern)
            )
        )
    if officer_id:
        query = query.join(Assignment).filter(
            Assignment.officer_id == officer_id)

    # Get total count before pagination
    total = query.count()

    # ✅ IMPORTANT: Apply joinedload AFTER filters but BEFORE pagination
    query = query.options(
        joinedload(ServiceRequest.submitted_by),
        joinedload(ServiceRequest.category),
        joinedload(ServiceRequest.assignment).joinedload(Assignment.officer)
    )

    # Apply pagination and ordering
    items = (
        query.order_by(ServiceRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return total, items


def change_status(
    db: Session,
    service_request: ServiceRequest,
    new_status: RequestStatus,
    changed_by_id: int,
    comment: str | None
) -> ServiceRequest:
    """
    Change the status of a service request.

    Args:
        db: Database session
        service_request: The request to update
        new_status: New status
        changed_by_id: ID of the user making the change
        comment: Optional comment

    Returns:
        ServiceRequest: The updated request
    """
    previous_status = service_request.status
    service_request.status = new_status
    db.commit()
    db.refresh(service_request)

    _log_status_change(
        db,
        service_request.id,
        changed_by_id,
        previous_status,
        new_status,
        comment
    )

    db.refresh(service_request)
    return service_request


def _log_status_change(
    db: Session,
    service_request_id: int,
    changed_by_id: int,
    previous_status: RequestStatus | None,
    new_status: RequestStatus,
    comment: str | None,
) -> StatusLog:
    """
    Log a status change for a service request.

    Args:
        db: Database session
        service_request_id: ID of the request
        changed_by_id: ID of the user who changed the status
        previous_status: Previous status (None for initial)
        new_status: New status
        comment: Optional comment

    Returns:
        StatusLog: The created log entry
    """
    try:
        log_entry = StatusLog(
            service_request_id=service_request_id,
            changed_by_id=changed_by_id,
            previous_status=previous_status.value if previous_status else None,
            new_status=new_status.value,
            comment=comment,
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        logger.info(
            f"Created status log for request {service_request_id}: {previous_status} -> {new_status}")
        return log_entry
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating status log: {e}")
        raise
