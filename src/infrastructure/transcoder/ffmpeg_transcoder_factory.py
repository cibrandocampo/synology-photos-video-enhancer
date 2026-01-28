"""FFmpeg transcoder factory implementation."""
from domain.ports.transcoder_factory import TranscoderFactory
from domain.ports.transcoder import Transcoder
from domain.ports.hardware_info import HardwareInfo
from domain.ports.logger import AppLogger
from domain.models.transcoding import Transcoding
from infrastructure.transcoder.ffmpeg_transcoder import FFmpegTranscoder


class FFmpegTranscoderFactory(TranscoderFactory):
    """Factory that creates FFmpegTranscoder instances."""

    def __init__(self, hardware_info: HardwareInfo, logger: AppLogger):
        """
        Initializes the factory.

        Args:
            hardware_info: Hardware information for transcoding
            logger: Application logger
        """
        self.hardware_info = hardware_info
        self.logger = logger

    def create(self, transcoding: Transcoding) -> Transcoder:
        """
        Creates an FFmpegTranscoder for the given transcoding.

        Args:
            transcoding: Transcoding object containing all necessary information

        Returns:
            A configured FFmpegTranscoder instance
        """
        return FFmpegTranscoder(transcoding, self.hardware_info, self.logger)
