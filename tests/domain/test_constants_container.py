"""Tests for container format constants."""
import pytest
from domain.constants.container import ContainerFormat, get_video_extensions


class TestContainerFormat:
    """Tests for ContainerFormat enum."""
    
    def test_from_str_valid(self):
        """Test creating ContainerFormat from valid string."""
        assert ContainerFormat.from_str("mp4") == ContainerFormat.MP4
        assert ContainerFormat.from_str("mkv") == ContainerFormat.MKV
        assert ContainerFormat.from_str("avi") == ContainerFormat.AVI
    
    def test_from_str_case_insensitive(self):
        """Test that from_str is case insensitive."""
        assert ContainerFormat.from_str("MP4") == ContainerFormat.MP4
        assert ContainerFormat.from_str("MkV") == ContainerFormat.MKV
    
    def test_from_str_invalid(self):
        """Test creating ContainerFormat from invalid string defaults to MP4."""
        assert ContainerFormat.from_str("invalid") == ContainerFormat.MP4
        assert ContainerFormat.from_str("") == ContainerFormat.MP4
    
    def test_from_str_strips_whitespace(self):
        """Test that from_str strips whitespace."""
        assert ContainerFormat.from_str("  mp4  ") == ContainerFormat.MP4
    
    def test_all_formats(self):
        """Test that all container formats are accessible."""
        assert ContainerFormat.MP4.value == "mp4"
        assert ContainerFormat.MOV.value == "mov"
        assert ContainerFormat.MKV.value == "mkv"
        assert ContainerFormat.AVI.value == "avi"
        assert ContainerFormat.THREE_GP.value == "3gp"


class TestGetVideoExtensions:
    """Tests for get_video_extensions function."""
    
    def test_returns_list(self):
        """Test that get_video_extensions returns a list."""
        extensions = get_video_extensions()
        assert isinstance(extensions, list)
    
    def test_returns_sorted(self):
        """Test that extensions are sorted."""
        extensions = get_video_extensions()
        assert extensions == sorted(extensions)
    
    def test_includes_lowercase_and_uppercase(self):
        """Test that extensions include both lowercase and uppercase."""
        extensions = get_video_extensions()
        assert "mp4" in extensions
        assert "MP4" in extensions
        assert "mkv" in extensions
        assert "MKV" in extensions
    
    def test_includes_all_formats(self):
        """Test that all container formats are included."""
        extensions = get_video_extensions()
        for container in ContainerFormat:
            assert container.value.lower() in extensions
            assert container.value.upper() in extensions
    
    def test_no_duplicates(self):
        """Test that there are no duplicate extensions."""
        extensions = get_video_extensions()
        assert len(extensions) == len(set(extensions))
