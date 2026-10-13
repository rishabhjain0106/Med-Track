import concurrent.futures
import pytest
from datetime import datetime, timezone
from fastapi import HTTPException
from app.models.user import User
from app.models.blood import BloodInventory
from app.models.reservation import Reservation
from app.schemas.reservation import ReservationCreate
from app.services.reservation_service import ReservationService
from app.tests.conftest import TestingSessionLocal


def test_create_and_cancel_reservation(db, sample_hospital, sample_user):
    # Setup initial blood stock
    blood = BloodInventory(
        hospital_id=sample_hospital.id,
        blood_group="A+",
        units_available=5,
        updated_at=datetime.now(timezone.utc)
    )
    db.add(blood)
    db.commit()

    # Reserve 2 units
    payload = ReservationCreate(
        hospital_id=sample_hospital.id,
        resource_type="blood",
        resource_ref="A+",
        quantity=2,
        is_emergency=False
    )
    res = ReservationService.create_reservation(db, sample_user, payload)
    assert res.status == "confirmed"
    assert res.quantity == 2

    # Check stock decreased to 3
    db.refresh(blood)
    assert blood.units_available == 3

    # User cancels reservation
    cancelled = ReservationService.cancel_reservation(db, sample_user, res.id)
    assert cancelled.status == "cancelled"

    # Check stock restored to 5
    db.refresh(blood)
    assert blood.units_available == 5


def test_o_negative_blood_is_display_only(db, sample_hospital, sample_user):
    blood = BloodInventory(
        hospital_id=sample_hospital.id,
        blood_group="O-",
        units_available=10,
        updated_at=datetime.now(timezone.utc)
    )
    db.add(blood)
    db.commit()

    payload = ReservationCreate(
        hospital_id=sample_hospital.id,
        resource_type="blood",
        resource_ref="O-",
        quantity=1,
        is_emergency=False
    )
    with pytest.raises(HTTPException) as exc:
        ReservationService.create_reservation(db, sample_user, payload)
    assert exc.value.status_code == 400
    assert "non-reservable" in exc.value.detail


def test_insufficient_stock_raises_409(db, sample_hospital, sample_user):
    blood = BloodInventory(
        hospital_id=sample_hospital.id,
        blood_group="B+",
        units_available=2,
        updated_at=datetime.now(timezone.utc)
    )
    db.add(blood)
    db.commit()

    payload = ReservationCreate(
        hospital_id=sample_hospital.id,
        resource_type="blood",
        resource_ref="B+",
        quantity=5,
        is_emergency=False
    )
    with pytest.raises(HTTPException) as exc:
        ReservationService.create_reservation(db, sample_user, payload)
    assert exc.value.status_code == 409


def test_fifty_concurrent_reservations_at_stock_of_ten(db, sample_hospital, sample_user):
    """
    CRITICAL CONCURRENCY TEST:
    Fires 50 concurrent reservation requests at stock of 10 and asserts exactly 10 succeed.
    """
    # Setup inventory with exactly 10 units of A- blood
    blood = BloodInventory(
        hospital_id=sample_hospital.id,
        blood_group="A-",
        units_available=10,
        updated_at=datetime.now(timezone.utc)
    )
    db.add(blood)
    db.commit()

    successes = []
    conflicts = []
    errors = []

    user_id = sample_user.id
    h_id = sample_hospital.id

    def attempt_reservation(index: int):
        session = TestingSessionLocal()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            payload = ReservationCreate(
                hospital_id=h_id,
                resource_type="blood",
                resource_ref="A-",
                quantity=1,
                is_emergency=True  # Emergency ensures full allocation of all 10 units down to 0
            )
            resp = ReservationService.create_reservation(
                db=session, user=user, payload=payload
            )
            return ("success", resp.id)
        except HTTPException as he:
            if he.status_code == 409:
                return ("conflict", he.detail)
            return ("http_error", he.detail)
        except Exception as e:
            return ("error", str(e))
        finally:
            session.close()

    # Fire 50 concurrent threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
        futures = [executor.submit(attempt_reservation, i) for i in range(50)]
        for f in concurrent.futures.as_completed(futures):
            res_type, detail = f.result()
            if res_type == "success":
                successes.append(detail)
            elif res_type == "conflict":
                conflicts.append(detail)
            else:
                errors.append(detail)

    # Assertions
    assert len(errors) == 0, f"Unexpected errors: {errors}"
    assert len(successes) == 10, f"Expected exactly 10 successes, got {len(successes)}"
    assert len(conflicts) == 40, f"Expected exactly 40 conflicts (409), got {len(conflicts)}"

    # Verify inventory is strictly 0
    db.refresh(blood)
    assert blood.units_available == 0

    # Verify 10 reservations exist in DB
    total_confirmed = (
        db.query(Reservation)
        .filter(
            Reservation.hospital_id == sample_hospital.id,
            Reservation.resource_ref == "A-",
            Reservation.status == "confirmed"
        )
        .count()
    )
    assert total_confirmed == 10
