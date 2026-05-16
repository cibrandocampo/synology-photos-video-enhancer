"""Dashboard controllers package."""
from fastapi import APIRouter

from controllers.dashboard.auth_router import router as auth_router
from controllers.dashboard.dashboard_router import router as dashboard_router
from controllers.dashboard.settings_router import router as settings_router


def build_routers() -> list[APIRouter]:
    """Returns the routers consumed by `infrastructure.web.app.create_app`."""
    return [auth_router, dashboard_router, settings_router]
