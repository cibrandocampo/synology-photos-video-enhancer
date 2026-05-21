"""Tests for FFmpegTranscoderFactory."""

from unittest.mock import Mock
from infrastructure.transcoder.ffmpeg_transcoder_factory import FFmpegTranscoderFactory
from infrastructure.transcoder.ffmpeg_transcoder import FFmpegTranscoder


class TestFFmpegTranscoderFactory:
    """Tests for FFmpegTranscoderFactory."""

    def test_create_returns_ffmpeg_transcoder(
        self, sample_transcoding_configuration, sample_video
    ):
        """Test that create() returns an FFmpegTranscoder instance."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        from domain.models.hardware import HardwareVideoAcceleration

        mock_hardware_info = Mock()
        mock_hardware_info.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=sample_video,
            configuration=sample_transcoding_configuration,
            status=TranscodingStatus.PENDING,
        )

        factory = FFmpegTranscoderFactory(mock_hardware_info, Mock())
        transcoder = factory.create(transcoding)

        assert isinstance(transcoder, FFmpegTranscoder)

    def test_create_with_hw_transcoding_false_produces_software_transcoder(
        self, sample_transcoding_configuration, sample_video
    ):
        """factory.create(hw_transcoding=False) must produce a transcoder with NONE backend."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        from domain.models.hardware import HardwareVideoAcceleration
        from domain.constants.hardware import HardwareBackend

        mock_hardware_info = Mock()
        mock_hardware_info.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=sample_video,
            configuration=sample_transcoding_configuration,
            status=TranscodingStatus.PENDING,
        )

        factory = FFmpegTranscoderFactory(mock_hardware_info, Mock())
        transcoder = factory.create(transcoding, hw_transcoding=False)

        assert transcoder.hardware_backend == HardwareBackend.NONE

    def test_create_with_hw_transcoding_true_uses_detected_hw(
        self, sample_transcoding_configuration, sample_video
    ):
        """factory.create(hw_transcoding=True) with VAAPI hardware must produce VAAPI backend."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        from domain.models.hardware import HardwareVideoAcceleration
        from domain.constants.hardware import HardwareBackend

        mock_hardware_info = Mock()
        mock_hardware_info.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=sample_video,
            configuration=sample_transcoding_configuration,
            status=TranscodingStatus.PENDING,
        )

        factory = FFmpegTranscoderFactory(mock_hardware_info, Mock())
        transcoder = factory.create(transcoding, hw_transcoding=True)

        assert transcoder.hardware_backend == HardwareBackend.VAAPI
