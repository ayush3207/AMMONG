from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.core.logging import logger
from app.services.dataset_service import dataset_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown events.
    Loads job requirements dataset and initializes database tables.
    """
    logger.info("Initializing AMMONG Placement Intelligence Backend...")
    
    # 1. Load and index the Kaggle Job Requirements Dataset (all_job_post.csv)
    dataset_loaded = dataset_service.load_dataset()
    if dataset_loaded:
        logger.info(f"Dataset ready: {dataset_service.total_jobs} job postings loaded.")
    else:
        logger.warning("Dataset failed to load! Check DATASET_PATH in .env.")

    # 2. Initialize Database tables
    await init_db()

    yield

    logger.info("AMMONG Backend shutting down.")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="AI-Powered Student Placement Intelligence & Skill-Gap Analysis API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes under /api
app.include_router(api_router)

@app.get("/", tags=["Root"])
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
        "dataset_stats": "/api/jobs/stats",
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error for {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred. Please try again."},
    )
