"""Health check routes."""

from fastapi import APIRouter

from src.core.database import check_db_connection
from src.core.redis import check_redis_connection

router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {"status": "ok"}


@router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with dependencies."""
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    
    status = "ok" if (db_ok and redis_ok) else "degraded"
    
    return {
        "status": status,
        "services": {
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        }
    }
