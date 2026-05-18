"""Integration tests for SettingsRepositorySQL against a temp SQLite DB."""
from unittest.mock import Mock

import pytest

from domain.models.app_config import DatabaseConfig
from domain.models.settings import TranscodingSettings
from domain.ports.settings_repository import SettingsRepository
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.settings_repository_sql import SettingsRepositorySQL


@pytest.fixture
def db_connection(temp_db_path):
    connection = DatabaseConnection(DatabaseConfig(path=temp_db_path), Mock())
    connection.initialize()
    return connection


@pytest.fixture
def repository(db_connection):
    return SettingsRepositorySQL(db_connection)


class TestSettingsRepositorySQLContract:
    def test_subclasses_port(self, repository):
        assert isinstance(repository, SettingsRepository)


class TestLoad:
    def test_empty_database_returns_defaults(self, repository):
        settings = repository.load()

        assert isinstance(settings, TranscodingSettings)
        assert settings == TranscodingSettings()

    def test_returns_persisted_values(self, repository):
        original = TranscodingSettings(
            hw_transcoding=False,
            execution_threads=4,
            startup_delay=60,
            execution_interval=120,
            video_codec="hevc",
            video_bitrate=4000,
            video_resolution="1080p",
            video_profile="main",
            audio_codec="aac",
            audio_bitrate=256,
            audio_channels=2,
            audio_profile="aac_lc",
        )
        repository.save(original)

        loaded = repository.load()

        assert loaded.hw_transcoding is False
        assert loaded.execution_threads == 4
        assert loaded.startup_delay == 60
        assert loaded.execution_interval == 120
        assert loaded.video_codec == "hevc"
        assert loaded.video_bitrate == 4000
        assert loaded.video_resolution == "1080p"
        assert loaded.video_profile == "main"
        assert loaded.audio_codec == "aac"
        assert loaded.audio_bitrate == 256
        assert loaded.audio_channels == 2
        assert loaded.audio_profile == "aac_lc"


class TestSave:
    def test_save_inserts_row_when_none_exists(self, repository):
        settings = TranscodingSettings(video_bitrate=9999)
        repository.save(settings)

        loaded = repository.load()

        assert loaded.video_bitrate == 9999

    def test_save_updates_existing_row(self, repository):
        repository.save(TranscodingSettings(video_bitrate=1000))
        repository.save(TranscodingSettings(video_bitrate=2000))

        loaded = repository.load()

        assert loaded.video_bitrate == 2000

    def test_save_stores_none_for_empty_profile(self, repository):
        settings = TranscodingSettings(video_codec="av1", video_profile=None, audio_profile=None)
        repository.save(settings)

        loaded = repository.load()

        assert loaded.video_profile is None
        assert loaded.audio_profile is None


class TestSeedDefaults:
    def test_inserts_defaults_when_no_row_exists(self, repository):
        repository.seed_defaults()

        loaded = repository.load()

        assert loaded == TranscodingSettings()

    def test_does_not_overwrite_existing_row(self, repository):
        repository.save(TranscodingSettings(video_bitrate=9999))
        repository.seed_defaults()

        loaded = repository.load()

        assert loaded.video_bitrate == 9999
