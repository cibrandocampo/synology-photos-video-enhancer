"""Tests for local filesystem."""
import pytest
import os
import tempfile
from pathlib import Path
from infrastructure.filesystem.local_filesystem import LocalFilesystem


class TestLocalFilesystem:
    """Tests for LocalFilesystem."""
    
    @pytest.fixture
    def filesystem(self):
        """Creates a LocalFilesystem instance."""
        return LocalFilesystem(["mp4", "avi", "mkv"])
    
    def test_init_sets_video_extensions(self, filesystem):
        """Test that __init__ sets video extensions."""
        assert filesystem.video_extensions == ["mp4", "avi", "mkv"]
    
    def test_find_videos_empty_directory(self, filesystem, temp_dir):
        """Test find_videos returns empty list for empty directory."""
        videos = filesystem.find_videos(temp_dir)
        assert videos == []
    
    def test_find_videos_nonexistent_directory(self, filesystem):
        """Test find_videos returns empty list for nonexistent directory."""
        videos = filesystem.find_videos("/nonexistent/path")
        assert videos == []
    
    def test_find_videos_with_files(self, filesystem, temp_dir):
        """Test find_videos finds video files."""
        # Create test video files
        video1 = os.path.join(temp_dir, "video1.mp4")
        video2 = os.path.join(temp_dir, "video2.avi")
        non_video = os.path.join(temp_dir, "document.txt")
        
        Path(video1).touch()
        Path(video2).touch()
        Path(non_video).touch()
        
        videos = filesystem.find_videos(temp_dir)
        
        assert len(videos) == 2
        assert video1 in videos
        assert video2 in videos
        assert non_video not in videos
    
    def test_find_videos_filters_eadir(self, filesystem, temp_dir):
        """Test find_videos filters out @eaDir directories."""
        # Create video in @eaDir
        eadir = os.path.join(temp_dir, "@eaDir", "video.mp4")
        Path(eadir).parent.mkdir(parents=True, exist_ok=True)
        Path(eadir).touch()
        
        # Create normal video
        normal_video = os.path.join(temp_dir, "normal.mp4")
        Path(normal_video).touch()
        
        videos = filesystem.find_videos(temp_dir)
        
        assert normal_video in videos
        assert eadir not in videos
    
    def test_find_videos_filters_recycle(self, filesystem, temp_dir):
        """Test find_videos filters out #recycle directories."""
        # Create video in #recycle
        recycle = os.path.join(temp_dir, "#recycle", "video.mp4")
        Path(recycle).parent.mkdir(parents=True, exist_ok=True)
        Path(recycle).touch()
        
        videos = filesystem.find_videos(temp_dir)
        
        assert recycle not in videos
    
    def test_file_exists_true(self, filesystem, temp_dir):
        """Test file_exists returns True for existing file."""
        test_file = os.path.join(temp_dir, "test.mp4")
        Path(test_file).touch()
        
        assert filesystem.file_exists(test_file) is True
    
    def test_file_exists_false(self, filesystem, temp_dir):
        """Test file_exists returns False for nonexistent file."""
        test_file = os.path.join(temp_dir, "nonexistent.mp4")
        
        assert filesystem.file_exists(test_file) is False
    
    def test_find_transcoded_video_not_exists(self, filesystem, temp_dir):
        """Test find_transcoded_video returns empty string when @eaDir doesn't exist."""
        video_path = os.path.join(temp_dir, "video.mp4")
        Path(video_path).touch()
        
        result = filesystem.find_transcoded_video(video_path)
        
        assert result == ""
    
    def test_find_transcoded_video_exists(self, filesystem, temp_dir):
        """Test find_transcoded_video finds transcoded video."""
        video_path = os.path.join(temp_dir, "video.mp4")
        Path(video_path).touch()
        
        # Create @eaDir structure
        ea_dir = Path(temp_dir) / '@eaDir' / 'video.mp4'
        ea_dir.mkdir(parents=True, exist_ok=True)
        transcoded = ea_dir / "SYNOPHOTO_FILM_H.mp4"
        transcoded.touch()
        
        result = filesystem.find_transcoded_video(video_path)
        
        assert result == str(transcoded)
    
    def test_find_transcoded_video_finds_m(self, filesystem, temp_dir):
        """Test find_transcoded_video finds SYNOPHOTO_FILM_M."""
        video_path = os.path.join(temp_dir, "video.mp4")
        Path(video_path).touch()
        
        # Create @eaDir structure with M file
        ea_dir = Path(temp_dir) / '@eaDir' / 'video.mp4'
        ea_dir.mkdir(parents=True, exist_ok=True)
        transcoded_m = ea_dir / "SYNOPHOTO_FILM_M.mp4"
        transcoded_m.touch()
        
        result = filesystem.find_transcoded_video(video_path)
        
        # Should return M (checked first in the list)
        assert result == str(transcoded_m)
    
    def test_find_videos_recursive(self, filesystem, temp_dir):
        """Test find_videos searches recursively."""
        # Create nested directory structure
        subdir = os.path.join(temp_dir, "subdir", "nested")
        os.makedirs(subdir, exist_ok=True)
        
        video1 = os.path.join(temp_dir, "video1.mp4")
        video2 = os.path.join(subdir, "video2.avi")
        
        Path(video1).touch()
        Path(video2).touch()
        
        videos = filesystem.find_videos(temp_dir)
        
        assert len(videos) == 2
        assert video1 in videos
        assert video2 in videos

