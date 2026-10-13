import logging
from app.cache.redis_client import cache_client
from app.cache.cache_keys import public_availability_key, hospital_availability_key

logger = logging.getLogger(__name__)


def invalidate_inventory_cache(hospital_id: int, resource_type: str = None):
    """
    Invalidates cached availability and nearest queries when stock changes.
    Called immediately on:
    - Staff stock update
    - New reservation created
    - Reservation cancellation
    - Reservation expiration
    - Emergency override
    """
    try:
        # Invalidate global public list
        cache_client.delete(public_availability_key())
        # Invalidate hospital-specific availability
        cache_client.delete(hospital_availability_key(hospital_id))
        
        # Invalidate nearest queries for the resource type or all
        if resource_type:
            cache_client.delete_pattern(f"nearest:{resource_type}:*")
        else:
            cache_client.delete_pattern("nearest:*")
            
        logger.info("Invalidated cache for hospital_id=%s, resource_type=%s", hospital_id, resource_type)
    except Exception as e:
        logger.error("Failed to invalidate cache: %s", str(e))
