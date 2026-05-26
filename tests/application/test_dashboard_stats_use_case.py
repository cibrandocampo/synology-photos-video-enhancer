"""Tests for the DashboardStatsUseCase."""
import pytest

from application.dashboard_stats_use_case import DashboardStatsUseCase
from domain.models.dashboard_stats import (
    CodecCount,
    DashboardStats,
    ErrorCount,
    LatestTranscoding,
    ResolutionCount,
)
from domain.ports.transcoding_stats_repository import TranscodingStatsRepository


class _StubStatsRepository(TranscodingStatsRepository):
    """Hand-rolled stub honoring the `TranscodingStatsRepository` port."""

    def __init__(self, payload: DashboardStats) -> None:
        self._payload = payload
        self.calls = 0

    def fetch_stats(self) -> DashboardStats:
        self.calls += 1
        return self._payload

    def fetch_latest_transcodings(self, page: int, page_size: int = 5):
        return [], 0

    def search_by_path(self, path: str):
        return []


class _ExplodingStatsRepository(TranscodingStatsRepository):
    """Stub that raises on every call to verify exception propagation."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    def fetch_stats(self) -> DashboardStats:
        raise self._error

    def fetch_latest_transcodings(self, page: int, page_size: int = 5):
        raise self._error

    def search_by_path(self, path: str):
        raise self._error


def _sample_stats() -> DashboardStats:
    return DashboardStats(
        total=3,
        status_counts={
            "pending": 0,
            "in_progress": 0,
            "completed": 2,
            "not_required": 0,
            "failed": 1,
        },
        success_rate=66.67,
        codec_distribution=[CodecCount(codec="h264", count=2)],
        resolution_distribution=[ResolutionCount(resolution="1280x720", count=2)],
        latest_transcodings=[
            LatestTranscoding(
                original_video_path="/m/a.mp4",
                transcoded_video_path="/m/a.out.mp4",
                status="completed",
                transcoded_video_codec="h264",
                transcoded_video_resolution="1280x720",
                error_message=None,
            )
        ],
        top_errors=[ErrorCount(error_summary="codec not supported", count=1)],
    )


class TestDashboardStatsUseCase:
    """Tests for DashboardStatsUseCase."""

    def test_constructor_stores_repository_reference(self):
        stub = _StubStatsRepository(_sample_stats())
        use_case = DashboardStatsUseCase(stub)
        assert use_case._stats_repository is stub

    def test_execute_returns_repository_payload_identity(self):
        payload = _sample_stats()
        stub = _StubStatsRepository(payload)
        use_case = DashboardStatsUseCase(stub)

        result = use_case.execute()

        assert result is payload
        assert stub.calls == 1

    def test_execute_calls_fetch_stats_on_each_invocation(self):
        stub = _StubStatsRepository(_sample_stats())
        use_case = DashboardStatsUseCase(stub)

        use_case.execute()
        use_case.execute()
        use_case.execute()

        assert stub.calls == 3

    def test_execute_propagates_repository_runtime_error(self):
        original = RuntimeError("db down")
        use_case = DashboardStatsUseCase(_ExplodingStatsRepository(original))

        with pytest.raises(RuntimeError) as exc_info:
            use_case.execute()

        assert exc_info.value is original

    def test_execute_propagates_arbitrary_exception(self):
        original = ValueError("schema mismatch")
        use_case = DashboardStatsUseCase(_ExplodingStatsRepository(original))

        with pytest.raises(ValueError) as exc_info:
            use_case.execute()

        assert exc_info.value is original


class TestExecuteLatestTranscodings:
    def test_delegates_to_repository_with_correct_args(self):
        stub = _StubStatsRepository(_sample_stats())
        use_case = DashboardStatsUseCase(stub)

        result, total = use_case.execute_latest_transcodings(page=2, page_size=10)

        assert result == []
        assert total == 0

    def test_propagates_repository_error(self):
        error = RuntimeError("db failure")
        use_case = DashboardStatsUseCase(_ExplodingStatsRepository(error))

        with pytest.raises(RuntimeError):
            use_case.execute_latest_transcodings(page=1)
