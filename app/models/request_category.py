"""
Request category entity.

Examples: Electrical, Plumbing, Furniture, Internet/Network,
Classroom Equipment, Hostel Maintenance.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RequestCategory(Base):
    __tablename__ = "request_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=True)

    service_requests = relationship("ServiceRequest", back_populates="category")
