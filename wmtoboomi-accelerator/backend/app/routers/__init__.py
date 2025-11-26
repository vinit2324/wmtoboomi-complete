"""
API routers package.
"""
from app.routers.customers import router as customers_router
from app.routers.projects import router as projects_router
from app.routers.conversions import router as conversions_router
from app.routers.mappings import router as mappings_router
from app.routers.ai import router as ai_router
from app.routers.logs import router as logs_router

__all__ = [
    "customers_router",
    "projects_router",
    "conversions_router",
    "mappings_router",
    "ai_router",
    "logs_router",
]
