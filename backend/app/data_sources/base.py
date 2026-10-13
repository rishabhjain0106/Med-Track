from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from app.schemas.blood import BloodInventoryResponse
from app.schemas.medicine import MedicineInventoryResponse
from app.schemas.beds import BedInventoryResponse


class InventoryDataSource(ABC):
    """
    Abstract interface for inventory data sources.
    Decouples services and routers from specific database models or external APIs.
    """

    @abstractmethod
    def get_blood_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[BloodInventoryResponse]:
        """Fetch blood inventory records across all or single hospital."""
        pass

    @abstractmethod
    def get_medicine_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[MedicineInventoryResponse]:
        """Fetch medicine inventory records across all or single hospital."""
        pass

    @abstractmethod
    def get_bed_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[BedInventoryResponse]:
        """Fetch bed inventory records across all or single hospital."""
        pass
