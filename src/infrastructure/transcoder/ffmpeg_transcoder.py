"""FFmpeg transcoder implementation."""
import subprocess
import shutil
from typing import List, Optional

from domain.ports.transcoder import Transcoder
from domain.ports.hardware_info import HardwareInfo

from domain.models.transcoding import Transcoding
from domain.constants.video import VideoCodec, SWVideoEncoder
from domain.constants.hardware import HardwareBackend
from domain.constants.audio import AudioCodec
from infrastructure.logger import Logger


class FFmpegTranscoder(Transcoder):
    """FFmpeg-based transcoder implementation for a specific video transcoding."""
    
    def __init__(self, transcoding: Transcoding, hardware_info: HardwareInfo):
        """
        Initializes the FFmpeg transcoder for a specific video transcoding.       
        
        Args:
            transcoding: Transcoding object containing all necessary information
            hardware_info: Hardware information to determine acceleration method
        """
              
        self.transcoding: Transcoding = transcoding
        self.hardware_info: HardwareInfo = hardware_info
        
        # Convert HardwareVideoAcceleration to HardwareBackend
        self.hardware_backend: HardwareBackend = HardwareBackend.from_hardware_acceleration(
            hardware_info.video_acceleration
        )
        
        # Get video encoder (already handles hardware vs software)
        self.video_encoder: str = transcoding.configuration.video_codec.encoder(
            hardware_backend=self.hardware_backend if self.hardware_backend != HardwareBackend.NONE else None
        )
        
        # Get audio encoder
        self.audio_encoder: str = transcoding.configuration.audio_codec.encoder()
   
    
    def transcode(self) -> bool:
        """
        Transcodes the video using ffmpeg with configured parameters.
        
        Returns:
            True if transcoding succeeded, False otherwise
        """
        if not shutil.which("ffmpeg"):
            return False
        
        # Build ffmpeg command using internal configuration
        cmd = self._build_ffmpeg_command()
        
        try:
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            logger = Logger.get_logger()
            error_output = e.stderr.decode('utf-8', errors='replace') if e.stderr else "No error output available"
            logger.warning(f"FFmpeg transcoding failed for {self.transcoding.original_video.path}:")
            logger.warning(error_output)
            return False
    
    def _build_ffmpeg_command(self) -> List[str]:
        """
        Builds ffmpeg command for transcoding using configuration from Transcoding object.
        
        Supports 4 modes:
        - QSV (Intel Quick Sync Video)
        - VAAPI (Video Acceleration API)
        - V4L2M2M (Video4Linux2 Memory-to-Memory for ARM)
        - Software (no hardware acceleration)
        """
        cmd = ["ffmpeg", "-hide_banner", "-y"]
        
        # Build video-specific command based on hardware backend
        if self.hardware_backend == HardwareBackend.QSV:
            cmd.extend(self._build_qsv_command())
        elif self.hardware_backend == HardwareBackend.VAAPI:
            cmd.extend(self._build_vaapi_command())
        elif self.hardware_backend == HardwareBackend.V4L2M2M:
            cmd.extend(self._build_v4l2m2m_command())
        else:
            # Software encoding
            cmd.extend(self._build_software_command())
        
        # Add audio (common for all backends)
        cmd.extend(self._build_audio_command())
        
        # Add output file
        cmd.append(self.transcoding.transcoded_video.path)
        
        return cmd
    
    def _build_qsv_command(self) -> List[str]:
        """Builds QSV-specific FFmpeg command arguments."""
        config = self.transcoding.configuration
        device_path = self.hardware_backend.device_path()
        
        cmd_parts = []
        
        # Initialize QSV hardware device
        # Format: qsv=hw:/dev/dri/renderD128 (hw: specifies hardware device)
        cmd_parts.extend(["-init_hw_device", f"qsv=hw:{device_path}"])
        cmd_parts.extend(["-filter_hw_device", "hw"])
        
        # Input file (no hwaccel before input - use software decoder, QSV encoder)
        cmd_parts.extend(["-i", self.transcoding.original_video.path])
        
        # Video filter: format conversion and hardware upload, then vpp_qsv for scaling/framerate
        vf = f"format=nv12,hwupload=extra_hw_frames=64,vpp_qsv=framerate={int(config.video_framerate)}:h={config.video_height}:w=trunc(oh*dar/2)*2,setsar=1"
        cmd_parts.extend(["-vf", vf])
        
        # Video encoder
        cmd_parts.extend(["-c:v", self.video_encoder])
        
        # Profile
        if config.video_profile:
            cmd_parts.extend(["-profile:v", config.video_profile.value])
        
        # Bitrate
        cmd_parts.extend(["-b:v", f"{config.video_bitrate}k"])
        cmd_parts.extend(["-maxrate", f"{config.video_bitrate}k"])
        
        # Common flags
        cmd_parts.extend(["-vsync", "cfr"])
        cmd_parts.extend(["-sar", "1"])
        cmd_parts.extend(["-movflags", "+faststart"])
        cmd_parts.extend(["-threads", str(self.transcoding.configuration.execution_threads)])
        
        return cmd_parts
    
    def _build_vaapi_command(self) -> List[str]:
        """Builds VAAPI-specific FFmpeg command arguments."""
        config = self.transcoding.configuration
        device_path = self.hardware_backend.device_path()
        
        cmd_parts = []
        
        cmd_parts.extend(["-vaapi_device", device_path])
        
        # Hardware acceleration
        cmd_parts.extend(["-hwaccel", "vaapi"])
        cmd_parts.extend(["-hwaccel_device", device_path])
        cmd_parts.extend(["-hwaccel_output_format", "vaapi"])
        
        # Input file
        cmd_parts.extend(["-i", self.transcoding.original_video.path])
        
        # Video filter: scale_vaapi
        cmd_parts.extend(["-vf", f"scale_vaapi=w=-2:h={config.video_height}"])
        
        # Framerate
        cmd_parts.extend(["-r", str(int(config.video_framerate))])
        
        # Video encoder
        cmd_parts.extend(["-c:v", self.video_encoder])
        
        # Profile
        if config.video_profile:
            cmd_parts.extend(["-profile:v", config.video_profile.value])
        
        # Bitrate
        cmd_parts.extend(["-b:v", f"{config.video_bitrate}k"])
        cmd_parts.extend(["-maxrate", f"{config.video_bitrate}k"])
        
        # Common flags
        cmd_parts.extend(["-vsync", "cfr"])
        cmd_parts.extend(["-sar", "1"])
        cmd_parts.extend(["-movflags", "+faststart"])
        cmd_parts.extend(["-threads", str(self.transcoding.configuration.execution_threads)])
        
        return cmd_parts
    
    def _build_v4l2m2m_command(self) -> List[str]:
        """Builds V4L2M2M-specific FFmpeg command arguments."""
        config = self.transcoding.configuration
        
        cmd_parts = []
        
        # V4L2M2M uses hardware decoder in input
        cmd_parts.extend(["-c:v", self.video_encoder])
        cmd_parts.extend(["-i", self.transcoding.original_video.path])
        
        # Video filter: software scale (no hardware scale available)
        cmd_parts.extend(["-vf", f"scale=w=-2:h={config.video_height}"])
        
        # Framerate
        cmd_parts.extend(["-r", str(int(config.video_framerate))])
        
        # Video encoder (output) with pixel format
        cmd_parts.extend(["-c:v", self.video_encoder])
        cmd_parts.extend(["-pix_fmt", "nv12"])
        
        # Bitrate
        cmd_parts.extend(["-b:v", f"{config.video_bitrate}k"])
        cmd_parts.extend(["-maxrate", f"{config.video_bitrate}k"])
        cmd_parts.extend(["-bufsize", f"{config.video_bitrate * 2}k"])
        
        # Common flags
        cmd_parts.extend(["-vsync", "cfr"])
        cmd_parts.extend(["-sar", "1"])
        
        return cmd_parts
    
    def _build_software_command(self) -> List[str]:
        """Builds software-only FFmpeg command arguments (no hardware acceleration)."""
        config = self.transcoding.configuration
        
        cmd_parts = []
        
        # Input file
        cmd_parts.extend(["-i", self.transcoding.original_video.path])
        
        # Video filter: software scale
        cmd_parts.extend(["-vf", f"scale=w=-2:h={config.video_height}"])
        
        # Framerate
        cmd_parts.extend(["-r", str(int(config.video_framerate))])
        
        # Video encoder (software)
        cmd_parts.extend(["-c:v", self.video_encoder])
        
        # Profile
        if config.video_profile:
            cmd_parts.extend(["-profile:v", config.video_profile.value])
        
        # Bitrate
        cmd_parts.extend(["-b:v", f"{config.video_bitrate}k"])
        
        # Common flags
        cmd_parts.extend(["-movflags", "+faststart"])
        
        return cmd_parts
    
    def _build_audio_command(self) -> List[str]:
        """
        Builds audio encoding command arguments (common for all backends).
        
        Returns:
            List of audio-related FFmpeg command arguments
        """
        config = self.transcoding.configuration
        cmd_parts = []
        
        cmd_parts.extend(["-c:a", self.audio_encoder])
        cmd_parts.extend(["-b:a", f"{config.audio_bitrate}k"])
        
        if config.audio_channels > 0:
            cmd_parts.extend(["-ac", str(config.audio_channels)])
        
        return cmd_parts
