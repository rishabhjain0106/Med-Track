from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.reservation import ReservationResponse, EmergencyOverrideRequest
from app.services.emergency_service import EmergencyService
from app.security.permissions import require_hospital_staff

router = APIRouter(prefix="/hospital/emergency-cancel", tags=["Emergency Override"])


@router.post("", response_model=ReservationResponse)
def emergency_cancel_reservation(
    payload: EmergencyOverrideRequest,
    db: Session = Depends(get_db),
    staff_user: User = Depends(require_hospital_staff)
):
    """
    Emergency override: hospital staff cancels a reservation with justification,
    freeing up critical hospital resources and notifying user via reservation status.
    """
    return EmergencyService.override_cancel_reservation(
        db=db, staff_user=staff_user, payload=payload
    )
