"""Use case for reading and saving transcoding settings."""
from domain.models.settings import TranscodingSettings
from domain.ports.settings_repository import SettingsRepository


class SettingsUseCase:
    def __init__(self, settings_repository: SettingsRepository) -> None:
        self._repo = settings_repository

    def load(self) -> TranscodingSettings:
        return self._repo.load()

    def save(self, settings: TranscodingSettings) -> None:
        self._repo.save(settings)

    def seed_defaults(self) -> None:
        self._repo.seed_defaults()
