"""Tests for SettingsUseCase."""
from unittest.mock import Mock

from application.settings_use_case import SettingsUseCase
from domain.models.settings import TranscodingSettings


class _StubSettingsRepository:
    def __init__(self, settings: TranscodingSettings) -> None:
        self._settings = settings
        self.saved: TranscodingSettings | None = None
        self.seed_defaults_calls = 0

    def load(self) -> TranscodingSettings:
        return self._settings

    def save(self, settings: TranscodingSettings) -> None:
        self.saved = settings

    def seed_defaults(self) -> None:
        self.seed_defaults_calls += 1


class TestSettingsUseCase:
    def test_load_delegates_to_repository(self):
        expected = TranscodingSettings(video_bitrate=9999)
        stub = _StubSettingsRepository(expected)
        use_case = SettingsUseCase(stub)

        result = use_case.load()

        assert result is expected

    def test_save_delegates_to_repository(self):
        stub = _StubSettingsRepository(TranscodingSettings())
        use_case = SettingsUseCase(stub)
        settings = TranscodingSettings(execution_threads=8)

        use_case.save(settings)

        assert stub.saved is settings

    def test_seed_defaults_delegates_to_repository(self):
        stub = _StubSettingsRepository(TranscodingSettings())
        use_case = SettingsUseCase(stub)

        use_case.seed_defaults()

        assert stub.seed_defaults_calls == 1
