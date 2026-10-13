from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address = Column(String(500), nullable=False)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    users = relationship("User", back_populates="hospital")
    blood_inventory = relationship("BloodInventory", back_populates="hospital", cascade="all, delete-orphan")
    medicine_inventory = relationship("MedicineInventory", back_populates="hospital", cascade="all, delete-orphan")
    bed_inventory = relationship("BedInventory", back_populates="hospital", cascade="all, delete-orphan")
    reservations = relationship("Reservation", back_populates="hospital")
    audit_logs = relationship("AuditLog", back_populates="hospital")
