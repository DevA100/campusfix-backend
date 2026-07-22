"""
Database access functions for users and roles.
"""

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.schemas.user import UserCreate
from app.core.security import hash_password


def get_role_by_name(db: Session, role_name: str) -> Role | None:
    """
    Get role by name with case-insensitive lookup.

    Args:
        db: Database session
        role_name: Role name (case-insensitive)

    Returns:
        Role | None: The role if found, None otherwise
    """
    # Normalize to uppercase for case-insensitive comparison
    normalized = role_name.upper().strip()
    return db.query(Role).filter(Role.name == normalized).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get a user by email address."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """
    Create a new user.

    Args:
        db: Database session
        user_in: User creation data

    Returns:
        User: The created user

    Raises:
        ValueError: If the role is invalid
    """
    # Normalize role name to uppercase for case-insensitive matching
    role_name = user_in.role_name.upper().strip()

    # Get the role from database
    role = get_role_by_name(db, role_name)
    if role is None:
        valid_roles = ["STUDENT", "STAFF", "MAINTENANCE_OFFICER", "ADMIN"]
        raise ValueError(
            f"Unknown role: '{user_in.role_name}'. "
            f"Valid roles are: {valid_roles} "
            f"(case-insensitive)"
        )

    # Create the user
    user = User(
        full_name=user_in.full_name,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        phone_number=user_in.phone_number,
        department=user_in.department,
        role_id=role.id,
        is_active=True,  # Explicitly set active by default
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, skip: int = 0, limit: int = 20) -> list[User]:
    """List users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()
