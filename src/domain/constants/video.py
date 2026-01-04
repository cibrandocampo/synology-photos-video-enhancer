"""Video-related constants and enums."""
from enum import Enum
from typing import List, Optional, TYPE_CHECKING
from domain.constants.hardware import HardwareBackend

class VideoCodec(str, Enum):
    """Supported video codecs."""
    H264 = "h264"
    HEVC = "hevc"
    MPEG4 = "mpeg4"
    MPEG2VIDEO = "mpeg2video"
    VP8 = "vp8"
    VP9 = "vp9"
    AV1 = "av1"
    
    @classmethod
    def from_str(cls, value: str) -> "VideoCodec":
        """
        Creates a VideoCodec from a string value.
        
        Args:
            value: Codec name (case insensitive)
            
        Returns:
            VideoCodec enum value (defaults to H264 if invalid or empty)
        """
        if not value:
            return cls.H264
        try:
            return cls(value.lower())
        except ValueError:
            return cls.H264
    
    def supported_profiles(self) -> List["VideoProfile"]:
        """
        Gets the supported profiles for this codec.
        
        Returns:
            List of VideoProfile enum values. Returns empty list if codec doesn't support profiles.
        """
        # VideoProfile is defined later in this file, so we can reference it directly
        valid_profiles = {
            VideoCodec.H264: [VideoProfile.BASELINE, VideoProfile.MAIN, VideoProfile.HIGH],
            VideoCodec.HEVC: [VideoProfile.MAIN, VideoProfile.MAIN10],
            VideoCodec.MPEG2VIDEO: [VideoProfile.SIMPLE, VideoProfile.MAIN, VideoProfile.HIGH],
            VideoCodec.MPEG4: [VideoProfile.SIMPLE, VideoProfile.ADVANCED_SIMPLE],
        }
        
        return valid_profiles.get(self, [])
    
    def supports_profile(self) -> bool:
        """
        Checks if this codec supports video profiles.
        
        Returns:
            True if the codec supports profiles (H264, HEVC, MPEG2VIDEO, MPEG4)
        """
        return len(self.supported_profiles()) > 0
    
    def encoder(self, hardware_backend: Optional["HardwareBackend"] = None) -> str:
        """
        Gets the encoder name for this codec, with optional hardware acceleration.
               
        Args:
            hardware_backend: Optional hardware acceleration backend
            
        Returns:
            Encoder name string (e.g., 'libx264', 'h264_vaapi', 'h264_qsv')
        """
        
        if hardware_backend and hardware_backend != HardwareBackend.NONE:
            hw_encoder = HWVideoEncoder.get_encoder(self, hardware_backend)
            if hw_encoder:
                return hw_encoder.value
        
        # Software encoder (fallback or no hardware acceleration)
        encoder_map = {
            VideoCodec.H264: SWVideoEncoder.H264,
            VideoCodec.HEVC: SWVideoEncoder.HEVC,
            VideoCodec.MPEG4: SWVideoEncoder.MPEG4,
            VideoCodec.MPEG2VIDEO: SWVideoEncoder.MPEG2VIDEO,
            VideoCodec.VP8: SWVideoEncoder.VP8,
            VideoCodec.VP9: SWVideoEncoder.VP9,
            VideoCodec.AV1: SWVideoEncoder.AV1,
        }
        encoder = encoder_map.get(self, SWVideoEncoder.H264)  # Default to H264
        return encoder.value


class SWVideoEncoder(Enum):
    """Software video encoders for FFmpeg."""
    H264 = "libx264"
    HEVC = "libx265"
    MPEG4 = "mpeg4"
    MPEG2VIDEO = "mpeg2video"
    VP8 = "libvpx"
    VP9 = "libvpx-vp9"
    AV1 = "libaom-av1"


class HWVideoEncoder(str, Enum):
    """Hardware-accelerated video encoders for FFmpeg."""
    # H264 hardware encoders
    H264_QSV = "h264_qsv"
    H264_VAAPI = "h264_vaapi"
    H264_V4L2M2M = "h264_v4l2m2m"
    
    # HEVC hardware encoders
    HEVC_QSV = "hevc_qsv"
    HEVC_VAAPI = "hevc_vaapi"
    HEVC_V4L2M2M = "hevc_v4l2m2m"
    
    # MPEG2VIDEO hardware encoders
    MPEG2VIDEO_QSV = "mpeg2video_qsv"
    MPEG2VIDEO_VAAPI = "mpeg2video_vaapi"
    MPEG2VIDEO_V4L2M2M = "mpeg2video_v4l2m2m"
    
    @classmethod
    def get_encoder(
        cls,
        codec: "VideoCodec",
        hardware_backend: HardwareBackend
    ) -> Optional["HWVideoEncoder"]:
        """
        Gets the hardware-accelerated encoder for a codec and backend.
        
        Only H264, HEVC, and MPEG2VIDEO support hardware acceleration.
        
        Args:
            codec: Video codec
            hardware_backend: Hardware acceleration backend
            
        Returns:
            HWVideoEncoder enum value or None if not supported
        """
        if hardware_backend == HardwareBackend.NONE:
            return None
        
        # Import here to avoid circular dependencies
        from domain.constants.video import VideoCodec
        
        # Only these codecs support hardware acceleration
        if codec not in {VideoCodec.H264, VideoCodec.HEVC, VideoCodec.MPEG2VIDEO}:
            return None
        
        # Use the mapping dictionary
        hw_encoder_map = {
            VideoCodec.H264: {
                HardwareBackend.QSV: cls.H264_QSV,
                HardwareBackend.VAAPI: cls.H264_VAAPI,
                HardwareBackend.V4L2M2M: cls.H264_V4L2M2M,
            },
            VideoCodec.HEVC: {
                HardwareBackend.QSV: cls.HEVC_QSV,
                HardwareBackend.VAAPI: cls.HEVC_VAAPI,
                HardwareBackend.V4L2M2M: cls.HEVC_V4L2M2M,
            },
            VideoCodec.MPEG2VIDEO: {
                HardwareBackend.QSV: cls.MPEG2VIDEO_QSV,
                HardwareBackend.VAAPI: cls.MPEG2VIDEO_VAAPI,
                HardwareBackend.V4L2M2M: cls.MPEG2VIDEO_V4L2M2M,
            },
        }
        
        return hw_encoder_map.get(codec, {}).get(hardware_backend)


class VideoProfile(str, Enum):
    """Supported video profiles for specific codecs."""
    # H264 profiles
    BASELINE = "baseline"
    MAIN = "main"
    HIGH = "high"
    # HEVC profiles
    MAIN10 = "main10"
    # MPEG2VIDEO profiles
    SIMPLE = "simple"
    # MPEG4 profiles
    ADVANCED_SIMPLE = "advanced-simple"
    
    @classmethod
    def from_str(cls, value: str, codec: "VideoCodec") -> "VideoProfile":
        """
        Creates a VideoProfile from a string value, validating it against the codec.
        
        Args:
            value: Profile name (case insensitive)
            codec: Video codec to validate against
            
        Returns:
            VideoProfile enum value (defaults to codec's default profile if invalid)
        """
        if not value:
            return cls.get_default(codec)
        
        value_lower = value.lower().strip()
        
        # Map of codec -> valid profiles
        valid_profiles = {
            VideoCodec.H264: [VideoProfile.BASELINE, VideoProfile.MAIN, VideoProfile.HIGH],
            VideoCodec.HEVC: [VideoProfile.MAIN, VideoProfile.MAIN10],
            VideoCodec.MPEG2VIDEO: [VideoProfile.SIMPLE, VideoProfile.MAIN, VideoProfile.HIGH],
            VideoCodec.MPEG4: [VideoProfile.SIMPLE, VideoProfile.ADVANCED_SIMPLE],
        }
        
        # If codec doesn't support profiles, return None (will be handled by VideoConfig)
        if codec not in valid_profiles:
            return cls.get_default(codec)
        
        # Try to find matching profile
        try:
            profile = cls(value_lower)
            # Validate it's valid for this codec
            if profile in valid_profiles[codec]:
                return profile
        except ValueError:
            pass
        
        # Invalid profile, return default
        return cls.get_default(codec)
    
    @classmethod
    def get_default(cls, codec: "VideoCodec") -> "VideoProfile":
        """
        Gets the default video profile for a codec.
        
        Args:
            codec: Video codec
            
        Returns:
            Default VideoProfile for the codec, or HIGH if codec doesn't support profiles
        """
        defaults = {
            VideoCodec.MPEG2VIDEO: cls.MAIN,
            VideoCodec.MPEG4: cls.SIMPLE,
            VideoCodec.H264: cls.HIGH,
            VideoCodec.HEVC: cls.MAIN,
        }
        return defaults.get(codec, cls.HIGH)
