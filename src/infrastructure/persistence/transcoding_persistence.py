from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from domain.models.transcoding import Transcoding, TranscodingStatus


class PersistentTranscoding(BaseModel):
    """Persistent representation of a transcoding for database storage."""
    original_video_path: str = Field(..., description="Path to the original video")
    transcoded_video_path: str = Field(..., description="Path to the transcoded video")
    transcoded_video_resolution: str = Field(..., description="Resolution in format 'widthxheight'")
    transcoded_video_codec: str = Field(..., description="Video codec name")
    status: TranscodingStatus = Field(default=TranscodingStatus.PENDING, description="Transcoding status")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    
    @classmethod
    def from_domain(cls, transcoding: Transcoding) -> "PersistentTranscoding":
        """
        Creates a PersistentTranscoding from a domain Transcoding entity.
        
        Args:
            transcoding: Domain Transcoding entity
            
        Returns:
            PersistentTranscoding with extracted data
        """
        # Extract resolution from transcoded video
        resolution = f"{transcoding.transcoded_video.video_track.width}x{transcoding.transcoded_video.video_track.height}"
        
        return cls(
            original_video_path=transcoding.original_video.path,
            transcoded_video_path=transcoding.transcoded_video.path,
            transcoded_video_resolution=resolution,
            transcoded_video_codec=transcoding.transcoded_video.video_track.codec_name,
            status=transcoding.status,
            error_message=transcoding.error_message
        )
    
    def to_dict(self) -> dict:
        """
        Converts to dictionary for database storage.
        
        Returns:
            Dictionary with all fields ready for database
        """
        return {
            "original_video_path": self.original_video_path,
            "transcoded_video_path": self.transcoded_video_path,
            "transcoded_video_resolution": self.transcoded_video_resolution,
            "transcoded_video_codec": self.transcoded_video_codec,
            "status": self.status.value if isinstance(self.status, TranscodingStatus) else self.status,
            "error_message": self.error_message
        }

