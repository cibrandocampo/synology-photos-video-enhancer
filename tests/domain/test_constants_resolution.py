"""Tests for video resolution constants."""
import pytest
from domain.constants.resolution import VideoResolution


class TestVideoResolution:
    """Tests for VideoResolution enum."""
    
    def test_from_str_valid(self):
        """Test creating VideoResolution from valid string."""
        assert VideoResolution.from_str("720p") == VideoResolution.P720
        assert VideoResolution.from_str("1080p") == VideoResolution.P1080
        assert VideoResolution.from_str("480p") == VideoResolution.P480
    
    def test_from_str_case_insensitive(self):
        """Test that from_str is case insensitive."""
        assert VideoResolution.from_str("720P") == VideoResolution.P720
        assert VideoResolution.from_str("1080P") == VideoResolution.P1080
    
    def test_from_str_invalid(self):
        """Test creating VideoResolution from invalid string defaults to P480."""
        assert VideoResolution.from_str("invalid") == VideoResolution.P480
        assert VideoResolution.from_str("") == VideoResolution.P480
    
    def test_from_str_strips_whitespace(self):
        """Test that from_str strips whitespace."""
        assert VideoResolution.from_str("  720p  ") == VideoResolution.P720
    
    def test_width_property(self):
        """Test width property for all resolutions."""
        assert VideoResolution.P144.width == 256
        assert VideoResolution.P240.width == 426
        assert VideoResolution.P360.width == 640
        assert VideoResolution.P480.width == 854
        assert VideoResolution.P720.width == 1280
        assert VideoResolution.P1080.width == 1920
        assert VideoResolution.P1440.width == 2560
        assert VideoResolution.P2160.width == 3840
    
    def test_height_property(self):
        """Test height property for all resolutions."""
        assert VideoResolution.P144.height == 144
        assert VideoResolution.P240.height == 240
        assert VideoResolution.P360.height == 360
        assert VideoResolution.P480.height == 480
        assert VideoResolution.P720.height == 720
        assert VideoResolution.P1080.height == 1080
        assert VideoResolution.P1440.height == 1440
        assert VideoResolution.P2160.height == 2160
    
    def test_name_property(self):
        """Test name property returns the value."""
        assert VideoResolution.P720.name == "720p"
        assert VideoResolution.P1080.name == "1080p"
