"""Tests for FFmpeg codecs utilities."""
import pytest
from unittest.mock import patch, Mock
from infrastructure.transcoder.ffmpeg_codecs import (
    get_available_hw_codecs,
    get_available_hwaccels,
    has_codec
)


class TestGetAvailableHwCodecs:
    """Tests for get_available_hw_codecs function."""
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.shutil.which')
    def test_ffmpeg_not_found(self, mock_which):
        """Test returns empty list when ffmpeg is not found."""
        mock_which.return_value = None
        
        codecs = get_available_hw_codecs()
        
        assert codecs == []
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.subprocess.run')
    @patch('infrastructure.transcoder.ffmpeg_codecs.shutil.which')
    def test_returns_hardware_codecs(self, mock_which, mock_subprocess):
        """Test returns list of hardware codecs."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        # Mock FFmpeg output with hardware codecs
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
 V..... h264_qsv           Intel QSV H.264 encoder
 V..... h264_vaapi         H.264 VAAPI encoder
 V..... hevc_qsv           Intel QSV HEVC encoder
 V..... libx264            H.264 encoder
        """
        mock_subprocess.return_value = mock_result
        
        codecs = get_available_hw_codecs()
        
        assert "h264_qsv" in codecs
        assert "h264_vaapi" in codecs
        assert "hevc_qsv" in codecs
        assert "libx264" not in codecs  # Software codec, not hardware
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.subprocess.run')
    @patch('infrastructure.transcoder.ffmpeg_codecs.shutil.which')
    def test_handles_subprocess_error(self, mock_which, mock_subprocess):
        """Test handles subprocess errors gracefully."""
        import subprocess
        
        mock_which.return_value = "/usr/bin/ffmpeg"
        mock_subprocess.side_effect = subprocess.TimeoutExpired("ffmpeg", 5)
        
        codecs = get_available_hw_codecs()
        
        assert codecs == []
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.subprocess.run')
    @patch('infrastructure.transcoder.ffmpeg_codecs.shutil.which')
    def test_handles_non_zero_returncode(self, mock_which, mock_subprocess):
        """Test handles non-zero return code."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result
        
        codecs = get_available_hw_codecs()
        
        assert codecs == []


class TestGetAvailableHwaccels:
    """Tests for get_available_hwaccels function."""
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.shutil.which')
    def test_ffmpeg_not_found(self, mock_which):
        """Test returns empty list when ffmpeg is not found."""
        mock_which.return_value = None
        
        hwaccels = get_available_hwaccels()
        
        assert hwaccels == []
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.subprocess.run')
    @patch('infrastructure.transcoder.ffmpeg_codecs.shutil.which')
    def test_returns_hwaccels(self, mock_which, mock_subprocess):
        """Test returns list of hardware acceleration methods."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
Hardware acceleration methods:
qsv
vaapi
v4l2m2m
        """
        mock_subprocess.return_value = mock_result
        
        hwaccels = get_available_hwaccels()
        
        assert "qsv" in hwaccels
        assert "vaapi" in hwaccels
        assert "v4l2m2m" in hwaccels
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.subprocess.run')
    @patch('infrastructure.transcoder.ffmpeg_codecs.shutil.which')
    def test_filters_header_line(self, mock_which, mock_subprocess):
        """Test filters out header line."""
        mock_which.return_value = "/usr/bin/ffmpeg"
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = """
Hardware acceleration methods:
qsv
        """
        mock_subprocess.return_value = mock_result
        
        hwaccels = get_available_hwaccels()
        
        assert "Hardware acceleration methods:" not in hwaccels
        assert "qsv" in hwaccels


class TestHasCodec:
    """Tests for has_codec function."""
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.get_available_hw_codecs')
    def test_has_codec_true(self, mock_get_codecs):
        """Test has_codec returns True when codec is available."""
        mock_get_codecs.return_value = ["h264_qsv", "h264_vaapi"]
        
        assert has_codec("h264_qsv") is True
    
    @patch('infrastructure.transcoder.ffmpeg_codecs.get_available_hw_codecs')
    def test_has_codec_false(self, mock_get_codecs):
        """Test has_codec returns False when codec is not available."""
        mock_get_codecs.return_value = ["h264_qsv", "h264_vaapi"]
        
        assert has_codec("h264_nvenc") is False
