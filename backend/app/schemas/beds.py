from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class BedInventoryBase(BaseModel):
    bed_type: str = Field(..., description="'general', 'icu', or 'emergency'")
    total_beds: int = Field(ge=0, description="Total bed capacity")
    available_beds: int = Field(ge=0, description="Currently available beds")


class BedInventoryCreate(BedInventoryBase):
    @model_validator(mode="after")
    def validate_beds(self):
        if self.available_beds > self.total_beds:
            raise ValueError("Available beds cannot exceed total beds")
        return self


class BedInventoryUpdate(BaseModel):
    total_beds: Optional[int] = Field(None, ge=0)
    available_beds: Optional[int] = Field(None, ge=0)


class BedInventoryResponse(BedInventoryBase):
    id: int
    hospital_id: int
    updated_at: Optional[datetime] = None
    source: str = "local"

    model_config = ConfigDict(from_attributes=True)
