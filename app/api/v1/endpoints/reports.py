"""
Reporting endpoints for administrators: summary counts and CSV export
of service requests.
"""

import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from sqlalchemy.sql.functions import count  # Import count directly

from app.database import get_db
from app.core.permissions import require_admin
from app.models.service_request import ServiceRequest, RequestStatus

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/summary")
def status_summary(db: Session = Depends(get_db), _=Depends(require_admin)):
    """
    Get summary counts of service requests by status.

    Returns:
        dict: Total count and breakdown by status
    """
    # SQLAlchemy 2.0 style using select() - more explicit and type-safe
    stmt = select(
        ServiceRequest.status,
        # Using imported count directly
        count(ServiceRequest.id).label("count")
    ).group_by(ServiceRequest.status)

    rows = db.execute(stmt).all()

    # Initialize counts for all possible statuses
    counts = {status.value: 0 for status in RequestStatus}

    # Populate counts from query results
    for row in rows:
        counts[row.status.value] = row.count

    return {
        "total": sum(counts.values()),
        "by_status": counts
    }


@router.get("/export.csv")
def export_requests_csv(db: Session = Depends(get_db), _=Depends(require_admin)):
    """
    Export all service requests as CSV file.

    Returns:
        StreamingResponse: CSV file download
    """
    requests = db.query(ServiceRequest).order_by(
        ServiceRequest.created_at.desc()
    ).all()

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write headers
    writer.writerow([
        "ID", "Title", "Category", "Location", "Priority",
        "Status", "Submitted By", "Created At"
    ])

    # Write data rows
    for request in requests:
        writer.writerow([
            request.id,
            request.title,
            request.category.name,
            request.location,
            request.priority.value,
            request.status.value,
            request.submitted_by.full_name,
            request.created_at.isoformat(),
        ])

    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=service_requests_export.csv"
        },
    )
