"""Tests for ProcessVideosUseCase."""
import pytest
import os
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
from domain.models.video import Video, VideoTrack, AudioTrack, Container
from domain.models.transcoding import Transcoding, TranscodingStatus
from domain.models.app_config import VideoConfig, AudioConfig
from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.resolution import VideoResolution
from domain.constants.audio import AudioCodec
from application.process_videos_use_case import ProcessVideosUseCase
from application.process_result import ProcessResult


class TestProcessVideosUseCase:
    """Tests for ProcessVideosUseCase."""
    
    @pytest.fixture
    def video_config(self):
        """Creates a VideoConfig for testing."""
        return VideoConfig(
            codec=VideoCodec.H264,
            bitrate=2048,
            resolution=VideoResolution.P720,
            width=1280,
            height=720,
            profile=VideoProfile.HIGH
        )
    
    @pytest.fixture
    def audio_config(self):
        """Creates an AudioConfig for testing."""
        return AudioConfig(
            codec=AudioCodec.AAC,
            bitrate=128,
            channels=2,
            profile=None
        )
    
    @pytest.fixture
    def use_case(self, mock_video_repository, mock_filesystem, mock_hardware_info, 
                 video_config, audio_config):
        """Creates a ProcessVideosUseCase instance for testing."""
        return ProcessVideosUseCase(
            video_repository=mock_video_repository,
            filesystem=mock_filesystem,
            hardware_info=mock_hardware_info,
            video_config=video_config,
            audio_config=audio_config,
            video_input_path="/test/media",
            execution_threads=2
        )
    
    def test_execute_no_videos(self, use_case, mock_filesystem):
        """Test execute when no videos are found."""
        mock_filesystem.find_videos.return_value = []
        
        result = use_case.execute()
        
        assert isinstance(result, ProcessResult)
        assert result.total_processed == 0
        assert result.transcoded == 0
        assert result.already_transcoded == 0
        assert result.errors == 0
        assert result.is_success is True
    
    def test_execute_video_already_transcoded(self, use_case, mock_filesystem, 
                                               mock_video_repository, sample_video):
        """Test execute when video is already transcoded."""
        from domain.models.video import Video, VideoTrack, AudioTrack, Container
        
        video_path = "/test/media/video.mp4"
        mock_filesystem.find_videos.return_value = [video_path]
        mock_filesystem.file_exists.return_value = True
        mock_filesystem.find_transcoded_video.return_value = "/test/media/@eaDir/video.mp4/SYNOPHOTO_FILM_H.mp4"
        
        # Create transcoded video with correct codec and resolution
        transcoded_video = Video(
            path="/test/media/@eaDir/video.mp4/SYNOPHOTO_FILM_H.mp4",
            video_track=VideoTrack(width=1280, height=720, codec_name="h264", framerate=30),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        # Mock existing transcoding
        existing_transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=transcoded_video,
            status=TranscodingStatus.COMPLETED
        )
        mock_video_repository.find_by_original_path.return_value = existing_transcoding
        
        with patch.object(use_case, '_read_video_metadata', return_value=sample_video):
            result = use_case.execute()
        
        assert result.total_processed == 1
        assert result.already_transcoded == 1
        assert result.transcoded == 0
    
    def test_execute_video_needs_transcoding(self, use_case, mock_filesystem,
                                              mock_video_repository, mock_transcoder,
                                              sample_video):
        """Test execute when video needs transcoding."""
        video_path = "/test/media/video.mp4"
        mock_filesystem.find_videos.return_value = [video_path]
        mock_filesystem.file_exists.return_value = False  # No transcoded video exists
        mock_video_repository.find_by_original_path.return_value = None  # No existing transcoding
        
        with patch.object(use_case, '_read_video_metadata', return_value=sample_video), \
             patch.object(use_case, '_transcode_video', return_value=True):
            result = use_case.execute()
        
        assert result.total_processed == 1
        assert result.transcoded == 1
        assert result.already_transcoded == 0
    
    def test_execute_transcoding_fails(self, use_case, mock_filesystem,
                                        mock_video_repository, sample_video):
        """Test execute when transcoding fails."""
        video_path = "/test/media/video.mp4"
        mock_filesystem.find_videos.return_value = [video_path]
        mock_filesystem.file_exists.return_value = False
        mock_video_repository.find_by_original_path.return_value = None
        
        with patch.object(use_case, '_read_video_metadata', return_value=sample_video), \
             patch.object(use_case, '_transcode_video', return_value=False):
            result = use_case.execute()
        
        assert result.total_processed == 1
        assert result.transcoded == 0
        assert result.errors == 1
    
    def test_calculate_output_height_landscape(self, use_case):
        """Test calculating output height for landscape video."""
        video_track = VideoTrack(width=1920, height=1080, codec_name="h264", framerate=30)
        height = use_case._calculate_output_height(video_track)
        
        # Should return configured height (720) for landscape
        assert height == 720
    
    def test_calculate_output_height_portrait(self, use_case):
        """Test calculating output height for portrait video."""
        video_track = VideoTrack(width=1080, height=1920, codec_name="h264", framerate=30)
        height = use_case._calculate_output_height(video_track)
        
        # Should return configured width (1280) for portrait (vertical video)
        assert height == 1280
    
    def test_calculate_output_height_square(self, use_case):
        """Test calculating output height for square video."""
        video_track = VideoTrack(width=1080, height=1080, codec_name="h264", framerate=30)
        height = use_case._calculate_output_height(video_track)
        
        # Square video is treated as vertical, so should return width
        assert height == 1280
    
    def test_calculate_output_audio_channels_less_than_config(self, use_case):
        """Test calculating audio channels when original has fewer channels."""
        # Original has 1 channel, config has 2
        channels = use_case._calculate_output_audio_channels(1)
        assert channels == 1  # Should use original (less than config)
    
    def test_calculate_output_audio_channels_more_than_config(self, use_case):
        """Test calculating audio channels when original has more channels."""
        # Original has 5 channels, config has 2
        channels = use_case._calculate_output_audio_channels(5)
        assert channels == 2  # Should use config value
    
    def test_calculate_output_audio_channels_equal(self, use_case):
        """Test calculating audio channels when original equals config."""
        channels = use_case._calculate_output_audio_channels(2)
        assert channels == 2  # Should use config value
    
    def test_calculate_output_framerate(self, use_case):
        """Test calculating output framerate."""
        framerate = use_case._calculate_output_framerate(60)
        # Should convert 60fps to 30fps for light videos
        assert framerate == 30.0
    
    def test_calculate_output_framerate_ntsc(self, use_case):
        """Test calculating output framerate for NTSC rates."""
        framerate = use_case._calculate_output_framerate(29)
        # Should find closest match (29.97) and convert if needed
        assert isinstance(framerate, float)
    
    def test_is_transcoding_valid_completed_status(self, use_case, sample_video):
        """Test _is_transcoding_valid with completed status."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        
        transcoded_video = Video(
            path="/test/transcoded.mp4",
            video_track=VideoTrack(width=1280, height=720, codec_name="h264", framerate=30),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=transcoded_video,
            status=TranscodingStatus.COMPLETED
        )
        
        # Should be valid if codec and resolution match
        result = use_case._is_transcoding_valid(transcoding)
        assert result is True
    
    def test_is_transcoding_valid_pending_status(self, use_case, sample_video):
        """Test _is_transcoding_valid with pending status."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        
        transcoding = Transcoding(
            original_video=sample_video,
            status=TranscodingStatus.PENDING
        )
        
        result = use_case._is_transcoding_valid(transcoding)
        assert result is False
    
    def test_is_transcoding_valid_wrong_codec(self, use_case, sample_video):
        """Test _is_transcoding_valid with wrong codec."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        
        transcoded_video = Video(
            path="/test/transcoded.mp4",
            video_track=VideoTrack(width=1280, height=720, codec_name="vp8", framerate=30),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=transcoded_video,
            status=TranscodingStatus.COMPLETED
        )
        
        result = use_case._is_transcoding_valid(transcoding)
        assert result is False
    
    def test_is_transcoding_valid_resolution_too_high(self, use_case, sample_video):
        """Test _is_transcoding_valid with resolution too high."""
        from domain.models.transcoding import Transcoding, TranscodingStatus
        
        transcoded_video = Video(
            path="/test/transcoded.mp4",
            video_track=VideoTrack(width=1920, height=1080, codec_name="h264", framerate=30),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        transcoding = Transcoding(
            original_video=sample_video,
            transcoded_video=transcoded_video,
            status=TranscodingStatus.COMPLETED
        )
        
        result = use_case._is_transcoding_valid(transcoding)
        assert result is False
    
    @pytest.mark.skip(reason="Complex file format - needs real Synology metadata file structure")
    def test_read_video_metadata_file_exists(self, use_case, temp_dir):
        """Test _read_video_metadata when file exists."""
        # This test is complex because it requires exact Synology metadata file format
        # Skipping for now - can be implemented with a real example file
        pass
    
    def test_read_video_metadata_file_not_exists(self, use_case, temp_dir):
        """Test _read_video_metadata when file doesn't exist."""
        import os
        from pathlib import Path
        
        video_path = os.path.join(temp_dir, "nonexistent.mp4")
        video = use_case._read_video_metadata(video_path)
        
        assert video.path == video_path
        assert video.video_track.width == 0
        assert video.video_track.height == 0
    
    def test_get_output_path(self, use_case, temp_dir):
        """Test _get_output_path creates correct path."""
        import os
        from pathlib import Path
        
        original_path = os.path.join(temp_dir, "video.mp4")
        output_path = use_case._get_output_path(original_path)
        
        expected = os.path.join(temp_dir, "@eaDir", "video.mp4", "SYNOPHOTO_FILM_H.mp4")
        assert output_path == expected
        
        # Verify directory was created
        assert Path(output_path).parent.exists()
    
    def test_read_video_metadata_file_error_handling(self, use_case, temp_dir):
        """Test _read_video_metadata handles file read errors."""
        from pathlib import Path
        
        video_path = os.path.join(temp_dir, "video.mp4")
        video_file = Path(video_path)
        ea_dir = video_file.parent / '@eaDir' / video_file.name
        ea_dir.mkdir(parents=True, exist_ok=True)
        syno_file = ea_dir / "SYNOINDEX_MEDIA_INFO"
        
        # Create a file that will cause an error when reading (e.g., binary file)
        with open(syno_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03')  # Binary data
        
        # Should return placeholder video on error
        video = use_case._read_video_metadata(video_path)
        
        assert video.path == video_path
        assert video.video_track.width == 0  # Placeholder values
    
    def test_read_video_metadata_invalid_format(self, use_case, temp_dir):
        """Test _read_video_metadata handles invalid file format."""
        from pathlib import Path
        
        video_path = os.path.join(temp_dir, "video.mp4")
        video_file = Path(video_path)
        ea_dir = video_file.parent / '@eaDir' / video_file.name
        ea_dir.mkdir(parents=True, exist_ok=True)
        syno_file = ea_dir / "SYNOINDEX_MEDIA_INFO"
        
        # Create file with only header (less than 2 lines)
        with open(syno_file, 'w') as f:
            f.write("header\n")  # Only one line
        
        video = use_case._read_video_metadata(video_path)
        
        assert video.path == video_path
        assert video.video_track.width == 0  # Placeholder values
    
    def test_calculate_output_height_vertical_video(self, use_case):
        """Test _calculate_output_height with vertical video."""
        # Vertical video: height >= width
        video_track = VideoTrack(width=720, height=1280, codec_name="h264", framerate=30)
        
        # For vertical video, output height should be video_config.width
        output_height = use_case._calculate_output_height(video_track)
        
        assert output_height == use_case.video_config.width  # 1280
    
    def test_calculate_output_height_horizontal_video(self, use_case):
        """Test _calculate_output_height with horizontal video."""
        # Horizontal video: width > height
        video_track = VideoTrack(width=1920, height=1080, codec_name="h264", framerate=30)
        
        # For horizontal video, output height should be video_config.height
        output_height = use_case._calculate_output_height(video_track)
        
        assert output_height == use_case.video_config.height  # 720
    
    def test_calculate_output_audio_channels_less_than_config(self, use_case):
        """Test _calculate_output_audio_channels when original has fewer channels."""
        # Original has 1 channel, config wants 2
        output_channels = use_case._calculate_output_audio_channels(1)
        
        # Should keep original (1 channel)
        assert output_channels == 1
    
    def test_calculate_output_audio_channels_more_than_config(self, use_case):
        """Test _calculate_output_audio_channels when original has more channels."""
        # Original has 6 channels, config wants 2
        output_channels = use_case._calculate_output_audio_channels(6)
        
        # Should use config (2 channels)
        assert output_channels == use_case.audio_config.channels
    
    def test_calculate_output_audio_channels_equal_to_config(self, use_case):
        """Test _calculate_output_audio_channels when original equals config."""
        # Original has 2 channels, config wants 2
        output_channels = use_case._calculate_output_audio_channels(2)
        
        # Should use config (2 channels)
        assert output_channels == use_case.audio_config.channels
    
    def test_execute_with_transcoding_error(self, use_case, mock_filesystem):
        """Test execute when transcoding fails."""
        video_path = "/test/media/video.mp4"
        mock_filesystem.find_videos.return_value = [video_path]
        mock_filesystem.file_exists.return_value = False
        mock_video_repository = use_case.video_repository
        mock_video_repository.find_by_original_path.return_value = None
        
        # Mock _transcode_video to return False (failure)
        with patch.object(use_case, '_transcode_video', return_value=False):
            result = use_case.execute()
        
        assert result.total_processed == 1
        assert result.errors == 1
        assert result.transcoded == 0
        assert result.is_success is False
