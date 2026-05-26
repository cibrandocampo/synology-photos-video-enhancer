"""Integration tests for the dashboard router (HTML, JSON, healthz)."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from controllers.dashboard import build_routers
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


def _build_app(stats=None, *, raise_on_execute=False):
    use_case = Mock()
    if raise_on_execute:
        use_case.execute.side_effect = AssertionError(
            "use_case.execute() must not be called for this endpoint"
        )
    else:
        use_case.execute.return_value = stats if stats is not None else _sample_stats()
    use_case.execute_latest_transcodings.return_value = ([], 0)
    return create_app(
        use_case=use_case,
        settings_use_case=Mock(),
        retranscode_use_case=Mock(),
        hardware_info=Mock(),
        translations=Mock(),
        config=_dashboard_config(),
        routers=build_routers(),
        logger=Mock(),
    ), use_case


def _login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "secret"},
        follow_redirects=False,
    )


@pytest.fixture
def stats():
    return _sample_stats()


@pytest.fixture
def client(stats):
    app, _ = _build_app(stats)
    return TestClient(app)


class TestDashboardHtml:
    def test_anonymous_redirects_to_login(self, client):
        response = client.get("/", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_authenticated_renders_dashboard(self, client, stats):
        _login(client)
        response = client.get("/")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        body = response.text
        assert str(stats.total) in body
        assert "71.4%" in body
        assert "h264" in body


class TestApiStats:
    def test_anonymous_returns_401_with_pinned_body(self, client):
        response = client.get("/api/stats")

        assert response.status_code == 401
        assert response.headers["content-type"].startswith("application/json")
        assert response.json() == {"detail": "Authentication required"}

    def test_authenticated_returns_full_stats_payload(self, client, stats):
        _login(client)
        response = client.get("/api/stats")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("application/json")
        payload = response.json()
        expected_keys = {
            "total",
            "status_counts",
            "success_rate",
            "codec_distribution",
            "resolution_distribution",
            "latest_transcodings",
            "top_errors",
        }
        assert expected_keys.issubset(payload.keys())
        assert payload["total"] == stats.total
        assert set(payload["status_counts"].keys()) == {
            "pending",
            "in_progress",
            "completed",
            "not_required",
            "failed",
        }


class TestHealthz:
    def test_anonymous_returns_ok(self, client):
        response = client.get("/healthz")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_does_not_invoke_use_case(self):
        app, use_case = _build_app(raise_on_execute=True)
        local_client = TestClient(app)

        response = local_client.get("/healthz")

        assert response.status_code == 200
        use_case.execute.assert_not_called()


class TestTranscodingsJson:
    def test_anonymous_returns_401(self, client):
        response = client.get("/api/transcodings")

        assert response.status_code == 401
        assert response.json() == {"detail": "Authentication required"}

    def test_authenticated_returns_pagination_payload(self, client):
        _login(client)
        response = client.get("/api/transcodings")

        assert response.status_code == 200
        payload = response.json()
        assert "transcodings" in payload
        assert "page" in payload
        assert "total_pages" in payload
        assert "total" in payload

    def test_page_clamped_to_total_pages(self):
        app, use_case = _build_app()
        use_case.execute_latest_transcodings.return_value = ([], 0)
        local_client = TestClient(app)
        _login(local_client)

        response = local_client.get("/api/transcodings?page=999")

        assert response.status_code == 200
        payload = response.json()
        assert payload["page"] == 1


def _build_app_with_retranscode(*, find_return=None, reset_return=True):
    retranscode_uc = Mock()
    retranscode_uc.find.return_value = find_return if find_return is not None else []
    retranscode_uc.reset.return_value = reset_return

    use_case = Mock()
    use_case.execute.return_value = _sample_stats()
    use_case.execute_latest_transcodings.return_value = ([], 0)

    app = create_app(
        use_case=use_case,
        settings_use_case=Mock(),
        retranscode_use_case=retranscode_uc,
        hardware_info=Mock(),
        translations=Mock(),
        config=_dashboard_config(),
        routers=build_routers(),
        logger=Mock(),
    )
    return app, retranscode_uc


class TestRetranscodeApi:
    # GET /api/transcodings/search

    def test_search_unauthenticated_returns_401(self):
        app, _ = _build_app_with_retranscode()
        client = TestClient(app)

        response = client.get("/api/transcodings/search?path=vacation")

        assert response.status_code == 401

    def test_search_path_shorter_than_3_returns_422(self):
        app, _ = _build_app_with_retranscode()
        client = TestClient(app)
        _login(client)

        response = client.get("/api/transcodings/search?path=ab")

        assert response.status_code == 422

    def test_search_valid_path_returns_200_with_results(self):
        item = LatestTranscoding(
            original_video_path="/media/vacation/beach.mp4",
            transcoded_video_path="/media/vacation/beach.out.mp4",
            status="completed",
            transcoded_video_codec="h264",
            transcoded_video_resolution="1280x720",
            error_message=None,
        )
        app, retranscode_uc = _build_app_with_retranscode(find_return=[item])
        client = TestClient(app)
        _login(client)

        response = client.get("/api/transcodings/search?path=vacation")

        assert response.status_code == 200
        payload = response.json()
        assert "results" in payload
        assert len(payload["results"]) == 1
        assert payload["results"][0]["original_video_path"] == "/media/vacation/beach.mp4"
        retranscode_uc.find.assert_called_once_with("vacation")

    def test_search_no_match_returns_empty_results(self):
        app, _ = _build_app_with_retranscode(find_return=[])
        client = TestClient(app)
        _login(client)

        response = client.get("/api/transcodings/search?path=zzz")

        assert response.status_code == 200
        assert response.json() == {"results": []}

    # POST /api/transcodings/retranscode

    def test_retranscode_unauthenticated_returns_401(self):
        app, _ = _build_app_with_retranscode()
        client = TestClient(app)

        response = client.post(
            "/api/transcodings/retranscode",
            json={"original_video_path": "/media/video.mp4"},
        )

        assert response.status_code == 401

    def test_retranscode_missing_field_returns_422(self):
        app, _ = _build_app_with_retranscode()
        client = TestClient(app)
        _login(client)

        response = client.post("/api/transcodings/retranscode", json={})

        assert response.status_code == 422

    def test_retranscode_eligible_path_returns_200(self):
        app, retranscode_uc = _build_app_with_retranscode(reset_return=True)
        client = TestClient(app)
        _login(client)

        response = client.post(
            "/api/transcodings/retranscode",
            json={"original_video_path": "/media/video.mp4"},
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "pending"
        assert payload["original_video_path"] == "/media/video.mp4"
        retranscode_uc.reset.assert_called_once_with("/media/video.mp4")

    def test_retranscode_non_eligible_path_returns_409(self):
        app, _ = _build_app_with_retranscode(reset_return=False)
        client = TestClient(app)
        _login(client)

        response = client.post(
            "/api/transcodings/retranscode",
            json={"original_video_path": "/media/pending.mp4"},
        )

        assert response.status_code == 409
