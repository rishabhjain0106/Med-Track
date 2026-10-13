from typing import Dict, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "MedTrack (CareOS)"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database & Redis Settings
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/medtrack"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT Security Settings
    SECRET_KEY: str = "careos-ultra-secure-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Reservation Rules
    RESERVATION_EXPIRY_MINUTES: int = 30
    EMERGENCY_RESERVATION_BUFFER_THRESHOLD: int = 2  # Low stock threshold
    
    # Blood Group Reservability (O+ and O- are display-only / non-reservable by default)
    BLOOD_GROUP_RESERVABLE: Dict[str, bool] = {
        "A+": True,
        "A-": True,
        "B+": True,
        "B-": True,
        "AB+": True,
        "AB-": True,
        "O+": False,
        "O-": False,
    }
    
    # Pluggable Data Sources: 'local' | 'external'
    BLOOD_DATA_SOURCE: str = "local"
    MEDICINE_DATA_SOURCE: str = "local"
    BEDS_DATA_SOURCE: str = "local"
    EXTERNAL_BLOOD_BANK_API_URL: str = "https://api.externalbloodbank.example.org/v1/availability"
    
    # Cache Settings
    CACHE_DEFAULT_TTL_SECONDS: int = 45
    NEAREST_SEARCH_CACHE_TTL_SECONDS: int = 30
    
    # Rate Limiting Settings
    RATE_LIMIT_REQUESTS: int = 120
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    
    # Background expiry check interval
    EXPIRY_CHECK_INTERVAL_SECONDS: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def is_blood_group_reservable(self, blood_group: str) -> bool:
        """Check if a specific blood group can be reserved by public users."""
        return self.BLOOD_GROUP_RESERVABLE.get(blood_group.upper().strip(), False)


settings = Settings()
