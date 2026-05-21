"""Auth router: login (GET/POST) and logout."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from infrastructure.web.auth import (
    SESSION_USER_KEY,
    html_require_session,
    verify_credentials,
)
from infrastructure.web.i18n import detect_locale


router = APIRouter()


@router.get("/login")
async def login_get(request: Request):
    if request.session.get(SESSION_USER_KEY):
        return RedirectResponse(url="/", status_code=302)
    locale = detect_locale(request)
    t = request.app.state.translations.for_locale(locale)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request, name="login.html", context={"t": t, "locale": locale}
    )


@router.post("/login")
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    config = request.app.state.dashboard_config
    if verify_credentials(username, password, config):
        request.session[SESSION_USER_KEY] = username
        return RedirectResponse(url="/", status_code=302)

    logger = request.app.state.logger
    client_host = request.client.host if request.client else "unknown"
    logger.warning(
        f"Failed dashboard login attempt for username={username!r} from {client_host}"
    )

    locale = detect_locale(request)
    t = request.app.state.translations.for_locale(locale)
    templates = request.app.state.templates
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"t": t, "locale": locale, "error": t("auth.invalid_credentials")},
        status_code=401,
    )


@router.get("/logout")
async def logout(request: Request, _user: str = Depends(html_require_session)):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=302)
