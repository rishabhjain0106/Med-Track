from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.hospital import Hospital
from app.models.blood import BloodInventory
from app.models.medicine import MedicineInventory
from app.models.beds import BedInventory
from app.models.user import User
from app.models.audit import AuditLog
from app.schemas.blood import BloodInventoryCreate, BloodInventoryUpdate, BloodInventoryResponse
from app.schemas.medicine import MedicineInventoryCreate, MedicineInventoryUpdate, MedicineInventoryResponse
from app.schemas.beds import BedInventoryCreate, BedInventoryUpdate, BedInventoryResponse
from app.schemas.public import HospitalInventorySummary, HospitalResponse
from app.data_sources import get_blood_data_source, get_medicine_data_source, get_bed_data_source
from app.cache.cache_invalidation import invalidate_inventory_cache
from app.config import settings


class InventoryService:
    @staticmethod
    def get_hospital_inventory(db: Session, hospital_id: int) -> HospitalInventorySummary:
        """Fetch full inventory for a single hospital using data sources."""
        hospital = db.query(Hospital).filter(Hospital.id == hospital_id).first()
        if not hospital:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

        blood_source = get_blood_data_source()
        med_source = get_medicine_data_source()
        bed_source = get_bed_data_source()

        blood = blood_source.get_blood_availability(db, hospital_id)
        medicines = med_source.get_medicine_availability(db, hospital_id)
        beds = bed_source.get_bed_availability(db, hospital_id)

        return HospitalInventorySummary(
            hospital=HospitalResponse.model_validate(hospital),
            blood=blood,
            medicines=medicines,
            beds=beds
        )

    @staticmethod
    def update_blood_inventory(
        db: Session, hospital_id: int, payload: BloodInventoryCreate, staff_user: User
    ) -> BloodInventoryResponse:
        """Staff adds or updates blood stock for their hospital."""
        blood_group = payload.blood_group.upper().strip()
        record = db.query(BloodInventory).filter(
            BloodInventory.hospital_id == hospital_id,
            BloodInventory.blood_group == blood_group
        ).first()

        now = datetime.now(timezone.utc)
        if record:
            record.units_available = payload.units_available
            record.expiry_date = payload.expiry_date
            record.updated_at = now
        else:
            record = BloodInventory(
                hospital_id=hospital_id,
                blood_group=blood_group,
                units_available=payload.units_available,
                expiry_date=payload.expiry_date,
                updated_at=now,
            )
            db.add(record)

        # Audit entry
        audit = AuditLog(
            action="STAFF_BLOOD_STOCK_UPDATE",
            performed_by_id=staff_user.id,
            hospital_id=hospital_id,
            details=f"Updated blood {blood_group} to {payload.units_available} units"
        )
        db.add(audit)
        db.commit()
        db.refresh(record)

        invalidate_inventory_cache(hospital_id, "blood")
        resp = BloodInventoryResponse.model_validate(record)
        resp.user_reservable = settings.is_blood_group_reservable(blood_group)
        return resp

    @staticmethod
    def update_medicine_inventory(
        db: Session, hospital_id: int, payload: MedicineInventoryCreate, staff_user: User
    ) -> MedicineInventoryResponse:
        """Staff adds or updates medicine inventory."""
        med_name = payload.name.strip()
        record = db.query(MedicineInventory).filter(
            MedicineInventory.hospital_id == hospital_id,
            MedicineInventory.name == med_name
        ).first()

        now = datetime.now(timezone.utc)
        if record:
            record.quantity_available = payload.quantity_available
            record.expiry_date = payload.expiry_date
            record.updated_at = now
        else:
            record = MedicineInventory(
                hospital_id=hospital_id,
                name=med_name,
                quantity_available=payload.quantity_available,
                expiry_date=payload.expiry_date,
                updated_at=now,
            )
            db.add(record)

        audit = AuditLog(
            action="STAFF_MEDICINE_STOCK_UPDATE",
            performed_by_id=staff_user.id,
            hospital_id=hospital_id,
            details=f"Updated medicine {med_name} to {payload.quantity_available} units"
        )
        db.add(audit)
        db.commit()
        db.refresh(record)

        invalidate_inventory_cache(hospital_id, "medicine")
        return MedicineInventoryResponse.model_validate(record)

    @staticmethod
    def update_bed_inventory(
        db: Session, hospital_id: int, payload: BedInventoryCreate, staff_user: User
    ) -> BedInventoryResponse:
        """Staff updates hospital bed inventory."""
        bed_type = payload.bed_type.lower().strip()
        record = db.query(BedInventory).filter(
            BedInventory.hospital_id == hospital_id,
            BedInventory.bed_type == bed_type
        ).first()

        now = datetime.now(timezone.utc)
        if record:
            record.total_beds = payload.total_beds
            record.available_beds = payload.available_beds
            record.updated_at = now
        else:
            record = BedInventory(
                hospital_id=hospital_id,
                bed_type=bed_type,
                total_beds=payload.total_beds,
                available_beds=payload.available_beds,
                updated_at=now,
            )
            db.add(record)

        audit = AuditLog(
            action="STAFF_BED_STOCK_UPDATE",
            performed_by_id=staff_user.id,
            hospital_id=hospital_id,
            details=f"Updated {bed_type} beds: {payload.available_beds}/{payload.total_beds} available"
        )
        db.add(audit)
        db.commit()
        db.refresh(record)

        invalidate_inventory_cache(hospital_id, "bed")
        return BedInventoryResponse.model_validate(record)
