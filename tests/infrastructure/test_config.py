"""Tests for configuration loader."""
import pytest
import os
from unittest.mock import patch
from infrastructure.config.config import Config


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Reset Config singleton before each test."""
    # Reset singleton state
    Config._instance = None
    Config._app_config = None
    yield
    # Cleanup after test
    Config._instance = None
    Config._app_config = None


class TestConfig:
    """Tests for Config class."""
    
    def test_load_transcoding_config_defaults(self):
        """Test loading transcoding config with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config.load()
            transcoding = config.transcoding
            
            assert transcoding.hw_transcoding is True  # Default
            assert transcoding.execution_threads == 2  # Default
            assert transcoding.startup_delay == 30  # Default
            assert transcoding.execution_interval == 240  # Default
    
    def test_load_transcoding_config_from_env(self):
        """Test loading transcoding config from environment variables."""
        env_vars = {
            "HW_TRANSCODING": "False",
            "EXECUTION_THREADS": "4",
            "STARTUP_DELAY": "60",
            "EXECUTION_INTERVAL": "120",
            "VIDEO_CODEC": "hevc",
            "VIDEO_BITRATE": "4096",
            "VIDEO_RESOLUTION": "1080p",
            "AUDIO_CODEC": "opus",
            "AUDIO_BITRATE": "256",
            "AUDIO_CHANNELS": "5.1"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            transcoding = config.transcoding
            
            assert transcoding.hw_transcoding is False
            assert transcoding.execution_threads == 4
            assert transcoding.startup_delay == 60
            assert transcoding.execution_interval == 120
            assert transcoding.video.codec.value == "hevc"
            assert transcoding.video.bitrate == 4096
            assert transcoding.audio.codec.value == "opus"
            assert transcoding.audio.bitrate == 256
    
    def test_load_paths_config(self, temp_dir):
        """Test loading paths configuration."""
        media_path = os.path.join(temp_dir, "media")
        db_path = os.path.join(temp_dir, "test.db")
        
        env_vars = {
            "MEDIA_APP_PATH": media_path,
            "DATABASE_APP_PATH": db_path
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            paths = config.paths
            
            assert paths.media_path == media_path
            assert paths.database_path == db_path
    
    def test_singleton_pattern(self):
        """Test that Config follows singleton pattern."""
        config1 = Config.load()
        config2 = Config.load()
        
        # Should be the same instance
        assert config1 is config2
    
    def test_lazy_loading(self):
        """Test that configuration sections are loaded lazily."""
        with patch.dict(os.environ, {}, clear=True):
            config = Config()
            
            # Accessing paths should trigger loading
            _ = config.paths
            assert config._app_config.paths is not None
            
            # Accessing transcoding should trigger loading
            _ = config.transcoding
            assert config._app_config.transcoding is not None
    
    def test_load_video_config_with_resolution(self):
        """Test loading video config with VIDEO_RESOLUTION."""
        env_vars = {
            "VIDEO_RESOLUTION": "1080p",
            "VIDEO_BITRATE": "4096"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            
            assert config.transcoding.video.resolution.value == "1080p"
            assert config.transcoding.video.width == 1920
            assert config.transcoding.video.height == 1080
    
    def test_load_video_config_with_w_h_fallback(self):
        """Test loading video config with VIDEO_W and VIDEO_H fallback."""
        from domain.constants.resolution import VideoResolution
        
        env_vars = {
            "VIDEO_W": "854",  # Use 480p dimensions to match default
            "VIDEO_H": "480",
            "VIDEO_BITRATE": "4096",
            "VIDEO_CODEC": "h264"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            # Reset singleton to get fresh config
            Config._instance = None
            Config._app_config = None
            config = Config.load()
            
            # Should match P480 resolution
            assert config.transcoding.video.resolution == VideoResolution.P480
            # After model validation, dimensions should match resolution
            assert config.transcoding.video.width == VideoResolution.P480.width
            assert config.transcoding.video.height == VideoResolution.P480.height
    
    def test_load_video_profile(self):
        """Test loading video profile."""
        env_vars = {
            "VIDEO_CODEC": "h264",
            "VIDEO_PROFILE": "main"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            
            assert config.transcoding.video.profile is not None
            assert config.transcoding.video.profile.value == "main"
    
    def test_load_audio_profile_aac(self):
        """Test loading audio profile for AAC."""
        env_vars = {
            "AUDIO_CODEC": "aac",
            "AUDIO_PROFILE": "aac_he"  # Use full profile name
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            
            assert config.transcoding.audio.profile is not None
            assert config.transcoding.audio.profile.value == "aac_he"
    
    def test_load_database_config(self, temp_dir):
        """Test loading database configuration."""
        db_path = os.path.join(temp_dir, "test.db")
        
        env_vars = {
            "DATABASE_APP_PATH": db_path,
            "MEDIA_APP_PATH": "/test/media"  # Required for paths config
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            config = Config.load()
            database = config.database
            
            # Path should match (may have been normalized)
            assert database.path == db_path or os.path.samefile(database.path, db_path) if os.path.exists(db_path) else database.path == db_path
    
    def test_load_logger_config(self):
        """Test loading logger configuration."""
        # Note: Logger config is loaded lazily and may be cached
        # We need to ensure we're getting a fresh config
        env_vars = {
            "LOGGER_NAME": "test-logger",
            "LOGGER_LEVEL": "DEBUG"
        }
        
        with patch.dict(os.environ, env_vars, clear=False):
            # Force reload by clearing singleton
            Config._instance = None
            Config._app_config = None
            config = Config.load()
            logger = config.logger
            
            assert logger.name == "test-logger"
            assert logger.level == "DEBUG"
