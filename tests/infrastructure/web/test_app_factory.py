"""Smoke tests for the dashboard FastAPI app factory."""

from unittest.mock import Mock

import pytest
from fastapi import APIRouter, Depends, Request
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from domain.models.app_config import DashboardConfig
from domain.models.dashboard_stats import (
    CodecCount,
    DashboardStats,
    ErrorCount,
    LatestTranscoding,
    ResolutionCount,
)
from domain.models.transcoding import TranscodingStatus
from infrastructure.web.app import create_app
from infrastructure.web.auth import (
    SESSION_USER_KEY,
    html_require_session,
    require_session,
)
from infrastructure.web.i18n import detect_locale


def _dashboard_config():
    return DashboardConfig(
        port=9200,
        user="admin",
        password="secret",
        secret_key="key123",
        cookie_secure=False,
    )


def _sample_stats():
    return DashboardStats(
        total=42,
        status_counts={
            TranscodingStatus.PENDING.value: 1,
            TranscodingStatus.IN_PROGRESS.value: 2,
            TranscodingStatus.COMPLETED.value: 30,
            TranscodingStatus.NOT_REQUIRED.value: 4,
            TranscodingStatus.FAILED.value: 5,
        },
        success_rate=71.43,
        codec_distribution=[
            CodecCount(codec="h264", count=20),
            CodecCount(codec="hevc", count=10),
        ],
        resolution_distribution=[
            ResolutionCount(resolution="1920x1080", count=18),
            ResolutionCount(resolution="1280x720", count=12),
        ],
        latest_transcodings=[
            LatestTranscoding(
                original_video_path="/m/a.mp4",
                transcoded_video_path="/m/a.out.mp4",
                status="completed",
                transcoded_video_codec="h264",
                transcoded_video_resolution="1920x1080",
                error_message=None,
            )
        ],
        top_errors=[ErrorCount(error_summary="codec not supported", count=3)],
    )


def _stub_router(stats: DashboardStats) -> APIRouter:
    router = APIRouter()

    @router.post("/__test/login")
    async def stub_login(request: Request):
        request.session[SESSION_USER_KEY] = "admin"
        return PlainTextResponse("logged-in")

    @router.get("/__test/protected", response_class=PlainTextResponse)
    async def stub_protected(_user: str = Depends(html_require_session)):
        return "ok"

    @router.get("/__test/json")
    async def stub_json(_user: str = Depends(require_session)):
        return {"ok": True}

    @router.get("/__test/render")
    async def stub_render(request: Request):
        locale = detect_locale(request)
        t = request.app.state.translations.for_locale(locale)
        templates = request.app.state.templates
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "stats": stats,
                "max_codec_count": max(
                    (c.count for c in stats.codec_distribution), default=0
                ),
                "max_resolution_count": max(
                    (r.count for r in stats.resolution_distribution), default=0
                ),
                "transcodings": [],
                "page": 1,
                "total_pages": 1,
                "total_transcodings": 0,
                "t": t,
                "locale": locale,
            },
        )

    return router


@pytest.fixture
def stats():
    return _sample_stats()


@pytest.fixture
def app(stats):
    use_case = Mock()
    use_case.execute.return_value = stats
    return create_app(
        use_case=use_case,
        settings_use_case=Mock(),
        hardware_info=Mock(),
        translations=Mock(),
        config=_dashboard_config(),
        routers=[_stub_router(stats)],
        logger=Mock(),
    )


@pytest.fixture
def client(app):
    return TestClient(app)


class TestAuthFlow:
    def test_anonymous_html_route_redirects_to_login(self, client):
        response = client.get("/__test/protected", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_anonymous_json_route_returns_401(self, client):
        response = client.get("/__test/json")

        assert response.status_code == 401

    def test_authenticated_routes_after_session_seeded(self, client):
        login_response = client.post("/__test/login")
        assert login_response.status_code == 200

        protected_response = client.get("/__test/protected")
        assert protected_response.status_code == 200
        assert protected_response.text == "ok"

        json_response = client.get("/__test/json")
        assert json_response.status_code == 200
        assert json_response.json() == {"ok": True}


class TestTemplateRendering:
    def test_dashboard_renders_with_stats_payload(self, client, stats):
        client.post("/__test/login")
        response = client.get("/__test/render")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        body = response.text
        assert str(stats.total) in body
        assert "71.4%" in body
        assert "h264" in body
        assert "codec not supported" in body
        assert "<script>" not in body  # no inline scripts

    def test_static_css_is_served(self, client):
        response = client.get("/static/style.css")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/css")
        assert ".bar" in response.text

    def test_service_worker_is_served_at_root(self, client):
        response = client.get("/sw.js")

        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]


class TestSecurityHeadersIntegration:
    def test_html_response_carries_full_header_set(self, client):
        client.post("/__test/login")
        response = client.get("/__test/render")

        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "same-origin"
        assert "script-src 'self'" in response.headers["Content-Security-Policy"]

    def test_json_response_only_carries_nosniff(self, client):
        client.post("/__test/login")
        response = client.get("/__test/json")

        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" not in response.headers
        assert "Content-Security-Policy" not in response.headers


class TestAppFactoryWiring:
    def test_app_state_exposes_use_case_and_config(self, app):
        assert app.state.use_case is not None
        assert app.state.dashboard_config.user == "admin"
        assert app.state.templates is not None
        assert app.state.logger is not None

    def test_app_state_exposes_hardware_info(self, app):
        assert app.state.hardware_info is not None

    def test_app_state_exposes_translations(self, app):
        assert app.state.translations is not None
