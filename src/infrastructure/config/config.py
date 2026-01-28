"""Application configuration loader - infrastructure layer."""
import os
from pathlib import Path
from typing import Optional

from domain.models.app_config import (
    AppConfig,
    PathsConfig,
    TranscodingConfig,
    VideoConfig,
    AudioConfig,
    DatabaseConfig,
    LoggerConfig
)
from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.resolution import VideoResolution
from domain.constants.audio import AudioCodec
from infrastructure.utils import to_int


class Config:
    """
    Configuration singleton - loads configuration from environment variables.
    
    Uses lazy loading: each section is loaded only when accessed.
    This allows accessing specific parts like config.transcoding without
    loading the entire configuration.
    
    Example:
        config = Config.load()
        transcoding = config.transcoding  # Only loads transcoding section
    """
    
    _instance: Optional['Config'] = None
    _app_config: Optional[AppConfig] = None
    
    def __new__(cls):
        """Singleton pattern - returns the same instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load(cls) -> 'Config':
        """
        Loads and returns the configuration instance.
        
        This method loads all configuration sections.
        The singleton pattern is used internally but is transparent to callers.
        
        Returns:
            Config instance with all sections loaded
        """
        return cls()
    
    @classmethod
    def get_instance(cls) -> 'Config':
        """
        Gets the singleton instance (deprecated, use load() instead).
        
        Returns:
            Config singleton instance
        """
        return cls()
    
    def log_config(self, logger):
        """Logs the current configuration."""
        logger.info("Loading configuration...")
        # Ensure all sections are loaded
        _ = self.paths
        _ = self.transcoding
        _ = self.database
        _ = self.logger
        logger.info("Configuration loaded successfully")
        logger.info(f"  - Media path: {self.paths.media_path}")
        logger.info(f"  - Database path: {self.database.path}")
        logger.info(f"  - Hardware transcoding: {self.transcoding.hw_transcoding}")
        logger.info(f"  - Execution threads: {self.transcoding.execution_threads}")
        logger.info(f"  - Startup delay: {self.transcoding.startup_delay} minutes")
        logger.info(f"  - Execution interval: {self.transcoding.execution_interval} minutes")
        profile_str = f" ({self.transcoding.video.profile.value})" if self.transcoding.video.profile else ""
        logger.info(
            f"  - Video: {self.transcoding.video.resolution.name} "
            f"({self.transcoding.video.width}x{self.transcoding.video.height}) "
            f"@ {self.transcoding.video.bitrate}kbps ({self.transcoding.video.codec.value}{profile_str})"
        )
        logger.info(
            f"  - Audio: {self.transcoding.audio.codec.value} "
            f"@ {self.transcoding.audio.bitrate}kbps ({self.transcoding.audio.channels}ch)"
        )
    
    @property
    def paths(self) -> PathsConfig:
        """Gets paths configuration (lazy loaded)."""
        if self._app_config is None or self._app_config.paths is None:
            self._load_paths()
        return self._app_config.paths
    
    @property
    def transcoding(self) -> TranscodingConfig:
        """Gets transcoding configuration (lazy loaded)."""
        if self._app_config is None or self._app_config.transcoding is None:
            self._load_transcoding()
        return self._app_config.transcoding
    
    @property
    def database(self) -> DatabaseConfig:
        """Gets database configuration (lazy loaded)."""
        if self._app_config is None or self._app_config.database is None:
            self._load_database()
        return self._app_config.database
    
    @property
    def logger(self) -> LoggerConfig:
        """Gets logger configuration (lazy loaded)."""
        if self._app_config is None or self._app_config.logger is None:
            self._load_logger()
        return self._app_config.logger
    
    
    def _ensure_app_config(self):
        """Ensures AppConfig instance exists."""
        if self._app_config is None:
            self._app_config = AppConfig(
                paths=None,
                transcoding=None,
                database=None,
                logger=None
            )
    
    def _load_paths(self):
        """Loads paths configuration from environment variables."""
        self._ensure_app_config()
        
        # Media path: path inside the container where media is mounted
        media_app_path = os.getenv("MEDIA_APP_PATH", "/media")
        
        # Database path: path inside the container where database is stored
        database_app_path = os.getenv("DATABASE_APP_PATH", "data/transcodings.db")
        # If path doesn't end with .db, it's a directory, so append the database filename
        if not database_app_path.endswith('.db'):
            # Ensure directory path ends with / for proper joining
            if not database_app_path.endswith('/'):
                database_app_path += '/'
            database_app_path = os.path.join(database_app_path, "transcodings.db")
        Path(database_app_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._app_config.paths = PathsConfig(
            media_path=media_app_path,
            database_path=database_app_path
        )
    
    def _load_transcoding(self):
        """Loads transcoding configuration from environment variables."""
        self._ensure_app_config()
        
        # General transcoding settings
        hw_transcoding = os.getenv("HW_TRANSCODING", "True").lower() in ("true", "1", "yes")
        execution_threads = to_int(os.getenv("EXECUTION_THREADS"), default=2)
        startup_delay = to_int(os.getenv("STARTUP_DELAY"), default=30)  # Default 30 minutes
        execution_interval = to_int(os.getenv("EXECUTION_INTERVAL"), default=240)  # Default 4 hours
        
        # Video configuration
        video_codec_raw = os.getenv("VIDEO_CODEC", "h264")
        video_codec = VideoCodec.from_str(video_codec_raw)
        video_bitrate = to_int(os.getenv("VIDEO_BITRATE"), default=2048)
        
        # Resolution: use VIDEO_RESOLUTION if available, otherwise fallback to VIDEO_W/VIDEO_H
        video_resolution_raw = os.getenv("VIDEO_RESOLUTION")
        if video_resolution_raw:
            # Use resolution name to get width/height
            video_resolution = VideoResolution.from_str(video_resolution_raw)
            video_width = video_resolution.width
            video_height = video_resolution.height
        else:
            # Fallback to individual width/height for backward compatibility
            video_width = to_int(os.getenv("VIDEO_W"), default=854)  # Default to 480p width
            video_height = to_int(os.getenv("VIDEO_H"), default=480)  # Default to 480p height
            # Try to match resolution based on dimensions
            video_resolution = VideoResolution.P480  # Default
            for res in VideoResolution:
                if res.width == video_width and res.height == video_height:
                    video_resolution = res
                    break
        
        # Profile: validate against codec, use default if invalid or not provided
        video_profile_raw = os.getenv("VIDEO_PROFILE")
        if video_profile_raw:
            video_profile = VideoProfile.from_str(video_profile_raw, video_codec)
        else:
            # Use default profile for the codec
            video_profile = VideoProfile.get_default(video_codec)
        
        # Only set profile if codec supports it
        video_profile_value = video_profile if video_codec.supports_profile() else None
        
        video_config = VideoConfig(
            codec=video_codec,
            bitrate=video_bitrate,
            resolution=video_resolution,
            width=video_width,
            height=video_height,
            profile=video_profile_value
        )
        
        # Audio configuration
        audio_codec_raw = os.getenv("AUDIO_CODEC", "aac")
        audio_codec = AudioCodec.from_str(audio_codec_raw)
        audio_bitrate = to_int(os.getenv("AUDIO_BITRATE"), default=128)
        audio_channels = to_int(os.getenv("AUDIO_CHANNELS"), default=1)
        
        # Audio profile (only for AAC)
        audio_profile_raw = os.getenv("AUDIO_PROFILE", "")
        audio_profile = None
        if audio_profile_raw and audio_codec == AudioCodec.AAC:
            from domain.constants.audio import AACProfile
            audio_profile = AACProfile.from_str(audio_profile_raw)
        
        audio_config = AudioConfig(
            codec=audio_codec,
            bitrate=audio_bitrate,  # Validation happens in AudioConfig model
            channels=audio_channels,
            profile=audio_profile
        )
        
        self._app_config.transcoding = TranscodingConfig(
            hw_transcoding=hw_transcoding,
            execution_threads=execution_threads,
            startup_delay=startup_delay,
            execution_interval=execution_interval,
            video=video_config,
            audio=audio_config
        )
    
    def _load_database(self):
        """Loads database configuration from environment variables."""
        self._ensure_app_config()
        
        # Database path is loaded with paths, but we ensure paths are loaded first
        if self._app_config.paths is None:
            self._load_paths()
        
        self._app_config.database = DatabaseConfig(
            path=self._app_config.paths.database_path
        )
    
    def _load_logger(self):
        """Loads logger configuration from environment variables."""
        self._ensure_app_config()
        
        logger_name = os.getenv("LOGGER_NAME", "synology-photos-video-enhancer")
        logger_level = os.getenv("LOGGER_LEVEL", "INFO").upper()
        
        self._app_config.logger = LoggerConfig(
            name=logger_name,
            level=logger_level
        )
    
    def load_all(self) -> AppConfig:
        """
        Loads all configuration sections at once.
        
        Returns:
            Complete AppConfig with all sections loaded
        """
        # Access all properties to trigger lazy loading
        _ = self.paths
        _ = self.transcoding
        _ = self.database
        _ = self.logger
        
        return self._app_config
