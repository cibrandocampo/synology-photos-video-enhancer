"""Integration tests for TranscodingStatsRepositorySQL against a temp SQLite DB."""
from unittest.mock import Mock

import pytest

from domain.models.app_config import DatabaseConfig
from domain.models.dashboard_stats import (
    CodecCount,
    ErrorCount,
    LatestTranscoding,
    ResolutionCount,
)
from domain.models.transcoding import TranscodingStatus
from domain.ports.transcoding_stats_repository import TranscodingStatsRepository
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import TranscodingModel
from infrastructure.db.transcoding_stats_repository_sql import (
    TranscodingStatsRepositorySQL,
)


@pytest.fixture
def db_connection(temp_db_path):
    """Initialised DatabaseConnection backed by an empty SQLite file."""
    connection = DatabaseConnection(DatabaseConfig(path=temp_db_path), Mock())
    connection.initialize()
    return connection


@pytest.fixture
def repository(db_connection):
    return TranscodingStatsRepositorySQL(db_connection)


def _seed(db_connection, rows):
    """Persists raw `TranscodingModel` rows via a fresh session."""
    session = db_connection.get_session()
    try:
        session.add_all(rows)
        session.commit()
    finally:
        session.close()


def _row(
    *,
    original,
    transcoded="/m/out.mp4",
    resolution="1280x720",
    codec="h264",
    status=TranscodingStatus.COMPLETED.value,
    error_message=None,
):
    return TranscodingModel(
        original_video_path=original,
        transcoded_video_path=transcoded,
        transcoded_video_resolution=resolution,
        transcoded_video_codec=codec,
        status=status,
        error_message=error_message,
    )


class TestTranscodingStatsRepositorySQL:
    """Behavioural tests for the SQL adapter."""

    def test_subclasses_port(self, repository):
        assert isinstance(repository, TranscodingStatsRepository)

    def test_empty_database_returns_zeroed_payload(self, repository):
        stats = repository.fetch_stats()

        assert stats.total == 0
        assert stats.status_counts == {status.value: 0 for status in TranscodingStatus}
        assert stats.success_rate == 0.0
        assert stats.codec_distribution == []
        assert stats.resolution_distribution == []
        assert stats.latest_transcodings == []
        assert stats.top_errors == []

    def test_mixed_statuses_aggregate_counts_and_success_rate(self, db_connection, repository):
        rows = []
        for index in range(3):
            rows.append(_row(original=f"/m/pending_{index}.mp4", status=TranscodingStatus.PENDING.value))
        for index in range(2):
            rows.append(_row(original=f"/m/inprog_{index}.mp4", status=TranscodingStatus.IN_PROGRESS.value))
        for index in range(5):
            rows.append(_row(original=f"/m/completed_{index}.mp4", status=TranscodingStatus.COMPLETED.value))
        rows.append(_row(original="/m/notreq.mp4", status=TranscodingStatus.NOT_REQUIRED.value))
        for index in range(4):
            rows.append(
                _row(
                    original=f"/m/failed_{index}.mp4",
                    status=TranscodingStatus.FAILED.value,
                    error_message="boom",
                )
            )
        _seed(db_connection, rows)

        stats = repository.fetch_stats()

        assert stats.total == 15
        assert stats.status_counts == {
            "pending": 3,
            "in_progress": 2,
            "completed": 5,
            "not_required": 1,
            "failed": 4,
        }
        assert stats.success_rate == 33.33

    def test_codec_distribution_excludes_non_completed_and_orders_desc(
        self, db_connection, repository
    ):
        rows = [
            _row(original="/m/c1.mp4", codec="h264"),
            _row(original="/m/c2.mp4", codec="h264"),
            _row(original="/m/c3.mp4", codec="h264"),
            _row(original="/m/c4.mp4", codec="hevc"),
            _row(original="/m/c5.mp4", codec="hevc"),
            _row(
                original="/m/c6.mp4",
                codec="h264",
                status=TranscodingStatus.FAILED.value,
                error_message="x",
            ),
        ]
        _seed(db_connection, rows)

        stats = repository.fetch_stats()

        assert stats.codec_distribution == [
            CodecCount(codec="h264", count=3),
            CodecCount(codec="hevc", count=2),
        ]

    def test_resolution_distribution_excludes_non_completed_and_orders_desc(
        self, db_connection, repository
    ):
        rows = [
            _row(original="/m/r1.mp4", resolution="1920x1080"),
            _row(original="/m/r2.mp4", resolution="1920x1080"),
            _row(original="/m/r3.mp4", resolution="1920x1080"),
            _row(original="/m/r4.mp4", resolution="1280x720"),
            _row(original="/m/r5.mp4", resolution="1280x720"),
            _row(
                original="/m/r6.mp4",
                resolution="1920x1080",
                status=TranscodingStatus.FAILED.value,
                error_message="x",
            ),
        ]
        _seed(db_connection, rows)

        stats = repository.fetch_stats()

        assert stats.resolution_distribution == [
            ResolutionCount(resolution="1920x1080", count=3),
            ResolutionCount(resolution="1280x720", count=2),
        ]

    def test_latest_transcodings_returns_first_five_alphabetically(
        self, db_connection, repository
    ):
        names = ["g.mp4", "a.mp4", "f.mp4", "b.mp4", "e.mp4", "c.mp4", "d.mp4"]
        rows = [_row(original=f"/m/{name}", transcoded=f"/m/{name}.out.mp4") for name in names]
        _seed(db_connection, rows)

        stats = repository.fetch_stats()

        expected_paths = ["/m/a.mp4", "/m/b.mp4", "/m/c.mp4", "/m/d.mp4", "/m/e.mp4"]
        assert [item.original_video_path for item in stats.latest_transcodings] == expected_paths
        assert all(isinstance(item, LatestTranscoding) for item in stats.latest_transcodings)

    def test_top_errors_groups_failed_rows_only_with_non_null_messages(
        self, db_connection, repository
    ):
        rows = []
        for index in range(3):
            rows.append(
                _row(
                    original=f"/m/codec_{index}.mp4",
                    status=TranscodingStatus.FAILED.value,
                    error_message="codec not supported",
                )
            )
        for index in range(2):
            rows.append(
                _row(
                    original=f"/m/perm_{index}.mp4",
                    status=TranscodingStatus.FAILED.value,
                    error_message="permission denied",
                )
            )
        rows.append(
            _row(
                original="/m/null_error.mp4",
                status=TranscodingStatus.FAILED.value,
                error_message=None,
            )
        )
        rows.append(
            _row(
                original="/m/completed_with_error.mp4",
                status=TranscodingStatus.COMPLETED.value,
                error_message="should not count",
            )
        )
        _seed(db_connection, rows)

        stats = repository.fetch_stats()

        assert stats.top_errors == [
            ErrorCount(error_summary="codec not supported", count=3),
            ErrorCount(error_summary="permission denied", count=2),
        ]

    def test_long_error_messages_are_truncated_to_100_chars(self, db_connection, repository):
        long_message = "x" * 200
        _seed(
            db_connection,
            [
                _row(
                    original="/m/long_error.mp4",
                    status=TranscodingStatus.FAILED.value,
                    error_message=long_message,
                )
            ],
        )

        stats = repository.fetch_stats()

        assert len(stats.top_errors) == 1
        assert len(stats.top_errors[0].error_summary) == 100
        assert stats.top_errors[0].error_summary == "x" * 100
