"""SQL adapter for the dashboard stats port (read-only)."""
from sqlalchemy import desc, func, text

from domain.models.dashboard_stats import (
    CodecCount,
    DashboardStats,
    ErrorCount,
    LatestTranscoding,
    ResolutionCount,
)
from domain.models.transcoding import TranscodingStatus
from domain.ports.transcoding_stats_repository import TranscodingStatsRepository
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import TranscodingModel


_COMPLETED = TranscodingStatus.COMPLETED.value
_FAILED = TranscodingStatus.FAILED.value
_ERROR_SUMMARY_LENGTH = 100


class TranscodingStatsRepositorySQL(TranscodingStatsRepository):
    """Aggregates the `transcodings` table into a `DashboardStats` payload."""

    def __init__(self, db_connection: DatabaseConnection) -> None:
        self._db_connection = db_connection

    def fetch_stats(self) -> DashboardStats:
        # One short-lived read-only session for the whole aggregation;
        # SQLite plus the queries below are cheap enough that splitting
        # into per-query sessions would add overhead without benefit.
        session = self._db_connection.get_session()
        try:
            total = session.query(func.count(TranscodingModel.original_video_path)).scalar() or 0

            status_rows = (
                session.query(TranscodingModel.status, func.count(TranscodingModel.original_video_path))
                .group_by(TranscodingModel.status)
                .all()
            )
            status_counts = {status: count for status, count in status_rows}

            completed = status_counts.get(_COMPLETED, 0)
            failed = status_counts.get(_FAILED, 0)
            finished = completed + failed
            success_rate = round(completed / finished * 100, 2) if finished else 0.0

            codec_rows = (
                session.query(
                    TranscodingModel.transcoded_video_codec,
                    func.count(TranscodingModel.original_video_path).label("count"),
                )
                .filter(TranscodingModel.status == _COMPLETED)
                .group_by(TranscodingModel.transcoded_video_codec)
                .order_by(desc("count"))
                .all()
            )
            codec_distribution = [CodecCount(codec=codec, count=count) for codec, count in codec_rows]

            resolution_rows = (
                session.query(
                    TranscodingModel.transcoded_video_resolution,
                    func.count(TranscodingModel.original_video_path).label("count"),
                )
                .filter(TranscodingModel.status == _COMPLETED)
                .group_by(TranscodingModel.transcoded_video_resolution)
                .order_by(desc("count"))
                .limit(10)
                .all()
            )
            resolution_distribution = [
                ResolutionCount(resolution=resolution, count=count)
                for resolution, count in resolution_rows
            ]

            latest_rows = (
                session.query(
                    TranscodingModel.original_video_path,
                    TranscodingModel.transcoded_video_path,
                    TranscodingModel.status,
                    TranscodingModel.transcoded_video_codec,
                    TranscodingModel.transcoded_video_resolution,
                    TranscodingModel.error_message,
                )
                .filter(TranscodingModel.status == _COMPLETED)
                .order_by(TranscodingModel.original_video_path)
                .limit(5)
                .all()
            )
            latest_transcodings = [
                LatestTranscoding(
                    original_video_path=row[0],
                    transcoded_video_path=row[1],
                    status=row[2],
                    transcoded_video_codec=row[3],
                    transcoded_video_resolution=row[4],
                    error_message=row[5],
                )
                for row in latest_rows
            ]

            error_summary = func.substr(
                TranscodingModel.error_message, 1, _ERROR_SUMMARY_LENGTH
            ).label("error_summary")
            error_rows = (
                session.query(
                    error_summary,
                    func.count(TranscodingModel.original_video_path).label("count"),
                )
                .filter(TranscodingModel.status == _FAILED)
                .filter(TranscodingModel.error_message.isnot(None))
                .group_by(error_summary)
                .order_by(desc("count"))
                .limit(5)
                .all()
            )
            top_errors = [
                ErrorCount(error_summary=summary, count=count) for summary, count in error_rows
            ]

            return DashboardStats(
                total=total,
                status_counts=status_counts,
                success_rate=success_rate,
                codec_distribution=codec_distribution,
                resolution_distribution=resolution_distribution,
                latest_transcodings=latest_transcodings,
                top_errors=top_errors,
            )
        finally:
            session.close()

    def fetch_latest_transcodings(
        self, page: int, page_size: int = 5
    ) -> tuple[list[LatestTranscoding], int]:
        session = self._db_connection.get_session()
        try:
            total = (
                session.query(func.count(TranscodingModel.original_video_path))
                .filter(TranscodingModel.status != TranscodingStatus.NOT_REQUIRED.value)
                .scalar()
                or 0
            )
            rows = (
                session.query(
                    TranscodingModel.original_video_path,
                    TranscodingModel.transcoded_video_path,
                    TranscodingModel.status,
                    TranscodingModel.transcoded_video_codec,
                    TranscodingModel.transcoded_video_resolution,
                )
                .filter(TranscodingModel.status != TranscodingStatus.NOT_REQUIRED.value)
                .order_by(text("rowid DESC"))
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            transcodings = [
                LatestTranscoding(
                    original_video_path=row[0],
                    transcoded_video_path=row[1],
                    status=row[2],
                    transcoded_video_codec=row[3],
                    transcoded_video_resolution=row[4],
                )
                for row in rows
            ]
            return transcodings, total
        finally:
            session.close()

    def search_by_path(self, path: str) -> list[LatestTranscoding]:
        if not path or len(path) < 3:
            return []
        session = self._db_connection.get_session()
        try:
            rows = (
                session.query(
                    TranscodingModel.original_video_path,
                    TranscodingModel.transcoded_video_path,
                    TranscodingModel.status,
                    TranscodingModel.transcoded_video_codec,
                    TranscodingModel.transcoded_video_resolution,
                    TranscodingModel.error_message,
                )
                .filter(TranscodingModel.original_video_path.ilike(f"%{path}%"))
                .order_by(TranscodingModel.original_video_path)
                .limit(20)
                .all()
            )
            return [
                LatestTranscoding(
                    original_video_path=row[0],
                    transcoded_video_path=row[1],
                    status=row[2],
                    transcoded_video_codec=row[3],
                    transcoded_video_resolution=row[4],
                    error_message=row[5],
                )
                for row in rows
            ]
        finally:
            session.close()
