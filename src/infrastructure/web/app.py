"""FastAPI application factory for the dashboard."""

from pathlib import Path

from fastapi import APIRouter, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse, RedirectResponse

from application.dashboard_stats_use_case import DashboardStatsUseCase
from application.retranscode_use_case import RetranscodeUseCase
from application.settings_use_case import SettingsUseCase
from domain.models.app_config import DashboardConfig
from domain.ports.hardware_info import HardwareInfo
from domain.ports.logger import AppLogger
from infrastructure.web.auth import RedirectToLoginRequired
from infrastructure.web.i18n import Translations
from infrastructure.web.security_headers import SecurityHeadersMiddleware


_HERE = Path(__file__).resolve().parent
_TEMPLATES_DIR = _HERE / "templates"
_STATIC_DIR = _HERE / "static"


def create_app(
    use_case: DashboardStatsUseCase,
    settings_use_case: SettingsUseCase,
    retranscode_use_case: RetranscodeUseCase,
    hardware_info: HardwareInfo,
    translations: Translations,
    config: DashboardConfig,
    routers: list[APIRouter],
    logger: AppLogger,
) -> FastAPI:
    """Builds the dashboard FastAPI app and wires its middlewares + routers."""
    app = FastAPI(title="Video Enhancer Dashboard", docs_url=None, redoc_url=None)

    # Order matters: SessionMiddleware must wrap routes so request.session is
    # populated before SecurityHeadersMiddleware sees the response. Starlette
    # applies middleware in reverse-add order, so the last add is outermost.
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(
        SessionMiddleware,
        secret_key=config.secret_key,
        same_site="lax",
        https_only=config.cookie_secure,
        session_cookie="dashboard_session",
    )

    @app.exception_handler(RedirectToLoginRequired)
    async def _redirect_to_login(_request: Request, _exc: RedirectToLoginRequired):
        return RedirectResponse(url="/login", status_code=302)

    app.state.templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    app.state.use_case = use_case
    app.state.settings_use_case = settings_use_case
    app.state.retranscode_use_case = retranscode_use_case
    app.state.hardware_info = hardware_info
    app.state.translations = translations
    app.state.dashboard_config = config
    app.state.logger = logger

    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    @app.get("/sw.js", include_in_schema=False)
    async def _service_worker():
        return FileResponse(str(_STATIC_DIR / "sw.js"), media_type="application/javascript")

    for router in routers:
        app.include_router(router)

    return app
