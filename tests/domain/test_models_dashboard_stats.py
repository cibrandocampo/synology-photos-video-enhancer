"""Tests for the DashboardStats DTO and its sub-DTOs."""
import pytest
from pydantic import ValidationError

from domain.models.dashboard_stats import (
    CANONICAL_STATUSES,
    CodecCount,
    DashboardStats,
    ErrorCount,
    LatestTranscoding,
    ResolutionCount,
)


def _full_stats(**overrides) -> DashboardStats:
    """Builds a fully populated DashboardStats with optional field overrides."""
    defaults = dict(
        total=10,
        status_counts={
            "pending": 1,
            "in_progress": 1,
            "completed": 5,
            "not_required": 1,
            "failed": 2,
        },
        success_rate=50.0,
        codec_distribution=[CodecCount(codec="h264", count=3)],
        resolution_distribution=[ResolutionCount(resolution="1280x720", count=3)],
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
        top_errors=[ErrorCount(error_summary="codec not supported", count=2)],
    )
    defaults.update(overrides)
    return DashboardStats(**defaults)


class TestDashboardStats:
    """Tests for the top-level DashboardStats DTO."""

    def test_canonical_statuses_match_enum(self):
        assert CANONICAL_STATUSES == (
            "pending",
            "in_progress",
            "completed",
            "not_required",
            "failed",
        )

    def test_construct_with_all_status_keys(self):
        stats = _full_stats()
        assert stats.total == 10
        assert stats.status_counts == {
            "pending": 1,
            "in_progress": 1,
            "completed": 5,
            "not_required": 1,
            "failed": 2,
        }
        assert stats.success_rate == 50.0

    def test_missing_status_keys_filled_with_zero(self):
        stats = _full_stats(
            status_counts={"completed": 3, "failed": 1},
            total=4,
            success_rate=75.0,
        )
        assert stats.status_counts == {
            "pending": 0,
            "in_progress": 0,
            "completed": 3,
            "not_required": 0,
            "failed": 1,
        }

    def test_empty_status_counts_filled_entirely(self):
        stats = _full_stats(status_counts={}, total=0, success_rate=0.0)
        assert stats.status_counts == {s: 0 for s in CANONICAL_STATUSES}

    def test_zero_total_zero_rate(self):
        stats = _full_stats(
            total=0,
            status_counts={},
            success_rate=0.0,
            codec_distribution=[],
            resolution_distribution=[],
            latest_transcodings=[],
            top_errors=[],
        )
        assert stats.total == 0
        assert stats.success_rate == 0.0

    def test_unknown_status_key_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            _full_stats(status_counts={"completed": 5, "unknown_status": 1})
        assert "unknown_status" in str(exc_info.value).lower()

    def test_negative_status_count_raises(self):
        with pytest.raises(ValidationError):
            _full_stats(status_counts={"completed": -1})

    def test_negative_total_raises(self):
        with pytest.raises(ValidationError):
            _full_stats(total=-1)

    def test_success_rate_above_100_raises(self):
        with pytest.raises(ValidationError):
            _full_stats(success_rate=150.0)

    def test_success_rate_below_zero_raises(self):
        with pytest.raises(ValidationError):
            _full_stats(success_rate=-1.0)

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError):
            DashboardStats(
                total=0,
                status_counts={},
                success_rate=0.0,
                codec_distribution=[],
                resolution_distribution=[],
                latest_transcodings=[],
                top_errors=[],
                unexpected_field="boom",
            )

    def test_frozen_total(self):
        stats = _full_stats()
        with pytest.raises(ValidationError):
            stats.total = 999

    def test_frozen_status_counts(self):
        stats = _full_stats()
        with pytest.raises(ValidationError):
            stats.status_counts = {}

    def test_latest_transcodings_max_length_enforced(self):
        too_many = [
            LatestTranscoding(
                original_video_path=f"/m/{i}.mp4",
                transcoded_video_path=f"/m/{i}.out.mp4",
                status="completed",
                transcoded_video_codec="h264",
                transcoded_video_resolution="1280x720",
                error_message=None,
            )
            for i in range(6)
        ]
        with pytest.raises(ValidationError):
            _full_stats(latest_transcodings=too_many)

    def test_top_errors_max_length_enforced(self):
        too_many = [ErrorCount(error_summary=f"err {i}", count=1) for i in range(6)]
        with pytest.raises(ValidationError):
            _full_stats(top_errors=too_many)


class TestCodecCount:
    """Tests for CodecCount sub-DTO."""

    def test_create(self):
        c = CodecCount(codec="h264", count=5)
        assert c.codec == "h264"
        assert c.count == 5

    def test_negative_count_raises(self):
        with pytest.raises(ValidationError):
            CodecCount(codec="h264", count=-1)

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError):
            CodecCount(codec="h264", count=1, percentage=10.0)

    def test_frozen(self):
        c = CodecCount(codec="h264", count=5)
        with pytest.raises(ValidationError):
            c.count = 6


class TestResolutionCount:
    """Tests for ResolutionCount sub-DTO."""

    def test_create(self):
        r = ResolutionCount(resolution="1920x1080", count=2)
        assert r.resolution == "1920x1080"
        assert r.count == 2

    def test_negative_count_raises(self):
        with pytest.raises(ValidationError):
            ResolutionCount(resolution="1920x1080", count=-1)

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError):
            ResolutionCount(resolution="1920x1080", count=2, percentage=10.0)

    def test_frozen(self):
        r = ResolutionCount(resolution="1920x1080", count=2)
        with pytest.raises(ValidationError):
            r.resolution = "1280x720"


class TestLatestTranscoding:
    """Tests for LatestTranscoding sub-DTO."""

    def test_create_with_error_message(self):
        lt = LatestTranscoding(
            original_video_path="/m/a.mp4",
            transcoded_video_path="/m/a.out.mp4",
            status="failed",
            transcoded_video_codec="h264",
            transcoded_video_resolution="1280x720",
            error_message="boom",
        )
        assert lt.error_message == "boom"

    def test_create_without_error_message(self):
        lt = LatestTranscoding(
            original_video_path="/m/a.mp4",
            transcoded_video_path="/m/a.out.mp4",
            status="completed",
            transcoded_video_codec="h264",
            transcoded_video_resolution="1280x720",
        )
        assert lt.error_message is None

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError):
            LatestTranscoding(
                original_video_path="/m/a.mp4",
                transcoded_video_path="/m/a.out.mp4",
                status="completed",
                transcoded_video_codec="h264",
                transcoded_video_resolution="1280x720",
                duration=10.0,
            )

    def test_frozen(self):
        lt = LatestTranscoding(
            original_video_path="/m/a.mp4",
            transcoded_video_path="/m/a.out.mp4",
            status="completed",
            transcoded_video_codec="h264",
            transcoded_video_resolution="1280x720",
        )
        with pytest.raises(ValidationError):
            lt.status = "failed"


class TestErrorCount:
    """Tests for ErrorCount sub-DTO."""

    def test_create(self):
        e = ErrorCount(error_summary="codec not supported", count=3)
        assert e.error_summary == "codec not supported"
        assert e.count == 3

    def test_negative_count_raises(self):
        with pytest.raises(ValidationError):
            ErrorCount(error_summary="x", count=-1)

    def test_extra_field_raises(self):
        with pytest.raises(ValidationError):
            ErrorCount(error_summary="x", count=1, last_seen="2024-01-01")

    def test_frozen(self):
        e = ErrorCount(error_summary="x", count=1)
        with pytest.raises(ValidationError):
            e.count = 2
