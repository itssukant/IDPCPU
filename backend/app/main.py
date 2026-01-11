"""
Main FastAPI application.
Offline-first, on-premises Intelligent Document Processing system.
"""

import logging
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import settings
from backend.app.routers import router as documents_router
from backend.app.models import ErrorResponse

# Configure logging
log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Document Processing with Offline LLM Inference"
)

# CORS middleware - only allow localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", f"http://localhost:{settings.PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": "An internal error occurred",
            "details": {"error": str(exc)} if settings.DEBUG else None
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"OCR Engine: {settings.OCR_ENGINE}")
    logger.info(f"LLM Model Path: {settings.LLM_MODEL_PATH}")
    logger.info(f"Upload Directory: {settings.UPLOAD_DIR}")
    
    # Verify critical directories exist
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info("Initialization complete")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info(f"Shutting down {settings.APP_NAME}")


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


# Include routers
app.include_router(documents_router, prefix=settings.API_PREFIX)


# Serve static files if they exist
static_dir = Path(__file__).parent.parent.parent / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# Serve web UI
@app.get("/ui")
async def web_ui():
    """Serve web UI main page."""
    from fastapi.responses import HTMLResponse
    
    # Load HTML template
    template_path = Path(__file__).parent.parent.parent / "ui" / "templates" / "index.html"
    if template_path.exists():
        with open(template_path) as f:
            return HTMLResponse(content=f.read())
    
    return HTMLResponse(content="<h1>Web UI not yet configured</h1>")


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_level=settings.LOG_LEVEL.lower()
    )
