"""Application configuration loader - infrastructure layer."""
import os
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from domain.models.app_config import (
    AppConfig,
    PathsConfig,
    DatabaseConfig,
    DashboardConfig,
    LoggerConfig,
)
from domain.models.settings import TranscodingSettings
from infrastructure.utils import to_int


_DASHBOARD_FIELD_TO_ENV = {
    "port": "DASHBOARD_PORT",
    "user": "DASHBOARD_USER",
    "password": "DASHBOARD_PASSWORD",
    "secret_key": "DASHBOARD_SECRET_KEY",
    "cookie_secure": "DASHBOARD_COOKIE_SECURE",
}


class Config:
    """
    Configuration singleton - loads infrastructure configuration from environment variables.

    Covers: paths, database, logger, dashboard.
    Transcoding settings are owned by the DB (see TranscodingSettings / SettingsRepositorySQL).

    Uses lazy loading: each section is loaded only when accessed.
    """

    _instance: Optional['Config'] = None
    _app_config: Optional[AppConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls) -> 'Config':
        return cls()

    def log_config(self, logger, db_settings: TranscodingSettings) -> None:
        """Logs current configuration. Transcoding values come from db_settings (DB row)."""
        logger.info("Loading configuration...")
        _ = self.paths
        _ = self.database
        _ = self.logger
        _ = self.dashboard
        logger.info("Configuration loaded successfully")
        logger.info(f"  - Media path: {self.paths.media_path}")
        logger.info(f"  - Database path: {self.database.path}")
        logger.info(f"  - Hardware transcoding: {db_settings.hw_transcoding}")
        logger.info(f"  - Execution threads: {db_settings.execution_threads}")
        logger.info(f"  - Startup delay: {db_settings.startup_delay} minutes")
        logger.info(f"  - Execution interval: {db_settings.execution_interval} minutes")
        logger.info(
            f"  - Video: {db_settings.video_resolution} @ {db_settings.video_bitrate}kbps"
            f" ({db_settings.video_codec})"
        )
        logger.info(
            f"  - Audio: {db_settings.audio_codec} @ {db_settings.audio_bitrate}kbps"
            f" ({db_settings.audio_channels}ch)"
        )
        # Dashboard credentials are intentionally never logged.
        logger.info(f"  - Dashboard: port={self.dashboard.port}, user={self.dashboard.user}")

    @property
    def paths(self) -> PathsConfig:
        if self._app_config is None or self._app_config.paths is None:
            self._load_paths()
        return self._app_config.paths

    @property
    def database(self) -> DatabaseConfig:
        if self._app_config is None or self._app_config.database is None:
            self._load_database()
        return self._app_config.database

    @property
    def logger(self) -> LoggerConfig:
        if self._app_config is None or self._app_config.logger is None:
            self._load_logger()
        return self._app_config.logger

    @property
    def dashboard(self) -> DashboardConfig:
        if self._app_config is None or self._app_config.dashboard is None:
            self._load_dashboard()
        return self._app_config.dashboard

    def _ensure_app_config(self):
        if self._app_config is None:
            self._app_config = AppConfig(
                paths=None,
                database=None,
                logger=None,
                dashboard=None,
            )

    def _load_paths(self):
        self._ensure_app_config()

        media_app_path = os.getenv("MEDIA_APP_PATH", "/media")

        database_app_path = os.getenv("DATABASE_APP_PATH", "data/transcodings.db")
        if not database_app_path.endswith('.db'):
            if not database_app_path.endswith('/'):
                database_app_path += '/'
            database_app_path = os.path.join(database_app_path, "transcodings.db")
        Path(database_app_path).parent.mkdir(parents=True, exist_ok=True)

        self._app_config.paths = PathsConfig(
            media_path=media_app_path,
            database_path=database_app_path,
        )

    def _load_database(self):
        self._ensure_app_config()
        if self._app_config.paths is None:
            self._load_paths()
        self._app_config.database = DatabaseConfig(
            path=self._app_config.paths.database_path,
        )

    def _load_logger(self):
        self._ensure_app_config()
        logger_name = os.getenv("LOGGER_NAME", "synology-photos-video-enhancer")
        logger_level = os.getenv("LOGGER_LEVEL", "INFO").upper()
        self._app_config.logger = LoggerConfig(
            name=logger_name,
            level=logger_level,
        )

    def _load_dashboard(self):
        """Hard-fails if DASHBOARD_PASSWORD or DASHBOARD_SECRET_KEY are missing/empty."""
        self._ensure_app_config()

        port = to_int(os.getenv("DASHBOARD_PORT"), default=9200)
        user = os.getenv("DASHBOARD_USER", "admin")
        password = os.getenv("DASHBOARD_PASSWORD", "")
        secret_key = os.getenv("DASHBOARD_SECRET_KEY", "")
        cookie_secure = os.getenv("DASHBOARD_COOKIE_SECURE", "false").lower() in ("true", "1", "yes")

        try:
            self._app_config.dashboard = DashboardConfig(
                port=port,
                user=user,
                password=password,
                secret_key=secret_key,
                cookie_secure=cookie_secure,
            )
        except ValidationError as exc:
            offending = sorted({
                _DASHBOARD_FIELD_TO_ENV[error["loc"][0]]
                for error in exc.errors()
                if error["loc"] and error["loc"][0] in _DASHBOARD_FIELD_TO_ENV
            })
            offending_text = ", ".join(offending) if offending else "unknown field"
            raise RuntimeError(
                f"Dashboard configuration error: invalid or missing values for: {offending_text}"
            ) from exc

