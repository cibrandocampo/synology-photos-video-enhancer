"""Use case for forcing a video re-transcoding."""
from domain.models.dashboard_stats import LatestTranscoding
from domain.ports.transcoding_stats_repository import TranscodingStatsRepository
from domain.ports.video_repository import VideoRepository


class RetranscodeUseCase:
    def __init__(
        self,
        video_repository: VideoRepository,
        stats_repository: TranscodingStatsRepository,
    ) -> None:
        self._video_repository = video_repository
        self._stats_repository = stats_repository

    def find(self, path: str) -> list[LatestTranscoding]:
        """Returns transcodings whose path contains the given substring (min 3 chars)."""
        return self._stats_repository.search_by_path(path)

    def reset(self, original_path: str) -> bool:
        """
        Resets a transcoding to PENDING. Returns True if the record was updated,
        False if it did not exist or was not in an eligible status (completed/failed).
        """
        return self._video_repository.reset_to_pending(original_path)
