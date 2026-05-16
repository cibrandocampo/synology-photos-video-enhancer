"""Integration tests for the auth router (login/logout)."""
from unittest.mock import Mock

import pytest
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from fastapi.testclient import TestClient

from controllers.dashboard import build_routers
from domain.models.app_config import DashboardConfig
from domain.models.dashboard_stats import DashboardStats
from domain.models.transcoding import TranscodingStatus
from infrastructure.web.app import create_app
from infrastructure.web.auth import html_require_session


def _dashboard_config():
    return DashboardConfig(
        port=9200,
        user="admin",
        password="secret",
        secret_key="key123",
        cookie_secure=False,
    )


def _empty_stats():
    return DashboardStats(
        total=0,
        status_counts={status.value: 0 for status in TranscodingStatus},
        success_rate=0.0,
        codec_distribution=[],
        resolution_distribution=[],
        latest_transcodings=[],
        top_errors=[],
    )


def _noop_protected_router() -> APIRouter:
    router = APIRouter()

    @router.get("/__noop_protected", response_class=PlainTextResponse)
    async def noop(_user: str = Depends(html_require_session)):
        return "ok"

    return router


@pytest.fixture
def stub_logger():
    return Mock()


@pytest.fixture
def stub_use_case():
    use_case = Mock()
    use_case.execute.return_value = _empty_stats()
    return use_case


@pytest.fixture
def app(stub_use_case, stub_logger):
    routers = [*build_routers(), _noop_protected_router()]
    return create_app(
        use_case=stub_use_case,
        settings_use_case=Mock(),
        config=_dashboard_config(),
        routers=routers,
        logger=stub_logger,
    )


@pytest.fixture
def client(app):
    return TestClient(app)


def _login(client, username="admin", password="secret"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


class TestLoginGet:
    def test_anonymous_get_login_renders_form(self, client):
        response = client.get("/login")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        body = response.text
        assert 'name="username"' in body
        assert 'name="password"' in body

    def test_get_login_with_existing_session_redirects_to_root(self, client):
        _login(client)
        response = client.get("/login", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/"


class TestLoginPost:
    def test_correct_credentials_set_session_and_redirect_to_root(self, client):
        response = _login(client)

        assert response.status_code == 302
        assert response.headers["location"] == "/"

        protected = client.get("/__noop_protected")
        assert protected.status_code == 200
        assert protected.text == "ok"

    def test_wrong_password_returns_401_with_error_message(self, client, stub_logger):
        response = _login(client, password="wrong")

        assert response.status_code == 401
        assert response.headers["content-type"].startswith("text/html")
        assert "Invalid credentials" in response.text

        stub_logger.warning.assert_called_once()
        warning_message = stub_logger.warning.call_args.args[0]
        assert "admin" in warning_message

    def test_wrong_username_returns_401(self, client, stub_logger):
        response = _login(client, username="intruder", password="secret")

        assert response.status_code == 401
        assert "Invalid credentials" in response.text
        stub_logger.warning.assert_called_once()
        warning_message = stub_logger.warning.call_args.args[0]
        assert "intruder" in warning_message


class TestLogout:
    def test_logout_authenticated_clears_session_and_redirects(self, client):
        _login(client)
        response = client.get("/logout", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"

        next_response = client.get("/__noop_protected", follow_redirects=False)
        assert next_response.status_code == 302
        assert next_response.headers["location"] == "/login"

    def test_logout_anonymous_redirects_to_login(self, client):
        response = client.get("/logout", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"
