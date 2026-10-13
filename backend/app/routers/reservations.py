from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.services.reservation_service import ReservationService
from app.services.expiry_service import ExpiryService
from app.security.auth import get_current_user

router = APIRouter(prefix="/reservations", tags=["Reservations"])


@router.post("", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED)
def create_reservation(
    payload: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Atomically reserve blood, medicine, or hospital bed with row-level locking.
    Returns 409 Conflict if stock is insufficient.
    """
    return ReservationService.create_reservation(db=db, user=current_user, payload=payload)


@router.get("/my", response_model=List[ReservationResponse])
def get_my_reservations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch all reservations created by the authenticated user."""
    return ReservationService.get_user_reservations(db=db, user=current_user)


@router.post("/{reservation_id}/cancel", response_model=ReservationResponse)
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel user's active reservation and release held stock back to inventory."""
    return ReservationService.cancel_reservation(
        db=db, user=current_user, reservation_id=reservation_id
    )


@router.post("/trigger-expiry", status_code=status.HTTP_200_OK)
def trigger_expiry_sweep(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually invoke the TTL expiry sweep to restore timed-out reservations."""
    count = ExpiryService.expire_stale_reservations(db)
    return {"status": "success", "expired_count": count}
