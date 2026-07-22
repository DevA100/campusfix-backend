"""
Service request entity.
"""

import enum
from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Enum, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    REOPENED = "REOPENED"


class RequestPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    priority: Mapped[RequestPriority] = mapped_column(
        Enum(RequestPriority), default=RequestPriority.MEDIUM
    )
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus), default=RequestStatus.PENDING, index=True
    )
    evidence_file_path: Mapped[str] = mapped_column(String(255), nullable=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("request_categories.id"), nullable=False)
    submitted_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    category = relationship(
        "RequestCategory", back_populates="service_requests")
    submitted_by = relationship(
        "User", back_populates="submitted_requests", foreign_keys=[submitted_by_id]
    )
    assignment = relationship(
        "Assignment", back_populates="service_request", uselist=False, cascade="all, delete-orphan"
    )
    status_logs = relationship(
        "StatusLog", back_populates="service_request", cascade="all, delete-orphan"
    )
