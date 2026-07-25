"""Use case for processing videos."""

import os
from typing import Optional
from domain.models.transcoding import (
    Transcoding,
    TranscodingConfiguration,
    TranscodingStatus,
)
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.ports.video_repository import VideoRepository
from domain.ports.filesystem import Filesystem
from domain.ports.transcoder_factory import TranscoderFactory
from domain.ports.logger import AppLogger
from domain.ports.settings_repository import SettingsRepository
from domain.ports.video_metadata_reader import VideoMetadataReader
from domain.constants.container import ContainerFormat
from domain.constants.framerate import FrameRate
from application.process_result import ProcessResult
from domain.models.app_config import AudioConfig, VideoConfig


class ProcessVideosUseCase:
    """Use case for processing videos - orchestrates the complete workflow."""

    def __init__(
        self,
        video_repository: VideoRepository,
        filesystem: Filesystem,
        transcoder_factory: TranscoderFactory,
        logger: AppLogger,
        video_config: VideoConfig,
        audio_config: AudioConfig,
        video_input_path: str,
        metadata_reader: VideoMetadataReader,
        output_metadata_reader: VideoMetadataReader,
        execution_threads: int = 2,
        settings_repository: Optional[SettingsRepository] = None,
    ):
        """
        Initializes the use case.

        Args:
            video_repository: Repository for video operations
            filesystem: Filesystem operations
            transcoder_factory: Factory to create transcoder instances
            logger: Logger instance
            video_config: Video configuration (codec, bitrate, resolution, profile)
            audio_config: Audio configuration (codec, bitrate, channels)
            video_input_path: Root path to search for videos
            metadata_reader: Reads metadata of source videos. Expected to prefer
                Synology's index and fall back to probing the file.
            output_metadata_reader: Reads metadata of the files this use case
                produces. It must not consult Synology's index: after the output
                file is overwritten, that index still describes the previous
                version, which is what made stored resolutions wrong.
            execution_threads: Number of threads to use for transcoding
        """
        self.video_repository = video_repository
        self.filesystem = filesystem
        self.transcoder_factory = transcoder_factory
        self.metadata_reader = metadata_reader
        self.output_metadata_reader = output_metadata_reader
        self.video_config = video_config
        self.audio_config = audio_config
        self.video_input_path = video_input_path
        self.execution_threads = execution_threads
        self.hw_transcoding: bool = True
        self.logger = logger
        self._settings_repository = settings_repository

    def execute(self) -> ProcessResult:
        """
        Executes the video processing workflow.

        Returns:
            ProcessResult: Detailed result of the processing operation
        """
        result = ProcessResult()

        if self._settings_repository is not None:
            try:
                settings = self._settings_repository.load()
                self.video_config = settings.to_video_config()
                self.audio_config = settings.to_audio_config()
                self.execution_threads = settings.execution_threads
                self.hw_transcoding = settings.hw_transcoding
            except Exception:
                pass  # keep env-derived defaults on any error

        # Find all videos
        video_paths = self.filesystem.find_videos(self.video_input_path)

        for video_path in video_paths:
            result.total_processed += 1

            # Step 1: Check if video is already transcoded
            if self._is_video_transcoded(video_path):
                result.already_transcoded += 1
                continue

            # Step 2: Transcode the video
            if self._transcode_video(video_path):
                result.transcoded += 1
            else:
                result.errors += 1

        return result

    def _is_video_transcoded(self, video_path: str) -> bool:
        """
        Checks if a video is already transcoded.

        Args:
            video_path: Path to the video file

        Returns:
            True if video is already transcoded and valid, False otherwise
        """
        existing_transcoding = self.video_repository.find_by_original_path(video_path)

        if not existing_transcoding:
            return False

        # Verify if existing transcoding is valid
        return self._is_transcoding_valid(existing_transcoding)

    def _transcode_video(self, video_path: str) -> bool:
        """
        Transcodes a video file.

        Args:
            video_path: Path to the video file to transcode

        Returns:
            True if transcoding was successful, False otherwise
        """
        self.logger.info(f"Video {video_path} needs to be transcoded")

        transcoded_video_path = self._get_output_path(video_path)

        original_video = self.metadata_reader.read(video_path)
        if original_video is None:
            # Orientation, framerate and channel count would all be guesses.
            # Guessing them is what produced 404x720 files and mono audio.
            self.logger.error(f"Could not determine video metadata for {video_path}")

            transcoding = Transcoding(
                original_video=self._unknown_video(video_path),
                transcoded_video=self._unknown_video(transcoded_video_path),
                configuration=None,
                status=TranscodingStatus.FAILED,
                error_message=f"Could not determine video metadata for {video_path}",
            )
            self.video_repository.save(transcoding)
            return False

        if not self.filesystem.file_exists(transcoded_video_path):
            self.logger.info(
                f"Transcoding not required for {video_path} (Synology determined it's not necessary)"
            )

            transcoding = Transcoding(
                original_video=original_video,
                transcoded_video=self._unknown_video(transcoded_video_path),
                configuration=None,
                status=TranscodingStatus.NOT_REQUIRED,
            )
            self.video_repository.save(transcoding)
            return True

        # Calculate output height based on video orientation
        output_height = self._calculate_output_height(original_video.video_track)

        # Calculate output framerate based on original framerate
        framerate = self._calculate_output_framerate(
            original_video.video_track.framerate
        )

        audio_channels = self._calculate_output_audio_channels(
            original_video.audio_track.channels
        )

        transcoder_configuration = TranscodingConfiguration(
            video_codec=self.video_config.codec,
            video_profile=self.video_config.profile,
            video_height=output_height,
            video_framerate=framerate,
            video_bitrate=self.video_config.bitrate,
            audio_codec=self.audio_config.codec,
            audio_profile=self.audio_config.profile,
            audio_channels=audio_channels,
            audio_bitrate=self.audio_config.bitrate,
            container=ContainerFormat.MP4,
            execution_threads=self.execution_threads,
        )

        # The output geometry is unknown until the file exists, so the pending
        # record carries a placeholder and is completed with the real values below.
        transcoding = Transcoding(
            original_video=original_video,
            transcoded_video=self._unknown_video(transcoded_video_path),
            configuration=transcoder_configuration,
            status=TranscodingStatus.PENDING,
        )

        # Save to repository (transcoding now has transcoded_video and configuration)
        self.video_repository.save(transcoding)

        # Execute transcoding
        transcoder = self.transcoder_factory.create(
            transcoding, hw_transcoding=self.hw_transcoding
        )
        success = transcoder.transcode()

        if not success:
            self.video_repository.save(transcoding.mark_as_failed("Transcoding failed"))
            return False

        # Describe what was actually produced, not what was asked for and not what
        # Synology had produced before this run overwrote it.
        produced_video = self.output_metadata_reader.read(transcoded_video_path)
        if produced_video is None:
            self.logger.error(
                f"Transcoding finished but {transcoded_video_path} could not be read"
            )
            self.video_repository.save(
                transcoding.mark_as_failed(
                    "Transcoding finished but the output file could not be read"
                )
            )
            return False

        self.video_repository.save(
            transcoding.model_copy(
                update={"transcoded_video": produced_video}
            ).mark_as_completed()
        )

        return True

    def _is_transcoding_valid(self, transcoding: Transcoding) -> bool:
        """
        Verifies if an existing transcoding is valid.

        Args:
            transcoding: Transcoding to verify

        Returns:
            True if valid, False otherwise
        """
        # Check status
        if (
            transcoding.status == TranscodingStatus.COMPLETED
            or transcoding.status == TranscodingStatus.NOT_REQUIRED
        ):
            return True

        return False

    def _calculate_output_height(self, video_track: VideoTrack) -> int:
        """
        Calculates the output height based on video orientation.

        Args:
            video_track: Video track with width and height information

        Returns:
            Output height to use for transcoding, never above the source height
        """

        if video_track.height >= video_track.width:
            target_height = self.video_config.width
            orientation = "Vertical"
        else:
            target_height = self.video_config.height
            orientation = "Horizontal"

        # Enlarging a video costs space and gains no detail. This also bounds the
        # damage should the source geometry ever be misread again.
        if video_track.height and target_height > video_track.height:
            self.logger.info(
                f"{orientation} video ({video_track.resolution}) - Source shorter than "
                f"target, capping output height at {video_track.height}px"
            )
            return video_track.height

        self.logger.info(
            f"{orientation} video ({video_track.resolution}) - Output height: {target_height}px"
        )
        return target_height

    def _calculate_output_audio_channels(self, original_channels: int) -> int:
        """
        Calculates the output audio channels based on original and configuration.


        Args:
            original_channels: Number of channels in the original video

        Returns:
            Number of audio channels to use for transcoding
        """
        if original_channels < self.audio_config.channels:
            self.logger.info(
                f"Audio channels: {original_channels} -> Output channels: {original_channels}"
            )
            return original_channels

        self.logger.info(
            f"Audio channels: {original_channels} -> Output channels: {self.audio_config.channels}"
        )
        return self.audio_config.channels

    def _calculate_output_framerate(self, original_framerate: int) -> float:
        """
        Calculates the output framerate based on the original framerate.

        Args:
            original_framerate: Original video framerate (as integer)

        Returns:
            Output framerate to use for transcoding (as float, can be decimal for NTSC rates)
        """
        # Find the closest FrameRate enum value
        closest_fps = FrameRate.from_int(original_framerate)

        # Get framerate optimized for light videos
        output_fps = FrameRate.get_framerate_for_light_videos(closest_fps)
        output_framerate = output_fps.to_float()

        self.logger.info(
            f"Framerate: {original_framerate}fps - Output framerate: {output_framerate}fps"
        )

        return output_framerate

    @staticmethod
    def _unknown_video(video_path: str) -> Video:
        """
        Builds a stand-in Video for a file whose geometry is not known.

        Used for records that must be persisted without real metadata: the
        repository stores the resolution as "<width>x<height>" and dereferences
        the track unconditionally, so a Video is always required. The resulting
        "0x0" is a marker of absence, never a measurement.

        Args:
            video_path: Path the record refers to

        Returns:
            Video with zeroed geometry
        """
        return Video(
            path=video_path,
            video_track=VideoTrack(width=0, height=0, codec_name="", framerate=30),
            audio_track=AudioTrack(),
            container=Container(format=""),
        )

    def _get_output_path(self, original_path: str) -> str:
        """
        Gets the output path for transcoded video.

        Args:
            original_path: Path to original video

        Returns:
            Output path for transcoded video
        """
        video_dir = os.path.dirname(original_path)
        video_name = os.path.basename(original_path)
        ea_dir = os.path.join(video_dir, "@eaDir", video_name)
        self.filesystem.ensure_directory(ea_dir)
        return os.path.join(ea_dir, "SYNOPHOTO_FILM_H.mp4")
