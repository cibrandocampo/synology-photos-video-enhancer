"""Video metadata reader backed by Synology's SYNOINDEX_MEDIA_INFO index."""
import os
from typing import Optional

from domain.models.video import Video
from domain.parsers.synoindex_media_info import SynoIndexMediaInfo
from domain.ports.filesystem import Filesystem
from domain.ports.logger import AppLogger
from domain.ports.video_metadata_reader import VideoMetadataReader

EA_DIR = "@eaDir"
INDEX_FILENAME = "SYNOINDEX_MEDIA_INFO"


class SynoIndexMetadataReader(VideoMetadataReader):
    """Reads video metadata from Synology's SYNOINDEX_MEDIA_INFO index."""

    def __init__(self, filesystem: Filesystem, logger: AppLogger):
        """
        Initializes the reader.

        Args:
            filesystem: Filesystem used to read the index file
            logger: Application logger
        """
        self.filesystem = filesystem
        self.logger = logger

    def read(self, video_path: str) -> Optional[Video]:
        """
        Reads metadata from the Synology index sitting next to the video.

        Args:
            video_path: Full path to the video file

        Returns:
            Video with the indexed metadata, or None when the index is missing,
            unreadable or does not parse.
        """
        index_path = self._index_path(video_path)

        try:
            content = self.filesystem.read_file(index_path)
        except Exception as error:
            # A path Synology wrote in a legacy encoding raises here. Falling
            # through to the next reader is correct; aborting the cycle is not.
            self.logger.warning(f"Could not read {index_path}: {error}")
            return None

        if content is None:
            # Videos Synology has not indexed are ordinary, not a problem.
            self.logger.debug(f"No Synology index at {index_path}")
            return None

        video = SynoIndexMediaInfo.parse(video_path, content)
        if video is None:
            self.logger.warning(
                f"Synology index at {index_path} did not yield usable metadata"
            )

        return video

    @staticmethod
    def _index_path(video_path: str) -> str:
        """Builds the path of the index file belonging to a video."""
        return os.path.join(
            os.path.dirname(video_path),
            EA_DIR,
            os.path.basename(video_path),
            INDEX_FILENAME,
        )
