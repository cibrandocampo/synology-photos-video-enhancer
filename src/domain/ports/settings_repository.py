"""Port for transcoding settings persistence."""
from abc import ABC, abstractmethod

from domain.models.settings import TranscodingSettings


class SettingsRepository(ABC):
    @abstractmethod
    def load(self) -> TranscodingSettings: ...

    @abstractmethod
    def save(self, settings: TranscodingSettings) -> None: ...

    @abstractmethod
    def seed_defaults(self) -> None: ...
