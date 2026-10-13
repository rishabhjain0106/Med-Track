from typing import List
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.public import NearestResourceItem
from app.services.nearest_service import NearestService
from app.routers.public_availability import apply_rate_limit

router = APIRouter(prefix="/public/nearest", tags=["Nearest Resource"])


@router.get("", response_model=List[NearestResourceItem])
def find_nearest_available(
    request: Request,
    lat: float = Query(..., description="User latitude (e.g. 30.3165 for Dehradun)"),
    lng: float = Query(..., description="User longitude (e.g. 78.0322 for Dehradun)"),
    resource_type: str = Query(..., description="'blood', 'medicine', or 'bed'"),
    resource_ref: str = Query(..., description="Blood group (e.g. 'B+'), medicine name, or bed type"),
    max_distance_km: float = Query(100.0, ge=1.0, le=500.0, description="Max search radius in km"),
    db: Session = Depends(get_db),
    _rate_limit=Depends(apply_rate_limit),
):
    """
    Search for closest hospitals with available stock matching user coordinates.
    Sorted by Haversine distance in ascending order. Cached in Redis.
    """
    return NearestService.find_nearest_resource(
        db=db,
        lat=lat,
        lng=lng,
        resource_type=resource_type,
        resource_ref=resource_ref,
        max_distance_km=max_distance_km,
    )
