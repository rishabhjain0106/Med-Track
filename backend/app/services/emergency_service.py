from datetime import datetime, timezone
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.reservation import Reservation
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.reservation import ReservationResponse, EmergencyOverrideRequest
from app.services.reservation_service import ReservationService
from app.cache.cache_invalidation import invalidate_inventory_cache

logger = logging.getLogger(__name__)


class EmergencyService:
    @staticmethod
    def override_cancel_reservation(
        db: Session, staff_user: User, payload: EmergencyOverrideRequest
    ) -> ReservationResponse:
        """
        Hospital staff cancels active reservation for triage/emergency.
        - Restores reserved stock back to local inventory.
        - Updates reservation status to 'cancelled_by_hospital'.
        - Records mandatory reason and comprehensive audit log entry.
        """
        reservation = db.query(Reservation).filter(Reservation.id == payload.reservation_id).first()
        if not reservation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Reservation ID {payload.reservation_id} not found"
            )

        # Check hospital authorization
        if staff_user.role != "admin" and reservation.hospital_id != staff_user.hospital_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to override reservations for this hospital"
            )

        if reservation.status not in ("confirmed", "pending"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot override reservation in state '{reservation.status}'"
            )

        now = datetime.now(timezone.utc)

        # Return stock back to inventory
        ReservationService._return_stock(db, reservation)

        # Update reservation record
        reservation.status = "cancelled_by_hospital"
        reservation.cancellation_reason = payload.reason.strip()
        reservation.updated_at = now

        # Create detailed audit record
        audit = AuditLog(
            action="EMERGENCY_OVERRIDE_CANCEL",
            performed_by_id=staff_user.id,
            hospital_id=reservation.hospital_id,
            reservation_id=reservation.id,
            details=f"Emergency override by staff '{staff_user.name}'. Reason: {payload.reason.strip()}"
        )
        db.add(audit)
        db.commit()

        # Invalidate cache so updated stock is visible to other requests
        invalidate_inventory_cache(reservation.hospital_id, reservation.resource_type)

        resp = ReservationResponse.model_validate(reservation)
        if reservation.hospital:
            resp.hospital_name = reservation.hospital.name
        return resp
