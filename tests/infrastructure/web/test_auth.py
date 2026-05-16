"""Tests for the dashboard auth helpers."""
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from domain.models.app_config import DashboardConfig
from infrastructure.web.auth import (
    RedirectToLoginRequired,
    SESSION_USER_KEY,
    html_require_session,
    require_session,
    verify_credentials,
)


def _config(user="admin", password="secret"):
    return DashboardConfig(
        port=9200,
        user=user,
        password=password,
        secret_key="key123",
        cookie_secure=False,
    )


def _request_with_session(session: dict):
    request = Mock()
    request.session = session
    return request


class TestVerifyCredentials:
    def test_returns_true_when_user_and_password_match(self):
        assert verify_credentials("admin", "secret", _config()) is True

    def test_returns_false_when_password_differs(self):
        assert verify_credentials("admin", "wrong", _config()) is False

    def test_returns_false_when_user_differs_even_with_matching_password(self):
        assert verify_credentials("intruder", "secret", _config()) is False

    def test_returns_false_when_both_differ(self):
        assert verify_credentials("intruder", "wrong", _config()) is False

    def test_returns_false_when_user_is_empty(self):
        assert verify_credentials("", "secret", _config()) is False


class TestRequireSession:
    def test_raises_401_when_session_empty(self):
        request = _request_with_session({})

        with pytest.raises(HTTPException) as exc_info:
            require_session(request)

        assert exc_info.value.status_code == 401

    def test_raises_401_when_user_key_missing(self):
        request = _request_with_session({"other_key": "value"})

        with pytest.raises(HTTPException) as exc_info:
            require_session(request)

        assert exc_info.value.status_code == 401

    def test_returns_user_when_session_populated(self):
        request = _request_with_session({SESSION_USER_KEY: "admin"})

        assert require_session(request) == "admin"


class TestHtmlRequireSession:
    def test_raises_redirect_to_login_when_session_empty(self):
        request = _request_with_session({})

        with pytest.raises(RedirectToLoginRequired):
            html_require_session(request)

    def test_returns_user_when_session_populated(self):
        request = _request_with_session({SESSION_USER_KEY: "admin"})

        assert html_require_session(request) == "admin"
