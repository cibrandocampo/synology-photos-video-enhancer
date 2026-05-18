"""Tests for configuration loader."""
import os
import pytest
from unittest.mock import Mock, patch

from domain.models.settings import TranscodingSettings
from infrastructure.config.config import Config


@pytest.fixture(autouse=True)
def reset_config_singleton():
    Config._instance = None
    Config._app_config = None
    yield
    Config._instance = None
    Config._app_config = None


class TestConfig:
    """Tests for Config class."""

    def test_load_paths_config(self, temp_dir):
        media_path = os.path.join(temp_dir, "media")
        db_path = os.path.join(temp_dir, "test.db")

        with patch.dict(os.environ, {"MEDIA_APP_PATH": media_path, "DATABASE_APP_PATH": db_path}):
            config = Config.load()

            assert config.paths.media_path == media_path
            assert config.paths.database_path == db_path

    def test_singleton_pattern(self):
        config1 = Config.load()
        config2 = Config.load()

        assert config1 is config2

    def test_lazy_loading(self):
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            _ = config.paths
            assert config._app_config.paths is not None

    def test_load_paths_normalises_db_path_without_extension(self, temp_dir):
        """DATABASE_APP_PATH without .db extension is normalised to a .db file inside it."""
        with patch.dict(os.environ, {
            "MEDIA_APP_PATH": "/media",
            "DATABASE_APP_PATH": temp_dir,
        }, clear=True):
            config = Config.load()
            assert config.paths.database_path.endswith("transcodings.db")

    def test_load_database_config(self, temp_dir):
        db_path = os.path.join(temp_dir, "test.db")

        with patch.dict(os.environ, {"DATABASE_APP_PATH": db_path, "MEDIA_APP_PATH": "/test/media"}):
            config = Config.load()
            database = config.database

            assert database.path == db_path or (
                os.path.exists(db_path) and os.path.samefile(database.path, db_path)
            )

    def test_load_logger_config(self):
        with patch.dict(os.environ, {"LOGGER_NAME": "test-logger", "LOGGER_LEVEL": "DEBUG"}):
            Config._instance = None
            Config._app_config = None
            config = Config.load()

            assert config.logger.name == "test-logger"
            assert config.logger.level == "DEBUG"


class TestDashboardConfig:
    """Tests for the dashboard config loader and its hard-fail validations."""

    @staticmethod
    def _env(**overrides):
        env = {
            "DASHBOARD_PASSWORD": "secret",
            "DASHBOARD_SECRET_KEY": "key123",
        }
        env.update(overrides)
        return env

    def test_dashboard_defaults_with_required_vars(self):
        with patch.dict(os.environ, self._env(), clear=True):
            dashboard = Config.load().dashboard

            assert dashboard.port == 9200
            assert dashboard.user == "admin"
            assert dashboard.password == "secret"
            assert dashboard.secret_key == "key123"
            assert dashboard.cookie_secure is False

    def test_dashboard_password_missing_raises(self):
        with patch.dict(os.environ, {"DASHBOARD_SECRET_KEY": "key123"}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                _ = Config.load().dashboard

            message = str(exc_info.value)
            assert message.startswith("Dashboard configuration error: ")
            assert "DASHBOARD_PASSWORD" in message

    def test_dashboard_password_empty_raises(self):
        env = {"DASHBOARD_PASSWORD": "", "DASHBOARD_SECRET_KEY": "key123"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                _ = Config.load().dashboard

            message = str(exc_info.value)
            assert message.startswith("Dashboard configuration error: ")
            assert "DASHBOARD_PASSWORD" in message

    def test_dashboard_secret_key_missing_raises(self):
        with patch.dict(os.environ, {"DASHBOARD_PASSWORD": "secret"}, clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                _ = Config.load().dashboard

            message = str(exc_info.value)
            assert message.startswith("Dashboard configuration error: ")
            assert "DASHBOARD_SECRET_KEY" in message

    def test_dashboard_custom_port(self):
        with patch.dict(os.environ, self._env(DASHBOARD_PORT="9300"), clear=True):
            assert Config.load().dashboard.port == 9300

    def test_dashboard_custom_user(self):
        with patch.dict(os.environ, self._env(DASHBOARD_USER="monitor"), clear=True):
            assert Config.load().dashboard.user == "monitor"

    def test_dashboard_cookie_secure_truthy(self):
        with patch.dict(os.environ, self._env(DASHBOARD_COOKIE_SECURE="true"), clear=True):
            assert Config.load().dashboard.cookie_secure is True

    def test_dashboard_port_out_of_range_raises(self):
        with patch.dict(os.environ, self._env(DASHBOARD_PORT="70000"), clear=True):
            with pytest.raises(RuntimeError) as exc_info:
                _ = Config.load().dashboard

            message = str(exc_info.value)
            assert message.startswith("Dashboard configuration error: ")
            assert "DASHBOARD_PORT" in message

    def test_dashboard_validation_error_unknown_field_raises_generic_message(self):
        """Covers the else branch of offending_text when no field maps to an env var name."""
        from unittest.mock import patch as _patch
        from pydantic import ValidationError as _ValidationError
        from pydantic import BaseModel

        class _Dummy(BaseModel):
            x: int

        try:
            _Dummy(x="bad")
        except _ValidationError as exc:
            fake_exc = exc

        with patch.dict(os.environ, self._env(), clear=True):
            with _patch("infrastructure.config.config._DASHBOARD_FIELD_TO_ENV", {}):
                with _patch(
                    "infrastructure.config.config.DashboardConfig",
                    side_effect=fake_exc,
                ):
                    with pytest.raises(RuntimeError) as exc_info:
                        _ = Config.load().dashboard

        assert "unknown field" in str(exc_info.value)

    def test_log_config_does_not_log_password_or_secret(self):
        """log_config must mention port/user but never the password or secret."""
        env = self._env(DASHBOARD_PASSWORD="topsecretpass", DASHBOARD_SECRET_KEY="topsecretkey")
        with patch.dict(os.environ, env, clear=True):
            mock_logger = Mock()
            Config.load().log_config(mock_logger, TranscodingSettings())

            logged_messages = [str(call.args[0]) for call in mock_logger.info.call_args_list]
            joined = "\n".join(logged_messages)
            assert "topsecretpass" not in joined
            assert "topsecretkey" not in joined
            assert any(
                "Dashboard:" in line and "port=9200" in line and "user=admin" in line
                for line in logged_messages
            )

    def test_log_config_reflects_db_settings(self):
        """log_config logs values from db_settings, not from env vars."""
        env = self._env()
        with patch.dict(os.environ, env, clear=True):
            db_settings = TranscodingSettings(
                video_bitrate=9999,
                video_resolution="1080p",
                audio_bitrate=256,
            )
            mock_logger = Mock()
            Config.load().log_config(mock_logger, db_settings)

            logged = "\n".join(str(c.args[0]) for c in mock_logger.info.call_args_list)
            assert "9999" in logged
            assert "1080p" in logged
            assert "256" in logged
