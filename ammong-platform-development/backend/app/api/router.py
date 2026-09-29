from fastapi import APIRouter
from app.api.endpoints.health import router as health_router
from app.api.endpoints.jobs import router as jobs_router
from app.api.endpoints.analyze import router as analyze_router

api_router = APIRouter(prefix="/api")
api_router.include_router(health_router)
api_router.include_router(jobs_router)
api_router.include_router(analyze_router)
