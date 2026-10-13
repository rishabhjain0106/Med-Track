from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.database import Base


class BedInventory(Base):
    __tablename__ = "bed_inventory"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    bed_type = Column(String(50), nullable=False, index=True)  # 'general', 'icu', 'emergency'
    total_beds = Column(Integer, nullable=False, default=0)
    available_beds = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("hospital_id", "bed_type", name="uq_hospital_bed_type"),
    )

    # Relationships
    hospital = relationship("Hospital", back_populates="bed_inventory")
