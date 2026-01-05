"""Use case for processing videos."""
from pathlib import Path
from domain.models.transcoding import Transcoding, TranscodingConfiguration, TranscodingStatus
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.ports.video_repository import VideoRepository
from domain.ports.filesystem import Filesystem
from domain.ports.hardware_info import HardwareInfo
from domain.constants.container import ContainerFormat
from domain.constants.framerate import FrameRate
from application.process_result import ProcessResult
from infrastructure.logger import Logger
from infrastructure.transcoder.ffmpeg_transcoder import FFmpegTranscoder
from domain.models.app_config import AudioConfig, VideoConfig



class ProcessVideosUseCase:
    """Use case for processing videos - orchestrates the complete workflow."""
    
    def __init__(
        self,
        video_repository: VideoRepository,
        filesystem: Filesystem,
        hardware_info: HardwareInfo,
        video_config: VideoConfig,
        audio_config: AudioConfig,
        video_input_path: str,
        execution_threads: int = 2
    ):
        """
        Initializes the use case.
        
        Args:
            video_repository: Repository for video operations
            filesystem: Filesystem operations
            hardware_info: Hardware information for transcoding
            video_config: Video configuration (codec, bitrate, resolution, profile)
            audio_config: Audio configuration (codec, bitrate, channels)
            video_input_path: Root path to search for videos
            execution_threads: Number of threads to use for transcoding
        """
        self.video_repository = video_repository
        self.filesystem = filesystem
        self.hardware_info = hardware_info
        self.video_config = video_config
        self.audio_config = audio_config
        self.video_input_path = video_input_path
        self.execution_threads = execution_threads
        self.logger = Logger.get_logger()
        
        # Calculate target resolution and codec for validation
        self.target_resolution = max(video_config.width, video_config.height)
        self.target_codec = video_config.codec.value
    
    def execute(self) -> ProcessResult:
        """
        Executes the video processing workflow.
        
        Returns:
            ProcessResult: Detailed result of the processing operation
        """
        result = ProcessResult()
        
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
        
        original_video = self._read_video_metadata(video_path)
        transcoded_video_path = self._get_output_path(video_path)
        transcoded_video = self._read_video_metadata(transcoded_video_path)
        
        # Calculate output height based on video orientation
        output_height = self._calculate_output_height(original_video.video_track)

        # Calculate output framerate based on original framerate
        framerate = self._calculate_output_framerate(original_video.video_track.framerate)
        
        audio_channels = self._calculate_output_audio_channels(original_video.audio_track.channels)

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
            execution_threads=self.execution_threads
        )
        
        
        transcoding = Transcoding(
            original_video=original_video,
            transcoded_video=transcoded_video,
            configuration=transcoder_configuration,
            status=TranscodingStatus.PENDING
        )
                
        # Save to repository (transcoding now has transcoded_video and configuration)
        self.video_repository.save(transcoding)
        
        # Execute transcoding
        transcoder = FFmpegTranscoder(transcoding, self.hardware_info)
        success = transcoder.transcode()
    
        transcoding.status = TranscodingStatus.COMPLETED if success else TranscodingStatus.FAILED
        self.video_repository.save(transcoding)
        
        return success

    
    def _is_transcoding_valid(self, transcoding: Transcoding) -> bool:
        """
        Verifies if an existing transcoding is valid.
        
        Args:
            transcoding: Transcoding to verify
            
        Returns:
            True if valid, False otherwise
        """
        # Check status
        if transcoding.status != TranscodingStatus.COMPLETED:
            return False
        
        # Get target configuration
        target_codec = self.target_codec
        target_resolution = self.target_resolution
        
        # Check codec
        actual_codec = transcoding.transcoded_video.video_track.codec_name.lower()
        if target_codec.lower() not in actual_codec and actual_codec not in target_codec.lower():
            return False
        
        # Check resolution
        width = transcoding.transcoded_video.video_track.width
        height = transcoding.transcoded_video.video_track.height
        max_dimension = max(width, height)
        
        if max_dimension > target_resolution:
            return False
        
        return True
       
    def _calculate_output_height(self, video_track: VideoTrack) -> int:
        """
        Calculates the output height based on video orientation.
        
        Args:
            video_track: Video track with width and height information
            
        Returns:
            Output height to use for transcoding
        """
        
        if video_track.height >= video_track.width:
            self.logger.info(f"Vertical video ({video_track.resolution}) - Output height: {self.video_config.width}px")
            return self.video_config.width
       
        self.logger.info(f"Horizontal video ({video_track.resolution}) - Output height: {self.video_config.height}px")
        return self.video_config.height

    
    def _calculate_output_audio_channels(self, original_channels: int) -> int:
        """
        Calculates the output audio channels based on original and configuration.

        
        Args:
            original_channels: Number of channels in the original video
            
        Returns:
            Number of audio channels to use for transcoding
        """
        if original_channels < self.audio_config.channels:
            self.logger.info(f"Audio channels: {original_channels} -> Output channels: {original_channels}")
            return original_channels
        
        self.logger.info(f"Audio channels: {original_channels} -> Output channels: {self.audio_config.channels}")
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
        
        self.logger.info(f"Framerate: {original_framerate}fps - Output framerate: {output_framerate}fps")
        
        return output_framerate
    
    def _read_video_metadata(self, video_path: str) -> Video:
        """
        Reads the original video metadata from SYNOINDEX_MEDIA_INFO file.
        
        The metadata file is located at:
        <video_directory>/@eaDir/<video_filename>/SYNOINDEX_MEDIA_INFO
        
        Args:
            video_path: Path to the original video file
            
        Returns:
            Video object with metadata from SYNOINDEX_MEDIA_INFO, or placeholder if file doesn't exist
        """
        video_file = Path(video_path)
        ea_dir = video_file.parent / '@eaDir' / video_file.name
        syno_file = ea_dir / "SYNOINDEX_MEDIA_INFO"
        
        # If file doesn't exist, return a placeholder
        if not syno_file.exists():
            self.logger.warning(f"SYNOINDEX_MEDIA_INFO not found for {video_path}, using placeholder")
            return Video(
                path=video_path,
                video_track=VideoTrack(width=0, height=0, codec_name="", framerate=30),
                audio_track=AudioTrack(),
                container=Container(format="")
            )
        
        try:
            # Read the file
            with open(syno_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # The main data is in line 2 (index 1)
            if len(lines) < 2:
                self.logger.warning(f"Invalid SYNOINDEX_MEDIA_INFO format for {video_path}, using placeholder")
                return Video(
                    path=video_path,
                    video_track=VideoTrack(width=0, height=0, codec_name="", framerate=30),
                    audio_track=AudioTrack(),
                    container=Container(format="")
                )
            
            # Parse line 2 into tokens (list of strings)
            tokens = lines[1].strip().split()
            
            # Create Video object from metadata
            return Video.from_synology_metadata(video_path, tokens)
            
        except Exception as e:
            self.logger.warning(f"Error reading SYNOINDEX_MEDIA_INFO for {video_path}: {e}, using placeholder")
            return Video(
                path=video_path,
                video_track=VideoTrack(width=0, height=0, codec_name="", framerate=30),
                audio_track=AudioTrack(),
                container=Container(format="")
            )
    
    
    def _get_output_path(self, original_path: str) -> str:
        """
        Gets the output path for transcoded video.
        
        Args:
            original_path: Path to original video
            
        Returns:
            Output path for transcoded video
        """
        video_file = Path(original_path)
        ea_dir = video_file.parent / '@eaDir' / video_file.name
        ea_dir.mkdir(parents=True, exist_ok=True)
        return str(ea_dir / "SYNOPHOTO_FILM_H.mp4")
