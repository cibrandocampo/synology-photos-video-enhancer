"""Tests for FFprobeMetadataReader.

Every case is driven through a stub runner returning canned ffprobe JSON: no real
process is spawned and no real media file is read.
"""
import json
import subprocess

import pytest

from infrastructure.metadata.ffprobe_metadata_reader import FFprobeMetadataReader

from .conftest import StubCompletedProcess, StubRunner


def video_stream(**overrides):
    """Builds an ffprobe video stream entry."""
    stream = {
        "codec_type": "video",
        "codec_name": "h264",
        "width": 1920,
        "height": 1080,
        "avg_frame_rate": "30/1",
        "r_frame_rate": "30/1",
        "bit_rate": "5000000",
    }
    stream.update(overrides)
    return stream


def audio_stream(**overrides):
    """Builds an ffprobe audio stream entry."""
    stream = {
        "codec_type": "audio",
        "codec_name": "aac",
        "channels": 2,
        "bit_rate": "128000",
    }
    stream.update(overrides)
    return stream


def payload(streams=None, container=None):
    """Builds a full ffprobe JSON payload."""
    return json.dumps(
        {
            "streams": streams if streams is not None else [video_stream()],
            "format": container
            if container is not None
            else {
                "format_name": "mov,mp4,m4a,3gp,3g2,mj2",
                "duration": "12.5",
                "bit_rate": "5128000",
                "size": "8012345",
            },
        }
    ).encode("utf-8")


def reader_for(logger, streams=None, container=None):
    """Builds a reader whose runner returns the given probe output."""
    runner = StubRunner(StubCompletedProcess(stdout=payload(streams, container)))
    return FFprobeMetadataReader(logger, runner=runner), runner


class TestCommand:
    """The probe must ask ffprobe for everything the mapping needs."""

    def test_command_shape(self, logger):
        reader, runner = reader_for(logger)

        reader.read("/media/album/video.mp4")

        assert runner.command[0] == "ffprobe"
        assert "-print_format" in runner.command
        assert "json" in runner.command
        assert "-show_streams" in runner.command
        assert "-show_format" in runner.command
        assert runner.command[-1] == "/media/album/video.mp4"

    def test_timeout_is_passed_to_the_runner(self, logger):
        runner = StubRunner(StubCompletedProcess(stdout=payload()))
        reader = FFprobeMetadataReader(logger, runner=runner, timeout=5)

        reader.read("/media/album/video.mp4")

        assert runner.timeout == 5


class TestMapping:
    """ffprobe output must land on the domain model."""

    def test_video_track(self, logger):
        reader, _ = reader_for(logger)

        video = reader.read("/media/album/video.mp4")

        assert video.path == "/media/album/video.mp4"
        assert video.video_track.width == 1920
        assert video.video_track.height == 1080
        assert video.video_track.codec_name == "h264"
        assert video.video_track.framerate == 30
        assert video.video_track.bitrate == 5000000.0

    def test_audio_track(self, logger):
        reader, _ = reader_for(logger, streams=[video_stream(), audio_stream()])

        video = reader.read("/media/album/video.mp4")

        assert video.audio_track.codec == "aac"
        assert video.audio_track.channels == 2
        assert video.audio_track.bitrate == 128000.0

    def test_container(self, logger):
        reader, _ = reader_for(logger)

        video = reader.read("/media/album/video.mp4")

        assert video.container.duration == 12.5
        assert video.container.total_bitrate == 5128000.0
        assert video.container.file_size == 8012345

    def test_video_without_audio_stream(self, logger):
        """A silent video is legal and must not crash the mapping."""
        reader, _ = reader_for(logger, streams=[video_stream()])

        video = reader.read("/media/album/video.mp4")

        assert video is not None
        assert video.audio_track.channels == 0

    def test_absent_optional_fields(self, logger):
        """Missing bitrate or size must fall back to defaults, not raise."""
        stream = video_stream()
        del stream["bit_rate"]
        reader, _ = reader_for(logger, streams=[stream], container={})

        video = reader.read("/media/album/video.mp4")

        assert video.video_track.bitrate == 0.0
        assert video.container.duration == 0.0
        assert video.container.file_size == 0


class TestRotation:
    """Rotation decides orientation; getting it wrong reproduces the 404x720 defect."""

    def test_no_rotation_keeps_geometry(self, logger):
        reader, _ = reader_for(logger)

        video = reader.read("/media/album/video.mp4")

        assert video.video_track.resolution == "1920x1080"

    @pytest.mark.parametrize("rotation", [-90, 90, 270, -270])
    def test_quarter_turns_swap_geometry(self, logger, rotation):
        stream = video_stream(
            side_data_list=[
                {"side_data_type": "Display Matrix", "rotation": rotation}
            ]
        )
        reader, _ = reader_for(logger, streams=[stream])

        video = reader.read("/media/album/video.mp4")

        assert video.video_track.resolution == "1080x1920"

    @pytest.mark.parametrize("rotation", [0, 180, -180])
    def test_half_turns_keep_geometry(self, logger, rotation):
        stream = video_stream(
            side_data_list=[
                {"side_data_type": "Display Matrix", "rotation": rotation}
            ]
        )
        reader, _ = reader_for(logger, streams=[stream])

        video = reader.read("/media/album/video.mp4")

        assert video.video_track.resolution == "1920x1080"

    def test_legacy_rotate_tag_is_honoured(self, logger):
        """Older files carry the rotation as a tag rather than as side data."""
        stream = video_stream(tags={"rotate": "90"})
        reader, _ = reader_for(logger, streams=[stream])

        video = reader.read("/media/album/video.mp4")

        assert video.video_track.resolution == "1080x1920"

    def test_side_data_without_rotation_is_ignored(self, logger):
        stream = video_stream(side_data_list=[{"side_data_type": "Stereo 3D"}])
        reader, _ = reader_for(logger, streams=[stream])

        video = reader.read("/media/album/video.mp4")

        assert video.video_track.resolution == "1920x1080"

    def test_unusable_rotation_value_is_ignored(self, logger):
        stream = video_stream(tags={"rotate": "sideways"})
        reader, _ = reader_for(logger, streams=[stream])

        video = reader.read("/media/album/video.mp4")

        assert video.video_track.resolution == "1920x1080"


class TestUnusableGeometry:
    """`0x0` means "unknown" everywhere else; the probe must not report it as measured."""

    @pytest.mark.parametrize(
        "overrides, description",
        [
            ({}, "no width or height at all"),
            ({"width": 1920}, "height missing"),
            ({"height": 1080}, "width missing"),
            ({"width": 0, "height": 0}, "explicit zeros"),
            ({"width": 1920, "height": 0}, "zero height"),
            ({"width": -1920, "height": -1080}, "negative dimensions"),
            ({"width": {}, "height": 8}, "width is a JSON object"),
            ({"width": "wide", "height": 1080}, "width is not a number"),
        ],
    )
    def test_returns_none(self, logger, overrides, description):
        stream = {"codec_type": "video", "codec_name": "h264", "avg_frame_rate": "25/1"}
        stream.update(overrides)
        reader, _ = reader_for(logger, streams=[stream])

        assert reader.read("/media/album/video.mp4") is None, description
        assert len(logger.warnings) == 1

    def test_rotation_is_applied_before_the_check(self, logger):
        """A swapped-but-valid geometry must survive, not be mistaken for garbage."""
        stream = video_stream(
            side_data_list=[{"side_data_type": "Display Matrix", "rotation": 90}]
        )
        reader, _ = reader_for(logger, streams=[stream])

        assert reader.read("/media/album/video.mp4").video_track.resolution == "1080x1920"

    def test_smallest_usable_geometry_is_accepted(self, logger):
        """The guard rejects non-answers, not small videos."""
        reader, _ = reader_for(logger, streams=[video_stream(width=2, height=2)])

        assert reader.read("/media/album/video.mp4").video_track.resolution == "2x2"


class TestFramerate:
    """The nominal rate is what the file declares; the average is what it measured."""

    def framerate_of(self, logger, **overrides):
        stream = video_stream(**overrides)
        reader, _ = reader_for(logger, streams=[stream])
        return reader.read("/media/album/video.mp4").video_track.framerate

    def test_nominal_rate_is_preferred_over_the_average(self, logger):
        """For a variable source the average is an artefact of the content."""
        rate = self.framerate_of(
            logger, r_frame_rate="30000/1001", avg_frame_rate="121500/2647"
        )

        assert rate == pytest.approx(30000 / 1001)

    def test_ntsc_rate_is_not_rounded(self, logger):
        """29.97 must survive; rounding is what the enum's fractions prevent."""
        rate = self.framerate_of(
            logger, r_frame_rate="30000/1001", avg_frame_rate="30000/1001"
        )

        assert rate != 30
        assert rate == pytest.approx(29.97002997002997)

    def test_falls_back_to_the_average_when_nominal_is_unusable(self, logger):
        rate = self.framerate_of(logger, r_frame_rate="0/0", avg_frame_rate="25/1")

        assert rate == 25

    def test_both_rates_unusable_yields_zero(self, logger):
        assert self.framerate_of(logger, r_frame_rate="0/0", avg_frame_rate="0/0") == 0

    def test_malformed_rate_does_not_raise(self, logger):
        assert self.framerate_of(
            logger, r_frame_rate="not/a/rate", avg_frame_rate=None
        ) == 0


class TestVariableFramerate:
    """Distinguishing a variable source is the only thing ffprobe can do that
    Synology's index cannot: the index stores one nominal rate, so a constant 30 fps
    video and a variable one are identical in it.

    The 1% threshold comes from measuring 900 real library videos: the relative
    difference clusters densely below 0.5% and again above 2%, with a trough between.
    """

    def variability_of(self, logger, **overrides):
        stream = video_stream(**overrides)
        reader, _ = reader_for(logger, streams=[stream])
        return reader.read("/media/album/video.mp4").video_track.is_variable_framerate

    def test_identical_rates_are_constant(self, logger):
        assert self.variability_of(
            logger, r_frame_rate="30/1", avg_frame_rate="30/1"
        ) is False

    def test_container_quirk_below_the_threshold_is_constant(self, logger):
        """A real library file: 30.004 average against a 30 nominal, 0.013% apart."""
        assert self.variability_of(
            logger, r_frame_rate="30/1", avg_frame_rate="16380000/545929"
        ) is False

    def test_clearly_variable_source(self, logger):
        """A real library file: nominally 59.94, averaging 19.98."""
        assert self.variability_of(
            logger, r_frame_rate="60000/1001", avg_frame_rate="20000/1001"
        ) is True

    def test_just_above_the_threshold_is_variable(self, logger):
        assert self.variability_of(
            logger, r_frame_rate="100/1", avg_frame_rate="98/1"
        ) is True

    def test_just_below_the_threshold_is_constant(self, logger):
        assert self.variability_of(
            logger, r_frame_rate="100/1", avg_frame_rate="99.5/1"
        ) is False

    def test_missing_average_is_not_variable(self, logger):
        """Unknown must not disable the reduction rule for high-rate sources."""
        assert self.variability_of(
            logger, r_frame_rate="60/1", avg_frame_rate="0/0"
        ) is False

    def test_missing_nominal_is_not_variable(self, logger):
        assert self.variability_of(
            logger, r_frame_rate="0/0", avg_frame_rate="60/1"
        ) is False


class TestFailureModes:
    """Nothing may escape read(); every failure is reported as unknown."""

    def test_non_zero_return_code(self, logger):
        runner = StubRunner(
            StubCompletedProcess(returncode=1, stderr=b"Invalid data found")
        )
        reader = FFprobeMetadataReader(logger, runner=runner)

        assert reader.read("/media/album/video.mp4") is None
        assert len(logger.warnings) == 1

    def test_non_zero_return_code_without_captured_stderr(self, logger):
        """A runner that does not capture stderr must still produce a usable warning."""
        runner = StubRunner(StubCompletedProcess(returncode=1, stderr=None))
        reader = FFprobeMetadataReader(logger, runner=runner)

        assert reader.read("/media/album/video.mp4") is None
        assert len(logger.warnings) == 1

    def test_invalid_json(self, logger):
        runner = StubRunner(StubCompletedProcess(stdout=b"not json at all"))
        reader = FFprobeMetadataReader(logger, runner=runner)

        assert reader.read("/media/album/video.mp4") is None
        assert len(logger.warnings) == 1

    def test_runner_times_out(self, logger):
        runner = StubRunner(error=subprocess.TimeoutExpired(cmd="ffprobe", timeout=60))
        reader = FFprobeMetadataReader(logger, runner=runner)

        assert reader.read("/media/album/video.mp4") is None
        assert len(logger.warnings) == 1

    def test_runner_raises_file_not_found(self, logger):
        """ffprobe absent from PATH must not crash the processing cycle."""
        runner = StubRunner(error=FileNotFoundError("ffprobe"))
        reader = FFprobeMetadataReader(logger, runner=runner)

        assert reader.read("/media/album/video.mp4") is None

    def test_no_video_stream(self, logger):
        reader, _ = reader_for(logger, streams=[audio_stream()])

        assert reader.read("/media/album/video.mp4") is None
        assert len(logger.warnings) == 1

    def test_empty_stream_list(self, logger):
        reader, _ = reader_for(logger, streams=[])

        assert reader.read("/media/album/video.mp4") is None

    def test_default_runner_is_subprocess_run(self, logger):
        """The production path must shell out; only tests inject a runner."""
        reader = FFprobeMetadataReader(logger)

        assert reader._runner is subprocess.run


class TestWellFormedJsonOfTheWrongShape:
    """Output can decode as JSON and still be unusable.

    `test_invalid_json` covers bytes that are not JSON at all. These cover the other
    half: valid JSON whose shape the mapping cannot consume. Without them the mapping
    raises AttributeError/TypeError straight out of read(), which the chain would have
    to absorb and which would abort an unchained caller.
    """

    @pytest.mark.parametrize(
        "document",
        [
            pytest.param(b"null", id="null"),
            pytest.param(b"[]", id="empty-array"),
            pytest.param(b'[{"codec_type": "video"}]', id="array-of-objects"),
            pytest.param(b"5", id="bare-number"),
            pytest.param(b'"hello"', id="bare-string"),
            pytest.param(b"true", id="bare-boolean"),
        ],
    )
    def test_non_object_payload_is_reported_as_unknown(self, logger, document):
        runner = StubRunner(StubCompletedProcess(stdout=document))
        reader = FFprobeMetadataReader(logger, runner=runner)

        assert reader.read("/media/album/video.mp4") is None
        assert len(logger.warnings) == 1

    @pytest.mark.parametrize(
        "document",
        [
            pytest.param(b'{"streams": "video", "format": {}}', id="streams-is-a-string"),
            pytest.param(b'{"streams": 7, "format": {}}', id="streams-is-a-number"),
            pytest.param(b'{"streams": ["video"], "format": {}}', id="stream-is-a-string"),
            pytest.param(b'{"streams": [null], "format": {}}', id="stream-is-null"),
            pytest.param(
                b'{"streams": [{"codec_type": "video", "width": 1920, "height": 1080}],'
                b' "format": "mp4"}',
                id="format-is-a-string",
            ),
            pytest.param(
                b'{"streams": [{"codec_type": "video", "width": 1920, "height": 1080,'
                b' "tags": "none"}], "format": {}}',
                id="tags-is-a-string",
            ),
        ],
    )
    def test_malformed_inner_shape_is_reported_as_unknown(self, logger, document):
        runner = StubRunner(StubCompletedProcess(stdout=document))
        reader = FFprobeMetadataReader(logger, runner=runner)

        assert reader.read("/media/album/video.mp4") is None
        assert len(logger.warnings) == 1

    def test_a_well_formed_payload_still_parses(self, logger):
        """The guards must not reject legitimate output."""
        reader, _ = reader_for(logger)

        video = reader.read("/media/album/video.mp4")

        assert video is not None
        assert video.video_track.resolution == "1920x1080"
        assert logger.warnings == []
