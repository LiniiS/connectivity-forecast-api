from fastapi import APIRouter

from app.api.v1 import activity, forecasts, health, locations, models

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(models.router, tags=["Models"])
api_v1_router.include_router(locations.router, tags=["Locations"])
api_v1_router.include_router(forecasts.router, tags=["Forecasts"])
api_v1_router.include_router(activity.router, tags=["Activity"])
