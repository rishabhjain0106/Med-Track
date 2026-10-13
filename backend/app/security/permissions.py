from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.security.auth import get_current_user


def require_role(*allowed_roles: str):
    """Factory for requiring specific user roles."""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker


def require_hospital_staff(current_user: User = Depends(get_current_user)) -> User:
    """Ensure user is hospital staff or admin and has an assigned hospital."""
    if current_user.role not in ("hospital_staff", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access restricted to hospital staff"
        )
    if current_user.role == "hospital_staff" and not current_user.hospital_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff user has no hospital assigned"
        )
    return current_user


def verify_hospital_access(hospital_id: int, current_user: User = Depends(require_hospital_staff)):
    """Ensure the staff user belongs to the requested hospital (unless admin)."""
    if current_user.role != "admin" and current_user.hospital_id != hospital_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You do not have permission to manage hospital ID {hospital_id}"
        )
    return current_user
