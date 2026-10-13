from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class HospitalBase(BaseModel):
    name: str
    lat: float
    lng: float
    address: str
    phone: Optional[str] = None


class HospitalCreate(HospitalBase):
    pass


class HospitalUpdate(BaseModel):
    name: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    address: Optional[str] = None
    phone: Optional[str] = None


class HospitalResponse(HospitalBase):
    id: int
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
