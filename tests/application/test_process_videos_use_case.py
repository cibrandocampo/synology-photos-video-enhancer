"""Tests for ProcessVideosUseCase."""

import pytest
import os
from typing import Dict, List, Optional
from unittest.mock import patch
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.models.transcoding import Transcoding, TranscodingStatus
from domain.models.app_config import VideoConfig, AudioConfig
from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.resolution import VideoResolution
from domain.constants.audio import AudioCodec
from domain.constants.framerate import FrameRate
from domain.ports.video_metadata_reader import VideoMetadataReader
from application.process_videos_use_case import ProcessVideosUseCase
from application.process_result import ProcessResult

VIDEO_PATH = "/test/media/video.mp4"
OUTPUT_PATH = "/test/media/@eaDir/video.mp4/SYNOPHOTO_FILM_H.mp4"


class _StubMetadataReader(VideoMetadataReader):
    """Hand-rolled stub honoring the `VideoMetadataReader` port."""

    def __init__(self, video: Optional[Video] = None,
                 by_path: Optional[Dict[str, Optional[Video]]] = None) -> None:
        self._video = video
        self._by_path = by_path
        self.requested: List[str] = []

    def read(self, video_path: str) -> Optional[Video]:
        self.requested.append(video_path)
        if self._by_path is not None:
            return self._by_path.get(video_path)
        return self._video


def make_video(path: str, width: int, height: int, framerate: int = 30,
               channels: int = 2, codec: str = "h264") -> Video:
    """Builds a Video with the given geometry."""
    return Video(
        path=path,
        video_track=VideoTrack(
            width=width, height=height, codec_name=codec, framerate=framerate
        ),
        audio_track=AudioTrack(codec="aac", bitrate=128.0, channels=channels),
        container=Container(format="mp4"),
    )


@pytest.fixture
def video_config():
    """Creates a VideoConfig for testing."""
    return VideoConfig(
        codec=VideoCodec.H264,
        bitrate=2048,
        resolution=VideoResolution.P720,
        width=1280,
        height=720,
        profile=VideoProfile.HIGH,
    )


@pytest.fixture
def audio_config():
    """Creates an AudioConfig for testing."""
    return AudioConfig(codec=AudioCodec.AAC, bitrate=128, channels=2, profile=None)


@pytest.fixture
def source_reader(sample_video):
    """Reader standing in for the SynoIndex/ffprobe chain over source videos."""
    return _StubMetadataReader(sample_video)


@pytest.fixture
def produced_video():
    """Metadata of the file the transcoder produced.

    The geometry is deliberately unlike anything the configuration or the
    source would yield, so a stale value cannot pass by coincidence.
    """
    return make_video(OUTPUT_PATH, 958, 720, codec="hevc")


@pytest.fixture
def output_reader(produced_video):
    """Reader standing in for probing the produced file."""
    return _StubMetadataReader(produced_video)


@pytest.fixture
def use_case(
    mock_video_repository,
    mock_filesystem,
    mock_transcoder_factory,
    mock_logger,
    video_config,
    audio_config,
    source_reader,
    output_reader,
):
    """Creates a ProcessVideosUseCase instance for testing."""
    return ProcessVideosUseCase(
        video_repository=mock_video_repository,
        filesystem=mock_filesystem,
        transcoder_factory=mock_transcoder_factory,
        logger=mock_logger,
        video_config=video_config,
        audio_config=audio_config,
        video_input_path="/test/media",
        metadata_reader=source_reader,
        output_metadata_reader=output_reader,
        execution_threads=2,
    )


class TestProcessVideosUseCase:
    """Tests for ProcessVideosUseCase."""

    def test_execute_no_videos(self, use_case, mock_filesystem):
        """Test execute when no videos are found."""
        mock_filesystem.find_videos.return_value = []

        result = use_case.execute()

        assert isinstance(result, ProcessResult)
        assert result.total_processed == 0
        assert result.transcoded == 0
        assert result.already_transcoded == 0
        assert result.errors == 0
        assert result.is_success is True

    def test_execute_video_already_transcoded(
        self, use_case, mock_filesystem, mock_video_repository, sample_video
    ):
        """Test execute when video is already transcoded."""
        mock_filesystem.find_videos.return_value = [VIDEO_PATH]
        mock_filesystem.file_exists.return_value = True
        mock_filesystem.find_transcoded_video.return_value = OUTPUT_PATH

        existing_transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=make_video(OUTPUT_PATH, 1280, 720),
            status=TranscodingStatus.COMPLETED,
        )
        mock_video_repository.find_by_original_path.return_value = existing_transcoding

        result = use_case.execute()

        assert result.total_processed == 1
        assert result.already_transcoded == 1
        assert result.transcoded == 0

    def test_execute_video_needs_transcoding(
        self, use_case, mock_filesystem, mock_video_repository
    ):
        """Test execute when video needs transcoding."""
        mock_filesystem.find_videos.return_value = [VIDEO_PATH]
        mock_video_repository.find_by_original_path.return_value = None

        with patch.object(use_case, "_transcode_video", return_value=True):
            result = use_case.execute()

        assert result.total_processed == 1
        assert result.transcoded == 1
        assert result.already_transcoded == 0

    def test_execute_transcoding_fails(
        self, use_case, mock_filesystem, mock_video_repository
    ):
        """Test execute when transcoding fails."""
        mock_filesystem.find_videos.return_value = [VIDEO_PATH]
        mock_video_repository.find_by_original_path.return_value = None

        with patch.object(use_case, "_transcode_video", return_value=False):
            result = use_case.execute()

        assert result.total_processed == 1
        assert result.transcoded == 0
        assert result.errors == 1

    def test_calculate_output_height_landscape(self, use_case):
        """Test calculating output height for landscape video."""
        video_track = VideoTrack(
            width=1920, height=1080, codec_name="h264", framerate=30
        )
        height = use_case._calculate_output_height(video_track)

        # Should return configured height (720) for landscape
        assert height == 720

    def test_calculate_output_height_portrait(self, use_case):
        """Test calculating output height for portrait video."""
        video_track = VideoTrack(
            width=1080, height=1920, codec_name="h264", framerate=30
        )
        height = use_case._calculate_output_height(video_track)

        # Should return configured width (1280) for portrait (vertical video)
        assert height == 1280

    def test_calculate_output_height_square(self, use_case):
        """Test calculating output height for square video."""
        video_track = VideoTrack(
            width=1080, height=1080, codec_name="h264", framerate=30
        )
        height = use_case._calculate_output_height(video_track)

        # Square video is treated as vertical, so should return width
        assert height == 1080

    def test_calculate_output_audio_channels_equal(self, use_case):
        """Test calculating audio channels when original equals config."""
        channels = use_case._calculate_output_audio_channels(2)
        assert channels == 2  # Should use config value

    def test_calculate_output_framerate(self, use_case):
        """Test calculating output framerate."""
        track = VideoTrack(width=1920, height=1080, codec_name="h264", framerate=60)
        framerate = use_case._calculate_output_framerate(track)
        # Should convert 60fps to 30fps for light videos
        assert framerate is FrameRate.FPS_30

    def test_calculate_output_framerate_ntsc(self, use_case):
        """An exact NTSC rate keeps its own standard member."""
        track = VideoTrack(
            width=1920, height=1080, codec_name="h264", framerate=30000 / 1001
        )
        framerate = use_case._calculate_output_framerate(track)

        assert framerate is FrameRate.FPS_29_97

    def test_is_transcoding_valid_completed_status(self, use_case, sample_video):
        """Test _is_transcoding_valid with completed status."""
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=make_video("/test/transcoded.mp4", 1280, 720),
            status=TranscodingStatus.COMPLETED,
        )

        result = use_case._is_transcoding_valid(transcoding)
        assert result is True

    def test_is_transcoding_valid_pending_status(self, use_case, sample_video):
        """Test _is_transcoding_valid with pending status."""
        transcoding = Transcoding(
            original_video=sample_video, status=TranscodingStatus.PENDING
        )

        result = use_case._is_transcoding_valid(transcoding)
        assert result is False

    def test_is_transcoding_valid_not_required_status(self, use_case, sample_video):
        """Test _is_transcoding_valid with NOT_REQUIRED status."""
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=use_case._unknown_video("/test/placeholder.mp4"),
            status=TranscodingStatus.NOT_REQUIRED,
        )

        result = use_case._is_transcoding_valid(transcoding)
        assert result is True

    def test_is_transcoding_valid_wrong_codec(self, use_case, sample_video):
        """Test _is_transcoding_valid with COMPLETED status (codec validation removed)."""
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=make_video("/test/transcoded.mp4", 1280, 720, codec="vp8"),
            status=TranscodingStatus.COMPLETED,
        )

        # COMPLETED status is always valid regardless of codec/resolution
        result = use_case._is_transcoding_valid(transcoding)
        assert result is True

    def test_is_transcoding_valid_resolution_too_high(self, use_case, sample_video):
        """Test _is_transcoding_valid with COMPLETED status (resolution validation removed)."""
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=make_video("/test/transcoded.mp4", 1920, 1080),
            status=TranscodingStatus.COMPLETED,
        )

        # COMPLETED status is always valid regardless of codec/resolution
        result = use_case._is_transcoding_valid(transcoding)
        assert result is True

    def test_get_output_path(self, use_case, mock_filesystem, temp_dir):
        """Test _get_output_path creates correct path."""

        original_path = os.path.join(temp_dir, "video.mp4")
        output_path = use_case._get_output_path(original_path)

        expected = os.path.join(temp_dir, "@eaDir", "video.mp4", "SYNOPHOTO_FILM_H.mp4")
        assert output_path == expected

        # Verify ensure_directory was called
        mock_filesystem.ensure_directory.assert_called_once()

    def test_calculate_output_height_vertical_video(self, use_case):
        """Test _calculate_output_height with vertical video."""
        # Vertical video: height >= width
        video_track = VideoTrack(
            width=720, height=1280, codec_name="h264", framerate=30
        )

        # For vertical video, output height should be video_config.width
        output_height = use_case._calculate_output_height(video_track)

        assert output_height == use_case.video_config.width  # 1280

    def test_calculate_output_height_horizontal_video(self, use_case):
        """Test _calculate_output_height with horizontal video."""
        # Horizontal video: width > height
        video_track = VideoTrack(
            width=1920, height=1080, codec_name="h264", framerate=30
        )

        # For horizontal video, output height should be video_config.height
        output_height = use_case._calculate_output_height(video_track)

        assert output_height == use_case.video_config.height  # 720

    def test_calculate_output_audio_channels_less_than_config(self, use_case):
        """Test _calculate_output_audio_channels when original has fewer channels."""
        # Original has 1 channel, config wants 2
        output_channels = use_case._calculate_output_audio_channels(1)

        # Should keep original (1 channel)
        assert output_channels == 1

    def test_calculate_output_audio_channels_more_than_config(self, use_case):
        """Test _calculate_output_audio_channels when original has more channels."""
        # Original has 6 channels, config wants 2
        output_channels = use_case._calculate_output_audio_channels(6)

        # Should use config (2 channels)
        assert output_channels == use_case.audio_config.channels

    def test_calculate_output_audio_channels_equal_to_config(self, use_case):
        """Test _calculate_output_audio_channels when original equals config."""
        # Original has 2 channels, config wants 2
        output_channels = use_case._calculate_output_audio_channels(2)

        # Should use config (2 channels)
        assert output_channels == use_case.audio_config.channels

    def test_execute_with_transcoding_error(self, use_case, mock_filesystem):
        """Test execute when transcoding fails."""
        mock_filesystem.find_videos.return_value = [VIDEO_PATH]
        mock_video_repository = use_case.video_repository
        mock_video_repository.find_by_original_path.return_value = None

        # Mock _transcode_video to return False (failure)
        with patch.object(use_case, "_transcode_video", return_value=False):
            result = use_case.execute()

        assert result.total_processed == 1
        assert result.errors == 1
        assert result.transcoded == 0
        assert result.is_success is False

    def test_transcode_video_success(
        self,
        use_case,
        mock_filesystem,
        mock_video_repository,
        mock_transcoder,
    ):
        """Test _transcode_video full path when the output exists (success)."""
        mock_filesystem.file_exists.return_value = True
        mock_transcoder.transcode.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            result = use_case._transcode_video(VIDEO_PATH)

        assert result is True
        assert mock_video_repository.save.call_count == 2
        last_saved = mock_video_repository.save.call_args_list[-1][0][0]
        assert last_saved.status == TranscodingStatus.COMPLETED

    def test_transcode_video_failure(
        self,
        use_case,
        mock_filesystem,
        mock_video_repository,
        mock_transcoder,
    ):
        """Test _transcode_video full path when transcoding fails."""
        mock_filesystem.file_exists.return_value = True
        mock_transcoder.transcode.return_value = False

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            result = use_case._transcode_video(VIDEO_PATH)

        assert result is False
        last_saved = mock_video_repository.save.call_args_list[-1][0][0]
        assert last_saved.status == TranscodingStatus.FAILED

    def test_execute_loads_settings_from_repository_when_provided(
        self,
        mock_video_repository,
        mock_filesystem,
        mock_transcoder_factory,
        mock_logger,
        video_config,
        audio_config,
        source_reader,
        output_reader,
    ):
        """execute() refreshes config from settings_repository before processing."""
        from unittest.mock import Mock
        from domain.models.settings import TranscodingSettings

        settings_repository = Mock()
        settings_repository.load.return_value = TranscodingSettings(
            execution_threads=8,
            video_bitrate=5000,
        )
        use_case = ProcessVideosUseCase(
            video_repository=mock_video_repository,
            filesystem=mock_filesystem,
            transcoder_factory=mock_transcoder_factory,
            logger=mock_logger,
            video_config=video_config,
            audio_config=audio_config,
            video_input_path="/test/media",
            metadata_reader=source_reader,
            output_metadata_reader=output_reader,
            settings_repository=settings_repository,
        )
        mock_filesystem.find_videos.return_value = []

        use_case.execute()

        settings_repository.load.assert_called_once()
        assert use_case.execution_threads == 8

    def test_execute_keeps_defaults_when_settings_repository_raises(
        self,
        mock_video_repository,
        mock_filesystem,
        mock_transcoder_factory,
        mock_logger,
        video_config,
        audio_config,
        source_reader,
        output_reader,
    ):
        """execute() silently falls back to env-derived config on repository error."""
        from unittest.mock import Mock

        settings_repository = Mock()
        settings_repository.load.side_effect = RuntimeError("db down")
        use_case = ProcessVideosUseCase(
            video_repository=mock_video_repository,
            filesystem=mock_filesystem,
            transcoder_factory=mock_transcoder_factory,
            logger=mock_logger,
            video_config=video_config,
            audio_config=audio_config,
            video_input_path="/test/media",
            metadata_reader=source_reader,
            output_metadata_reader=output_reader,
            execution_threads=2,
            settings_repository=settings_repository,
        )
        mock_filesystem.find_videos.return_value = []

        result = use_case.execute()

        assert result.errors == 0
        assert use_case.execution_threads == 2

    def test_execute_reads_hw_transcoding_from_settings_and_passes_to_factory(
        self,
        mock_video_repository,
        mock_filesystem,
        mock_transcoder_factory,
        mock_transcoder,
        mock_logger,
        video_config,
        audio_config,
        source_reader,
        output_reader,
    ):
        """execute() must read hw_transcoding from settings and forward it to factory.create()."""
        from unittest.mock import Mock
        from domain.models.settings import TranscodingSettings

        settings_repository = Mock()
        settings_repository.load.return_value = TranscodingSettings(
            hw_transcoding=False
        )

        use_case = ProcessVideosUseCase(
            video_repository=mock_video_repository,
            filesystem=mock_filesystem,
            transcoder_factory=mock_transcoder_factory,
            logger=mock_logger,
            video_config=video_config,
            audio_config=audio_config,
            video_input_path="/test/media",
            metadata_reader=source_reader,
            output_metadata_reader=output_reader,
            settings_repository=settings_repository,
        )

        mock_filesystem.find_videos.return_value = [VIDEO_PATH]
        mock_filesystem.file_exists.return_value = True
        mock_video_repository.find_by_original_path.return_value = None
        mock_transcoder.transcode.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case.execute()

        mock_transcoder_factory.create.assert_called_once()
        assert (
            mock_transcoder_factory.create.call_args.kwargs.get("hw_transcoding")
            is False
        )


class TestMetadataSource:
    """The use case asks the port; it no longer reads files itself."""

    def test_source_metadata_is_read_from_the_source_reader(
        self, use_case, mock_filesystem, source_reader, mock_transcoder
    ):
        mock_filesystem.file_exists.return_value = True
        mock_transcoder.transcode.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        assert source_reader.requested == [VIDEO_PATH]

    def test_output_reader_is_not_consulted_before_transcoding(
        self, use_case, mock_filesystem, output_reader, mock_transcoder
    ):
        """Reading the output before transcoding is what stored stale resolutions."""
        mock_filesystem.file_exists.return_value = True
        mock_transcoder.transcode.return_value = False

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        assert output_reader.requested == []

    def test_read_video_metadata_is_gone(self, use_case):
        """Metadata reading belongs to the adapters now."""
        assert not hasattr(use_case, "_read_video_metadata")


class TestUnknownSourceMetadata:
    """Unknown geometry must stop the transcode, not feed it guesses."""

    @pytest.fixture
    def use_case(self, use_case):
        use_case.metadata_reader = _StubMetadataReader(None)
        return use_case

    def test_returns_false(self, use_case, mock_filesystem):
        mock_filesystem.file_exists.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            assert use_case._transcode_video(VIDEO_PATH) is False

    def test_no_transcoder_is_created(
        self, use_case, mock_filesystem, mock_transcoder_factory
    ):
        mock_filesystem.file_exists.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        mock_transcoder_factory.create.assert_not_called()

    def test_record_is_saved_as_failed_with_a_message(
        self, use_case, mock_filesystem, mock_video_repository
    ):
        mock_filesystem.file_exists.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        saved = mock_video_repository.save.call_args[0][0]
        assert saved.status == TranscodingStatus.FAILED
        assert saved.error_message
        assert VIDEO_PATH in saved.error_message


class TestNotRequired:
    """The decision is now the absence of the output file, nothing else."""

    def test_missing_output_file_is_not_required(
        self, use_case, mock_filesystem, mock_video_repository
    ):
        mock_filesystem.file_exists.return_value = False

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            result = use_case._transcode_video(VIDEO_PATH)

        assert result is True
        saved = mock_video_repository.save.call_args[0][0]
        assert saved.status == TranscodingStatus.NOT_REQUIRED
        assert saved.configuration is None

    def test_decision_uses_the_output_path(self, use_case, mock_filesystem):
        mock_filesystem.file_exists.return_value = False

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        mock_filesystem.file_exists.assert_called_once_with(OUTPUT_PATH)

    def test_no_transcoder_is_created(
        self, use_case, mock_filesystem, mock_transcoder_factory
    ):
        mock_filesystem.file_exists.return_value = False

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        mock_transcoder_factory.create.assert_not_called()

    def test_source_metadata_is_still_recorded(
        self, use_case, mock_filesystem, mock_video_repository, sample_video
    ):
        """The row must still describe which video was skipped."""
        mock_filesystem.file_exists.return_value = False

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        saved = mock_video_repository.save.call_args[0][0]
        assert saved.original_video == sample_video

    def test_existing_output_file_runs_the_transcode(
        self, use_case, mock_filesystem, mock_transcoder_factory, mock_transcoder
    ):
        mock_filesystem.file_exists.return_value = True
        mock_transcoder.transcode.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        mock_transcoder_factory.create.assert_called_once()


class TestPostTranscodeReRead:
    """The stored row must describe the file that was produced."""

    @pytest.fixture(autouse=True)
    def transcoding_succeeds(self, mock_filesystem, mock_transcoder):
        mock_filesystem.file_exists.return_value = True
        mock_transcoder.transcode.return_value = True

    def test_output_is_probed_after_transcoding(self, use_case, output_reader):
        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        assert output_reader.requested == [OUTPUT_PATH]

    def test_saved_resolution_comes_from_the_produced_file(
        self, use_case, mock_video_repository
    ):
        """Not the configured height, not the source, not Synology's old file."""
        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        saved = mock_video_repository.save.call_args_list[-1][0][0]
        assert saved.transcoded_video.video_track.resolution == "958x720"

    def test_saved_codec_comes_from_the_produced_file(
        self, use_case, mock_video_repository
    ):
        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        saved = mock_video_repository.save.call_args_list[-1][0][0]
        assert saved.transcoded_video.video_track.codec_name == "hevc"

    def test_pending_record_does_not_claim_a_resolution(
        self, use_case, mock_video_repository
    ):
        """Before the file exists there is nothing truthful to store."""
        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        pending = mock_video_repository.save.call_args_list[0][0][0]
        assert pending.status == TranscodingStatus.PENDING
        assert pending.transcoded_video.video_track.resolution == "0x0"

    def test_unreadable_output_is_recorded_as_failed(
        self, use_case, mock_video_repository
    ):
        """A file we cannot probe is not a transcode we can claim succeeded."""
        use_case.output_metadata_reader = _StubMetadataReader(None)

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            result = use_case._transcode_video(VIDEO_PATH)

        assert result is False
        saved = mock_video_repository.save.call_args_list[-1][0][0]
        assert saved.status == TranscodingStatus.FAILED
        assert saved.error_message

    def test_failed_transcode_does_not_probe_the_output(
        self, use_case, mock_transcoder, output_reader
    ):
        mock_transcoder.transcode.return_value = False

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        assert output_reader.requested == []


class TestUpscaleGuard:
    """Never produce a file taller than the source."""

    @pytest.mark.parametrize(
        "width, height, expected",
        [
            (480, 854, 854),    # vertical, target 1280 would enlarge it
            (640, 360, 360),    # horizontal, target 720 would enlarge it
            (1080, 1920, 1280),  # vertical, target below source
            (1920, 1080, 720),  # horizontal, target below source
            (720, 1280, 1280),  # vertical, target equals source
            (1280, 720, 720),   # horizontal, target equals source
        ],
    )
    def test_output_height(self, use_case, width, height, expected):
        track = VideoTrack(width=width, height=height, codec_name="h264", framerate=30)

        assert use_case._calculate_output_height(track) == expected

    def test_never_exceeds_the_source_height(self, use_case):
        """The property that matters, stated directly."""
        for width, height in [(320, 240), (240, 320), (4096, 2160), (1, 1)]:
            track = VideoTrack(
                width=width, height=height, codec_name="h264", framerate=30
            )
            assert use_case._calculate_output_height(track) <= height


class TestProductionIncidentRegression:
    """The exact case that shipped as 404x720 at 30 fps with mono audio."""

    @pytest.fixture
    def portrait_source(self):
        """A rotated iPhone clip as Synology's index describes it."""
        return make_video(VIDEO_PATH, 1080, 1920, framerate=25, channels=1)

    @pytest.fixture
    def use_case(self, use_case, portrait_source):
        use_case.metadata_reader = _StubMetadataReader(portrait_source)
        return use_case

    @pytest.fixture
    def configuration(
        self, use_case, mock_filesystem, mock_transcoder, mock_transcoder_factory
    ):
        mock_filesystem.file_exists.return_value = True
        mock_transcoder.transcode.return_value = True

        with patch.object(use_case, "_get_output_path", return_value=OUTPUT_PATH):
            use_case._transcode_video(VIDEO_PATH)

        return mock_transcoder_factory.create.call_args[0][0].configuration

    def test_treated_as_vertical(self, configuration):
        """Read through the old parser this was 44100x2 and came out at 404x720."""
        assert configuration.video_height == 1280

    def test_framerate_is_preserved(self, configuration):
        """The shifted bitrate field snapped every one of these to 30 fps."""
        assert configuration.video_framerate is FrameRate.FPS_25

    def test_audio_is_not_upmixed(self, configuration):
        assert configuration.audio_channels == 1


class TestFramerateDecision:
    """Constant sources get a chosen rate; variable ones keep their own cadence."""

    def decide(self, use_case, rate, variable=False):
        track = VideoTrack(
            width=1920, height=1080, codec_name="h264",
            framerate=rate, is_variable_framerate=variable,
        )
        return use_case._calculate_output_framerate(track)

    def test_variable_source_is_passed_through(self, use_case):
        """The camera spent frames where there was motion; that is worth keeping."""
        assert self.decide(use_case, 30.0, variable=True) is None

    def test_variable_source_is_passed_through_even_at_a_high_rate(self, use_case):
        """Reduction does not override the source's own decision to vary."""
        assert self.decide(use_case, 60.0, variable=True) is None

    def test_unknown_rate_is_passed_through(self, use_case):
        """Imposing a cadence we never measured is the guess this series removed."""
        assert self.decide(use_case, 0) is None

    @pytest.mark.parametrize(
        "rate, expected",
        [
            (30000 / 1001, FrameRate.FPS_29_97),
            (25.0, FrameRate.FPS_25),
            (30.0, FrameRate.FPS_30),
            (24.0, FrameRate.FPS_24),
        ],
    )
    def test_constant_source_at_or_below_thirty_keeps_its_rate(
        self, use_case, rate, expected
    ):
        assert self.decide(use_case, rate) is expected

    @pytest.mark.parametrize(
        "rate, expected",
        [
            (50.0, FrameRate.FPS_25),
            (60000 / 1001, FrameRate.FPS_29_97),
            (60.0, FrameRate.FPS_30),
            (120.0, FrameRate.FPS_30),
            (240.0, FrameRate.FPS_30),
        ],
    )
    def test_high_rates_are_reduced(self, use_case, rate, expected):
        assert self.decide(use_case, rate) is expected

    def test_one_hundred_and_forty_four_uses_the_map_not_halving(self, use_case):
        """Halving would give 18, a rate the enum does not contain."""
        assert self.decide(use_case, 144.0) is FrameRate.FPS_24

    @pytest.mark.parametrize("rate", [23.0, 15.0, 12.0, 8.0])
    def test_slow_sources_are_never_sped_up(self, use_case, rate):
        """Below every standard rate, so the source's own cadence is the answer."""
        assert self.decide(use_case, rate) is None

    def test_a_rate_just_below_a_standard_one_is_passed_through(self, use_case):
        """29 must not gain frames at 29.97 nor lose them at 25."""
        assert self.decide(use_case, 29.0) is None

    def test_no_decision_ever_exceeds_the_source(self, use_case):
        """The property the guard exists for, stated directly."""
        for rate in (8.0, 12.0, 23.0, 24.0, 25.0, 29.0, 30000 / 1001, 30.0,
                     50.0, 60.0, 120.0, 144.0, 240.0):
            chosen = self.decide(use_case, rate)
            if chosen is not None:
                assert chosen.to_float() <= rate, f"{chosen} exceeds source {rate}"
