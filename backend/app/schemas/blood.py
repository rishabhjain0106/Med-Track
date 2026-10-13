from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class BloodInventoryBase(BaseModel):
    blood_group: str = Field(..., description="e.g. A+, A-, B+, B-, AB+, AB-, O+, O-")
    units_available: int = Field(ge=0, description="Number of units in stock")
    expiry_date: Optional[datetime] = None


class BloodInventoryCreate(BloodInventoryBase):
    pass


class BloodInventoryUpdate(BaseModel):
    units_available: Optional[int] = Field(None, ge=0)
    expiry_date: Optional[datetime] = None


class BloodInventoryResponse(BloodInventoryBase):
    id: int
    hospital_id: int
    updated_at: Optional[datetime] = None
    user_reservable: bool = False
    source: str = "local"  # 'local' or 'external'

    model_config = ConfigDict(from_attributes=True)
