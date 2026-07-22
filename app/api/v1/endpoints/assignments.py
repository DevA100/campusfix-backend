"""
Assignment endpoints: administrators assign pending requests to a
maintenance officer.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.core.permissions import require_admin, require_any_authenticated
from app.models.user import User
from app.models.assignment import Assignment
from app.crud.service_request import get_request
from app.crud.assignment import create_assignment
from app.schemas.assignment import AssignmentCreate, AssignmentOut

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("", response_model=AssignmentOut, status_code=status.HTTP_201_CREATED)
def assign_request(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service_request = get_request(db, payload.service_request_id)
    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    if service_request.assignment is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Request already assigned")

    officer = db.query(User).filter(User.id == payload.officer_id).first()
    if not officer or officer.role.name != "MAINTENANCE_OFFICER":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Target user is not a maintenance officer")

    return create_assignment(db, service_request, payload.officer_id, current_user.id, payload.notes)


# ✅ ADD THIS ENDPOINT
@router.get("/request/{request_id}", response_model=AssignmentOut)
def get_assignment_by_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_authenticated),
):
    """
    Get the assignment for a specific service request.
    """
    # Check if request exists
    service_request = get_request(db, request_id)
    if not service_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service request {request_id} not found"
        )

    # Get assignment with officer loaded
    assignment = (
        db.query(Assignment)
        .options(joinedload(Assignment.officer))
        .filter(Assignment.service_request_id == request_id)
        .first()
    )

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No assignment found for request {request_id}"
        )

    return assignment
