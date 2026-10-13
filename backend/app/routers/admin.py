from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogResponse
from app.schemas.public import CacheStatsResponse
from app.cache.redis_client import cache_client

router = APIRouter(prefix="/admin", tags=["Admin & Monitoring"])


@router.get("/cache-stats", response_model=CacheStatsResponse)
def get_cache_stats():
    """Retrieve Redis cache hit/miss metrics and key counters."""
    stats = cache_client.get_stats()
    return CacheStatsResponse(**stats)


@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(db: Session = Depends(get_db)):
    """Retrieve system audit logs for emergency overrides and inventory operations."""
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100).all()
    results = []
    for l in logs:
        item = AuditLogResponse.model_validate(l)
        if l.performed_by:
            item.performer_name = l.performed_by.name
        results.append(item)
    return results
