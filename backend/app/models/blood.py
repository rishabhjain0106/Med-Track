from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class BloodInventory(Base):
    __tablename__ = "blood_inventory"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    blood_group = Column(String(10), nullable=False, index=True)  # e.g., A+, A-, B+, B-, AB+, AB-, O+, O-
    units_available = Column(Integer, nullable=False, default=0)
    expiry_date = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("hospital_id", "blood_group", name="uq_hospital_blood_group"),
    )

    # Relationships
    hospital = relationship("Hospital", back_populates="blood_inventory")
