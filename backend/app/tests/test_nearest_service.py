from datetime import datetime, timezone
from app.models.hospital import Hospital
from app.models.beds import BedInventory
from app.services.nearest_service import NearestService, haversine_km


def test_haversine_calculation():
    # Distance between Clock Tower Dehradun and Max Hospital Dehradun (~4.9 km)
    dist = haversine_km(30.3165, 78.0322, 30.3402, 78.0782)
    assert 4.0 <= dist <= 6.0


def test_nearest_resource_search(db, sample_hospital):
    # Add second farther hospital (Rishikesh, ~35km away)
    h2 = Hospital(
        name="AIIMS Rishikesh",
        lat=30.0768,
        lng=78.2882,
        address="Virbhadra Road, Rishikesh",
        phone="+91-135-2462929"
    )
    db.add(h2)
    db.commit()

    # Add ICU beds to both
    now = datetime.now(timezone.utc)
    db.add(BedInventory(hospital_id=sample_hospital.id, bed_type="icu", total_beds=10, available_beds=3, updated_at=now))
    db.add(BedInventory(hospital_id=h2.id, bed_type="icu", total_beds=50, available_beds=12, updated_at=now))
    db.commit()

    # User searches from Dehradun city center (30.3165, 78.0322)
    nearest = NearestService.find_nearest_resource(
        db, lat=30.3165, lng=78.0322, resource_type="bed", resource_ref="icu"
    )

    assert len(nearest) == 2
    # First result must be Dehradun Central Hospital (closer)
    assert nearest[0].hospital_id == sample_hospital.id
    assert nearest[0].distance_km < nearest[1].distance_km
    assert nearest[1].hospital_id == h2.id
