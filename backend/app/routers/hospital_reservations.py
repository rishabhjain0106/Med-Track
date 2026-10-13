from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.reservation import ReservationResponse
from app.services.reservation_service import ReservationService
from app.security.permissions import verify_hospital_access

router = APIRouter(prefix="/hospital/reservations", tags=["Hospital Reservations"])


@router.get("/{hospital_id}", response_model=List[ReservationResponse])
def get_hospital_reservations(
    hospital_id: int,
    db: Session = Depends(get_db),
    staff_user: User = Depends(verify_hospital_access)
):
    """Retrieve all reservations created for the staff user's hospital."""
    return ReservationService.get_hospital_reservations(db, hospital_id)
