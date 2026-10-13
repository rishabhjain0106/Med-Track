from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)  # 'blood', 'medicine', 'bed'
    resource_ref = Column(String(200), nullable=False, index=True)  # 'A+', 'Paracetamol', 'icu'
    quantity = Column(Integer, nullable=False, default=1)
    status = Column(String(50), nullable=False, default="confirmed", index=True)
    # statuses: 'pending', 'confirmed', 'cancelled', 'expired', 'cancelled_by_hospital'
    expires_at = Column(DateTime, nullable=False)
    cancellation_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="reservations")
    hospital = relationship("Hospital", back_populates="reservations")
    audit_logs = relationship("AuditLog", back_populates="reservation")
