import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger, request_id_ctx
from app.api.v1.router import api_router
from app.api.v1.routes.health import router as health_router
from app.services.scheduler import SchedulerService


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database schemas...")
    init_db()
    logger.info("Starting background report scheduler...")
    SchedulerService.start()
    logger.info("INSLIGHT Backend initialized successfully.")
    yield
    logger.info("Stopping background report scheduler...")
    SchedulerService.stop()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    lifespan=lifespan
)

# CORS middleware with explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    """Attach a unique X-Request-ID to every request and log context."""
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:12]
    token = request_id_ctx.set(req_id)
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = req_id
        return response
    finally:
        request_id_ctx.reset(token)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "request_id": request_id_ctx.get("-"),
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "detail": "Invalid request parameters.",
            "errors": exc.errors(),
            "request_id": request_id_ctx.get("-"),
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = request_id_ctx.get("-")
    logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "An internal server error occurred. Reference the request_id for diagnostics.",
            "request_id": req_id,
        },
    )


# Mount root-level health probes for standard load balancers
app.include_router(health_router)

# Mount primary versioned API router
app.include_router(api_router, prefix="/api/v1")

# Mount legacy compatibility router
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": "INSLIGHT AI Business Intelligence Platform Running",
        "version": settings.PROJECT_VERSION,
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
