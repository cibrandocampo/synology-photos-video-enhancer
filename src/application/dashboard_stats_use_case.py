"""Use case that produces the dashboard stats payload."""
from domain.models.dashboard_stats import DashboardStats, LatestTranscoding
from domain.ports.transcoding_stats_repository import TranscodingStatsRepository


class DashboardStatsUseCase:
    """Returns a `DashboardStats` DTO consumed by both HTML and JSON routes."""

    def __init__(self, stats_repository: TranscodingStatsRepository) -> None:
        self._stats_repository = stats_repository

    def execute(self) -> DashboardStats:
        """Returns the dashboard stats from the repository unchanged."""
        return self._stats_repository.fetch_stats()

    def execute_latest_transcodings(
        self, page: int, page_size: int = 5
    ) -> tuple[list[LatestTranscoding], int]:
        """Returns a page of completed transcodings and the total count."""
        return self._stats_repository.fetch_latest_transcodings(page, page_size)
