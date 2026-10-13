from datetime import datetime, timezone
from app.schemas.blood import BloodInventoryCreate
from app.schemas.medicine import MedicineInventoryCreate
from app.schemas.beds import BedInventoryCreate
from app.services.inventory_service import InventoryService


def test_staff_inventory_updates(db, sample_hospital, sample_staff):
    # 1. Update Blood
    blood_in = BloodInventoryCreate(
        blood_group="AB+",
        units_available=15,
        expiry_date=datetime.now(timezone.utc)
    )
    blood_resp = InventoryService.update_blood_inventory(
        db, sample_hospital.id, blood_in, sample_staff
    )
    assert blood_resp.blood_group == "AB+"
    assert blood_resp.units_available == 15
    assert blood_resp.user_reservable is True

    # 2. Update Medicine
    med_in = MedicineInventoryCreate(
        name="Azithromycin 500mg",
        quantity_available=100
    )
    med_resp = InventoryService.update_medicine_inventory(
        db, sample_hospital.id, med_in, sample_staff
    )
    assert med_resp.name == "Azithromycin 500mg"
    assert med_resp.quantity_available == 100

    # 3. Update Beds
    bed_in = BedInventoryCreate(
        bed_type="icu",
        total_beds=20,
        available_beds=6
    )
    bed_resp = InventoryService.update_bed_inventory(
        db, sample_hospital.id, bed_in, sample_staff
    )
    assert bed_resp.bed_type == "icu"
    assert bed_resp.available_beds == 6
    assert bed_resp.total_beds == 20

    # 4. Fetch Hospital Inventory Summary
    summary = InventoryService.get_hospital_inventory(db, sample_hospital.id)
    assert summary.hospital.name == sample_hospital.name
    assert len(summary.blood) >= 1
    assert len(summary.medicines) >= 1
    assert len(summary.beds) >= 1
