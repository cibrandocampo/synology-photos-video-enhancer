"""Port for video transcoding operations."""
from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.models.video import Video


class Transcoder(ABC):
    """Interface for video transcoding operations."""
    
    @abstractmethod
    def transcode(self) -> bool:
        """
        Transcodes a video file.
        
        The transcoder uses its internal configuration (codec, bitrate, resolution, etc.)
        and input/output paths that were set during initialization or through other means.
        
        Returns:
            True if transcoding succeeded, False otherwise
        """
        pass
