from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class MedicineInventoryBase(BaseModel):
    name: str = Field(..., description="Medicine name and dosage")
    quantity_available: int = Field(ge=0, description="Quantity available in stock")
    expiry_date: Optional[datetime] = None


class MedicineInventoryCreate(MedicineInventoryBase):
    pass


class MedicineInventoryUpdate(BaseModel):
    quantity_available: Optional[int] = Field(None, ge=0)
    expiry_date: Optional[datetime] = None


class MedicineInventoryResponse(MedicineInventoryBase):
    id: int
    hospital_id: int
    updated_at: Optional[datetime] = None
    source: str = "local"

    model_config = ConfigDict(from_attributes=True)
