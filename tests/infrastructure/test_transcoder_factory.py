"""Tests for FFmpegTranscoderFactory."""
import pytest
from unittest.mock import Mock
from infrastructure.transcoder.ffmpeg_transcoder_factory import FFmpegTranscoderFactory
from infrastructure.transcoder.ffmpeg_transcoder import FFmpegTranscoder


class TestFFmpegTranscoderFactory:
    """Tests for FFmpegTranscoderFactory."""

    def test_create_returns_ffmpeg_transcoder(self, sample_transcoding_configuration, sample_video):
        """Test that create() returns an FFmpegTranscoder instance."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        from domain.models.hardware import HardwareVideoAcceleration

        mock_hardware_info = Mock()
        mock_hardware_info.video_acceleration = HardwareVideoAcceleration.VAAPI

        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=sample_video,
            configuration=sample_transcoding_configuration,
            status=TranscodingStatus.PENDING
        )

        factory = FFmpegTranscoderFactory(mock_hardware_info, Mock())
        transcoder = factory.create(transcoding)

        assert isinstance(transcoder, FFmpegTranscoder)
