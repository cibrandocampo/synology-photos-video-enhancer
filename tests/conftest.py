"""Pytest configuration and shared fixtures."""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add current directory to path for imports (src is already in /app)
import sys
from pathlib import Path
# The src code is mounted at /app, so we need to add it to path
# But since we're running from /app, imports should work directly
if str(Path(__file__).parent.parent / "src") not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def temp_dir():
    """Creates a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def temp_db_path(temp_dir):
    """Creates a temporary database path."""
    return os.path.join(temp_dir, "test.db")


@pytest.fixture
def mock_video_repository():
    """Creates a mock VideoRepository."""
    mock = Mock()
    mock.find_by_original_path = Mock(return_value=None)
    mock.exists_by_original_path = Mock(return_value=False)
    mock.save = Mock()
    return mock


@pytest.fixture
def mock_filesystem():
    """Creates a mock Filesystem."""
    mock = Mock()
    mock.find_videos = Mock(return_value=[])
    mock.file_exists = Mock(return_value=False)
    mock.find_transcoded_video = Mock(return_value="")
    return mock


@pytest.fixture
def mock_hardware_info():
    """Creates a mock HardwareInfo."""
    from domain.models.hardware import HardwareVideoAcceleration
    
    mock = Mock()
    mock.video_acceleration = HardwareVideoAcceleration.VAAPI
    mock.cpu = Mock()
    mock.cpu.vendor = Mock()
    return mock


@pytest.fixture
def mock_transcoder():
    """Creates a mock Transcoder."""
    mock = Mock()
    mock.transcode = Mock(return_value=True)
    return mock


@pytest.fixture
def sample_video():
    """Creates a sample Video object for testing."""
    from domain.models.video import Video, VideoTrack, AudioTrack, Container
    
    return Video(
        path="/test/video.mp4",
        video_track=VideoTrack(
            width=1920,
            height=1080,
            codec_name="h264",
            framerate=30,
            bitrate=5000.0
        ),
        audio_track=AudioTrack(
            bitrate=128.0,
            codec="aac",
            channels=2
        ),
        container=Container(
            format="mp4",
            duration=120.0,
            total_bitrate=5128.0,
            file_size=76920000
        )
    )


@pytest.fixture
def sample_transcoding_configuration():
    """Creates a sample TranscodingConfiguration for testing."""
    from domain.models.transcoding import TranscodingConfiguration
    from domain.constants.video import VideoCodec, VideoProfile
    from domain.constants.audio import AudioCodec
    from domain.constants.container import ContainerFormat
    
    return TranscodingConfiguration(
        video_codec=VideoCodec.H264,
        video_profile=VideoProfile.HIGH,
        video_height=720,
        video_framerate=30.0,
        video_bitrate=2048,
        audio_codec=AudioCodec.AAC,
        audio_profile=None,
        audio_channels=2,
        audio_bitrate=128,
        container=ContainerFormat.MP4,
        execution_threads=2
    )


@pytest.fixture
def sample_video_track():
    """Creates a sample VideoTrack for testing."""
    from domain.models.video import VideoTrack
    
    return VideoTrack(
        width=1920,
        height=1080,
        codec_name="h264",
        framerate=30,
        bitrate=5000.0
    )


@pytest.fixture
def sample_audio_track():
    """Creates a sample AudioTrack for testing."""
    from domain.models.video import AudioTrack
    
    return AudioTrack(
        bitrate=128.0,
        codec="aac",
        channels=2
    )


@pytest.fixture
def sample_container():
    """Creates a sample Container for testing."""
    from domain.models.video import Container
    
    return Container(
        format="mp4",
        duration=120.0,
        total_bitrate=5128.0,
        file_size=76920000
    )
