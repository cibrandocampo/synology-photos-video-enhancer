"""Integration tests for the settings router (GET form + POST save)."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from controllers.dashboard import build_routers
from domain.models.app_config import DashboardConfig
from domain.models.hardware import HardwareVideoAcceleration
from domain.models.settings import TranscodingSettings
from infrastructure.web.app import create_app
from infrastructure.web.i18n import Translations


def _dashboard_config():
    return DashboardConfig(
        port=9200,
        user="admin",
        password="secret",
        secret_key="key123",
        cookie_secure=False,
    )


def _default_settings():
    return TranscodingSettings()


def _build_app(settings=None, hw_acceleration=None, translations=None):
    settings_use_case = Mock()
    settings_use_case.load.return_value = (
        settings if settings is not None else _default_settings()
    )
    settings_use_case.save = Mock()
    hardware_info = Mock()
    hardware_info.video_acceleration = hw_acceleration
    if translations is None:
        translations = Mock()
    app = create_app(
        use_case=Mock(),
        settings_use_case=settings_use_case,
        retranscode_use_case=Mock(),
        hardware_info=hardware_info,
        translations=translations,
        config=_dashboard_config(),
        routers=build_routers(),
        logger=Mock(),
    )
    return app, settings_use_case


def _login(client):
    return client.post(
        "/login",
        data={"username": "admin", "password": "secret"},
        follow_redirects=False,
    )


@pytest.fixture
def client():
    app, _ = _build_app()
    return TestClient(app)


class TestSettingsGet:
    def test_anonymous_redirects_to_login(self, client):
        response = client.get("/settings", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_authenticated_renders_settings_page(self, client):
        _login(client)
        response = client.get("/settings")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        assert "settings" in response.text.lower()

    def test_saved_query_param_shows_confirmation(self, client):
        _login(client)
        response = client.get("/settings?saved=1")

        assert response.status_code == 200

    def test_settings_get_includes_hw_detected_in_context_when_hw_present(self):
        app, _ = _build_app(
            hw_acceleration=HardwareVideoAcceleration.VAAPI,
            translations=Translations(),
        )
        client = TestClient(app)
        _login(client)

        response = client.get("/settings")

        assert response.status_code == 200
        assert "VAAPI" in response.text

    def test_settings_get_includes_hw_detected_none_when_no_hw(self):
        app, _ = _build_app(hw_acceleration=None, translations=Translations())
        client = TestClient(app)
        _login(client)

        response = client.get("/settings")

        assert response.status_code == 200
        assert "No compatible hardware" in response.text

    def test_settings_get_renders_es_locale(self):
        real_translations = Translations()
        app, _ = _build_app(translations=real_translations)
        client = TestClient(app)
        _login(client)

        response = client.get("/settings", headers={"accept-language": "es"})

        assert response.status_code == 200
        assert "Ejecución" in response.text


class TestSettingsPost:
    def test_anonymous_redirects_to_login(self, client):
        response = client.post("/settings", data={}, follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    def test_authenticated_saves_and_redirects(self):
        app, settings_use_case = _build_app()
        client = TestClient(app)
        _login(client)

        response = client.post(
            "/settings",
            data={
                "execution_threads": "4",
                "startup_delay": "60",
                "execution_interval": "120",
                "video_codec": "h264_high",
                "video_bitrate": "3000",
                "video_resolution": "1080p",
                "audio_codec": "aac_lc",
                "audio_bitrate": "192",
                "audio_channels": "2",
            },
            follow_redirects=False,
        )

        assert response.status_code == 303
        assert response.headers["location"] == "/settings?saved=1"
        settings_use_case.save.assert_called_once()

    def test_hw_transcoding_absent_sets_false(self):
        app, settings_use_case = _build_app()
        client = TestClient(app)
        _login(client)

        client.post(
            "/settings",
            data={
                "execution_threads": "2",
                "startup_delay": "30",
                "execution_interval": "240",
                "video_codec": "h264_high",
                "video_bitrate": "2000",
                "video_resolution": "720p",
                "audio_codec": "aac_lc",
                "audio_bitrate": "128",
                "audio_channels": "2",
            },
            follow_redirects=False,
        )

        saved: TranscodingSettings = settings_use_case.save.call_args[0][0]
        assert saved.hw_transcoding is False

    def test_hw_transcoding_present_sets_true(self):
        app, settings_use_case = _build_app()
        client = TestClient(app)
        _login(client)

        client.post(
            "/settings",
            data={
                "hw_transcoding": "on",
                "execution_threads": "2",
                "startup_delay": "30",
                "execution_interval": "240",
                "video_codec": "h264_high",
                "video_bitrate": "2000",
                "video_resolution": "720p",
                "audio_codec": "aac_lc",
                "audio_bitrate": "128",
                "audio_channels": "2",
            },
            follow_redirects=False,
        )

        saved: TranscodingSettings = settings_use_case.save.call_args[0][0]
        assert saved.hw_transcoding is True

    def test_invalid_integer_fields_fall_back_to_defaults(self):
        app, settings_use_case = _build_app()
        client = TestClient(app)
        _login(client)

        client.post(
            "/settings",
            data={
                "execution_threads": "not_a_number",
                "startup_delay": "",
                "execution_interval": "240",
                "video_codec": "h264_high",
                "video_bitrate": "2000",
                "video_resolution": "720p",
                "audio_codec": "aac_lc",
                "audio_bitrate": "128",
                "audio_channels": "2",
            },
            follow_redirects=False,
        )

        saved: TranscodingSettings = settings_use_case.save.call_args[0][0]
        assert saved.execution_threads == 2
        assert saved.startup_delay == 30

    def test_unknown_video_codec_falls_back_to_h264_high(self):
        app, settings_use_case = _build_app()
        client = TestClient(app)
        _login(client)

        client.post(
            "/settings",
            data={
                "execution_threads": "2",
                "startup_delay": "30",
                "execution_interval": "240",
                "video_codec": "unknown_codec",
                "video_bitrate": "2000",
                "video_resolution": "720p",
                "audio_codec": "aac_lc",
                "audio_bitrate": "128",
                "audio_channels": "2",
            },
            follow_redirects=False,
        )

        saved: TranscodingSettings = settings_use_case.save.call_args[0][0]
        assert saved.video_codec == "h264"
        assert saved.video_profile == "high"
