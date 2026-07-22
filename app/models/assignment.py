"""
Assignment entity.

Links one service request to one maintenance officer. Kept as its own
table (rather than a foreign key directly on ServiceRequest) so the
assignment history, reassignment, and assignment-specific metadata
(assigned_by, assigned_at, notes) are modeled explicitly.
"""

from sqlalchemy import Integer, ForeignKey, DateTime, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    service_request_id: Mapped[int] = mapped_column(
        ForeignKey("service_requests.id"), unique=True, nullable=False
    )
    officer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)
    assigned_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    assigned_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    service_request = relationship(
        "ServiceRequest", back_populates="assignment")
    officer = relationship(
        "User",
        foreign_keys=[officer_id],
        back_populates="assignments"
    )
    assigned_by = relationship(
        "User",
        foreign_keys=[assigned_by_id],
        back_populates="assignments_created"
    )
