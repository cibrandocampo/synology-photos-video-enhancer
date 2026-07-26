"""Repairs transcoding records damaged before the metadata parser was fixed.

Until 2026-07, media paths containing spaces shifted every field of Synology's
metadata index, so orientation, framerate and channel decisions were taken from
misaligned values. Two distinct kinds of damage remain in the database:

- Files encoded with the wrong parameters. These need re-encoding, which the
  normal processing cycle does once the record is reset to `pending`.
- Records describing a file that was already replaced, because the stored
  resolution and codec were read before transcoding and never refreshed. The
  file is fine; only the row is stale, and a targeted update fixes it.

Telling the two apart matters: a re-encode costs minutes of CPU, an update costs
nothing. This script measures every completed row and classifies it, reporting
by default and writing only with --apply.

It requires the fixed pipeline to be deployed: re-encoding with the previous
code reproduces the original damage.

    python /app/scripts/repair_transcoding_metadata.py --verbose
    python /app/scripts/repair_transcoding_metadata.py --apply
"""
import argparse
import os
import sys
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

# Running `python /app/scripts/repair_transcoding_metadata.py` puts /app/scripts on
# sys.path, not /app, so the application packages would be invisible. Adding the
# parent keeps the documented invocation working from any working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from application.process_videos_use_case import (  # noqa: E402
    calculate_output_audio_channels,
    calculate_output_framerate,
    calculate_output_height,
)
from domain.constants.container import get_video_extensions  # noqa: E402
from domain.models.app_config import DatabaseConfig  # noqa: E402
from domain.models.video import Video  # noqa: E402
from domain.ports.logger import AppLogger  # noqa: E402
from domain.ports.video_metadata_reader import VideoMetadataReader  # noqa: E402
from domain.ports.video_repository import VideoRepository  # noqa: E402
from infrastructure.db.connection import DatabaseConnection  # noqa: E402
from infrastructure.db.models import TranscodingModel  # noqa: E402
from infrastructure.db.settings_repository_sql import SettingsRepositorySQL  # noqa: E402
from infrastructure.db.video_repository_sql import VideoRepositorySQL  # noqa: E402
from infrastructure.filesystem.local_filesystem import LocalFilesystem  # noqa: E402
from infrastructure.logger import Logger  # noqa: E402
from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader  # noqa: E402
from infrastructure.metadata.ffprobe_metadata_reader import FFprobeMetadataReader  # noqa: E402
from infrastructure.metadata.synoindex_metadata_reader import SynoIndexMetadataReader  # noqa: E402

DEFAULT_DB_PATH = "/app/data/transcodings.db"
COMPLETED = "completed"
# Frame rates are compared as floats derived from rationals; an exact equality test
# would report a file as damaged over the last bits of 30000/1001.
_RATE_TOLERANCE = 0.01


class Classification(str, Enum):
    """What a completed record turned out to need."""

    OK = "OK"
    NEEDS_REENCODE = "NEEDS_REENCODE"
    NEEDS_ROW_UPDATE = "NEEDS_ROW_UPDATE"
    MISSING = "MISSING"
    UNREADABLE = "UNREADABLE"
    SOURCE_UNKNOWN = "SOURCE_UNKNOWN"


@dataclass
class Finding:
    """One record, its measurements and what should happen to it."""

    original_path: str
    stored_resolution: str
    stored_codec: str
    classification: Classification
    measured_resolution: str = "-"
    measured_codec: str = "-"
    expected_height: str = "-"
    reason: str = ""
    applied: bool = False
    # Kept so applying a row update does not have to probe the file a second time.
    measured: Optional[Video] = None


@dataclass
class Record:
    """The columns of a transcoding row this script reads."""

    original_path: str
    transcoded_path: str
    resolution: str
    codec: str


class RepairPlanner:
    """Classifies completed records, and applies the repairs when asked to."""

    def __init__(
        self,
        repository: VideoRepository,
        source_reader: VideoMetadataReader,
        output_reader: VideoMetadataReader,
        video_config,
        audio_config,
    ):
        self.repository = repository
        self.source_reader = source_reader
        self.output_reader = output_reader
        self.video_config = video_config
        self.audio_config = audio_config

    def _mismatches(self, source: Video, produced: Video) -> List[str]:
        """
        Lists the ways the produced file differs from what the pipeline would make.

        The defect being repaired misread orientation, framerate and channel count
        alike, so checking geometry alone would leave a file at the wrong framerate
        looking healthy. Every axis the configuration controls is compared here.

        Args:
            source: Metadata of the source video
            produced: Metadata of the file on disk

        Returns:
            Human-readable descriptions of each difference; empty when the file is
            what the pipeline would produce today.
        """
        differences = []
        skipped = []

        expected_height = calculate_output_height(source.video_track, self.video_config)
        if produced.video_track.height != expected_height:
            differences.append(
                f"height {produced.video_track.height} != {expected_height}"
            )

        if source.video_track.is_variable_framerate:
            # A variable cadence is passed through, so there is no single rate the
            # output should carry. ffprobe reports the mean over the file, which
            # describes the content rather than the format and shifts between
            # measurements — comparing against it would queue the file on every run.
            skipped.append("framerate not compared (variable source)")
        else:
            # The exact rational now reaches FFmpeg, so the produced file carries the
            # target rate itself rather than a truncated version of it. A constant
            # source with no standard rate at or below it is passed through, and the
            # rate it should then carry is its own.
            expected_framerate = calculate_output_framerate(source.video_track)
            expected_rate = (
                expected_framerate.to_float()
                if expected_framerate is not None
                else source.video_track.framerate
            )
            if expected_rate > 0 and (
                abs(produced.video_track.framerate - expected_rate) > _RATE_TOLERANCE
            ):
                differences.append(
                    f"framerate {produced.video_track.framerate} != {expected_rate}"
                )

        expected_channels = calculate_output_audio_channels(
            source.audio_track.channels, self.audio_config
        )
        if produced.audio_track.channels != expected_channels:
            differences.append(
                f"channels {produced.audio_track.channels} != {expected_channels}"
            )

        # Naming the unjudged axis only matters once the record is being queued: the
        # operator reading the reason has to know one axis was not part of the verdict.
        if differences:
            differences.extend(skipped)

        return differences

    def classify(self, record: Record) -> Finding:
        """
        Measures one record and decides what it needs.

        Args:
            record: Stored columns of a completed transcoding

        Returns:
            Finding describing the record, unapplied.
        """
        finding = Finding(
            original_path=record.original_path,
            stored_resolution=record.resolution,
            stored_codec=record.codec,
            classification=Classification.OK,
        )

        produced = self.output_reader.read(record.transcoded_path)
        if produced is None:
            # Absent and unreadable are reported apart because they need different
            # answers: one is a lost file, the other is usually a permission the
            # operator can grant and re-run.
            finding.classification = (
                Classification.MISSING
                if not os.path.exists(record.transcoded_path)
                else Classification.UNREADABLE
            )
            return finding

        finding.measured = produced
        finding.measured_resolution = produced.video_track.resolution
        finding.measured_codec = produced.video_track.codec_name

        source = self.source_reader.read(record.original_path)
        if source is None:
            # Without the source there is no way to know what the output should
            # have been, and guessing is what caused the damage in the first place.
            finding.classification = Classification.SOURCE_UNKNOWN
            return finding

        finding.expected_height = str(
            calculate_output_height(source.video_track, self.video_config)
        )

        differences = self._mismatches(source, produced)
        if differences:
            # The file itself is wrong; only re-encoding fixes it.
            finding.classification = Classification.NEEDS_REENCODE
            finding.reason = ", ".join(differences)
        elif (
            record.resolution != finding.measured_resolution
            or record.codec != finding.measured_codec
        ):
            # The file is right in every respect the configuration controls, so the
            # stored strings are simply describing the version it replaced.
            finding.classification = Classification.NEEDS_ROW_UPDATE
            finding.reason = "stored values describe a replaced file"

        return finding

    def apply(self, finding: Finding) -> bool:
        """
        Performs the repair a finding calls for.

        Args:
            finding: Classified finding

        Returns:
            True if the database was changed.
        """
        if finding.classification is Classification.NEEDS_REENCODE:
            return self.repository.reset_to_pending(finding.original_path)

        if finding.classification is Classification.NEEDS_ROW_UPDATE and finding.measured:
            track = finding.measured.video_track
            return self.repository.update_transcoded_metadata(
                finding.original_path, track.width, track.height, track.codec_name
            )

        return False


def fetch_completed_records(
    db_connection: DatabaseConnection, limit: Optional[int] = None
) -> List[Record]:
    """Reads the completed rows, in a stable order so --limit is reproducible."""
    session = db_connection.get_session()
    try:
        query = (
            session.query(
                TranscodingModel.original_video_path,
                TranscodingModel.transcoded_video_path,
                TranscodingModel.transcoded_video_resolution,
                TranscodingModel.transcoded_video_codec,
            )
            .filter(TranscodingModel.status == COMPLETED)
            .order_by(TranscodingModel.original_video_path)
        )
        if limit is not None:
            query = query.limit(limit)
        return [Record(*row) for row in query.all()]
    finally:
        session.close()


def build_readers(logger: AppLogger):
    """Builds the same reader chain the application uses.

    The order matters twice over here. It has to match `main.py` or the script judges
    files by a different standard than the one that produced them; and the framerate
    axis can only be skipped for variable-rate sources if the reader that detects
    variability — ffprobe — is the one consulted first.
    """
    filesystem = LocalFilesystem(get_video_extensions())
    ffprobe_reader = FFprobeMetadataReader(logger)
    source_reader = ChainedMetadataReader(
        [ffprobe_reader, SynoIndexMetadataReader(filesystem, logger)], logger
    )
    return source_reader, ffprobe_reader


def report(findings: List[Finding], verbose: bool, applied: bool) -> None:
    """Prints the per-record detail and the summary."""
    if verbose:
        interesting = [f for f in findings if f.classification is not Classification.OK]
        if interesting:
            print()
            print(f"{'stored':<12} {'measured':<12} {'action':<17} why / path")
            print("-" * 110)
            for f in interesting:
                print(
                    f"{f.stored_resolution:<12} {f.measured_resolution:<12} "
                    f"{f.classification.value:<17} {f.reason or '-'}"
                )
                print(f"{'':<42} {f.original_path}")

    counts = {c: 0 for c in Classification}
    for f in findings:
        counts[f.classification] += 1

    print()
    print(f"Examined {len(findings)} completed records")
    for classification in Classification:
        if counts[classification]:
            print(f"  {classification.value:<17} {counts[classification]}")

    queued = counts[Classification.NEEDS_REENCODE]
    if applied:
        changed = sum(1 for f in findings if f.applied)
        print()
        print(f"Applied: {changed} records changed")
        if queued:
            print(
                f"  {queued} queued for re-encoding; the next processing cycle "
                f"will pick them up"
            )
    elif queued or counts[Classification.NEEDS_ROW_UPDATE]:
        print()
        print("Dry run: nothing was written. Re-run with --apply to repair.")
        if queued:
            print(f"  {queued} records would be queued for re-encoding")


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """Parses the command line."""
    parser = argparse.ArgumentParser(
        description="Repair transcoding records damaged by the metadata parsing defect."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the repairs. Without it the script only reports.",
    )
    parser.add_argument(
        "--db-path",
        default=os.getenv("REPAIR_DB_PATH", DEFAULT_DB_PATH),
        help=f"SQLite database to repair (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--limit", type=int, default=None, help="Process only the first N records."
    )
    parser.add_argument(
        "--verbose", action="store_true", help="List every record needing attention."
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace, logger: AppLogger) -> int:
    """
    Runs the repair.

    Args:
        args: Parsed command line
        logger: Application logger

    Returns:
        Process exit code.
    """
    if not os.path.exists(args.db_path):
        print(f"Database not found: {args.db_path}", file=sys.stderr)
        return 1

    db_connection = DatabaseConnection(DatabaseConfig(path=args.db_path), logger)
    try:
        repository = VideoRepositorySQL(db_connection)
        settings = SettingsRepositorySQL(db_connection).load()
        video_config = settings.to_video_config()
        audio_config = settings.to_audio_config()
        source_reader, output_reader = build_readers(logger)

        planner = RepairPlanner(
            repository, source_reader, output_reader, video_config, audio_config
        )
        records = fetch_completed_records(db_connection, args.limit)

        print(f"Repairing {args.db_path}")
        print(f"Output target: {video_config.resolution.value} "
              f"({video_config.width}x{video_config.height})")
        print("Mode: APPLY" if args.apply else "Mode: dry run (no writes)")

        findings = []
        for record in records:
            finding = planner.classify(record)
            if args.apply:
                finding.applied = planner.apply(finding)
            findings.append(finding)

        report(findings, args.verbose, args.apply)
        return 0
    finally:
        db_connection.dispose()


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point."""
    args = parse_args(argv)
    return run(args, Logger.get_logger("repair"))


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
