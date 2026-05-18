"""SQL adapter for settings persistence."""
from domain.models.settings import TranscodingSettings
from domain.ports.settings_repository import SettingsRepository
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import SettingsModel

_ROW_ID = 1


class SettingsRepositorySQL(SettingsRepository):
    def __init__(self, db_connection: DatabaseConnection) -> None:
        self._db = db_connection

    def load(self) -> TranscodingSettings:
        session = self._db.get_session()
        try:
            row = session.get(SettingsModel, _ROW_ID)
            if row is None:
                return TranscodingSettings()
            return TranscodingSettings(
                hw_transcoding=row.hw_transcoding,
                execution_threads=row.execution_threads,
                startup_delay=row.startup_delay,
                execution_interval=row.execution_interval,
                video_codec=row.video_codec,
                video_bitrate=row.video_bitrate,
                video_resolution=row.video_resolution,
                video_profile=row.video_profile,
                audio_codec=row.audio_codec,
                audio_bitrate=row.audio_bitrate,
                audio_channels=row.audio_channels,
                audio_profile=row.audio_profile,
            )
        finally:
            session.close()

    def seed_defaults(self) -> None:
        session = self._db.get_session()
        try:
            exists = session.get(SettingsModel, _ROW_ID) is not None
        finally:
            session.close()
        if not exists:
            self.save(TranscodingSettings())

    def save(self, settings: TranscodingSettings) -> None:
        session = self._db.get_session()
        try:
            row = session.get(SettingsModel, _ROW_ID)
            if row is None:
                row = SettingsModel(id=_ROW_ID)
                session.add(row)
            row.hw_transcoding = settings.hw_transcoding
            row.execution_threads = settings.execution_threads
            row.startup_delay = settings.startup_delay
            row.execution_interval = settings.execution_interval
            row.video_codec = settings.video_codec
            row.video_bitrate = settings.video_bitrate
            row.video_resolution = settings.video_resolution
            row.video_profile = settings.video_profile or None
            row.audio_codec = settings.audio_codec
            row.audio_bitrate = settings.audio_bitrate
            row.audio_channels = settings.audio_channels
            row.audio_profile = settings.audio_profile or None
            session.commit()
        finally:
            session.close()
