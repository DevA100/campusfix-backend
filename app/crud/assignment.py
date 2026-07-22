"""
Database access functions for assigning service requests to officers.
"""

from sqlalchemy.orm import Session, joinedload
from app.models.assignment import Assignment
from app.models.service_request import ServiceRequest, RequestStatus
from app.crud.service_request import _log_status_change
import logging

logger = logging.getLogger(__name__)


def create_assignment(
    db: Session, service_request: ServiceRequest, officer_id: int, assigned_by_id: int, notes: str | None
) -> Assignment:
    """Create a new assignment for a service request."""
    assignment = Assignment(
        service_request_id=service_request.id,
        officer_id=officer_id,
        assigned_by_id=assigned_by_id,
        notes=notes,
    )
    db.add(assignment)

    previous_status = service_request.status
    service_request.status = RequestStatus.ASSIGNED
    db.commit()
    db.refresh(assignment)

    _log_status_change(
        db, service_request.id, assigned_by_id, previous_status, RequestStatus.ASSIGNED,
        f"Assigned to officer id {officer_id}",
    )

    # ✅ Refresh with relationships loaded
    db.refresh(service_request)

    return assignment


def update_assignment(
    db: Session, service_request: ServiceRequest, officer_id: int, assigned_by_id: int, notes: str | None
) -> Assignment:
    """Update an existing assignment for a service request."""
    # Find existing assignment with officer loaded
    assignment = (
        db.query(Assignment)
        .options(joinedload(Assignment.officer))
        .filter(Assignment.service_request_id == service_request.id)
        .first()
    )

    if not assignment:
        raise ValueError(
            f"No assignment found for request {service_request.id}")

    # Update the assignment
    assignment.officer_id = officer_id
    assignment.assigned_by_id = assigned_by_id
    assignment.notes = notes or "Re-assigned via admin console"

    # Update request status if needed
    if service_request.status != RequestStatus.ASSIGNED:
        previous_status = service_request.status
        service_request.status = RequestStatus.ASSIGNED
        _log_status_change(
            db, service_request.id, assigned_by_id, previous_status, RequestStatus.ASSIGNED,
            f"Re-assigned to officer id {officer_id}",
        )

    db.commit()
    db.refresh(assignment)
    db.refresh(service_request)

    logger.info(
        f"Updated assignment for request {service_request.id} to officer {officer_id}")
    return assignment


def get_assignment_by_request(db: Session, service_request_id: int) -> Assignment | None:
    """Get assignment by service request ID with officer loaded."""
    return (
        db.query(Assignment)
        .options(joinedload(Assignment.officer))
        .filter(Assignment.service_request_id == service_request_id)
        .first()
    )
