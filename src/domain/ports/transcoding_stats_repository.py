"""Port for read-only aggregation of the `transcodings` table."""
from abc import ABC, abstractmethod

from domain.models.dashboard_stats import DashboardStats, LatestTranscoding


class TranscodingStatsRepository(ABC):
    """Interface for read-only aggregation queries used by the dashboard."""

    @abstractmethod
    def fetch_stats(self) -> DashboardStats:  # pragma: no cover
        """Returns a fully populated `DashboardStats` payload."""
        pass

    @abstractmethod
    def fetch_latest_transcodings(  # pragma: no cover
        self, page: int, page_size: int = 5
    ) -> tuple[list[LatestTranscoding], int]:
        """
        Returns a page of completed transcodings ordered by insertion (newest first)
        and the total count of completed transcodings.
        """
        pass

    @abstractmethod
    def search_by_path(self, path: str) -> list[LatestTranscoding]:  # pragma: no cover
        """
        Returns transcodings whose original_video_path contains `path`
        (case-insensitive substring match). Returns an empty list if nothing
        matches or if `path` is shorter than 3 characters. Results are ordered
        by original_video_path ascending and capped at 20.
        """
        pass
