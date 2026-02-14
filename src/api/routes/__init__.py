"""API routes setup."""

from fastapi import FastAPI

from src.api.routes.auth import router as auth_router
from src.api.routes.user import router as user_router
from src.api.routes.models import router as models_router
from src.api.routes.generation import router as generation_router
from src.api.routes.gallery import router as gallery_router
from src.api.routes.payments import router as payments_router
from src.api.routes.admin import router as admin_router
from src.api.routes.upload import router as upload_router
from src.api.websockets.logs import router as logs_ws_router


def setup_routes(app: FastAPI) -> None:
    """Setup all API routes."""
    
    # Health check
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok"}
    
    # API routes
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
    app.include_router(user_router, prefix="/api/v1/user", tags=["User"])
    app.include_router(models_router, prefix="/api/v1/models", tags=["Models"])
    app.include_router(generation_router, prefix="/api/v1/generation", tags=["Generation"])
    app.include_router(gallery_router, prefix="/api/v1/gallery", tags=["Gallery"])
    app.include_router(payments_router, prefix="/api/v1/payments", tags=["Payments"])
    app.include_router(upload_router, prefix="/api/v1/upload", tags=["Upload"])
    
    # Admin routes
    app.include_router(admin_router, prefix="/api/v1/admin", tags=["Admin"])
    
    # WebSocket routes
    app.include_router(logs_ws_router, tags=["WebSocket"])

