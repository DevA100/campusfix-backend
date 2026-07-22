"""
User entity.

Covers students, staff, maintenance officers, and administrators.
The specific behaviour per role is enforced at the API layer via
role-based access control (see app/core/permissions.py).
"""

from sqlalchemy import Integer, String, Boolean, ForeignKey, DateTime, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(30), nullable=True)
    department: Mapped[str] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), nullable=False)
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )

    # Relationships
    role = relationship("Role", back_populates="users")
    submitted_requests = relationship(
        "ServiceRequest",
        back_populates="submitted_by",
        foreign_keys="ServiceRequest.submitted_by_id",
    )
    assignments = relationship(
        "Assignment",
        back_populates="officer",
        foreign_keys="Assignment.officer_id"
    )
    assignments_created = relationship(
        "Assignment",
        back_populates="assigned_by",
        foreign_keys="Assignment.assigned_by_id"
    )
    status_logs = relationship("StatusLog", back_populates="changed_by")
