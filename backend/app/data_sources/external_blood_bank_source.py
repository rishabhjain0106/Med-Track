import json
import logging
from typing import List, Optional
import httpx
from sqlalchemy.orm import Session
from app.data_sources.base import InventoryDataSource
from app.data_sources.local_db_source import LocalDbDataSource
from app.schemas.blood import BloodInventoryResponse
from app.schemas.medicine import MedicineInventoryResponse
from app.schemas.beds import BedInventoryResponse
from app.cache.redis_client import cache_client
from app.cache.cache_keys import external_blood_bank_key
from app.config import settings

logger = logging.getLogger(__name__)


class ExternalBloodBankSource(InventoryDataSource):
    """
    Pluggable external blood bank inventory provider (e.g. e-RaktKosh integration).
    - Checks Redis cache first.
    - Queries configured external API.
    - Displays external units as display-only (user_reservable = False, source = 'external').
    - Gracefully falls back to LocalDbDataSource on network or parsing failure.
    """

    def __init__(self):
        self.local_fallback = LocalDbDataSource()

    def get_blood_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[BloodInventoryResponse]:
        cache_key = f"external_source:blood_all:{hospital_id or 'all'}"
        cached = cache_client.get(cache_key)
        if cached:
            try:
                data = json.loads(cached)
                return [BloodInventoryResponse(**item) for item in data]
            except Exception as e:
                logger.warning("Failed to deserialize cached external blood data: %s", str(e))

        try:
            # Attempt to fetch from external blood bank API
            response = httpx.get(
                settings.EXTERNAL_BLOOD_BANK_API_URL,
                params={"hospital_id": hospital_id} if hospital_id else {},
                timeout=2.0
            )
            response.raise_for_status()
            payload = response.json()

            # -------------------------------------------------------------
            # TODO: Add vendor-specific schema parsing logic here.
            # Example: Map e-RaktKosh or National Blood Transfusion Council JSON:
            # [
            #    {"hospital_id": 1, "blood_group": "A+", "stock": 14, "last_updated": "..."}
            # ]
            # -------------------------------------------------------------
            parsed_results: List[BloodInventoryResponse] = []
            for item in payload.get("data", []):
                parsed_results.append(
                    BloodInventoryResponse(
                        id=item.get("id", 9999),
                        hospital_id=item.get("hospital_id", hospital_id or 1),
                        blood_group=item.get("blood_group"),
                        units_available=item.get("stock", 0),
                        expiry_date=None,
                        updated_at=None,
                        user_reservable=False,  # External stock is strictly display-only
                        source="external"
                    )
                )

            if parsed_results:
                cache_client.set(
                    cache_key,
                    json.dumps([r.model_dump(mode="json") for r in parsed_results]),
                    ex=settings.CACHE_DEFAULT_TTL_SECONDS
                )
                return parsed_results

        except Exception as e:
            logger.info("External blood bank fetch failed or simulated stub (%s); falling back to local DB.", str(e))

        # Fallback to local DB data if external source fails or returns empty
        fallback_data = self.local_fallback.get_blood_availability(db, hospital_id)
        return fallback_data

    def get_medicine_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[MedicineInventoryResponse]:
        # Medicines use local DB source
        return self.local_fallback.get_medicine_availability(db, hospital_id)

    def get_bed_availability(
        self, db: Session, hospital_id: Optional[int] = None
    ) -> List[BedInventoryResponse]:
        # Beds use local DB source
        return self.local_fallback.get_bed_availability(db, hospital_id)
