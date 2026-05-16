"""Port for read-only aggregation of the `transcodings` table."""
from abc import ABC, abstractmethod

from domain.models.dashboard_stats import DashboardStats, LatestTranscoding


class TranscodingStatsRepository(ABC):
    """Interface for read-only aggregation queries used by the dashboard."""

    @abstractmethod
    def fetch_stats(self) -> DashboardStats:
        """Returns a fully populated `DashboardStats` payload."""
        pass

    @abstractmethod
    def fetch_latest_transcodings(
        self, page: int, page_size: int = 5
    ) -> tuple[list[LatestTranscoding], int]:
        """
        Returns a page of completed transcodings ordered by insertion (newest first)
        and the total count of completed transcodings.
        """
        pass
