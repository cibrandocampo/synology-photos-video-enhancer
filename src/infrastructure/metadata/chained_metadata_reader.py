"""Video metadata reader that consults several sources in order."""
from typing import Optional, Sequence

from domain.models.video import Video
from domain.ports.logger import AppLogger
from domain.ports.video_metadata_reader import VideoMetadataReader


class ChainedMetadataReader(VideoMetadataReader):
    """Tries several readers in order; the first non-None result wins."""

    def __init__(self, readers: Sequence[VideoMetadataReader], logger: AppLogger):
        """
        Initializes the chain.

        Args:
            readers: Readers to consult, in order of preference
            logger: Application logger
        """
        self.readers = readers
        self.logger = logger

    def read(self, video_path: str) -> Optional[Video]:
        """
        Reads metadata from the first source able to provide it.

        Args:
            video_path: Full path to the video file

        Returns:
            Video from the first reader that returns one, or None when no reader can.
        """
        for reader in self.readers:
            try:
                video = reader.read(video_path)
            except Exception as error:
                # One broken source must not hide the ones behind it.
                self.logger.warning(
                    f"{type(reader).__name__} failed for {video_path}: {error}"
                )
                continue

            if video is not None:
                return video

        return None
