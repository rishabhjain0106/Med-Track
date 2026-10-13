from datetime import datetime, timezone
from app.models.medicine import MedicineInventory
from app.models.audit import AuditLog
from app.schemas.reservation import ReservationCreate, EmergencyOverrideRequest
from app.services.reservation_service import ReservationService
from app.services.emergency_service import EmergencyService


def test_emergency_override_cancel(db, sample_hospital, sample_user, sample_staff):
    # Setup initial medicine stock
    med = MedicineInventory(
        hospital_id=sample_hospital.id,
        name="Adrenaline 1mg",
        quantity_available=10,
        updated_at=datetime.now(timezone.utc)
    )
    db.add(med)
    db.commit()

    # User reserves 3 units
    payload = ReservationCreate(
        hospital_id=sample_hospital.id,
        resource_type="medicine",
        resource_ref="Adrenaline 1mg",
        quantity=3,
        is_emergency=False
    )
    res = ReservationService.create_reservation(db, sample_user, payload)
    assert res.status == "confirmed"

    # Stock should be 7
    db.refresh(med)
    assert med.quantity_available == 7

    # Hospital staff executes emergency override
    override_req = EmergencyOverrideRequest(
        reservation_id=res.id,
        reason="Immediate trauma surgery requirement in ER room 3."
    )
    overridden = EmergencyService.override_cancel_reservation(
        db, sample_staff, override_req
    )

    # Check status and reason
    assert overridden.status == "cancelled_by_hospital"
    assert "trauma surgery" in overridden.cancellation_reason

    # Stock restored back to 10
    db.refresh(med)
    assert med.quantity_available == 10

    # Audit log check
    audit = db.query(AuditLog).filter(
        AuditLog.action == "EMERGENCY_OVERRIDE_CANCEL",
        AuditLog.reservation_id == res.id
    ).first()
    assert audit is not None
    assert audit.performed_by_id == sample_staff.id
    assert "trauma surgery" in audit.details
