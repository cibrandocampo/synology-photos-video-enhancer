from typing import List, Any
from pydantic import BaseModel, Field, field_validator
from domain.constants.synology import MetadataIndex
from domain.constants.video import VideoCodec
from domain.constants.audio import AudioCodec
from domain.constants.container import ContainerFormat


class VideoTrack(BaseModel):
    """Video track information."""
    width: int = Field(..., description="Video width in pixels")
    height: int = Field(..., description="Video height in pixels")
    codec_name: str = Field(..., description="Video codec name")
    profile: str = Field(default="", description="Codec profile")
    framerate: int = Field(..., description="Frames per second")
    bitrate: float = Field(default=0.0, description="Video bitrate")
    
    @field_validator('codec_name')
    @classmethod
    def validate_codec(cls, v: str) -> str:
        """Validates that the codec is one of the supported video codecs."""
        if not v:
            return VideoCodec.H264.value  # Default to h264
        # Try to match the codec (case insensitive)
        codec_lower = v.lower()
        for codec in VideoCodec:
            if codec.value == codec_lower:
                return codec.value
        # If not found, return default h264
        return VideoCodec.H264.value
    
    @property
    def resolution(self) -> str:
        """
        Gets the video resolution as a string in format 'width x height'.
        
        Returns:
            Resolution string (e.g., '1920x1080')
        """
        return f"{self.width}x{self.height}"


class AudioTrack(BaseModel):
    """Audio track information."""
    bitrate: float = Field(default=0.0, description="Bitrate")
    codec: str = Field(default="", description="Codec name")
    channels: int = Field(default=0, description="Audio channels")
    
    @field_validator('codec')
    @classmethod
    def validate_codec(cls, v: str) -> str:
        """Validates that the codec is one of the supported audio codecs."""
        if not v:
            return AudioCodec.MP3.value  # Default to mp3
        # Try to match the codec (case insensitive)
        codec_lower = v.lower()
        for codec in AudioCodec:
            if codec.value == codec_lower:
                return codec.value
        # If not found, return default mp3
        return AudioCodec.MP3.value


class Container(BaseModel):
    """Container information."""
    format: str = Field(..., description="Container format")
    duration: float = Field(default=0.0, description="Video duration in seconds")
    total_bitrate: float = Field(default=0.0, description="Total bitrate")
    file_size: int = Field(default=0, description="File size in bytes")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validates that the format is one of the supported container formats."""
        if not v:
            return ContainerFormat.MP4.value  # Default to mp4
        # Try to match the format (case insensitive)
        format_lower = v.lower()
        for container in ContainerFormat:
            if container.value == format_lower:
                return container.value
        # If not found, return default mp4
        return ContainerFormat.MP4.value


class Video(BaseModel):
    """Domain entity representing a video."""
    path: str = Field(..., description="Full path to the video file")
    video_track: VideoTrack = Field(..., description="Video track information")
    audio_track: AudioTrack = Field(..., description="Audio track information")
    container: Container = Field(..., description="Container information")
    
    @classmethod
    def from_synology_metadata(cls, path: str, metadata_list: List[Any]) -> "Video":
        """
        Creates a Video from Synology's metadata list.
        
        Uses MetadataIndex to get values from correct positions.
        Never raises errors, uses default values if data is missing.
        
        Args:
            path: Full path to the video file
            metadata_list: List with Synology metadata
            
        Returns:
            Video with extracted data (uses defaults for missing fields)
        """
        def safe_get(index: int, default: Any = None) -> Any:
            """Safely gets a value from the list."""
            try:
                return metadata_list[index] if index < len(metadata_list) else default
            except (IndexError, TypeError):
                return default
        
        def safe_int(value: Any, default: int = 0) -> int:
            """Safely converts a value to int."""
            try:
                return int(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        def safe_float(value: Any, default: float = 0.0) -> float:
            """Safely converts a value to float."""
            try:
                return float(value) if value is not None else default
            except (ValueError, TypeError):
                return default
        
        def safe_str(value: Any, default: str = "") -> str:
            """Safely converts a value to string."""
            return str(value) if value is not None else default
        
        # Extract video metadata fields (use defaults if missing)
        width = safe_int(safe_get(MetadataIndex.WIDTH), default=0)
        height = safe_int(safe_get(MetadataIndex.HEIGHT), default=0)
        video_codec = safe_str(safe_get(MetadataIndex.VIDEO_CODEC), default="")
        framerate = safe_int(safe_get(MetadataIndex.FRAMERATE), default=0)
        video_bitrate = safe_float(safe_get(MetadataIndex.VIDEO_BITRATE), default=0.0)
        
        # Extract audio metadata fields (use defaults if missing)
        audio_bitrate = safe_float(safe_get(MetadataIndex.AUDIO_BITRATE), default=0.0)
        audio_codec = safe_str(safe_get(MetadataIndex.AUDIO_CODEC), default="")
        channels = safe_int(safe_get(MetadataIndex.CHANNELS), default=0)
        
        # Extract container metadata fields (use defaults if missing)
        container_format = safe_str(safe_get(MetadataIndex.CONTAINER), default="")
        duration = safe_float(safe_get(MetadataIndex.DURATION), default=0.0)
        total_bitrate = safe_float(safe_get(MetadataIndex.TOTAL_BITRATE), default=0.0)
        file_size = safe_int(safe_get(MetadataIndex.FILE_SIZE), default=0)
        
        # Create track objects (validation happens in the models)
        video_track = VideoTrack(
            width=width,
            height=height,
            codec_name=video_codec,
            framerate=framerate,
            bitrate=video_bitrate,
            profile=""  # Not available in Synology's list
        )
        
        audio_track = AudioTrack(
            bitrate=audio_bitrate,
            codec=audio_codec,
            channels=channels
        )
        
        container_info = Container(
            format=container_format,
            duration=duration,
            total_bitrate=total_bitrate,
            file_size=file_size
        )
        
        return cls(
            path=path,
            video_track=video_track,
            audio_track=audio_track,
            container=container_info
        )
    
    class Config:
        frozen = True  # Immutable to maintain integrity

