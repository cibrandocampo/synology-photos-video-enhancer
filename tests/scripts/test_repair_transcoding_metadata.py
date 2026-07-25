"""Integration tests for the repair script against a temp SQLite database.

The classifier decides between a free database update and a costly re-encode, so
the tests are built around the two production cases it must tell apart: a file
that was encoded wrongly, and a row that merely describes a file already replaced.
No real ffprobe runs and no media is read.
"""
import os
import sys
from typing import Dict, Optional
from unittest.mock import Mock

import pytest

from domain.models.app_config import AudioConfig, DatabaseConfig, VideoConfig
from domain.constants.resolution import VideoResolution
from domain.constants.audio import AudioCodec
from domain.constants.video import VideoCodec, VideoProfile
from domain.models.transcoding import TranscodingStatus
from domain.models.video import AudioTrack, Container, Video, VideoTrack
from domain.ports.video_metadata_reader import VideoMetadataReader
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import TranscodingModel
from infrastructure.db.video_repository_sql import VideoRepositorySQL
from scripts.repair_transcoding_metadata import (
    Classification,
    Record,
    RepairPlanner,
    fetch_completed_records,
    main,
    run,
    parse_args,
)

SOURCE = "/media/user/album/IMG_0001.MOV"
OUTPUT = "/media/user/album/@eaDir/IMG_0001.MOV/SYNOPHOTO_FILM_H.mp4"


class _StubReader(VideoMetadataReader):
    """Returns canned metadata per path; anything unknown reads as unavailable."""

    def __init__(self, by_path: Optional[Dict[str, Optional[Video]]] = None):
        self._by_path = by_path or {}
        self.calls = 0

    def read(self, video_path: str) -> Optional[Video]:
        self.calls += 1
        return self._by_path.get(video_path)


def video(path: str, width: int, height: int, codec: str = "h264",
          framerate: int = 25, channels: int = 2) -> Video:
    return Video(
        path=path,
        video_track=VideoTrack(
            width=width, height=height, codec_name=codec, framerate=framerate
        ),
        audio_track=AudioTrack(codec="aac", channels=channels),
        container=Container(format="mp4"),
    )


@pytest.fixture
def video_config():
    """720p, matching production."""
    return VideoConfig(
        codec=VideoCodec.H264,
        bitrate=2000,
        resolution=VideoResolution.P720,
        width=1280,
        height=720,
        profile=VideoProfile.HIGH,
    )


@pytest.fixture
def audio_config():
    """Stereo AAC, matching production."""
    return AudioConfig(codec=AudioCodec.AAC, bitrate=128, channels=2, profile=None)


@pytest.fixture
def db_connection(temp_db_path):
    connection = DatabaseConnection(DatabaseConfig(path=temp_db_path), Mock())
    connection.initialize()
    yield connection
    # Release the pool; leaving it to interpreter shutdown surfaces as a
    # ResourceWarning once coverage changes collection timing.
    connection.dispose()


@pytest.fixture
def repository(db_connection):
    return VideoRepositorySQL(db_connection)


def seed(db_connection, **overrides):
    """Inserts one transcoding row, completed by default."""
    row = TranscodingModel(
        original_video_path=overrides.get("original", SOURCE),
        transcoded_video_path=overrides.get("transcoded", OUTPUT),
        transcoded_video_resolution=overrides.get("resolution", "1280x720"),
        transcoded_video_codec=overrides.get("codec", "h264"),
        status=overrides.get("status", TranscodingStatus.COMPLETED.value),
        error_message=overrides.get("error_message", None),
    )
    session = db_connection.get_session()
    try:
        session.add(row)
        session.commit()
    finally:
        session.close()


def read_row(db_connection, original=SOURCE):
    session = db_connection.get_session()
    try:
        row = session.get(TranscodingModel, original)
        return {
            "resolution": row.transcoded_video_resolution,
            "codec": row.transcoded_video_codec,
            "status": row.status,
            "error_message": row.error_message,
        }
    finally:
        session.close()


def planner_for(repository, video_config, audio_config, source=None, output=None):
    return RepairPlanner(
        repository,
        _StubReader(source or {}),
        _StubReader(output or {}),
        video_config,
        audio_config,
    )


def record(resolution="1280x720", codec="h264"):
    return Record(SOURCE, OUTPUT, resolution, codec)


class TestClassification:
    """The two damaged states must be told apart; they cost very different things."""

    def test_correct_record_is_ok(self, repository, video_config, audio_config):
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080)},
            output={OUTPUT: video(OUTPUT, 1280, 720)},
        )

        assert planner.classify(record()).classification is Classification.OK

    def test_production_44100x2_case_needs_reencode(self, repository, video_config, audio_config):
        """Portrait source stored as 44100x2, encoded at 404x720; expected 1280."""
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1080, 1920)},
            output={OUTPUT: video(OUTPUT, 404, 720)},
        )

        finding = planner.classify(record(resolution="44100x2"))

        assert finding.classification is Classification.NEEDS_REENCODE
        assert finding.expected_height == "1280"
        assert finding.measured_resolution == "404x720"

    def test_production_upscale_case_needs_reencode(self, repository, video_config, audio_config):
        """1080p source read as 2x1280 and upscaled to 2274x1280; expected 720."""
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080)},
            output={OUTPUT: video(OUTPUT, 2274, 1280)},
        )

        finding = planner.classify(record(resolution="2x1280"))

        assert finding.classification is Classification.NEEDS_REENCODE
        assert finding.expected_height == "720"

    def test_stale_row_needs_update_not_reencode(self, repository, video_config, audio_config):
        """The file is right; only the stored string describes the replaced version."""
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1080, 1920)},
            output={OUTPUT: video(OUTPUT, 960, 1280)},
        )

        finding = planner.classify(record(resolution="720x960"))

        assert finding.classification is Classification.NEEDS_ROW_UPDATE

    def test_stale_codec_needs_update(self, repository, video_config, audio_config):
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080)},
            output={OUTPUT: video(OUTPUT, 1280, 720, codec="hevc")},
        )

        finding = planner.classify(record(codec="h264"))

        assert finding.classification is Classification.NEEDS_ROW_UPDATE
        assert finding.measured_codec == "hevc"

    def test_source_smaller_than_target_is_ok(self, repository, video_config, audio_config):
        """The upscale guard applies here too, or every small clip looks damaged."""
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 480, 854)},
            output={OUTPUT: video(OUTPUT, 480, 854)},
        )

        finding = planner.classify(record(resolution="480x854"))

        assert finding.expected_height == "854"
        assert finding.classification is Classification.OK

    def test_correct_geometry_but_wrong_framerate_needs_reencode(
        self, repository, video_config, audio_config
    ):
        """24 of the 41 damaged production files look like this.

        A landscape source read as `44100x2` was still given height 720 by accident,
        so the geometry matches — but the shifted bitrate field became the framerate
        and the file came out at 30 fps instead of 25. Judging on height alone marks
        these as merely stale, corrects the stored string, and leaves the file wrong
        while making it look healthy.
        """
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080, framerate=25, channels=1)},
            output={OUTPUT: video(OUTPUT, 1280, 720, framerate=30, channels=1)},
        )

        finding = planner.classify(record(resolution="44100x2"))

        assert finding.classification is Classification.NEEDS_REENCODE
        assert "framerate" in finding.reason

    def test_correct_geometry_but_downmixed_audio_needs_reencode(
        self, repository, video_config, audio_config
    ):
        """The stereo source that came out mono; geometry and framerate both match."""
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080, framerate=30, channels=2)},
            output={OUTPUT: video(OUTPUT, 1280, 720, framerate=30, channels=1)},
        )

        finding = planner.classify(record(resolution="44100x2"))

        assert finding.classification is Classification.NEEDS_REENCODE
        assert "channels" in finding.reason

    def test_ntsc_framerate_is_not_reported_as_damage(
        self, repository, video_config, audio_config
    ):
        """The command builders pass `-r int(fps)`, so a 29.97 target yields 29.

        Comparing against the exact rate would classify every NTSC output as damaged
        and queue a mass re-encode of files that are exactly what the pipeline makes.
        """
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080, framerate=29, channels=2)},
            output={OUTPUT: video(OUTPUT, 1280, 720, framerate=29, channels=2)},
        )

        finding = planner.classify(record(resolution="1280x720"))

        assert finding.classification is Classification.OK

    def test_source_with_fewer_channels_than_configured_is_not_damage(
        self, repository, video_config, audio_config
    ):
        """A mono source produces mono output by design, not by defect."""
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080, framerate=25, channels=1)},
            output={OUTPUT: video(OUTPUT, 1280, 720, framerate=25, channels=1)},
        )

        assert planner.classify(record()).classification is Classification.OK

    def test_silent_source_is_not_damage(
        self, repository, video_config, audio_config
    ):
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1920, 1080, framerate=25, channels=0)},
            output={OUTPUT: video(OUTPUT, 1280, 720, framerate=25, channels=0)},
        )

        assert planner.classify(record()).classification is Classification.OK

    def test_reason_names_every_axis_that_differs(
        self, repository, video_config, audio_config
    ):
        """The operator has to be able to tell why a file is being re-encoded."""
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1080, 1920, framerate=25, channels=2)},
            output={OUTPUT: video(OUTPUT, 404, 720, framerate=30, channels=1)},
        )

        reason = planner.classify(record(resolution="44100x2")).reason

        assert "height" in reason
        assert "framerate" in reason
        assert "channels" in reason

    def test_missing_output_file(self, repository, video_config, audio_config):
        planner = planner_for(
            repository, video_config, audio_config, source={SOURCE: video(SOURCE, 1920, 1080)}
        )

        finding = planner.classify(Record(SOURCE, "/does/not/exist.mp4", "1280x720", "h264"))

        assert finding.classification is Classification.MISSING

    def test_unreadable_output_file(self, repository, video_config, audio_config, tmp_path):
        """The file is there but cannot be probed — a permission problem, not a loss."""
        existing = tmp_path / "SYNOPHOTO_FILM_H.mp4"
        existing.write_bytes(b"")
        planner = planner_for(
            repository, video_config, audio_config, source={SOURCE: video(SOURCE, 1920, 1080)}
        )

        finding = planner.classify(Record(SOURCE, str(existing), "1280x720", "h264"))

        assert finding.classification is Classification.UNREADABLE

    def test_unreadable_source(self, repository, video_config, audio_config):
        planner = planner_for(
            repository, video_config, audio_config, output={OUTPUT: video(OUTPUT, 1280, 720)}
        )

        assert planner.classify(record()).classification is Classification.SOURCE_UNKNOWN

    def test_source_is_not_probed_when_output_is_unavailable(
        self, repository, video_config
    ):
        """No point measuring a source when there is no output to compare it with."""
        source_reader = _StubReader({SOURCE: video(SOURCE, 1920, 1080)})
        planner = RepairPlanner(
            repository, source_reader, _StubReader({}), video_config, audio_config
        )

        planner.classify(record())

        assert source_reader.calls == 0


class TestApply:
    """Only the two repairable classifications may write."""

    def test_reencode_resets_to_pending(self, repository, db_connection, video_config, audio_config):
        seed(db_connection, resolution="44100x2", error_message="stale error")
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1080, 1920)},
            output={OUTPUT: video(OUTPUT, 404, 720)},
        )

        finding = planner.classify(record(resolution="44100x2"))
        assert planner.apply(finding) is True

        row = read_row(db_connection)
        assert row["status"] == TranscodingStatus.PENDING.value
        assert row["error_message"] is None

    def test_reencode_leaves_the_stored_resolution_for_the_cycle_to_fix(
        self, repository, db_connection, video_config, audio_config
    ):
        """The pipeline measures the new file; writing a value here would be a guess."""
        seed(db_connection, resolution="44100x2")
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1080, 1920)},
            output={OUTPUT: video(OUTPUT, 404, 720)},
        )

        planner.apply(planner.classify(record(resolution="44100x2")))

        assert read_row(db_connection)["resolution"] == "44100x2"

    def test_row_update_writes_measured_values(
        self, repository, db_connection, video_config, audio_config
    ):
        seed(db_connection, resolution="720x960")
        planner = planner_for(
            repository,
            video_config,
            audio_config,
            source={SOURCE: video(SOURCE, 1080, 1920)},
            output={OUTPUT: video(OUTPUT, 960, 1280, codec="hevc")},
        )

        finding = planner.classify(record(resolution="720x960"))
        assert planner.apply(finding) is True

        row = read_row(db_connection)
        assert row["resolution"] == "960x1280"
        assert row["codec"] == "hevc"
        assert row["status"] == TranscodingStatus.COMPLETED.value

    def test_row_update_does_not_probe_the_file_again(
        self, repository, db_connection, video_config, audio_config
    ):
        """96 needless subprocesses if the measurement is not carried through."""
        seed(db_connection, resolution="720x960")
        output_reader = _StubReader({OUTPUT: video(OUTPUT, 960, 1280)})
        planner = RepairPlanner(
            repository,
            _StubReader({SOURCE: video(SOURCE, 1080, 1920)}),
            output_reader,
            video_config,
            audio_config,
        )

        planner.apply(planner.classify(record(resolution="720x960")))

        assert output_reader.calls == 1

    @pytest.mark.parametrize(
        "classification",
        [Classification.OK, Classification.MISSING, Classification.UNREADABLE,
         Classification.SOURCE_UNKNOWN],
    )
    def test_non_repairable_classifications_never_write(
        self, repository, db_connection, video_config, audio_config, classification
    ):
        seed(db_connection)
        planner = planner_for(repository, video_config, audio_config)
        finding = planner.classify(record())
        finding.classification = classification

        assert planner.apply(finding) is False
        assert read_row(db_connection)["status"] == TranscodingStatus.COMPLETED.value


class TestRecordSelection:
    """Only completed rows are eligible, and --limit must be reproducible."""

    def test_only_completed_rows_are_fetched(self, db_connection):
        seed(db_connection, original="/m/a.mp4", status=TranscodingStatus.COMPLETED.value)
        seed(db_connection, original="/m/b.mp4", status=TranscodingStatus.PENDING.value)
        seed(db_connection, original="/m/c.mp4", status=TranscodingStatus.FAILED.value)
        seed(db_connection, original="/m/d.mp4", status=TranscodingStatus.NOT_REQUIRED.value)

        records = fetch_completed_records(db_connection)

        assert [r.original_path for r in records] == ["/m/a.mp4"]

    def test_limit_caps_and_is_ordered(self, db_connection):
        for name in ("c", "a", "b"):
            seed(db_connection, original=f"/m/{name}.mp4")

        records = fetch_completed_records(db_connection, limit=2)

        assert [r.original_path for r in records] == ["/m/a.mp4", "/m/b.mp4"]


class TestDryRun:
    """The default must be incapable of changing anything."""

    def _stub_readers(self, monkeypatch):
        import scripts.repair_transcoding_metadata as module

        monkeypatch.setattr(
            module,
            "build_readers",
            lambda logger: (
                _StubReader({SOURCE: video(SOURCE, 1080, 1920)}),
                _StubReader({OUTPUT: video(OUTPUT, 404, 720)}),
            ),
        )

    def test_dry_run_leaves_every_row_untouched(
        self, db_connection, temp_db_path, monkeypatch, capsys
    ):
        seed(db_connection, resolution="44100x2", error_message="original error")
        before = read_row(db_connection)
        self._stub_readers(monkeypatch)

        assert run(parse_args(["--db-path", temp_db_path]), Mock()) == 0

        assert read_row(db_connection) == before
        assert "dry run" in capsys.readouterr().out.lower()

    def test_dry_run_reports_the_size_of_the_queue_it_would_create(
        self, db_connection, temp_db_path, monkeypatch, capsys
    ):
        seed(db_connection, resolution="44100x2")
        self._stub_readers(monkeypatch)

        run(parse_args(["--db-path", temp_db_path]), Mock())

        out = capsys.readouterr().out
        assert "NEEDS_REENCODE" in out
        assert "1 records would be queued" in out

    def test_apply_changes_rows(self, db_connection, temp_db_path, monkeypatch, capsys):
        seed(db_connection, resolution="44100x2")
        self._stub_readers(monkeypatch)

        assert run(parse_args(["--db-path", temp_db_path, "--apply"]), Mock()) == 0

        assert read_row(db_connection)["status"] == TranscodingStatus.PENDING.value
        assert "1 records changed" in capsys.readouterr().out

    def test_verbose_lists_the_affected_records(
        self, db_connection, temp_db_path, monkeypatch, capsys
    ):
        seed(db_connection, resolution="44100x2")
        self._stub_readers(monkeypatch)

        run(parse_args(["--db-path", temp_db_path, "--verbose"]), Mock())

        assert SOURCE in capsys.readouterr().out

    def _stale_row_readers(self, monkeypatch):
        """Output is correct; only the stored string is out of date."""
        import scripts.repair_transcoding_metadata as module

        monkeypatch.setattr(
            module,
            "build_readers",
            lambda logger: (
                _StubReader({SOURCE: video(SOURCE, 1080, 1920)}),
                _StubReader({OUTPUT: video(OUTPUT, 960, 1280)}),
            ),
        )

    def test_dry_run_with_only_stale_rows_queues_nothing(
        self, db_connection, temp_db_path, monkeypatch, capsys
    ):
        """The 96-row case: repairable, but no re-encode queue is created."""
        seed(db_connection, resolution="720x960")
        self._stale_row_readers(monkeypatch)

        run(parse_args(["--db-path", temp_db_path]), Mock())

        out = capsys.readouterr().out
        assert "NEEDS_ROW_UPDATE" in out
        assert "Dry run" in out
        assert "would be queued" not in out

    def test_apply_with_only_stale_rows_reports_no_queue(
        self, db_connection, temp_db_path, monkeypatch, capsys
    ):
        seed(db_connection, resolution="720x960")
        self._stale_row_readers(monkeypatch)

        run(parse_args(["--db-path", temp_db_path, "--apply"]), Mock())

        out = capsys.readouterr().out
        assert "1 records changed" in out
        assert "queued for re-encoding" not in out
        assert read_row(db_connection)["resolution"] == "960x1280"

    def test_verbose_prints_no_table_when_everything_is_fine(
        self, db_connection, temp_db_path, monkeypatch, capsys
    ):
        """A clean database must not print an empty detail table."""
        seed(db_connection)
        import scripts.repair_transcoding_metadata as module

        monkeypatch.setattr(
            module,
            "build_readers",
            lambda logger: (
                _StubReader({SOURCE: video(SOURCE, 1920, 1080)}),
                _StubReader({OUTPUT: video(OUTPUT, 1280, 720)}),
            ),
        )

        run(parse_args(["--db-path", temp_db_path, "--verbose"]), Mock())

        out = capsys.readouterr().out
        assert "action" not in out
        assert "OK" in out

    def test_missing_database_is_reported_and_exits_non_zero(self, capsys):
        assert run(parse_args(["--db-path", "/no/such.db"]), Mock()) == 1
        assert "not found" in capsys.readouterr().err


class TestCommandLine:
    """Defaults are the safety net; they must be what they claim."""

    def test_apply_defaults_to_false(self):
        assert parse_args([]).apply is False

    def test_verbose_defaults_to_false(self):
        assert parse_args([]).verbose is False

    def test_limit_defaults_to_none(self):
        assert parse_args([]).limit is None

    def test_db_path_default_is_the_container_location(self):
        assert parse_args([]).db_path == "/app/data/transcodings.db"

    def test_db_path_can_be_overridden_by_environment(self, monkeypatch):
        monkeypatch.setenv("REPAIR_DB_PATH", "/tmp/other.db")
        import importlib
        import scripts.repair_transcoding_metadata as module

        importlib.reload(module)
        try:
            assert module.parse_args([]).db_path == "/tmp/other.db"
        finally:
            monkeypatch.delenv("REPAIR_DB_PATH")
            importlib.reload(module)

    def test_main_wires_parse_args_into_run(self, db_connection, temp_db_path,
                                            monkeypatch, capsys):
        seed(db_connection)
        import scripts.repair_transcoding_metadata as module

        monkeypatch.setattr(
            module,
            "build_readers",
            lambda logger: (
                _StubReader({SOURCE: video(SOURCE, 1920, 1080)}),
                _StubReader({OUTPUT: video(OUTPUT, 1280, 720)}),
            ),
        )

        assert main(["--db-path", temp_db_path]) == 0
        assert "Examined 1 completed records" in capsys.readouterr().out


class TestReaderWiring:
    """The script must measure the way the application does, or it repairs blindly."""

    def test_source_reader_prefers_the_synology_index(self):
        from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader
        from infrastructure.metadata.synoindex_metadata_reader import (
            SynoIndexMetadataReader,
        )
        from scripts.repair_transcoding_metadata import build_readers

        source_reader, _ = build_readers(Mock())

        assert isinstance(source_reader, ChainedMetadataReader)
        assert isinstance(source_reader.readers[0], SynoIndexMetadataReader)

    def test_output_reader_is_ffprobe_alone(self):
        """Measuring output through Synology's index would read the replaced file."""
        from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader
        from infrastructure.metadata.ffprobe_metadata_reader import FFprobeMetadataReader
        from scripts.repair_transcoding_metadata import build_readers

        _, output_reader = build_readers(Mock())

        assert isinstance(output_reader, FFprobeMetadataReader)
        assert not isinstance(output_reader, ChainedMetadataReader)

    def test_the_two_readers_are_distinct(self):
        from scripts.repair_transcoding_metadata import build_readers

        source_reader, output_reader = build_readers(Mock())

        assert source_reader is not output_reader
        assert source_reader.readers[-1] is output_reader


class TestScriptLocation:
    """The script has to be inside the image, which means inside src/."""

    def test_lives_under_src_so_the_dockerfile_copies_it(self):
        import scripts.repair_transcoding_metadata as module

        assert os.path.basename(os.path.dirname(module.__file__)) == "scripts"


class TestOperatorInvocation:
    """The documented command must work, not merely the importable module.

    Importing under pytest succeeds because the runner puts the application root on
    sys.path. `python /app/scripts/repair_transcoding_metadata.py` does not: it puts
    the script's own directory there, and nothing else. These tests run the script
    the way the recovery procedure does — as a subprocess, from an unrelated working
    directory — which is the only way to catch that difference.
    """

    def _script_path(self):
        import scripts.repair_transcoding_metadata as module

        return os.path.abspath(module.__file__)

    def test_runs_as_a_standalone_script_from_another_directory(self, tmp_path):
        import subprocess

        result = subprocess.run(
            [sys.executable, self._script_path(), "--help"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, result.stderr
        assert "--apply" in result.stdout

    def test_reports_a_missing_database_instead_of_crashing(self, tmp_path):
        """The operator path all the way through argument parsing and startup."""
        import subprocess

        result = subprocess.run(
            [sys.executable, self._script_path(), "--db-path", str(tmp_path / "no.db")],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 1
        assert "not found" in result.stderr
        assert "Traceback" not in result.stderr
