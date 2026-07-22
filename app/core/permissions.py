"""
Role-based access control.

require_role() returns a FastAPI dependency that only allows the
listed role names through; anyone else receives 403 Forbidden. This
keeps role checks declarative in each endpoint's signature instead of
repeated if/else blocks inside the handler bodies.
"""

from fastapi import Depends, HTTPException, status
from app.core.deps import get_current_user
from app.models.user import User


def require_role(*allowed_roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker


#  Use separate STUDENT and STAFF roles
require_admin = require_role("ADMIN")
require_officer = require_role("MAINTENANCE_OFFICER", "ADMIN")
require_any_authenticated = require_role(
    "STUDENT", "STAFF", "MAINTENANCE_OFFICER", "ADMIN")
