import os
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    """
    Public health check endpoint reporting system operational status.
    Does not leak user, environment, or dataset metadata.
    """
    return {
        "status": "healthy",
        "version": settings.PROJECT_VERSION,
        "service": "Inslight AI Platform",
    }


@router.get("/health/live")
def health_live():
    """Liveness probe confirming the FastAPI process is responsive."""
    return {"status": "alive", "service": "Inslight AI Platform"}


@router.get("/health/ready")
def health_ready(response: Response, db: Session = Depends(get_db)):
    """
    Readiness probe verifying database connectivity and storage availability.
    Exposes no credentials, internal paths, or environment variables.
    """
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    storage_ok = os.path.isdir(settings.DATASET_STORAGE_DIR) or os.access(".", os.W_OK)
    ai_configured = bool(settings.GROQ_API_KEY)

    ready = db_ok and storage_ok
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if ready else "degraded",
        "checks": {
            "database": "connected" if db_ok else "unavailable",
            "storage": "available" if storage_ok else "unavailable",
            "ai_provider": "configured" if ai_configured else "unconfigured",
        },
    }
