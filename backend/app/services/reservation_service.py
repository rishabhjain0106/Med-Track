import time
import random
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, DBAPIError
from fastapi import HTTPException, status
from app.config import settings
from app.models.hospital import Hospital
from app.models.user import User
from app.models.blood import BloodInventory
from app.models.medicine import MedicineInventory
from app.models.beds import BedInventory
from app.models.reservation import Reservation
from app.models.audit import AuditLog
from app.schemas.reservation import ReservationCreate, ReservationResponse
from app.cache.cache_invalidation import invalidate_inventory_cache

logger = logging.getLogger(__name__)


def apply_for_update(query, db: Session):
    """Apply row-level locking FOR UPDATE, gracefully adapting for SQLite in tests."""
    try:
        bind = db.get_bind()
        if bind and bind.dialect.name == "sqlite":
            return query
    except Exception:
        pass
    return query.with_for_update()


class ReservationService:
    @staticmethod
    def create_reservation(
        db: Session, user: User, payload: ReservationCreate, max_retries: int = 3
    ) -> ReservationResponse:
        """
        Creates an atomic reservation with row-level locking (SELECT ... FOR UPDATE).
        Handles:
        - Blood group reservability rule check (O+, O- blocked for public users)
        - Atomic decrement & reservation creation in a single transaction
        - 409 Conflict if stock is insufficient
        - Deadlock/serialization retries with backoff
        - Cache invalidation on success
        """
        resource_type = payload.resource_type.lower().strip()
        ref = payload.resource_ref.strip()

        # Blood reservability rule validation
        if resource_type == "blood":
            if not settings.is_blood_group_reservable(ref):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Blood group '{ref}' is designated as non-reservable (display-only) for public users."
                )

        hospital = db.query(Hospital).filter(Hospital.id == payload.hospital_id).first()
        if not hospital:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hospital ID {payload.hospital_id} not found."
            )

        attempt = 0
        while attempt < max_retries:
            attempt += 1
            try:
                # Execute in an isolated transaction
                reservation = ReservationService._execute_atomic_reservation(
                    db=db, user=user, payload=payload, hospital=hospital
                )
                db.commit()

                # Invalidate cached read endpoints
                invalidate_inventory_cache(payload.hospital_id, resource_type)

                resp = ReservationResponse.model_validate(reservation)
                resp.hospital_name = hospital.name
                return resp

            except HTTPException:
                db.rollback()
                raise
            except (OperationalError, DBAPIError) as exc:
                db.rollback()
                error_msg = str(exc).lower()
                if "deadlock" in error_msg or "serialization" in error_msg or "database is locked" in error_msg:
                    if attempt < max_retries:
                        time.sleep(random.uniform(0.05, 0.15) * attempt)
                        continue
                logger.error("DB Error during reservation: %s", str(exc))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database concurrency error while reserving resource."
                )
            except Exception as e:
                db.rollback()
                logger.error("Unexpected error creating reservation: %s", str(e))
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Unexpected error occurred while creating reservation."
                )

    @staticmethod
    def _execute_atomic_reservation(
        db: Session, user: User, payload: ReservationCreate, hospital: Hospital
    ) -> Reservation:
        resource_type = payload.resource_type.lower().strip()
        ref = payload.resource_ref.strip()
        qty = payload.quantity

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=settings.RESERVATION_EXPIRY_MINUTES)

        if resource_type == "blood":
            q = db.query(BloodInventory).filter(
                BloodInventory.hospital_id == payload.hospital_id,
                BloodInventory.blood_group == ref
            )
            q = apply_for_update(q, db)
            item = q.first()

            if not item or item.units_available < qty:
                available = item.units_available if item else 0
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient blood units available. Requested: {qty}, Available: {available}"
                )

            # Prioritize emergency requests when stock is low
            if not payload.is_emergency and (item.units_available - qty < settings.EMERGENCY_RESERVATION_BUFFER_THRESHOLD):
                if item.units_available <= settings.EMERGENCY_RESERVATION_BUFFER_THRESHOLD:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Remaining units reserved for critical emergency triage."
                    )

            # Atomic conditional update preventing concurrent overselling
            rows_updated = db.query(BloodInventory).filter(
                BloodInventory.id == item.id,
                BloodInventory.units_available >= qty
            ).update(
                {
                    BloodInventory.units_available: BloodInventory.units_available - qty,
                    BloodInventory.updated_at: now
                },
                synchronize_session="fetch"
            )
            if rows_updated == 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Concurrent reservation conflict: Insufficient blood units remaining."
                )

        elif resource_type == "medicine":
            q = db.query(MedicineInventory).filter(
                MedicineInventory.hospital_id == payload.hospital_id,
                MedicineInventory.name == ref
            )
            q = apply_for_update(q, db)
            item = q.first()

            if not item or item.quantity_available < qty:
                available = item.quantity_available if item else 0
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient medicine quantity available. Requested: {qty}, Available: {available}"
                )

            if not payload.is_emergency and (item.quantity_available - qty < settings.EMERGENCY_RESERVATION_BUFFER_THRESHOLD):
                if item.quantity_available <= settings.EMERGENCY_RESERVATION_BUFFER_THRESHOLD:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Remaining units reserved for emergency medical procedures."
                    )

            rows_updated = db.query(MedicineInventory).filter(
                MedicineInventory.id == item.id,
                MedicineInventory.quantity_available >= qty
            ).update(
                {
                    MedicineInventory.quantity_available: MedicineInventory.quantity_available - qty,
                    MedicineInventory.updated_at: now
                },
                synchronize_session="fetch"
            )
            if rows_updated == 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Concurrent reservation conflict: Insufficient medicine quantity remaining."
                )

        elif resource_type == "bed":
            q = db.query(BedInventory).filter(
                BedInventory.hospital_id == payload.hospital_id,
                BedInventory.bed_type == ref.lower()
            )
            q = apply_for_update(q, db)
            item = q.first()

            if not item or item.available_beds < qty:
                available = item.available_beds if item else 0
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Insufficient beds available. Requested: {qty}, Available: {available}"
                )

            rows_updated = db.query(BedInventory).filter(
                BedInventory.id == item.id,
                BedInventory.available_beds >= qty
            ).update(
                {
                    BedInventory.available_beds: BedInventory.available_beds - qty,
                    BedInventory.updated_at: now
                },
                synchronize_session="fetch"
            )
            if rows_updated == 0:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Concurrent reservation conflict: Insufficient beds remaining."
                )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported resource type: '{resource_type}'"
            )

        # Create reservation record
        reservation = Reservation(
            user_id=user.id,
            hospital_id=payload.hospital_id,
            resource_type=resource_type,
            resource_ref=ref,
            quantity=qty,
            status="confirmed",
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )
        db.add(reservation)
        db.flush()

        # Audit entry
        audit = AuditLog(
            action="RESERVATION_CONFIRMED",
            performed_by_id=user.id,
            hospital_id=hospital.id,
            reservation_id=reservation.id,
            details=f"Reserved {qty} of {resource_type} ({ref})"
        )
        db.add(audit)

        return reservation

    @staticmethod
    def cancel_reservation(db: Session, user: User, reservation_id: int) -> ReservationResponse:
        """User cancels their own active reservation and returns stock to inventory."""
        reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
        if not reservation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found")

        # Public users can only cancel their own reservations
        if user.role != "admin" and reservation.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to cancel this reservation")

        if reservation.status != "confirmed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel reservation with status '{reservation.status}'"
            )

        # Restore stock atomically
        ReservationService._return_stock(db, reservation)
        reservation.status = "cancelled"
        reservation.cancellation_reason = "Cancelled by user"
        reservation.updated_at = datetime.now(timezone.utc)

        audit = AuditLog(
            action="RESERVATION_USER_CANCELLED",
            performed_by_id=user.id,
            hospital_id=reservation.hospital_id,
            reservation_id=reservation.id,
            details=f"User cancelled reservation of {reservation.quantity} {reservation.resource_ref}"
        )
        db.add(audit)
        db.commit()

        invalidate_inventory_cache(reservation.hospital_id, reservation.resource_type)
        resp = ReservationResponse.model_validate(reservation)
        if reservation.hospital:
            resp.hospital_name = reservation.hospital.name
        return resp

    @staticmethod
    def _return_stock(db: Session, reservation: Reservation):
        """Restores reserved stock back to the inventory table."""
        res_type = reservation.resource_type.lower()
        qty = reservation.quantity
        h_id = reservation.hospital_id
        ref = reservation.resource_ref

        if res_type == "blood":
            q = db.query(BloodInventory).filter(
                BloodInventory.hospital_id == h_id,
                BloodInventory.blood_group == ref
            )
            q = apply_for_update(q, db)
            item = q.first()
            if item:
                item.units_available += qty
                item.updated_at = datetime.now(timezone.utc)

        elif res_type == "medicine":
            q = db.query(MedicineInventory).filter(
                MedicineInventory.hospital_id == h_id,
                MedicineInventory.name == ref
            )
            q = apply_for_update(q, db)
            item = q.first()
            if item:
                item.quantity_available += qty
                item.updated_at = datetime.now(timezone.utc)

        elif res_type == "bed":
            q = db.query(BedInventory).filter(
                BedInventory.hospital_id == h_id,
                BedInventory.bed_type == ref.lower()
            )
            q = apply_for_update(q, db)
            item = q.first()
            if item:
                item.available_beds = min(item.total_beds, item.available_beds + qty)
                item.updated_at = datetime.now(timezone.utc)

    @staticmethod
    def get_user_reservations(db: Session, user: User) -> List[ReservationResponse]:
        """Fetch all reservations created by the current user."""
        reservations = db.query(Reservation).filter(Reservation.user_id == user.id).order_by(Reservation.created_at.desc()).all()
        results = []
        for r in reservations:
            resp = ReservationResponse.model_validate(r)
            if r.hospital:
                resp.hospital_name = r.hospital.name
            results.append(resp)
        return results

    @staticmethod
    def get_hospital_reservations(db: Session, hospital_id: int) -> List[ReservationResponse]:
        """Fetch all reservations for a specific hospital (staff view)."""
        reservations = db.query(Reservation).filter(Reservation.hospital_id == hospital_id).order_by(Reservation.created_at.desc()).all()
        results = []
        for r in reservations:
            resp = ReservationResponse.model_validate(r)
            if r.hospital:
                resp.hospital_name = r.hospital.name
            results.append(resp)
        return results
