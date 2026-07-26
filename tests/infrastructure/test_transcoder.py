"""Tests for FFmpeg transcoder."""

import pytest
from unittest.mock import Mock, patch
from domain.models.transcoding import (
    Transcoding,
    TranscodingConfiguration,
    TranscodingStatus,
)
from domain.models.hardware import HardwareVideoAcceleration
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.audio import AudioCodec
from domain.constants.container import ContainerFormat
from domain.constants.framerate import FrameRate
from domain.constants.hardware import HardwareBackend
from infrastructure.transcoder.ffmpeg_transcoder import FFmpegTranscoder


class TestFFmpegTranscoder:
    """Tests for FFmpegTranscoder."""

    @pytest.fixture
    def sample_transcoding(self):
        """Creates a sample Transcoding object for testing."""
        original_video = Video(
            path="/test/original.mp4",
            video_track=VideoTrack(
                width=1920, height=1080, codec_name="h264", framerate=30
            ),
            audio_track=AudioTrack(),
            container=Container(format="mp4"),
        )

        transcoded_video = Video(
            path="/test/@eaDir/original.mp4/SYNOPHOTO_FILM_H.mp4",
            video_track=VideoTrack(
                width=1280, height=720, codec_name="h264", framerate=30
            ),
            audio_track=AudioTrack(),
            container=Container(format="mp4"),
        )

        configuration = TranscodingConfiguration(
            video_codec=VideoCodec.H264,
            video_profile=VideoProfile.HIGH,
            video_height=720,
            video_framerate=30.0,
            video_bitrate=2048,
            audio_codec=AudioCodec.AAC,
            audio_profile=None,
            audio_channels=2,
            audio_bitrate=128,
            container=ContainerFormat.MP4,
            execution_threads=2,
        )

        return Transcoding(
            original_video=original_video,
            transcoded_video=transcoded_video,
            configuration=configuration,
            status=TranscodingStatus.PENDING,
        )

    @pytest.fixture
    def mock_hardware_info(self):
        """Creates a mock HardwareInfo."""
        mock = Mock()
        mock.video_acceleration = HardwareVideoAcceleration.VAAPI
        return mock

    @pytest.fixture
    def mock_logger(self):
        """Creates a mock logger."""
        return Mock()

    @pytest.fixture
    def transcoder(self, sample_transcoding, mock_hardware_info, mock_logger):
        """Creates an FFmpegTranscoder instance for testing."""
        return FFmpegTranscoder(sample_transcoding, mock_hardware_info, mock_logger)

    def test_init_sets_hardware_backend(self, transcoder):
        """Test that __init__ sets hardware_backend correctly."""
        assert transcoder.hardware_backend == HardwareBackend.VAAPI

    def test_init_sets_encoders(self, transcoder):
        """Test that __init__ sets video and audio encoders."""
        assert transcoder.video_encoder is not None
        assert transcoder.audio_encoder is not None

    @patch("infrastructure.transcoder.ffmpeg_transcoder.shutil.which")
    @patch("infrastructure.transcoder.ffmpeg_transcoder.subprocess.run")
    def test_transcode_failure(self, mock_subprocess, mock_which, transcoder):
        """Test transcoding failure."""
        import subprocess

        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=["ffmpeg"], stderr=b"Error: codec not supported"
        )

        result = transcoder.transcode()

        assert result is False

    def test_build_ffmpeg_command_includes_output(self, transcoder):
        """Test that build_ffmpeg_command includes output file."""
        cmd = transcoder._build_ffmpeg_command()

        assert transcoder.transcoding.transcoded_video.path in cmd

    def test_build_ffmpeg_command_includes_input(self, transcoder):
        """Test that build_ffmpeg_command includes input file."""
        cmd = transcoder._build_ffmpeg_command()

        # Input file should be in the command (before output)
        input_idx = cmd.index("-i")
        assert cmd[input_idx + 1] == transcoder.transcoding.original_video.path

    def test_build_qsv_command(self, sample_transcoding):
        """Test building QSV command."""
        from domain.models.hardware import HardwareVideoAcceleration

        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.QSV

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_qsv_command()

        # QSV command should use init_hw_device with qsv=hw: format
        assert "-init_hw_device" in cmd
        assert "-filter_hw_device" in cmd
        # Check that qsv is in the init_hw_device value
        init_idx = cmd.index("-init_hw_device")
        assert "qsv" in cmd[init_idx + 1]

    def test_build_vaapi_command(self, sample_transcoding):
        """Test building VAAPI command."""
        from domain.models.hardware import HardwareVideoAcceleration

        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_vaapi_command()

        assert "-hwaccel" in cmd
        assert "vaapi" in cmd
        assert "-vaapi_device" in cmd

    def test_build_v4l2m2m_command(self, sample_transcoding):
        """Test building V4L2M2M command."""
        from domain.models.hardware import HardwareVideoAcceleration

        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.V4L2M2M

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_v4l2m2m_command()

        assert "-pix_fmt" in cmd
        assert "nv12" in cmd

    def test_build_software_command(self, sample_transcoding):
        """Test building software command."""

        mock_hw = Mock()
        mock_hw.video_acceleration = None  # No hardware acceleration

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_software_command()

        # Software command should not have hardware-specific flags
        assert "-hwaccel" not in cmd
        assert "-vaapi_device" not in cmd

    def test_build_audio_command(self, transcoder):
        """Test building audio command."""
        cmd = transcoder._build_audio_command()

        assert "-c:a" in cmd
        assert "-b:a" in cmd
        assert transcoder.audio_encoder in cmd

    def test_build_audio_command_with_channels(self, sample_transcoding):
        """Test building audio command includes channels when specified."""
        from domain.models.hardware import HardwareVideoAcceleration

        # Create transcoding with audio channels > 0
        sample_transcoding.configuration.audio_channels = 2

        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_audio_command()

        assert "-ac" in cmd
        assert "2" in cmd

    def test_build_audio_command_no_channels(self, sample_transcoding):
        """Test building audio command without channels."""
        from domain.models.hardware import HardwareVideoAcceleration

        # Create transcoding with audio channels = 0
        sample_transcoding.configuration.audio_channels = 0

        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_audio_command()

        # Should not include -ac when channels is 0
        assert "-ac" not in cmd

    def test_build_qsv_command_includes_profile(self, sample_transcoding):
        """Test that QSV command includes profile when specified."""
        from domain.models.hardware import HardwareVideoAcceleration

        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.QSV

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_qsv_command()

        # Should include profile if configured
        if sample_transcoding.configuration.video_profile:
            assert "-profile:v" in cmd

    def test_build_vaapi_command_includes_profile(self, sample_transcoding):
        """Test that VAAPI command includes profile when specified."""
        from domain.models.hardware import HardwareVideoAcceleration

        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_vaapi_command()

        # Should include profile if configured
        if sample_transcoding.configuration.video_profile:
            assert "-profile:v" in cmd

    def test_build_software_command_includes_profile(self, sample_transcoding):
        """Test that software command includes profile when specified."""

        mock_hw = Mock()
        mock_hw.video_acceleration = None

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_software_command()

        # Should include profile if configured
        if sample_transcoding.configuration.video_profile:
            assert "-profile:v" in cmd

    def test_build_software_command_no_profile(self, sample_transcoding):
        """Test that software command doesn't include profile when None."""

        sample_transcoding.configuration.video_profile = None

        mock_hw = Mock()
        mock_hw.video_acceleration = None

        transcoder = FFmpegTranscoder(sample_transcoding, mock_hw, Mock())
        cmd = transcoder._build_software_command()

        # Should not include profile when None
        assert "-profile:v" not in cmd

    @patch("infrastructure.transcoder.ffmpeg_transcoder.subprocess.run")
    def test_transcode_success(self, mock_subprocess, transcoder):
        """Test successful transcoding."""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = transcoder.transcode()

        assert result is True
        mock_subprocess.assert_called_once()

    @patch("infrastructure.transcoder.ffmpeg_transcoder.subprocess.run")
    def test_transcode_failure_logs_error(self, mock_subprocess, transcoder):
        """Test that transcoding failure logs error output."""
        import subprocess

        # Simulate CalledProcessError
        error = subprocess.CalledProcessError(
            returncode=1, cmd=["ffmpeg", "..."], stderr=b"FFmpeg error: codec not found"
        )
        mock_subprocess.side_effect = error

        result = transcoder.transcode()

        assert result is False
        transcoder.logger.warning.assert_called()
        # Should log the error message
        assert any(
            "FFmpeg transcoding failed" in str(call)
            for call in transcoder.logger.warning.call_args_list
        )

    @patch("infrastructure.transcoder.ffmpeg_transcoder.shutil.which")
    def test_transcode_ffmpeg_not_found(self, mock_which, transcoder):
        """Test that transcode returns False when ffmpeg is not found."""
        mock_which.return_value = None

        result = transcoder.transcode()

        assert result is False

    @patch("infrastructure.transcoder.ffmpeg_transcoder.subprocess.run")
    def test_transcode_failure_no_stderr(self, mock_subprocess, transcoder):
        """Test that transcoding failure handles missing stderr."""
        import subprocess

        # Simulate CalledProcessError with no stderr
        error = subprocess.CalledProcessError(
            returncode=1, cmd=["ffmpeg", "..."], stderr=None
        )
        mock_subprocess.side_effect = error

        result = transcoder.transcode()

        assert result is False
        transcoder.logger.warning.assert_called()

    def test_hw_transcoding_false_forces_software_even_with_hw_present(
        self, sample_transcoding
    ):
        """hw_transcoding=False must select NONE backend even when hardware is available."""
        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoder = FFmpegTranscoder(
            sample_transcoding, mock_hw, Mock(), hw_transcoding=False
        )

        assert transcoder.hardware_backend == HardwareBackend.NONE

    def test_hw_transcoding_true_with_no_hardware_falls_back_to_software(
        self, sample_transcoding
    ):
        """hw_transcoding=True with no detected device must fall back to NONE."""
        mock_hw = Mock()
        mock_hw.video_acceleration = None

        transcoder = FFmpegTranscoder(
            sample_transcoding, mock_hw, Mock(), hw_transcoding=True
        )

        assert transcoder.hardware_backend == HardwareBackend.NONE

    def test_hw_transcoding_true_with_hw_present_uses_detected_backend(
        self, sample_transcoding
    ):
        """hw_transcoding=True with detected VAAPI must produce VAAPI backend."""
        mock_hw = Mock()
        mock_hw.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoder = FFmpegTranscoder(
            sample_transcoding, mock_hw, Mock(), hw_transcoding=True
        )

        assert transcoder.hardware_backend == HardwareBackend.VAAPI


class TestFramerateArguments:
    """The exact rational must reach FFmpeg, and passthrough must ask for nothing.

    Truncating with int() is what turned every 29.97 target into `-r 29`; the four
    builders are asserted individually because each one assembles its command
    separately and a fix applied to three of them would look green.
    """

    def _transcoding(self, framerate, profile=VideoProfile.HIGH):
        return Transcoding(
            original_video=Video(
                path="/test/original.mp4",
                video_track=VideoTrack(
                    width=1920, height=1080, codec_name="h264", framerate=30
                ),
                audio_track=AudioTrack(),
                container=Container(format="mp4"),
            ),
            transcoded_video=Video(
                path="/test/out.mp4",
                video_track=VideoTrack(
                    width=1280, height=720, codec_name="h264", framerate=30
                ),
                audio_track=AudioTrack(),
                container=Container(format="mp4"),
            ),
            configuration=TranscodingConfiguration(
                video_codec=VideoCodec.H264,
                video_profile=profile,
                video_height=720,
                video_framerate=framerate,
                video_bitrate=2048,
                audio_codec=AudioCodec.AAC,
                audio_profile=None,
                audio_channels=2,
                audio_bitrate=128,
                container=ContainerFormat.MP4,
                execution_threads=2,
            ),
            status=TranscodingStatus.PENDING,
        )

    def _command(self, framerate, backend, profile=VideoProfile.HIGH):
        hardware = Mock()
        hardware.video_acceleration = None
        transcoder = FFmpegTranscoder(
            self._transcoding(framerate, profile), hardware, Mock()
        )
        transcoder.hardware_backend = backend
        return transcoder._build_ffmpeg_command()

    BACKENDS = [
        HardwareBackend.QSV,
        HardwareBackend.VAAPI,
        HardwareBackend.V4L2M2M,
        HardwareBackend.NONE,
    ]

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_exact_rational_reaches_ffmpeg(self, backend):
        command = " ".join(self._command(FrameRate.FPS_29_97, backend))

        assert "30000/1001" in command
        assert "-r 29 " not in command + " "
        assert "-r 30 " not in command + " "

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_passthrough_asks_for_no_rate(self, backend):
        command = self._command(None, backend)

        assert "-r" not in command
        assert "passthrough" in " ".join(command)

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_chosen_rate_uses_constant_mode(self, backend):
        command = self._command(FrameRate.FPS_25, backend)

        assert "cfr" in " ".join(command)
        assert "25/1" in " ".join(command)

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_no_builder_uses_the_deprecated_vsync(self, backend):
        assert "-vsync" not in self._command(FrameRate.FPS_30, backend)

    def test_qsv_filter_carries_the_rate_itself(self):
        command = " ".join(self._command(FrameRate.FPS_29_97, HardwareBackend.QSV))

        assert "vpp_qsv=framerate=30000/1001:h=720" in command

    def test_qsv_filter_omits_the_rate_for_passthrough(self):
        command = " ".join(self._command(None, HardwareBackend.QSV))

        assert "vpp_qsv=h=720" in command
        assert "framerate=" not in command

    @pytest.mark.parametrize("backend", BACKENDS)
    def test_a_codec_without_profiles_emits_none(self, backend):
        """Profile is optional, and every builder guards on it independently."""
        command = self._command(FrameRate.FPS_30, backend, profile=None)

        assert "-profile:v" not in command
        assert "-fps_mode" in command
