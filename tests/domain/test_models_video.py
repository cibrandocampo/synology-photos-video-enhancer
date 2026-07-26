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
        
        # Create metadata list with correct indices according to MetadataIndex
        metadata = [None] * 60  # Create list with enough space
        metadata[MetadataIndex.WIDTH] = "1920"
        metadata[MetadataIndex.HEIGHT] = "1080"
        metadata[MetadataIndex.VIDEO_CODEC] = "h264"
        metadata[MetadataIndex.FRAMERATE_NUMERATOR] = "30"
        metadata[MetadataIndex.FRAMERATE_DENOMINATOR] = "1"
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

        assert video.path == "/test/video.mp4"

    def test_from_synology_metadata_non_numeric_int_fields(self):
        """Test safe_int exception branch: non-numeric value at an integer field index."""
        from domain.constants.synology import MetadataIndex
        metadata = [None] * 60
        metadata[MetadataIndex.WIDTH] = "not_a_number"
        metadata[MetadataIndex.HEIGHT] = "also_bad"
        metadata[MetadataIndex.FRAMERATE_NUMERATOR] = "bad"
        metadata[MetadataIndex.FRAMERATE_DENOMINATOR] = "bad"

        video = Video.from_synology_metadata("/test/video.mp4", metadata)

        assert video.video_track.width == 0
        assert video.video_track.height == 0
        assert video.video_track.framerate == 0

    def test_from_synology_metadata_non_numeric_float_fields(self):
        """Test safe_float exception branch: non-numeric value at a float field index."""
        from domain.constants.synology import MetadataIndex
        metadata = [None] * 60
        metadata[MetadataIndex.VIDEO_BITRATE] = "bad_float"
        metadata[MetadataIndex.AUDIO_BITRATE] = "also_bad"

        video = Video.from_synology_metadata("/test/video.mp4", metadata)

        assert video.video_track.bitrate == 0.0
        assert video.audio_track.bitrate == 0.0


class TestFractionalFramerate:
    """The measured rate is carried exactly; NTSC sources are not whole numbers."""

    def test_framerate_accepts_a_fractional_value(self):
        track = VideoTrack(
            width=1920, height=1080, codec_name="h264", framerate=30000 / 1001
        )

        assert track.framerate == pytest.approx(29.97002997002997)

    def test_framerate_is_not_coerced_to_an_integer(self):
        track = VideoTrack(
            width=1920, height=1080, codec_name="h264", framerate=29.97
        )

        assert track.framerate != 30
        assert track.framerate != 29

    def test_variable_framerate_defaults_to_false(self):
        """Only ffprobe can determine variability; everything else must not guess."""
        track = VideoTrack(width=1920, height=1080, codec_name="h264", framerate=30)

        assert track.is_variable_framerate is False

    def test_variable_framerate_can_be_set(self):
        track = VideoTrack(
            width=1920, height=1080, codec_name="h264", framerate=30,
            is_variable_framerate=True,
        )

        assert track.is_variable_framerate is True


def _synology_metadata(framerate_num="30", framerate_den="1", size=60):
    """A metadata list complete enough to be realistic; only the rate fields vary."""
    metadata = [None] * 60
    metadata[MetadataIndex.WIDTH] = "1920"
    metadata[MetadataIndex.HEIGHT] = "1080"
    metadata[MetadataIndex.VIDEO_CODEC] = "h264"
    metadata[MetadataIndex.FRAMERATE_NUMERATOR] = framerate_num
    metadata[MetadataIndex.FRAMERATE_DENOMINATOR] = framerate_den
    metadata[MetadataIndex.CHANNELS] = "2"
    metadata[MetadataIndex.CONTAINER] = "mp4"
    return metadata[:size]


class TestDenominatorIsNeverDefaulted:
    """An unusable denominator yields no rate at all, rather than one made up.

    These assertions live on the model rather than on the parser on purpose. The
    parser applies a plausibility gate, and a gate rejects an implausible *result*
    for its own reasons — so a parser-level test can pass against code that defaults
    a zero denominator to 1, provided the resulting rate happens to look wrong for
    some other reason. Here there is no gate, so the rate is the only thing under
    test.
    """

    def test_a_zero_denominator_yields_no_rate(self):
        """30/0 is not 30 fps, and it is not 30000 fps either. It is unknown."""
        video = Video.from_synology_metadata(
            "/test/video.mp4", _synology_metadata(framerate_den="0")
        )

        assert video.video_track.framerate == 0

    def test_a_zero_denominator_does_not_yield_the_bare_numerator(self):
        """Dividing by a defaulted 1 is the specific defect this rule prevents."""
        video = Video.from_synology_metadata(
            "/test/video.mp4", _synology_metadata(framerate_num="30", framerate_den="0")
        )

        assert video.video_track.framerate != 30

    def test_the_geometry_survives_so_the_rate_is_what_is_asserted(self):
        """Guards the two assertions above against becoming vacuous.

        If width and height were lost along with the denominator, the record would
        be unusable for reasons that have nothing to do with the framerate, and the
        assertions would no longer be about the rule they name.
        """
        video = Video.from_synology_metadata(
            "/test/video.mp4", _synology_metadata(framerate_den="0")
        )

        assert video.video_track.width == 1920
        assert video.video_track.height == 1080

    def test_an_absent_denominator_yields_no_rate(self):
        """A record truncated before position 36 has a numerator and nothing to divide by."""
        video = Video.from_synology_metadata(
            "/test/video.mp4", _synology_metadata(size=36)
        )

        assert video.video_track.framerate == 0

    def test_a_non_numeric_denominator_yields_no_rate(self):
        video = Video.from_synology_metadata(
            "/test/video.mp4", _synology_metadata(framerate_den="n/a")
        )

        assert video.video_track.framerate == 0
