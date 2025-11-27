from fastapi import APIRouter

from . import routes_projects, routes_auth, routes_metrics

api_router = APIRouter()

api_router.include_router(routes_auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(routes_projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(routes_metrics.router, tags=["metrics"])