from typing import List, Optional, Any
from pydantic import BaseModel
from app.schemas.blood import BloodInventoryResponse
from app.schemas.medicine import MedicineInventoryResponse
from app.schemas.beds import BedInventoryResponse
from app.schemas.hospital import HospitalResponse


class HospitalInventorySummary(BaseModel):
    hospital: HospitalResponse
    blood: List[BloodInventoryResponse]
    medicines: List[MedicineInventoryResponse]
    beds: List[BedInventoryResponse]


class NearestResourceItem(BaseModel):
    hospital_id: int
    hospital_name: str
    hospital_address: str
    hospital_phone: Optional[str] = None
    lat: float
    lng: float
    distance_km: float
    resource_type: str
    resource_ref: str
    available_units: int
    user_reservable: bool = True
    source: str = "local"


class CacheStatsResponse(BaseModel):
    hits: int
    misses: int
    keys_count: int
    hit_ratio: float
    status: str
