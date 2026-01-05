"""Tests for frame rate constants."""
import pytest
from fractions import Fraction
from domain.constants.framerate import FrameRate


class TestFrameRate:
    """Tests for FrameRate enum."""
    
    def test_to_float(self):
        """Test to_float method converts Fraction to float."""
        assert FrameRate.FPS_30.to_float() == 30.0
        assert FrameRate.FPS_24.to_float() == 24.0
        assert abs(FrameRate.FPS_29_97.to_float() - 29.97) < 0.01
        assert abs(FrameRate.FPS_23_976.to_float() - 23.976) < 0.01
    
    def test_from_int_exact_match(self):
        """Test from_int with exact matches."""
        assert FrameRate.from_int(30) == FrameRate.FPS_30
        assert FrameRate.from_int(24) == FrameRate.FPS_24
        assert FrameRate.from_int(60) == FrameRate.FPS_60
    
    def test_from_int_closest_match(self):
        """Test from_int finds closest match."""
        assert FrameRate.from_int(29) == FrameRate.FPS_29_97  # Closer to 29.97 than 30
        assert FrameRate.from_int(25) == FrameRate.FPS_25
        assert FrameRate.from_int(50) == FrameRate.FPS_50
    
    def test_from_int_zero_or_negative(self):
        """Test from_int with zero or negative returns default."""
        assert FrameRate.from_int(0) == FrameRate.FPS_30
        assert FrameRate.from_int(-1) == FrameRate.FPS_30
    
    def test_from_int_high_framerate(self):
        """Test from_int with high framerates."""
        assert FrameRate.from_int(120) == FrameRate.FPS_120
        assert FrameRate.from_int(144) == FrameRate.FPS_144
        assert FrameRate.from_int(240) == FrameRate.FPS_240
    
    def test_get_framerate_for_light_videos_fps_50(self):
        """Test get_framerate_for_light_videos converts FPS_50 to FPS_25."""
        result = FrameRate.get_framerate_for_light_videos(FrameRate.FPS_50)
        assert result == FrameRate.FPS_25
    
    def test_get_framerate_for_light_videos_fps_59_94(self):
        """Test get_framerate_for_light_videos converts FPS_59_94 to FPS_29_97."""
        result = FrameRate.get_framerate_for_light_videos(FrameRate.FPS_59_94)
        assert result == FrameRate.FPS_29_97
    
    def test_get_framerate_for_light_videos_fps_60(self):
        """Test get_framerate_for_light_videos converts FPS_60 to FPS_30."""
        result = FrameRate.get_framerate_for_light_videos(FrameRate.FPS_60)
        assert result == FrameRate.FPS_30
    
    def test_get_framerate_for_light_videos_fps_120(self):
        """Test get_framerate_for_light_videos converts FPS_120 to FPS_30."""
        result = FrameRate.get_framerate_for_light_videos(FrameRate.FPS_120)
        assert result == FrameRate.FPS_30
    
    def test_get_framerate_for_light_videos_fps_144(self):
        """Test get_framerate_for_light_videos converts FPS_144 to FPS_24."""
        result = FrameRate.get_framerate_for_light_videos(FrameRate.FPS_144)
        assert result == FrameRate.FPS_24
    
    def test_get_framerate_for_light_videos_fps_240(self):
        """Test get_framerate_for_light_videos converts FPS_240 to FPS_30."""
        result = FrameRate.get_framerate_for_light_videos(FrameRate.FPS_240)
        assert result == FrameRate.FPS_30
    
    def test_get_framerate_for_light_videos_no_conversion(self):
        """Test get_framerate_for_light_videos returns same for non-convertible rates."""
        assert FrameRate.get_framerate_for_light_videos(FrameRate.FPS_30) == FrameRate.FPS_30
        assert FrameRate.get_framerate_for_light_videos(FrameRate.FPS_24) == FrameRate.FPS_24
        assert FrameRate.get_framerate_for_light_videos(FrameRate.FPS_25) == FrameRate.FPS_25
