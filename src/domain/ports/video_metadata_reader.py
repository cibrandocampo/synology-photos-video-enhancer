"""Port for reading video metadata."""
from abc import ABC, abstractmethod
from typing import Optional

from domain.models.video import Video


class VideoMetadataReader(ABC):
    """Interface for reading video metadata from a source."""

    @abstractmethod
    def read(self, video_path: str) -> Optional[Video]:
        """
        Reads metadata for the video at the given path.

        Args:
            video_path: Full path to the video file

        Returns:
            Video with the metadata, or None when it cannot be determined.
            Callers must treat None as "unknown", never as "empty": deriving
            transcoding parameters from unknown geometry is what produced
            incorrectly encoded files in the past.
        """
        pass  # pragma: no cover
