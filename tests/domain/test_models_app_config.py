"""Tests for application configuration models."""
import pytest
from domain.models.app_config import (
    VideoConfig,
    AudioConfig,
    TranscodingConfig,
    PathsConfig,
    DatabaseConfig,
    LoggerConfig
)
from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.resolution import VideoResolution
from domain.constants.audio import AudioCodec, AACProfile


class TestVideoConfig:
    """Tests for VideoConfig model."""
    
    def test_create_video_config(self):
        """Test creating a VideoConfig."""
        config = VideoConfig(
            codec=VideoCodec.H264,
            bitrate=2048,
            resolution=VideoResolution.P720,
            width=1280,
            height=720,
            profile=VideoProfile.HIGH
        )
        
        assert config.codec == VideoCodec.H264
        assert config.bitrate == 2048
        assert config.resolution == VideoResolution.P720
    
    def test_dimensions_match_resolution(self):
        """Test that dimensions are corrected to match resolution."""
        config = VideoConfig(
            codec=VideoCodec.H264,
            bitrate=2048,
            resolution=VideoResolution.P720,
            width=999,  # Wrong width
            height=999,  # Wrong height
            profile=VideoProfile.HIGH
        )
        
        # Should be corrected to match resolution
        assert config.width == 1280
        assert config.height == 720
    
    def test_profile_set_to_none_for_unsupported_codec(self):
        """Test that profile is set to None for codecs that don't support profiles."""
        config = VideoConfig(
            codec=VideoCodec.VP8,  # Doesn't support profiles
            bitrate=2048,
            resolution=VideoResolution.P720,
            width=1280,
            height=720,
            profile=VideoProfile.HIGH  # Should be ignored
        )
        
        assert config.profile is None
    
    def test_profile_defaults_for_codec(self):
        """Test that profile defaults to codec's default if not provided."""
        config = VideoConfig(
            codec=VideoCodec.H264,
            bitrate=2048,
            resolution=VideoResolution.P720,
            width=1280,
            height=720,
            profile=None  # Should default to HIGH for H264
        )
        
        assert config.profile == VideoProfile.HIGH


class TestAudioConfig:
    """Tests for AudioConfig model."""
    
    def test_create_audio_config(self):
        """Test creating an AudioConfig."""
        config = AudioConfig(
            codec=AudioCodec.AAC,
            bitrate=128,
            channels=2,
            profile=AACProfile.LC
        )
        
        assert config.codec == AudioCodec.AAC
        assert config.bitrate == 128
        assert config.channels == 2
    
    def test_bitrate_validation_clamps_to_range(self):
        """Test that bitrate is clamped to valid range [64, 320]."""
        config_low = AudioConfig(codec=AudioCodec.AAC, bitrate=30, channels=2)
        assert config_low.bitrate == 64  # Clamped to minimum
        
        config_high = AudioConfig(codec=AudioCodec.AAC, bitrate=500, channels=2)
        assert config_high.bitrate == 320  # Clamped to maximum
    
    def test_channels_validation_clamps_to_range(self):
        """Test that channels are clamped to valid range [1, 8]."""
        config_low = AudioConfig(codec=AudioCodec.AAC, bitrate=128, channels=0)
        assert config_low.channels == 1  # Clamped to minimum
        
        config_high = AudioConfig(codec=AudioCodec.AAC, bitrate=128, channels=10)
        assert config_high.channels == 8  # Clamped to maximum


class TestTranscodingConfig:
    """Tests for TranscodingConfig model."""
    
    def test_create_transcoding_config(self):
        """Test creating a TranscodingConfig."""
        from domain.models.transcoding import TranscodingConfiguration
        from domain.constants.video import VideoCodec, VideoProfile
        from domain.constants.audio import AudioCodec
        from domain.constants.container import ContainerFormat
        
        config = TranscodingConfiguration(
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
            execution_threads=2
        )
        
        assert config.execution_threads == 2
        # Note: startup_delay and execution_interval are in TranscodingConfig, not TranscodingConfiguration


class TestPathsConfig:
    """Tests for PathsConfig model."""
    
    def test_create_paths_config(self):
        """Test creating a PathsConfig."""
        config = PathsConfig(
            media_path="/media",
            database_path="/data/db.sqlite"
        )
        
        assert config.media_path == "/media"
        assert config.database_path == "/data/db.sqlite"


class TestDatabaseConfig:
    """Tests for DatabaseConfig model."""
    
    def test_create_database_config(self):
        """Test creating a DatabaseConfig."""
        config = DatabaseConfig(path="/data/db.sqlite")
        
        assert config.path == "/data/db.sqlite"


class TestLoggerConfig:
    """Tests for LoggerConfig model."""
    
    def test_create_logger_config(self):
        """Test creating a LoggerConfig."""
        config = LoggerConfig(name="test-logger", level="DEBUG")
        
        assert config.name == "test-logger"
        assert config.level == "DEBUG"
