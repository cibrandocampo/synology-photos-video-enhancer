"""Application configuration domain model."""
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator

from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.resolution import VideoResolution
from domain.constants.audio import AudioCodec, AACProfile


class PathsConfig(BaseModel):
    """Paths configuration."""
    media_path: str  # Path where media folders are mounted in Docker
    database_path: str  # Path to database file


class VideoConfig(BaseModel):
    """Video transcoding configuration."""
    codec: VideoCodec  # Video codec enum
    bitrate: int  # Video bitrate in kbps
    resolution: VideoResolution  # Video resolution enum (e.g., '720p')
    width: int  # Output video width (must match resolution)
    height: int  # Output video height (must match resolution)
    profile: Optional[VideoProfile] = None  # Video profile (only for H264, HEVC, MPEG2VIDEO, MPEG4)
    
    @model_validator(mode='after')
    def ensure_dimensions_match_resolution_and_profile(self) -> 'VideoConfig':
        """
        Ensures width and height match the resolution, and profile is valid for codec.
        
        Returns:
            VideoConfig with corrected dimensions and profile
        """
        # Override width and height to match resolution
        self.width = self.resolution.width
        self.height = self.resolution.height
        
        # Set profile to None if codec doesn't support profiles
        if not self.codec.supports_profile():
            self.profile = None
        elif self.profile is None:
            # Set default profile if codec supports profiles but none was provided
            self.profile = VideoProfile.get_default(self.codec)
        
        return self


class AudioConfig(BaseModel):
    """Audio transcoding configuration."""
    codec: AudioCodec  # Audio codec enum
    bitrate: int  # Audio bitrate in kbps (validated between 64 and 320)
    channels: int  # Audio channels (validated between 1 and 8)
    profile: Optional[AACProfile] = None  # AAC profile (only for AAC codec)
    
    @field_validator('bitrate')
    @classmethod
    def validate_bitrate(cls, v: int) -> int:
        """
        Validates that audio bitrate is between 64 and 320 kbps.
        
        Args:
            v: Bitrate value
            
        Returns:
            Bitrate clamped to valid range [64, 320]
        """
        return max(64, min(320, v))
    
    @field_validator('channels')
    @classmethod
    def validate_channels(cls, v: int) -> int:
        """
        Validates that audio channels are between 1 and 8.
        
        Args:
            v: Channels value
            
        Returns:
            Channels clamped to valid range [1, 8]
        """
        return max(1, min(8, v))


class TranscodingConfig(BaseModel):
    """Transcoding configuration."""
    hw_transcoding: bool  # Enable hardware transcoding
    execution_threads: int  # Number of execution threads
    startup_delay: int  # Delay in minutes before first execution after container startup
    execution_interval: int  # Interval in minutes between executions
    video: VideoConfig  # Video configuration
    audio: AudioConfig  # Audio configuration


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str  # Path to database file


class LoggerConfig(BaseModel):
    """Logger configuration."""
    name: str  # Logger name
    level: str  # Logger level


class AppConfig(BaseModel):
    """Domain model for application configuration."""
    paths: Optional[PathsConfig] = None
    transcoding: Optional[TranscodingConfig] = None
    database: Optional[DatabaseConfig] = None
    logger: Optional[LoggerConfig] = None
