from typing import List, Optional
from sqlalchemy.orm import Session
from app.data_sources.base import InventoryDataSource
from app.models.blood import BloodInventory
from app.models.medicine import MedicineInventory
from app.models.beds import BedInventory
from app.schemas.blood import BloodInventoryResponse
from app.schemas.medicine import MedicineInventoryResponse
from app.schemas.beds import BedInventoryResponse
from app.config import settings


class LocalDbDataSource(InventoryDataSource):
    """
    Default data source reading directly from PostgreSQL/SQLAlchemy.
    Supports atomic transactional locking and write operations.
    """

    def get_blood_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[BloodInventoryResponse]:
        query = db.query(BloodInventory)
        if hospital_id is not None:
            query = query.filter(BloodInventory.hospital_id == hospital_id)
        records = query.all()

        results = []
        for r in records:
            item = BloodInventoryResponse.model_validate(r)
            # Evaluate reservability based on config settings
            item.user_reservable = settings.is_blood_group_reservable(r.blood_group)
            item.source = "local"
            results.append(item)
        return results

    def get_medicine_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[MedicineInventoryResponse]:
        query = db.query(MedicineInventory)
        if hospital_id is not None:
            query = query.filter(MedicineInventory.hospital_id == hospital_id)
        records = query.all()

        results = []
        for r in records:
            item = MedicineInventoryResponse.model_validate(r)
            item.source = "local"
            results.append(item)
        return results

    def get_bed_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[BedInventoryResponse]:
        query = db.query(BedInventory)
        if hospital_id is not None:
            query = query.filter(BedInventory.hospital_id == hospital_id)
        records = query.all()

        results = []
        for r in records:
            item = BedInventoryResponse.model_validate(r)
            item.source = "local"
            results.append(item)
        return results
