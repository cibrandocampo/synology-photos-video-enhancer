"""Tests for video-related constants."""
import pytest
from domain.constants.video import VideoCodec, VideoProfile, SWVideoEncoder, HWVideoEncoder
from domain.constants.hardware import HardwareBackend


class TestVideoCodec:
    """Tests for VideoCodec enum."""
    
    def test_from_str_valid(self):
        """Test creating VideoCodec from valid string."""
        assert VideoCodec.from_str("h264") == VideoCodec.H264
        assert VideoCodec.from_str("HEVC") == VideoCodec.HEVC
        assert VideoCodec.from_str("mpeg4") == VideoCodec.MPEG4
    
    def test_from_str_invalid(self):
        """Test creating VideoCodec from invalid string defaults to H264."""
        assert VideoCodec.from_str("invalid") == VideoCodec.H264
        assert VideoCodec.from_str("") == VideoCodec.H264
    
    def test_from_str_case_insensitive(self):
        """Test that from_str is case insensitive."""
        assert VideoCodec.from_str("H264") == VideoCodec.H264
        assert VideoCodec.from_str("HeVc") == VideoCodec.HEVC
    
    def test_supported_profiles_h264(self):
        """Test that H264 returns correct supported profiles."""
        profiles = VideoCodec.H264.supported_profiles()
        assert VideoProfile.BASELINE in profiles
        assert VideoProfile.MAIN in profiles
        assert VideoProfile.HIGH in profiles
    
    def test_supported_profiles_hevc(self):
        """Test that HEVC returns correct supported profiles."""
        profiles = VideoCodec.HEVC.supported_profiles()
        assert VideoProfile.MAIN in profiles
        assert VideoProfile.MAIN10 in profiles
    
    def test_supported_profiles_no_profiles(self):
        """Test that codecs without profiles return empty list."""
        assert VideoCodec.VP8.supported_profiles() == []
        assert VideoCodec.VP9.supported_profiles() == []
        assert VideoCodec.AV1.supported_profiles() == []
    
    def test_supports_profile(self):
        """Test supports_profile method."""
        assert VideoCodec.H264.supports_profile() is True
        assert VideoCodec.HEVC.supports_profile() is True
        assert VideoCodec.VP8.supports_profile() is False
        assert VideoCodec.VP9.supports_profile() is False
    
    def test_encoder_software(self):
        """Test encoder method returns software encoder when no hardware backend."""
        encoder = VideoCodec.H264.encoder()
        assert encoder == SWVideoEncoder.H264.value
    
    def test_encoder_hardware(self):
        """Test encoder method returns hardware encoder when hardware backend provided."""
        encoder = VideoCodec.H264.encoder(hardware_backend=HardwareBackend.VAAPI)
        assert encoder == HWVideoEncoder.H264_VAAPI.value
    
    def test_encoder_hardware_none_backend(self):
        """Test encoder method returns software encoder when NONE backend."""
        encoder = VideoCodec.H264.encoder(hardware_backend=HardwareBackend.NONE)
        assert encoder == SWVideoEncoder.H264.value


class TestVideoProfile:
    """Tests for VideoProfile enum."""
    
    def test_from_str_valid(self):
        """Test creating VideoProfile from valid string."""
        assert VideoProfile.from_str("high", VideoCodec.H264) == VideoProfile.HIGH
        assert VideoProfile.from_str("main", VideoCodec.H264) == VideoProfile.MAIN
    
    def test_from_str_invalid_codec(self):
        """Test that invalid profile for codec returns default."""
        # VP8 doesn't support profiles
        profile = VideoProfile.from_str("high", VideoCodec.VP8)
        assert profile == VideoProfile.get_default(VideoCodec.VP8)
    
    def test_get_default(self):
        """Test get_default returns correct default profile for codec."""
        assert VideoProfile.get_default(VideoCodec.H264) == VideoProfile.HIGH
        assert VideoProfile.get_default(VideoCodec.HEVC) == VideoProfile.MAIN
        assert VideoProfile.get_default(VideoCodec.MPEG2VIDEO) == VideoProfile.MAIN
        assert VideoProfile.get_default(VideoCodec.MPEG4) == VideoProfile.SIMPLE
        assert VideoProfile.get_default(VideoCodec.VP8) == VideoProfile.HIGH  # Default fallback
    
    def test_from_str_valid_profile_for_codec(self):
        """Test from_str with valid profile for specific codec."""
        assert VideoProfile.from_str("baseline", VideoCodec.H264) == VideoProfile.BASELINE
        assert VideoProfile.from_str("main10", VideoCodec.HEVC) == VideoProfile.MAIN10
        assert VideoProfile.from_str("simple", VideoCodec.MPEG2VIDEO) == VideoProfile.SIMPLE
    
    def test_from_str_invalid_profile_for_codec(self):
        """Test from_str with invalid profile for codec returns default."""
        # MAIN10 is not valid for H264
        profile = VideoProfile.from_str("main10", VideoCodec.H264)
        assert profile == VideoProfile.get_default(VideoCodec.H264)
    
    def test_from_str_empty_returns_default(self):
        """Test from_str with empty string returns default."""
        assert VideoProfile.from_str("", VideoCodec.H264) == VideoProfile.get_default(VideoCodec.H264)
        assert VideoProfile.from_str("   ", VideoCodec.HEVC) == VideoProfile.get_default(VideoCodec.HEVC)


class TestSWVideoEncoder:
    """Tests for SWVideoEncoder enum."""
    
    def test_encoder_values(self):
        """Test that encoder values are correct."""
        assert SWVideoEncoder.H264.value == "libx264"
        assert SWVideoEncoder.HEVC.value == "libx265"
        assert SWVideoEncoder.AV1.value == "libaom-av1"


class TestHWVideoEncoder:
    """Tests for HWVideoEncoder enum."""
    
    def test_get_encoder_h264_qsv(self):
        """Test getting H264 QSV encoder."""
        encoder = HWVideoEncoder.get_encoder(VideoCodec.H264, HardwareBackend.QSV)
        assert encoder == HWVideoEncoder.H264_QSV
    
    def test_get_encoder_hevc_vaapi(self):
        """Test getting HEVC VAAPI encoder."""
        encoder = HWVideoEncoder.get_encoder(VideoCodec.HEVC, HardwareBackend.VAAPI)
        assert encoder == HWVideoEncoder.HEVC_VAAPI
    
    def test_get_encoder_none_backend(self):
        """Test that NONE backend returns None."""
        encoder = HWVideoEncoder.get_encoder(VideoCodec.H264, HardwareBackend.NONE)
        assert encoder is None
    
    def test_get_encoder_unsupported_codec(self):
        """Test that unsupported codec returns None."""
        encoder = HWVideoEncoder.get_encoder(VideoCodec.VP8, HardwareBackend.VAAPI)
        assert encoder is None
    
    def test_encoder_all_codecs_software(self):
        """Test encoder method for all codecs without hardware."""
        assert VideoCodec.MPEG4.encoder() == SWVideoEncoder.MPEG4.value
        assert VideoCodec.MPEG2VIDEO.encoder() == SWVideoEncoder.MPEG2VIDEO.value
        assert VideoCodec.VP8.encoder() == SWVideoEncoder.VP8.value
        assert VideoCodec.VP9.encoder() == SWVideoEncoder.VP9.value
        assert VideoCodec.AV1.encoder() == SWVideoEncoder.AV1.value
    
    def test_encoder_hardware_all_backends_h264(self):
        """Test H264 encoder with all hardware backends."""
        assert VideoCodec.H264.encoder(HardwareBackend.QSV) == HWVideoEncoder.H264_QSV.value
        assert VideoCodec.H264.encoder(HardwareBackend.VAAPI) == HWVideoEncoder.H264_VAAPI.value
        assert VideoCodec.H264.encoder(HardwareBackend.V4L2M2M) == HWVideoEncoder.H264_V4L2M2M.value
    
    def test_encoder_hardware_all_backends_hevc(self):
        """Test HEVC encoder with all hardware backends."""
        assert VideoCodec.HEVC.encoder(HardwareBackend.QSV) == HWVideoEncoder.HEVC_QSV.value
        assert VideoCodec.HEVC.encoder(HardwareBackend.VAAPI) == HWVideoEncoder.HEVC_VAAPI.value
        assert VideoCodec.HEVC.encoder(HardwareBackend.V4L2M2M) == HWVideoEncoder.HEVC_V4L2M2M.value
    
    def test_encoder_hardware_mpeg2video(self):
        """Test MPEG2VIDEO encoder with hardware backends."""
        assert VideoCodec.MPEG2VIDEO.encoder(HardwareBackend.QSV) == HWVideoEncoder.MPEG2VIDEO_QSV.value
        assert VideoCodec.MPEG2VIDEO.encoder(HardwareBackend.VAAPI) == HWVideoEncoder.MPEG2VIDEO_VAAPI.value
    
    def test_supported_profiles_mpeg2video(self):
        """Test that MPEG2VIDEO returns correct supported profiles."""
        profiles = VideoCodec.MPEG2VIDEO.supported_profiles()
        assert VideoProfile.SIMPLE in profiles
        assert VideoProfile.MAIN in profiles
        assert VideoProfile.HIGH in profiles
    
    def test_supported_profiles_mpeg4(self):
        """Test that MPEG4 returns correct supported profiles."""
        profiles = VideoCodec.MPEG4.supported_profiles()
        assert VideoProfile.SIMPLE in profiles
        assert VideoProfile.ADVANCED_SIMPLE in profiles
