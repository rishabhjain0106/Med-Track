def public_availability_key() -> str:
    """Cache key for all hospital inventory availability summary."""
    return "availability:all_hospitals"


def hospital_availability_key(hospital_id: int) -> str:
    """Cache key for a specific hospital inventory."""
    return f"availability:hospital:{hospital_id}"


def nearest_resource_key(resource_type: str, resource_ref: str, lat: float, lng: float, radius_km: float) -> str:
    """
    Cache key for nearest resource queries.
    Round coordinates to ~110m (3 decimals) to increase cache reuse while retaining accuracy.
    """
    rounded_lat = round(lat, 3)
    rounded_lng = round(lng, 3)
    ref_slug = resource_ref.lower().replace(" ", "_").replace("+", "plus").replace("-", "minus")
    return f"nearest:{resource_type}:{ref_slug}:{rounded_lat}:{rounded_lng}:{radius_km}"


def external_blood_bank_key(blood_group: str) -> str:
    """Cache key for external blood bank provider."""
    return f"external_source:blood:{blood_group.upper().strip()}"


def rate_limit_key(identifier: str) -> str:
    """Cache key for rate limiting by IP/user."""
    return f"ratelimit:{identifier}"
