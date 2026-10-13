import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.services.expiry_service import run_expiry_background_loop
from app.routers import (
    auth_router,
    hospital_inventory_router,
    hospital_reservations_router,
    emergency_router,
    public_availability_router,
    nearest_router,
    reservations_router,
    admin_router,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("medtrack")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start background TTL expiration loop
    task = asyncio.create_task(run_expiry_background_loop())
    logger.info("CareOS (MedTrack) service initialized.")
    try:
        yield
    finally:
        # Shutdown
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        logger.info("CareOS (MedTrack) service stopped.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CareOS (MedTrack): Concurrent Inventory and Reservation System for Blood, Medicines, and Beds",
    lifespan=lifespan,
)

# CORS Middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registration Only
app.include_router(auth_router)
app.include_router(hospital_inventory_router)
app.include_router(hospital_reservations_router)
app.include_router(emergency_router)
app.include_router(public_availability_router)
app.include_router(nearest_router)
app.include_router(reservations_router)
app.include_router(admin_router)


@app.get("/", tags=["Health"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}
