from app.routers.auth import router as auth_router
from app.routers.hospital_inventory import router as hospital_inventory_router
from app.routers.hospital_reservations import router as hospital_reservations_router
from app.routers.emergency import router as emergency_router
from app.routers.public_availability import router as public_availability_router
from app.routers.nearest import router as nearest_router
from app.routers.reservations import router as reservations_router
from app.routers.admin import router as admin_router

__all__ = [
    "auth_router",
    "hospital_inventory_router",
    "hospital_reservations_router",
    "emergency_router",
    "public_availability_router",
    "nearest_router",
    "reservations_router",
    "admin_router",
]
