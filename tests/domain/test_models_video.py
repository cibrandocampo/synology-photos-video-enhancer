"""Tests for video domain models."""
import pytest
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.constants.synology import MetadataIndex


class TestVideoTrack:
    """Tests for VideoTrack model."""
    
    def test_create_video_track(self):
        """Test creating a VideoTrack."""
        track = VideoTrack(
            width=1920,
            height=1080,
            codec_name="h264",
            framerate=30,
            bitrate=5000.0
        )
        
        assert track.width == 1920
        assert track.height == 1080
        assert track.codec_name == "h264"
        assert track.framerate == 30
    
    def test_resolution_property(self):
        """Test resolution property."""
        track = VideoTrack(width=1920, height=1080, codec_name="h264", framerate=30)
        assert track.resolution == "1920x1080"
    
    def test_codec_validation_defaults_to_h264(self):
        """Test that invalid codec defaults to h264."""
        track = VideoTrack(width=1920, height=1080, codec_name="invalid", framerate=30)
        assert track.codec_name == "h264"
    
    def test_codec_validation_empty_defaults_to_h264(self):
        """Test that empty codec defaults to h264."""
        track = VideoTrack(width=1920, height=1080, codec_name="", framerate=30)
        assert track.codec_name == "h264"


class TestAudioTrack:
    """Tests for AudioTrack model."""
    
    def test_create_audio_track(self):
        """Test creating an AudioTrack."""
        track = AudioTrack(bitrate=128.0, codec="aac", channels=2)
        
        assert track.bitrate == 128.0
        assert track.codec == "aac"
        assert track.channels == 2
    
    def test_codec_validation_defaults_to_mp3(self):
        """Test that invalid codec defaults to mp3."""
        track = AudioTrack(codec="invalid")
        assert track.codec == "mp3"
    
    def test_codec_validation_empty_defaults_to_mp3(self):
        """Test that empty codec defaults to mp3."""
        track = AudioTrack(codec="")
        assert track.codec == "mp3"


class TestContainer:
    """Tests for Container model."""
    
    def test_create_container(self):
        """Test creating a Container."""
        container = Container(format="mp4", duration=120.0, total_bitrate=5000.0, file_size=75000000)
        
        assert container.format == "mp4"
        assert container.duration == 120.0
        assert container.total_bitrate == 5000.0
        assert container.file_size == 75000000
    
    def test_format_validation_defaults_to_mp4(self):
        """Test that invalid format defaults to mp4."""
        container = Container(format="invalid")
        assert container.format == "mp4"
    
    def test_format_validation_empty_defaults_to_mp4(self):
        """Test that empty format defaults to mp4."""
        container = Container(format="")
        assert container.format == "mp4"


class TestVideo:
    """Tests for Video model."""
    
    def test_create_video(self):
        """Test creating a Video."""
        video = Video(
            path="/test/video.mp4",
            video_track=VideoTrack(width=1920, height=1080, codec_name="h264", framerate=30),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        assert video.path == "/test/video.mp4"
        assert video.video_track.width == 1920
        assert video.container.format == "mp4"
    
    def test_from_synology_metadata_complete(self):
        """Test creating Video from complete Synology metadata."""
        from domain.constants.synology import MetadataIndex
        
        # Create metadata list with correct indices according to MetadataIndex
        metadata = [None] * 60  # Create list with enough space
        metadata[MetadataIndex.WIDTH] = "1920"
        metadata[MetadataIndex.HEIGHT] = "1080"
        metadata[MetadataIndex.VIDEO_CODEC] = "h264"
        metadata[MetadataIndex.FRAMERATE] = "30"
        metadata[MetadataIndex.VIDEO_BITRATE] = "5000.0"
        metadata[MetadataIndex.AUDIO_BITRATE] = "128.0"
        metadata[MetadataIndex.AUDIO_CODEC] = "aac"
        metadata[MetadataIndex.CHANNELS] = "2"
        metadata[MetadataIndex.CONTAINER] = "mp4"
        metadata[MetadataIndex.DURATION] = "120.0"
        metadata[MetadataIndex.TOTAL_BITRATE] = "5128.0"
        metadata[MetadataIndex.FILE_SIZE] = "76920000"
        
        video = Video.from_synology_metadata("/test/video.mp4", metadata)
        
        assert video.path == "/test/video.mp4"
        assert video.video_track.width == 1920
        assert video.video_track.height == 1080
        assert video.video_track.codec_name == "h264"
        assert video.audio_track.codec == "aac"
        assert video.container.format == "mp4"
    
    def test_from_synology_metadata_incomplete(self):
        """Test creating Video from incomplete Synology metadata uses defaults."""
        from domain.constants.synology import MetadataIndex
        
        # Create metadata list with only width
        metadata = [None] * 60
        metadata[MetadataIndex.WIDTH] = "1920"
        # Other fields missing
        
        video = Video.from_synology_metadata("/test/video.mp4", metadata)
        
        assert video.path == "/test/video.mp4"
        assert video.video_track.width == 1920
        # Other fields should use defaults
        assert video.video_track.height == 0
        assert video.video_track.codec_name == "h264"  # Default
    
    def test_from_synology_metadata_empty_list(self):
        """Test creating Video from empty metadata list uses defaults."""
        metadata = []
        
        video = Video.from_synology_metadata("/test/video.mp4", metadata)
        
        assert video.path == "/test/video.mp4"
        assert video.video_track.width == 0
        assert video.video_track.height == 0
    
    def test_from_synology_metadata_invalid_types(self):
        """Test creating Video from metadata with invalid types uses defaults."""
        metadata = ["header", None, "invalid", "not_a_number"]
        
        video = Video.from_synology_metadata("/test/video.mp4", metadata)
        
        # Should handle invalid types gracefully
        assert video.path == "/test/video.mp4"
