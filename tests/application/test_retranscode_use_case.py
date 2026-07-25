"""Unit tests for RetranscodeUseCase."""
import pytest

from application.retranscode_use_case import RetranscodeUseCase
from domain.models.dashboard_stats import LatestTranscoding
from domain.ports.transcoding_stats_repository import TranscodingStatsRepository
from domain.ports.video_repository import VideoRepository


class _StubVideoRepository(VideoRepository):
    def __init__(self, reset_result: bool = True) -> None:
        self._reset_result = reset_result
        self.reset_calls: list[str] = []

    def find_by_original_path(self, original_path: str):
        return None

    def exists_by_original_path(self, original_path: str) -> bool:
        return False

    def save(self, transcoding):
        return transcoding

    def update_transcoded_metadata(
        self, original_path: str, width: int, height: int, codec: str
    ) -> bool:
        return False

    def reset_to_pending(self, original_path: str) -> bool:
        self.reset_calls.append(original_path)
        return self._reset_result


class _ExplodingVideoRepository(VideoRepository):
    def __init__(self, error: Exception) -> None:
        self._error = error

    def find_by_original_path(self, original_path: str):
        raise self._error

    def exists_by_original_path(self, original_path: str) -> bool:
        raise self._error

    def save(self, transcoding):
        raise self._error

    def update_transcoded_metadata(
        self, original_path: str, width: int, height: int, codec: str
    ) -> bool:
        raise self._error

    def reset_to_pending(self, original_path: str) -> bool:
        raise self._error


class _StubStatsRepository(TranscodingStatsRepository):
    def __init__(self, results: list[LatestTranscoding] | None = None) -> None:
        self._results = results or []
        self.search_calls: list[str] = []

    def fetch_stats(self):
        return None

    def fetch_latest_transcodings(self, page: int, page_size: int = 5):
        return [], 0

    def search_by_path(self, path: str) -> list[LatestTranscoding]:
        self.search_calls.append(path)
        return self._results


def _make_transcoding(path: str) -> LatestTranscoding:
    return LatestTranscoding(
        original_video_path=path,
        transcoded_video_path=path + ".out.mp4",
        status="completed",
        transcoded_video_codec="h264",
        transcoded_video_resolution="1280x720",
        error_message=None,
    )


class TestFind:
    def test_delegates_to_stats_repository_with_given_path(self):
        stub = _StubStatsRepository()
        use_case = RetranscodeUseCase(_StubVideoRepository(), stub)

        use_case.find("vacation")

        assert stub.search_calls == ["vacation"]

    def test_returns_list_from_repository(self):
        item = _make_transcoding("/media/vacation/beach.mp4")
        stub = _StubStatsRepository([item])
        use_case = RetranscodeUseCase(_StubVideoRepository(), stub)

        result = use_case.find("vacation")

        assert result is stub._results
        assert len(result) == 1
        assert result[0].original_video_path == "/media/vacation/beach.mp4"

    def test_returns_empty_list_when_repository_returns_empty(self):
        stub = _StubStatsRepository([])
        use_case = RetranscodeUseCase(_StubVideoRepository(), stub)

        result = use_case.find("zzz")

        assert result == []


class TestReset:
    def test_delegates_to_video_repository_with_given_path(self):
        stub_video = _StubVideoRepository(reset_result=True)
        use_case = RetranscodeUseCase(stub_video, _StubStatsRepository())

        use_case.reset("/media/video.mp4")

        assert stub_video.reset_calls == ["/media/video.mp4"]

    def test_returns_true_when_repository_returns_true(self):
        use_case = RetranscodeUseCase(_StubVideoRepository(True), _StubStatsRepository())

        assert use_case.reset("/media/video.mp4") is True

    def test_returns_false_when_repository_returns_false(self):
        use_case = RetranscodeUseCase(_StubVideoRepository(False), _StubStatsRepository())

        assert use_case.reset("/media/video.mp4") is False

    def test_propagates_exception_from_repository(self):
        error = RuntimeError("db down")
        use_case = RetranscodeUseCase(_ExplodingVideoRepository(error), _StubStatsRepository())

        with pytest.raises(RuntimeError) as exc_info:
            use_case.reset("/media/video.mp4")

        assert exc_info.value is error
