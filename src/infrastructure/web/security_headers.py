"""Security-headers middleware for dashboard responses."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_HTML_ONLY_HEADERS = {
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "same-origin",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'"
    ),
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds defensive headers to every response.

    `X-Content-Type-Options: nosniff` is applied unconditionally because it
    is meaningful for both HTML and JSON. The remaining headers (frame
    options, referrer policy, CSP) target HTML content only — applying CSP
    to JSON would have no effect and could mislead a future reader into
    expecting browser-side enforcement on API endpoints.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        response.headers["X-Content-Type-Options"] = "nosniff"

        content_type = response.headers.get("Content-Type", "")
        if content_type.startswith("text/html"):
            for header, value in _HTML_ONLY_HEADERS.items():
                response.headers[header] = value

        return response
