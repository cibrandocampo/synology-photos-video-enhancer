"""Tests for video repository SQL implementation."""
import pytest
from unittest.mock import Mock
from domain.models.transcoding import Transcoding, TranscodingStatus
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.models.app_config import DatabaseConfig
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.video_repository_sql import VideoRepositorySQL


class TestVideoRepositorySQL:
    """Tests for VideoRepositorySQL."""
    
    @pytest.fixture
    def db_connection(self, temp_db_path):
        """Creates a database connection for testing."""
        db_config = DatabaseConfig(path=temp_db_path)
        conn = DatabaseConnection(db_config, Mock())
        conn.initialize()
        return conn
    
    @pytest.fixture
    def repository(self, db_connection):
        """Creates a VideoRepositorySQL instance."""
        return VideoRepositorySQL(db_connection)
    
    @pytest.fixture
    def sample_transcoding(self, sample_video):
        """Creates a sample Transcoding for testing."""
        transcoded_video = Video(
            path="/test/transcoded.mp4",
            video_track=VideoTrack(width=1280, height=720, codec_name="h264", framerate=30),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        return Transcoding(
            original_video=sample_video,
            transcoded_video=transcoded_video,
            status=TranscodingStatus.COMPLETED
        )
    
    def test_save_transcoding(self, repository, sample_transcoding):
        """Test saving a transcoding."""
        repository.save(sample_transcoding)
        
        # Verify it was saved
        found = repository.find_by_original_path(sample_transcoding.original_video.path)
        assert found is not None
        assert found.original_video.path == sample_transcoding.original_video.path
    
    def test_find_by_original_path_exists(self, repository, sample_transcoding):
        """Test finding transcoding by original path when it exists."""
        repository.save(sample_transcoding)
        
        found = repository.find_by_original_path(sample_transcoding.original_video.path)
        
        assert found is not None
        assert found.original_video.path == sample_transcoding.original_video.path
    
    def test_find_by_original_path_not_exists(self, repository):
        """Test finding transcoding by original path when it doesn't exist."""
        found = repository.find_by_original_path("/nonexistent/video.mp4")
        
        assert found is None
    
    def test_exists_by_original_path_true(self, repository, sample_transcoding):
        """Test exists_by_original_path returns True when transcoding exists."""
        repository.save(sample_transcoding)
        
        exists = repository.exists_by_original_path(sample_transcoding.original_video.path)
        
        assert exists is True
    
    def test_exists_by_original_path_false(self, repository):
        """Test exists_by_original_path returns False when transcoding doesn't exist."""
        exists = repository.exists_by_original_path("/nonexistent/video.mp4")
        
        assert exists is False
    
    def test_save_updates_existing(self, repository, sample_transcoding):
        """Test that save updates existing transcoding."""
        # Save first time
        repository.save(sample_transcoding)
        
        # Update and save again
        updated = sample_transcoding.mark_as_failed("Test error")
        repository.save(updated)
        
        # Verify update
        found = repository.find_by_original_path(sample_transcoding.original_video.path)
        assert found is not None
        assert found.status == TranscodingStatus.FAILED
        assert found.error_message == "Test error"
    
    def test_save_raises_integrity_error_and_rolls_back(self, sample_transcoding):
        """Test that IntegrityError triggers rollback and propagates."""
        from unittest.mock import MagicMock
        from sqlalchemy.exc import IntegrityError

        mock_session = MagicMock()
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.commit.side_effect = IntegrityError("duplicate", {}, None)

        mock_db = MagicMock()
        mock_db.get_session.return_value = mock_session

        repo = VideoRepositorySQL(mock_db)

        with pytest.raises(IntegrityError):
            repo.save(sample_transcoding)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

