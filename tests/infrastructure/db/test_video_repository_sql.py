"""Integration tests for VideoRepositorySQL against a temp SQLite DB."""
from unittest.mock import Mock

import pytest

from domain.models.app_config import DatabaseConfig
from domain.models.transcoding import TranscodingStatus
from domain.ports.video_repository import VideoRepository
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import TranscodingModel
from infrastructure.db.video_repository_sql import VideoRepositorySQL


@pytest.fixture
def db_connection(temp_db_path):
    connection = DatabaseConnection(DatabaseConfig(path=temp_db_path), Mock())
    connection.initialize()
    return connection


@pytest.fixture
def repository(db_connection):
    return VideoRepositorySQL(db_connection)


def _seed(db_connection, rows):
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


def _get_row(db_connection, original_path):
    session = db_connection.get_session()
    try:
        return session.query(TranscodingModel).filter_by(
            original_video_path=original_path
        ).first()
    finally:
        session.close()


class TestVideoRepositorySubclassesPort:
    def test_subclasses_port(self, repository):
        assert isinstance(repository, VideoRepository)


class TestResetToPending:
    def test_completed_record_is_reset(self, db_connection, repository):
        _seed(db_connection, [_row(original="/m/v.mp4", status=TranscodingStatus.COMPLETED.value)])

        result = repository.reset_to_pending("/m/v.mp4")

        assert result is True
        row = _get_row(db_connection, "/m/v.mp4")
        assert row.status == TranscodingStatus.PENDING.value
        assert row.error_message is None

    def test_failed_record_is_reset_and_error_cleared(self, db_connection, repository):
        _seed(db_connection, [_row(
            original="/m/v.mp4",
            status=TranscodingStatus.FAILED.value,
            error_message="codec not supported",
        )])

        result = repository.reset_to_pending("/m/v.mp4")

        assert result is True
        row = _get_row(db_connection, "/m/v.mp4")
        assert row.status == TranscodingStatus.PENDING.value
        assert row.error_message is None

    def test_pending_record_is_not_changed(self, db_connection, repository):
        _seed(db_connection, [_row(original="/m/v.mp4", status=TranscodingStatus.PENDING.value)])

        result = repository.reset_to_pending("/m/v.mp4")

        assert result is False
        row = _get_row(db_connection, "/m/v.mp4")
        assert row.status == TranscodingStatus.PENDING.value

    def test_in_progress_record_is_not_changed(self, db_connection, repository):
        _seed(db_connection, [_row(original="/m/v.mp4", status=TranscodingStatus.IN_PROGRESS.value)])

        result = repository.reset_to_pending("/m/v.mp4")

        assert result is False
        row = _get_row(db_connection, "/m/v.mp4")
        assert row.status == TranscodingStatus.IN_PROGRESS.value

    def test_not_required_record_is_not_changed(self, db_connection, repository):
        _seed(db_connection, [_row(original="/m/v.mp4", status=TranscodingStatus.NOT_REQUIRED.value)])

        result = repository.reset_to_pending("/m/v.mp4")

        assert result is False
        row = _get_row(db_connection, "/m/v.mp4")
        assert row.status == TranscodingStatus.NOT_REQUIRED.value

    def test_non_existent_path_returns_false(self, repository):
        result = repository.reset_to_pending("/m/does_not_exist.mp4")

        assert result is False
