from datetime import datetime, timedelta, timezone
from app.models.blood import BloodInventory
from app.models.reservation import Reservation
from app.services.expiry_service import ExpiryService


def test_expire_stale_reservations(db, sample_hospital, sample_user):
    now = datetime.now(timezone.utc)
    # Blood inventory with 5 units
    blood = BloodInventory(
        hospital_id=sample_hospital.id,
        blood_group="B-",
        units_available=5,
        updated_at=now
    )
    db.add(blood)
    db.commit()

    # Create an expired reservation (expires_at 10 minutes in the past)
    res_stale = Reservation(
        user_id=sample_user.id,
        hospital_id=sample_hospital.id,
        resource_type="blood",
        resource_ref="B-",
        quantity=3,
        status="confirmed",
        expires_at=now - timedelta(minutes=10),
        created_at=now - timedelta(minutes=40),
        updated_at=now - timedelta(minutes=40),
    )
    # Create an active reservation (expires_at 20 minutes in the future)
    res_active = Reservation(
        user_id=sample_user.id,
        hospital_id=sample_hospital.id,
        resource_type="blood",
        resource_ref="B-",
        quantity=2,
        status="confirmed",
        expires_at=now + timedelta(minutes=20),
        created_at=now,
        updated_at=now,
    )
    db.add_all([res_stale, res_active])
    db.commit()

    # Expire stale reservations
    count = ExpiryService.expire_stale_reservations(db)
    assert count == 1

    # Stale reservation is marked expired
    db.refresh(res_stale)
    assert res_stale.status == "expired"
    assert "Expired automatically" in res_stale.cancellation_reason

    # Active reservation remains confirmed
    db.refresh(res_active)
    assert res_active.status == "confirmed"

    # Stock should have 3 units restored (5 + 3 = 8)
    db.refresh(blood)
    assert blood.units_available == 8
