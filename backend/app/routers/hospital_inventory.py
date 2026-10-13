from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.blood import BloodInventoryCreate, BloodInventoryResponse
from app.schemas.medicine import MedicineInventoryCreate, MedicineInventoryResponse
from app.schemas.beds import BedInventoryCreate, BedInventoryResponse
from app.schemas.public import HospitalInventorySummary
from app.services.inventory_service import InventoryService
from app.security.permissions import require_hospital_staff, verify_hospital_access

router = APIRouter(prefix="/hospital/inventory", tags=["Hospital Inventory"])


@router.get("/{hospital_id}", response_model=HospitalInventorySummary)
def get_hospital_inventory(
    hospital_id: int,
    db: Session = Depends(get_db),
    staff_user: User = Depends(verify_hospital_access)
):
    """Retrieve complete inventory for a hospital managed by staff."""
    return InventoryService.get_hospital_inventory(db, hospital_id)


@router.post("/blood", response_model=BloodInventoryResponse, status_code=status.HTTP_200_OK)
def update_blood(
    payload: BloodInventoryCreate,
    db: Session = Depends(get_db),
    staff_user: User = Depends(require_hospital_staff)
):
    """Hospital staff adds or updates blood inventory."""
    return InventoryService.update_blood_inventory(
        db=db,
        hospital_id=staff_user.hospital_id,
        payload=payload,
        staff_user=staff_user
    )


@router.post("/medicine", response_model=MedicineInventoryResponse, status_code=status.HTTP_200_OK)
def update_medicine(
    payload: MedicineInventoryCreate,
    db: Session = Depends(get_db),
    staff_user: User = Depends(require_hospital_staff)
):
    """Hospital staff adds or updates medicine inventory."""
    return InventoryService.update_medicine_inventory(
        db=db,
        hospital_id=staff_user.hospital_id,
        payload=payload,
        staff_user=staff_user
    )


@router.post("/beds", response_model=BedInventoryResponse, status_code=status.HTTP_200_OK)
def update_beds(
    payload: BedInventoryCreate,
    db: Session = Depends(get_db),
    staff_user: User = Depends(require_hospital_staff)
):
    """Hospital staff updates hospital bed capacities."""
    return InventoryService.update_bed_inventory(
        db=db,
        hospital_id=staff_user.hospital_id,
        payload=payload,
        staff_user=staff_user
    )
