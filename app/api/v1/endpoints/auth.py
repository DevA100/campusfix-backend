"""
Authentication endpoints: registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token
from app.crud.user import create_user, get_user_by_email
from app.core.security import verify_password, create_access_token
from app.models.role import Role

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        user_in: User registration data
        db: Database session

    Returns:
        UserOut: The created user

    Raises:
        HTTPException: If email already registered or role is invalid
    """
    # Check if email already registered
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # ===== ROLE VALIDATION =====
    # Normalize role to uppercase (using role_name, not role)
    role_name = user_in.role_name.upper().strip()

    # Check if role exists in database
    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        valid_roles = ["STUDENT", "STAFF", "MAINTENANCE_OFFICER", "ADMIN"]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role: '{user_in.role_name}'. Valid roles are: {valid_roles} (case-insensitive)"
        )
    # ===== END ROLE VALIDATION =====

    try:
        # Create the user (role validation also happens inside create_user)
        user = create_user(db, user_in)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    return user


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login user and return access token.

    Args:
        form_data: OAuth2 password request form (email as username)
        db: Database session

    Returns:
        Token: Access token

    Raises:
        HTTPException: If credentials are invalid
    """
    # OAuth2PasswordRequestForm exposes the submitted email as .username
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    access_token = create_access_token(
        subject=user.email,
        role=user.role.name
    )
    return Token(access_token=access_token)
