from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ReservationCreate(BaseModel):
    hospital_id: int
    resource_type: str = Field(..., description="'blood', 'medicine', or 'bed'")
    resource_ref: str = Field(..., description="e.g. 'A+', 'Paracetamol 650mg', 'icu'")
    quantity: int = Field(default=1, gt=0, description="Quantity to reserve")
    is_emergency: bool = Field(default=False, description="Emergency priority flag")


class ReservationResponse(BaseModel):
    id: int
    user_id: int
    hospital_id: int
    hospital_name: Optional[str] = None
    resource_type: str
    resource_ref: str
    quantity: int
    status: str
    expires_at: datetime
    cancellation_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class EmergencyOverrideRequest(BaseModel):
    reservation_id: int
    reason: str = Field(..., min_length=5, description="Mandatory medical justification for emergency override")
