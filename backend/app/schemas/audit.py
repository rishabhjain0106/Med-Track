from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    action: str
    performed_by_id: Optional[int] = None
    performer_name: Optional[str] = None
    hospital_id: Optional[int] = None
    reservation_id: Optional[int] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
