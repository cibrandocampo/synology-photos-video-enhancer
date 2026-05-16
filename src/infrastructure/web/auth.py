"""Authentication helpers for the dashboard web layer."""
import secrets

from fastapi import HTTPException, Request

from domain.models.app_config import DashboardConfig


SESSION_USER_KEY = "user"


class RedirectToLoginRequired(Exception):
    """Raised by HTML routes when the session is missing.

    The app's exception handler translates this into a 302 redirect to
    `/login`. It is a separate signal from `HTTPException(401)` so JSON and
    HTML routes can opt into different unauthenticated behaviours without
    branching inside route handlers.
    """


def verify_credentials(
    provided_user: str,
    provided_password: str,
    config: DashboardConfig,
) -> bool:
    """Returns True iff both username and password match the configured ones.

    Uses `secrets.compare_digest` for both fields so the comparison is
    constant-time regardless of which (if any) field is wrong.
    """
    user_match = secrets.compare_digest(provided_user, config.user)
    password_match = secrets.compare_digest(provided_password, config.password)
    return user_match and password_match


def require_session(request: Request) -> str:
    """FastAPI dependency: return the session user or raise 401.

    Use this on JSON endpoints. HTML endpoints should depend on
    `html_require_session` instead so the user is redirected to /login.
    """
    user = request.session.get(SESSION_USER_KEY)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def html_require_session(request: Request) -> str:
    """FastAPI dependency: return the session user or trigger a /login redirect."""
    user = request.session.get(SESSION_USER_KEY)
    if not user:
        raise RedirectToLoginRequired()
    return user
