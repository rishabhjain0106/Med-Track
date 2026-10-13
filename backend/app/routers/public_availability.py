import json
import logging
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.hospital import Hospital
from app.schemas.public import HospitalInventorySummary, HospitalResponse
from app.data_sources import get_blood_data_source, get_medicine_data_source, get_bed_data_source
from app.cache.redis_client import cache_client
from app.cache.cache_keys import public_availability_key
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/public/availability", tags=["Public Availability"])


def apply_rate_limit(request: Request):
    """Enforce basic IP rate limiting on public endpoints."""
    client_ip = request.client.host if request.client else "unknown"
    allowed = cache_client.check_rate_limit(
        identifier=client_ip,
        limit=settings.RATE_LIMIT_REQUESTS,
        window=settings.RATE_LIMIT_WINDOW_SECONDS,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again shortly."
        )


@router.get("", response_model=List[HospitalInventorySummary])
def get_all_availability(
    request: Request,
    db: Session = Depends(get_db),
    _rate_limit=Depends(apply_rate_limit)
):
    """
    Public inventory catalog across all hospitals for blood, medicines, and beds.
    Served from Redis cache with 45s TTL.
    """
    cache_key = public_availability_key()
    cached = cache_client.get(cache_key)
    if cached:
        try:
            data = json.loads(cached)
            return [HospitalInventorySummary(**item) for item in data]
        except Exception as e:
            logger.warning("Cache deserialization failed: %s", str(e))

    # Query from database / data sources
    hospitals = db.query(Hospital).order_by(Hospital.name).all()
    blood_source = get_blood_data_source()
    med_source = get_medicine_data_source()
    bed_source = get_bed_data_source()

    results: List[HospitalInventorySummary] = []
    for h in hospitals:
        blood = blood_source.get_blood_availability(db, h.id)
        medicines = med_source.get_medicine_availability(db, h.id)
        beds = bed_source.get_bed_availability(db, h.id)

        results.append(
            HospitalInventorySummary(
                hospital=HospitalResponse.model_validate(h),
                blood=blood,
                medicines=medicines,
                beds=beds
            )
        )

    # Cache output in Redis
    cache_client.set(
        cache_key,
        json.dumps([r.model_dump(mode="json") for r in results]),
        ex=settings.CACHE_DEFAULT_TTL_SECONDS
    )
    return results


@router.get("/hospitals", response_model=List[HospitalResponse])
def get_hospitals_list(
    db: Session = Depends(get_db),
    _rate_limit=Depends(apply_rate_limit)
):
    """List all registered hospitals."""
    hospitals = db.query(Hospital).order_by(Hospital.name).all()
    return [HospitalResponse.model_validate(h) for h in hospitals]
