"""Tests for transcoding domain models."""
import pytest
from datetime import datetime
from domain.models.transcoding import (
    Transcoding,
    TranscodingConfiguration,
    TranscodingStatus
)
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.audio import AudioCodec
from domain.constants.container import ContainerFormat


class TestTranscodingConfiguration:
    """Tests for TranscodingConfiguration model."""
    
    def test_create_valid_configuration(self, sample_transcoding_configuration):
        """Test creating a valid TranscodingConfiguration."""
        assert sample_transcoding_configuration.video_codec == VideoCodec.H264
        assert sample_transcoding_configuration.video_height == 720
        assert sample_transcoding_configuration.execution_threads == 2
    
    def test_configuration_required_fields(self):
        """Test that required fields are enforced."""
        with pytest.raises(Exception):  # Pydantic validation error
            TranscodingConfiguration(
                video_codec=VideoCodec.H264,
                # Missing required fields
            )


class TestTranscoding:
    """Tests for Transcoding model."""
    
    def test_create_transcoding(self, sample_video):
        """Test creating a Transcoding object."""
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=None,
            configuration=None,
            status=TranscodingStatus.PENDING
        )
        
        assert transcoding.original_video == sample_video
        assert transcoding.transcoded_video is None
        assert transcoding.status == TranscodingStatus.PENDING
        assert transcoding.error_message is None
    
    def test_mark_as_completed(self, sample_video):
        """Test marking transcoding as completed."""
        transcoding = Transcoding(
            original_video=sample_video,
            status=TranscodingStatus.PENDING
        )
        
        completed = transcoding.mark_as_completed()
        
        assert completed.status == TranscodingStatus.COMPLETED
        assert completed.updated_at > transcoding.updated_at
    
    def test_mark_as_in_progress(self, sample_video):
        """Test marking transcoding as in progress."""
        transcoding = Transcoding(
            original_video=sample_video,
            status=TranscodingStatus.PENDING
        )
        
        in_progress = transcoding.mark_as_in_progress()
        
        assert in_progress.status == TranscodingStatus.IN_PROGRESS
        assert in_progress.updated_at > transcoding.updated_at
    
    def test_mark_as_failed(self, sample_video):
        """Test marking transcoding as failed."""
        transcoding = Transcoding(
            original_video=sample_video,
            status=TranscodingStatus.PENDING
        )
        
        error_msg = "FFmpeg error: codec not supported"
        failed = transcoding.mark_as_failed(error_msg)
        
        assert failed.status == TranscodingStatus.FAILED
        assert failed.error_message == error_msg
        assert failed.updated_at > transcoding.updated_at
    
    def test_default_timestamps(self, sample_video):
        """Test that timestamps are set by default."""
        transcoding = Transcoding(
            original_video=sample_video
        )
        
        assert transcoding.created_at is not None
        assert transcoding.updated_at is not None
        assert isinstance(transcoding.created_at, datetime)
        assert isinstance(transcoding.updated_at, datetime)
