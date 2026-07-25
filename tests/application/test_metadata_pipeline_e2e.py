"""End-to-end regression for the video metadata pipeline.

These tests wire the real parser, the real `SynoIndexMetadataReader`, the real
`ChainedMetadataReader` and the real `LocalFilesystem` over a temporary directory
laid out the way Synology lays out `@eaDir`. Only the transcoder and the repository
are stubbed.

The per-layer unit tests would each have passed before the fix as well; what proves
the production incident cannot recur is pushing a real `SYNOINDEX_MEDIA_INFO` record
through every layer and asserting the transcoding configuration that comes out.
"""
from pathlib import Path
from typing import List, Optional

import pytest

from application.process_videos_use_case import ProcessVideosUseCase
from domain.constants.audio import AudioCodec
from domain.constants.resolution import VideoResolution
from domain.constants.video import VideoCodec, VideoProfile
from domain.models.app_config import AudioConfig, VideoConfig
from domain.models.transcoding import Transcoding
from domain.models.video import AudioTrack, Container, Video, VideoTrack
from domain.ports.video_metadata_reader import VideoMetadataReader
from infrastructure.filesystem.local_filesystem import LocalFilesystem
from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader
from infrastructure.metadata.synoindex_metadata_reader import SynoIndexMetadataReader

FIXTURES = Path(__file__).parent.parent / "fixtures" / "synoindex"


class _StubLogger:
    """Silent logger honoring the `AppLogger` surface used by these collaborators."""

    def debug(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def title(self, text, char="="):
        pass

    def subtitle(self, text, char="-"):
        pass


class _StubTranscoder:
    def __init__(self, succeeds: bool = True):
        self._succeeds = succeeds

    def transcode(self) -> bool:
        return self._succeeds


class _RecordingTranscoderFactory:
    """Captures the Transcoding it is handed instead of running FFmpeg."""

    def __init__(self, succeeds: bool = True):
        self._succeeds = succeeds
        self.transcodings: List[Transcoding] = []

    def create(self, transcoding: Transcoding, hw_transcoding: bool = True):
        self.transcodings.append(transcoding)
        return _StubTranscoder(self._succeeds)


class _RecordingRepository:
    """Captures saved records; the real one writes to SQLite."""

    def __init__(self):
        self.saved: List[Transcoding] = []

    def find_by_original_path(self, original_path: str) -> Optional[Transcoding]:
        return None

    def exists_by_original_path(self, original_path: str) -> bool:
        return False

    def save(self, transcoding: Transcoding) -> Transcoding:
        self.saved.append(transcoding)
        return transcoding

    def reset_to_pending(self, original_path: str) -> bool:
        return False


class _StubMetadataReader(VideoMetadataReader):
    """Stands in for probing a file."""

    def __init__(self, video: Optional[Video] = None):
        self._video = video
        self.requested: List[str] = []

    def read(self, video_path: str) -> Optional[Video]:
        self.requested.append(video_path)
        return self._video


def probed(path: str, width: int, height: int, codec: str = "h264") -> Video:
    """Builds the metadata a probe would report for a produced file."""
    return Video(
        path=path,
        video_track=VideoTrack(
            width=width, height=height, codec_name=codec, framerate=30
        ),
        audio_track=AudioTrack(codec="aac", bitrate=128.0, channels=2),
        container=Container(format="mp4"),
    )


def build_media_tree(root: Path, directory: str, filename: str,
                     fixture: Optional[str], with_output: bool = True) -> Path:
    """Lays out a video the way Synology does, and returns its path.

    <root>/<directory>/<filename>
    <root>/<directory>/@eaDir/<filename>/SYNOINDEX_MEDIA_INFO   (when `fixture`)
    <root>/<directory>/@eaDir/<filename>/SYNOPHOTO_FILM_H.mp4   (when `with_output`)
    """
    album = root / directory
    album.mkdir(parents=True, exist_ok=True)

    video = album / filename
    video.write_bytes(b"")

    ea_dir = album / "@eaDir" / filename
    ea_dir.mkdir(parents=True, exist_ok=True)

    if fixture is not None:
        (ea_dir / "SYNOINDEX_MEDIA_INFO").write_text(
            (FIXTURES / fixture).read_text(encoding="utf-8"), encoding="utf-8"
        )

    if with_output:
        (ea_dir / "SYNOPHOTO_FILM_H.mp4").write_bytes(b"")

    return video


@pytest.fixture
def video_config():
    """720p output, matching the production default."""
    return VideoConfig(
        codec=VideoCodec.H264,
        bitrate=2048,
        resolution=VideoResolution.P720,
        width=1280,
        height=720,
        profile=VideoProfile.HIGH,
    )


@pytest.fixture
def audio_config():
    return AudioConfig(codec=AudioCodec.AAC, bitrate=128, channels=2, profile=None)


@pytest.fixture
def repository():
    return _RecordingRepository()


@pytest.fixture
def factory():
    return _RecordingTranscoderFactory()


@pytest.fixture
def output_reader():
    """Reports a geometry unlike the source and unlike the configuration."""
    return _StubMetadataReader(probed("<output>", 958, 720, codec="hevc"))


@pytest.fixture
def build_use_case(video_config, audio_config, repository, factory, output_reader):
    """Builds a use case whose metadata path is entirely real."""

    def _build(root: Path, fallback: Optional[VideoMetadataReader] = None):
        logger = _StubLogger()
        filesystem = LocalFilesystem(["mp4", "mov", "MOV"])

        readers: List[VideoMetadataReader] = [
            SynoIndexMetadataReader(filesystem, logger)
        ]
        if fallback is not None:
            readers.append(fallback)

        return ProcessVideosUseCase(
            video_repository=repository,
            filesystem=filesystem,
            transcoder_factory=factory,
            logger=logger,
            video_config=video_config,
            audio_config=audio_config,
            video_input_path=str(root),
            metadata_reader=ChainedMetadataReader(readers, logger),
            output_metadata_reader=output_reader,
            execution_threads=2,
        )

    return _build


class TestTwoSpacePathIncident:
    """The `44100x2` case: 13 of these shipped at 404x720 instead of 720x1280."""

    @pytest.fixture
    def configuration(self, tmp_path, build_use_case, factory):
        video = build_media_tree(
            tmp_path, "My Old Phone", "IMG_0001.MOV", "two_spaces.txt"
        )
        use_case = build_use_case(tmp_path)

        assert use_case._transcode_video(str(video)) is True

        return factory.transcodings[0].configuration

    def test_treated_as_vertical(self, configuration):
        """Read through the old parser the source was 44100x2, so 'horizontal'."""
        assert configuration.video_height == 1280

    def test_framerate_is_preserved(self, configuration):
        """The shifted bitrate field snapped every one of these to 30 fps."""
        assert configuration.video_framerate == 25.0

    def test_audio_is_not_upmixed(self, configuration):
        assert configuration.audio_channels == 1


class TestOneSpacePathIncident:
    """The `2x1280` case: 1080p sources upscaled to 2274x1280."""

    @pytest.fixture
    def configuration(self, tmp_path, build_use_case, factory):
        video = build_media_tree(
            tmp_path, "PhotoLibrary", "2023 Trip.mp4", "one_space.txt"
        )
        use_case = build_use_case(tmp_path)

        assert use_case._transcode_video(str(video)) is True

        return factory.transcodings[0].configuration

    def test_treated_as_horizontal(self, configuration):
        """Read through the old parser this was 2x1280, so 'vertical'."""
        assert configuration.video_height == 720

    def test_framerate_is_halved_for_light_output(self, configuration):
        assert configuration.video_framerate == 25.0


class TestAccentedPath:
    """A multibyte path must not shift the record, and must not be enlarged."""

    @pytest.fixture
    def configuration(self, tmp_path, build_use_case, factory):
        video = build_media_tree(
            tmp_path, "2020 Cumpleaños", "VID-20200511-WA0002.mp4", "accented_path.txt"
        )
        use_case = build_use_case(tmp_path)

        assert use_case._transcode_video(str(video)) is True

        return factory.transcodings[0].configuration

    def test_output_is_capped_at_the_source_height(self, configuration):
        """352x640 is vertical, so the target would be 1280 without the guard."""
        assert configuration.video_height == 640


class TestFallbackToProbe:
    """With no Synology index the chain must fall through, not give up."""

    def test_configuration_is_built_from_the_fallback(
        self, tmp_path, build_use_case, factory
    ):
        video = build_media_tree(
            tmp_path, "No Index", "clip.mp4", fixture=None
        )
        fallback = _StubMetadataReader(probed(str(video), 1080, 1920))

        use_case = build_use_case(tmp_path, fallback=fallback)

        assert use_case._transcode_video(str(video)) is True
        assert fallback.requested == [str(video)]
        assert factory.transcodings[0].configuration.video_height == 1280

    def test_no_index_and_no_fallback_is_a_failure(
        self, tmp_path, build_use_case, factory, repository
    ):
        """Unknown geometry must stop the transcode rather than guess."""
        video = build_media_tree(tmp_path, "No Index", "clip.mp4", fixture=None)

        use_case = build_use_case(tmp_path)

        assert use_case._transcode_video(str(video)) is False
        assert factory.transcodings == []
        assert repository.saved[-1].error_message


class TestPersistedResolution:
    """The stored row must describe the produced file, not the source or the config."""

    @pytest.fixture
    def saved(self, tmp_path, build_use_case, repository):
        video = build_media_tree(
            tmp_path, "My Old Phone", "IMG_0001.MOV", "two_spaces.txt"
        )
        use_case = build_use_case(tmp_path)

        use_case._transcode_video(str(video))

        return repository.saved[-1]

    def test_resolution_comes_from_the_produced_file(self, saved):
        assert saved.transcoded_video.video_track.resolution == "958x720"

    def test_codec_comes_from_the_produced_file(self, saved):
        assert saved.transcoded_video.video_track.codec_name == "hevc"

    def test_resolution_is_not_the_source_geometry(self, saved):
        assert saved.transcoded_video.video_track.resolution != "1080x1920"

    def test_resolution_is_not_a_historical_corruption(self, saved):
        """Neither of the two values the dashboard used to show."""
        assert saved.transcoded_video.video_track.resolution not in ("44100x2", "2x1280")


class TestNotRequiredWithoutOutputFile:
    """Absence of the output file is the only thing that means 'not required'."""

    def test_missing_output_is_not_required(self, tmp_path, build_use_case, factory,
                                            repository):
        video = build_media_tree(
            tmp_path, "My Old Phone", "IMG_0001.MOV", "two_spaces.txt",
            with_output=False,
        )
        use_case = build_use_case(tmp_path)

        assert use_case._transcode_video(str(video)) is True
        assert factory.transcodings == []
        assert repository.saved[-1].status == "not_required"

    def test_source_metadata_was_still_parsed(self, tmp_path, build_use_case,
                                              repository):
        """The skipped row must still describe the real video."""
        video = build_media_tree(
            tmp_path, "My Old Phone", "IMG_0001.MOV", "two_spaces.txt",
            with_output=False,
        )
        use_case = build_use_case(tmp_path)

        use_case._transcode_video(str(video))

        assert repository.saved[-1].original_video.video_track.resolution == "1080x1920"
