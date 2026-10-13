import math
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.hospital import Hospital
from app.models.blood import BloodInventory
from app.models.medicine import MedicineInventory
from app.models.beds import BedInventory
from app.schemas.public import NearestResourceItem
from app.cache.redis_client import cache_client
from app.cache.cache_keys import nearest_resource_key
from app.config import settings

logger = logging.getLogger(__name__)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance in kilometers between two points
    on the earth (specified in decimal degrees).
    """
    radius = 6371.0  # Earth radius in kilometers

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return round(radius * c, 2)


class NearestService:
    @staticmethod
    def find_nearest_resource(
        db: Session,
        lat: float,
        lng: float,
        resource_type: str,
        resource_ref: str,
        max_distance_km: float = 100.0
    ) -> List[NearestResourceItem]:
        """
        Locates hospitals with active stock for the requested item,
        computes Haversine distance, sorts by distance, and caches result in Redis.
        """
        r_type = resource_type.lower().strip()
        r_ref = resource_ref.strip()

        # Check Redis Cache
        cache_key = nearest_resource_key(r_type, r_ref, lat, lng, max_distance_km)
        cached_data = cache_client.get(cache_key)
        if cached_data:
            try:
                items = json.loads(cached_data)
                return [NearestResourceItem(**i) for i in items]
            except Exception as e:
                logger.warning("Cache parsing error in nearest_service: %s", str(e))

        results: List[NearestResourceItem] = []
        hospitals = db.query(Hospital).all()

        for h in hospitals:
            available_qty = 0
            user_reservable = True

            if r_type == "blood":
                rec = db.query(BloodInventory).filter(
                    BloodInventory.hospital_id == h.id,
                    BloodInventory.blood_group == r_ref.upper()
                ).first()
                if rec:
                    available_qty = rec.units_available
                user_reservable = settings.is_blood_group_reservable(r_ref.upper())

            elif r_type == "medicine":
                # Case-insensitive match on name
                rec = db.query(MedicineInventory).filter(
                    MedicineInventory.hospital_id == h.id,
                    MedicineInventory.name.ilike(f"%{r_ref}%")
                ).first()
                if rec:
                    available_qty = rec.quantity_available
                    r_ref = rec.name  # Use exact name

            elif r_type == "bed":
                rec = db.query(BedInventory).filter(
                    BedInventory.hospital_id == h.id,
                    BedInventory.bed_type == r_ref.lower()
                ).first()
                if rec:
                    available_qty = rec.available_beds

            if available_qty > 0:
                dist = haversine_km(lat, lng, h.lat, h.lng)
                if dist <= max_distance_km:
                    results.append(
                        NearestResourceItem(
                            hospital_id=h.id,
                            hospital_name=h.name,
                            hospital_address=h.address,
                            hospital_phone=h.phone,
                            lat=h.lat,
                            lng=h.lng,
                            distance_km=dist,
                            resource_type=r_type,
                            resource_ref=r_ref,
                            available_units=available_qty,
                            user_reservable=user_reservable,
                            source="local",
                        )
                    )

        # Sort by distance in ascending order
        results.sort(key=lambda x: x.distance_km)

        # Cache in Redis with short TTL
        cache_client.set(
            cache_key,
            json.dumps([r.model_dump(mode="json") for r in results]),
            ex=settings.NEAREST_SEARCH_CACHE_TTL_SECONDS
        )

        return results
