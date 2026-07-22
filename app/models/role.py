"""
Role entity.

Roles: STUDENT, STAFF, MAINTENANCE_OFFICER, ADMIN.
Stored as a table (rather than a plain enum) so new roles can be added
without a code change, and so it can be referenced by foreign key.
"""

from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class RoleName(str, PyEnum):
    """Enum for valid role names - matches your permissions system."""

    STUDENT = "STUDENT"  # Matches your require_any_authenticated
    STAFF = "STAFF"      # Matches your require_any_authenticated
    MAINTENANCE_OFFICER = "MAINTENANCE_OFFICER"  # Matches your require_officer
    ADMIN = "ADMIN"      # Matches your require_admin

    @classmethod
    def get_valid_roles(cls) -> List[str]:
        """Get list of all valid role names."""
        return [role.value for role in cls]

    @classmethod
    def get_valid_roles_lower(cls) -> List[str]:
        """Get list of all valid role names in lowercase."""
        return [role.value.lower() for role in cls]

    @classmethod
    def is_valid(cls, role_name: str) -> bool:
        """Check if a role name is valid (case-insensitive)."""
        return role_name.upper() in cls.get_valid_roles()

    @classmethod
    def normalize(cls, role_name: str) -> str:
        """Normalize role name to uppercase for consistency."""
        return role_name.upper()

    @classmethod
    def get_display_names(cls) -> List[str]:
        """Get human-readable role names."""
        return [
            "Student",
            "Staff",
            "Maintenance Officer",
            "Administrator"
        ]


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True)

    # Relationships
    users = relationship("User", back_populates="role")

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name={self.name})>"

    @classmethod
    def get_by_name(cls, db_session, name: str):
        """Get role by name with case-insensitive lookup."""
        from sqlalchemy.orm import Session
        normalized = name.upper()
        return db_session.query(cls).filter(
            cls.name == normalized
        ).first()

    @classmethod
    def get_or_create(cls, db_session, name: str, description: Optional[str] = None):
        """Get or create a role by name."""
        role = cls.get_by_name(db_session, name)
        if not role:
            normalized = name.upper()
            role = cls(
                name=normalized,
                description=description or f"{normalized} role"
            )
            db_session.add(role)
            db_session.commit()
            db_session.refresh(role)
        return role

    @classmethod
    def validate_and_get(cls, db_session, role_name: str) -> 'Role':
        """
        Validate role name and return Role object.

        Args:
            db_session: Database session
            role_name: Role name to validate

        Returns:
            Role: The validated role object

        Raises:
            HTTPException: If role name is invalid or not found
        """
        from fastapi import HTTPException, status

        # Normalize to uppercase
        normalized = role_name.upper().strip()

        # Validate role exists in enum
        if not RoleName.is_valid(normalized):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role: '{role_name}'. Valid roles are: {RoleName.get_valid_roles()}"
            )

        # Get role from database
        role = cls.get_by_name(db_session, normalized)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Role '{normalized}' not found in database. Please run database seeds."
            )

        return role
