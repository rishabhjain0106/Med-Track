import asyncio
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.reservation import Reservation
from app.models.audit import AuditLog
from app.services.reservation_service import ReservationService
from app.cache.cache_invalidation import invalidate_inventory_cache
from app.config import settings

logger = logging.getLogger(__name__)


class ExpiryService:
    @staticmethod
    def expire_stale_reservations(db: Session) -> int:
        """
        Scans for active reservations past their TTL expires_at,
        restores stock back to inventory, updates status to 'expired',
        and invalidates corresponding cache.
        """
        now = datetime.now(timezone.utc)
        # Check active reservations that have passed expiry
        stale_reservations = (
            db.query(Reservation)
            .filter(
                Reservation.status.in_(["confirmed", "pending"]),
                Reservation.expires_at <= now,
            )
            .all()
        )

        expired_count = 0
        for res in stale_reservations:
            try:
                # Return stock atomically
                ReservationService._return_stock(db, res)
                res.status = "expired"
                res.cancellation_reason = "Expired automatically after reservation timeout window."
                res.updated_at = now

                audit = AuditLog(
                    action="TTL_EXPIRATION_RELEASE",
                    hospital_id=res.hospital_id,
                    reservation_id=res.id,
                    details=f"Released {res.quantity} of {res.resource_ref} ({res.resource_type}) back to inventory.",
                )
                db.add(audit)
                db.flush()

                invalidate_inventory_cache(res.hospital_id, res.resource_type)
                expired_count += 1
            except Exception as e:
                logger.error("Failed to expire reservation %s: %s", res.id, str(e))

        if expired_count > 0:
            db.commit()
            logger.info("Expired %d stale reservations and returned stock.", expired_count)

        return expired_count


async def run_expiry_background_loop():
    """Async background worker that periodically purges expired reservations."""
    logger.info("Started background reservation TTL expiry worker.")
    while True:
        try:
            db = SessionLocal()
            try:
                ExpiryService.expire_stale_reservations(db)
            finally:
                db.close()
        except Exception as e:
            logger.error("Error in expiry background worker: %s", str(e))
        await asyncio.sleep(settings.EXPIRY_CHECK_INTERVAL_SECONDS)
