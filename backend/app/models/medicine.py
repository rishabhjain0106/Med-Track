from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class MedicineInventory(Base):
    __tablename__ = "medicine_inventory"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    name = Column(String(200), nullable=False, index=True)
    quantity_available = Column(Integer, nullable=False, default=0)
    expiry_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("hospital_id", "name", name="uq_hospital_medicine_name"),
    )

    # Relationships
    hospital = relationship("Hospital", back_populates="medicine_inventory")
