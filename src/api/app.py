"""FastAPI application factory."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from src.config import STORAGE_DIR, settings, BASE_DIR
from src.core.database import check_db_connection, close_db
from src.core.redis import check_redis_connection, close_redis
from src.shared.logger import enable_websocket_logging, logger


# Путь к билду фронтенда
FRONTEND_DIR = BASE_DIR / "frontend" / "dist"

# Создаем папку для uploads если не существует
UPLOAD_DIR = STORAGE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("FastAPI starting up...")
    
    if not await check_db_connection():
        raise RuntimeError("Database connection failed")
    
    if not await check_redis_connection():
        raise RuntimeError("Redis connection failed")
    
    # Enable WebSocket logging for admin panel
    enable_websocket_logging(level="DEBUG")
    
    logger.info(f"Frontend dir exists: {FRONTEND_DIR.exists()}")
    logger.info("FastAPI started")
    
    yield
    
    # Shutdown
    logger.info("FastAPI shutting down...")
    await close_db()
    await close_redis()
    logger.info("FastAPI stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="AI Content Bot API",
        description="API для Mini App генератора AI контента",
        version="1.0.0",
        docs_url="/api/docs" if settings.DEV_MODE else None,
        redoc_url="/api/redoc" if settings.DEV_MODE else None,
        lifespan=lifespan,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://telegram.org",
            "https://*.telegram.org",
            settings.WEBAPP_URL,
            "http://localhost:5173",  # Vite dev server
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Mount static files for generations
    app.mount(
        "/static/generations",
        StaticFiles(directory=str(STORAGE_DIR / "generations")),
        name="generations",
    )
    
    # Mount static files for uploads
    app.mount(
        "/static/uploads",
        StaticFiles(directory=str(UPLOAD_DIR)),
        name="uploads",
    )
    
    # Include API routers
    from src.api.routes import setup_routes
    setup_routes(app)
    
    # Mount frontend (должен быть ПОСЛЕ API роутов)
    if FRONTEND_DIR.exists():
        # Статические файлы фронтенда (js, css, assets)
        app.mount(
            "/assets",
            StaticFiles(directory=str(FRONTEND_DIR / "assets")),
            name="frontend_assets",
        )
        
        # SPA fallback - все остальные запросы отдают index.html
        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            """Serve SPA for all non-API routes."""
            # Если запрос к API - пропускаем (уже обработан выше)
            if full_path.startswith("api/") or full_path.startswith("ws/"):
                return {"detail": "Not Found"}
            
            index_file = FRONTEND_DIR / "index.html"
            if index_file.exists():
                return FileResponse(str(index_file))
            return {"detail": "Frontend not found"}
    else:
        logger.warning(f"Frontend directory not found: {FRONTEND_DIR}")
    
    return app


# Create app instance
app = create_app()

