from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, Field
from domain.constants.audio import AACProfile, AudioCodec
from domain.constants.container import ContainerFormat
from domain.constants.video import VideoCodec, VideoProfile

if TYPE_CHECKING:
    from domain.models.video import Video
    from domain.models.app_config import VideoConfig, AudioConfig
    from domain.models.hardware import HardwareVideoAcceleration


class TranscodingStatus(str, Enum):
    """Possible states of a transcoding."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class TranscodingConfiguration(BaseModel):
    """Configuration used for a specific transcoding."""
    video_codec: VideoCodec = Field(..., description="Video codec used for transcoding")
    video_profile: Optional[VideoProfile] = Field(default=None, description="Video profile (only for supported codecs)")
    video_height: int = Field(..., description="Output video height in pixels")
    video_framerate: float = Field(..., description="Video framerate (can be decimal for NTSC rates like 29.97, 59.94, 23.976)")
    video_bitrate: int = Field(..., description="Video bitrate in kbps")
    audio_codec: AudioCodec = Field(..., description="Audio codec used for transcoding")
    audio_profile: Optional[AACProfile] = Field(default=None, description="AAC profile (only for AAC codec)")
    audio_channels: int = Field(..., description="Number of audio channels")
    audio_bitrate: int = Field(..., description="Audio bitrate in kbps")
    container: ContainerFormat = Field(..., description="Container format for the output video")
    execution_threads: int = Field(..., description="Number of threads to use for transcoding")


class Transcoding(BaseModel):
    """Domain entity representing a transcoding."""
    original_video: Video = Field(..., description="Original video object")
    transcoded_video: Optional[Video] = Field(default=None, description="Transcoded video object (calculated during transcoding)")
    configuration: Optional[TranscodingConfiguration] = Field(default=None, description="Transcoding configuration used (calculated during transcoding)")
    status: TranscodingStatus = Field(default=TranscodingStatus.PENDING, description="Transcoding status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    def mark_as_completed(self) -> "Transcoding":
        """Marks the transcoding as completed."""
        return self.model_copy(update={
            "status": TranscodingStatus.COMPLETED,
            "updated_at": datetime.now()
        })
    
    def mark_as_in_progress(self) -> "Transcoding":
        """Marks the transcoding as in progress."""
        return self.model_copy(update={
            "status": TranscodingStatus.IN_PROGRESS,
            "updated_at": datetime.now()
        })
    
    def mark_as_failed(self, error_message: str) -> "Transcoding":
        """Marks the transcoding as failed."""
        return self.model_copy(update={
            "status": TranscodingStatus.FAILED,
            "error_message": error_message,
            "updated_at": datetime.now()
        })
    
    class Config:
        use_enum_values = True


# Rebuild model to resolve forward references
# Import Video here to avoid circular imports
from domain.models.video import Video  # noqa: E402
Transcoding.model_rebuild()
