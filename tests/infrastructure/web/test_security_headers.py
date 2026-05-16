"""Tests for SecurityHeadersMiddleware."""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.testclient import TestClient

from infrastructure.web.security_headers import SecurityHeadersMiddleware


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)

    @app.get("/html", response_class=HTMLResponse)
    async def html_endpoint():
        return "<p>hi</p>"

    @app.get("/json")
    async def json_endpoint():
        return JSONResponse({"ok": True})

    @app.get("/text", response_class=PlainTextResponse)
    async def text_endpoint():
        return "plain"

    return app


class TestSecurityHeadersMiddleware:
    def test_html_response_carries_full_header_set(self):
        client = TestClient(_build_app())
        response = client.get("/html")

        assert response.status_code == 200
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["Referrer-Policy"] == "same-origin"
        csp = response.headers["Content-Security-Policy"]
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp

    def test_json_response_only_has_nosniff(self):
        client = TestClient(_build_app())
        response = client.get("/json")

        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" not in response.headers
        assert "Referrer-Policy" not in response.headers
        assert "Content-Security-Policy" not in response.headers

    def test_plaintext_response_only_has_nosniff(self):
        client = TestClient(_build_app())
        response = client.get("/text")

        assert response.status_code == 200
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "Content-Security-Policy" not in response.headers
