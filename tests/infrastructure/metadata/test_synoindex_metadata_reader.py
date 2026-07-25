"""Tests for SynoIndexMetadataReader."""
from pathlib import Path
from typing import List, Optional

from domain.ports.filesystem import Filesystem
from infrastructure.metadata.synoindex_metadata_reader import SynoIndexMetadataReader

FIXTURES = Path(__file__).parent.parent.parent / "fixtures" / "synoindex"


class _StubFilesystem(Filesystem):
    """Hand-rolled stub honoring the `Filesystem` port, capturing requested paths."""

    def __init__(self, content: Optional[str] = None,
                 error: Optional[Exception] = None) -> None:
        self._content = content
        self._error = error
        self.requested: List[str] = []

    def find_videos(self, directory: str) -> List[str]:
        return []

    def file_exists(self, path: str) -> bool:
        return False

    def read_file(self, path: str) -> Optional[str]:
        self.requested.append(path)
        if self._error is not None:
            raise self._error
        return self._content

    def ensure_directory(self, path: str) -> None:
        pass

    def find_transcoded_video(self, original_video_path: str) -> str:
        return ""


def fixture(name: str) -> str:
    """Reads a SYNOINDEX fixture as UTF-8 text."""
    return (FIXTURES / name).read_text(encoding="utf-8")


class TestIndexLocation:
    """The index sits inside the @eaDir directory belonging to the video."""

    def test_builds_the_eadir_index_path(self, logger):
        filesystem = _StubFilesystem(content=fixture("no_spaces.txt"))
        reader = SynoIndexMetadataReader(filesystem, logger)

        reader.read("/media/album/video.mp4")

        assert filesystem.requested == [
            "/media/album/@eaDir/video.mp4/SYNOINDEX_MEDIA_INFO"
        ]

    def test_handles_a_path_with_spaces(self, logger):
        filesystem = _StubFilesystem(content=fixture("two_spaces.txt"))
        reader = SynoIndexMetadataReader(filesystem, logger)

        reader.read("/media/My Old Phone/IMG_0001.MOV")

        assert filesystem.requested == [
            "/media/My Old Phone/@eaDir/IMG_0001.MOV/SYNOINDEX_MEDIA_INFO"
        ]


class TestSuccessfulRead:
    """A readable, parseable index yields a Video."""

    def test_returns_parsed_metadata(self, logger):
        filesystem = _StubFilesystem(content=fixture("two_spaces.txt"))
        reader = SynoIndexMetadataReader(filesystem, logger)

        video = reader.read("/media/album/IMG_0001.MOV")

        assert video is not None
        assert video.path == "/media/album/IMG_0001.MOV"
        assert video.video_track.resolution == "1080x1920"
        assert video.video_track.framerate == 25
        assert video.audio_track.channels == 1

    def test_does_not_warn_on_success(self, logger):
        filesystem = _StubFilesystem(content=fixture("no_spaces.txt"))
        reader = SynoIndexMetadataReader(filesystem, logger)

        reader.read("/media/album/video.mp4")

        assert logger.warnings == []


class TestUnavailableIndex:
    """Every failure must be reported as unknown, never raised."""

    def test_missing_index_returns_none(self, logger):
        reader = SynoIndexMetadataReader(_StubFilesystem(content=None), logger)

        assert reader.read("/media/album/video.mp4") is None

    def test_missing_index_logs_at_debug_not_warning(self, logger):
        """Unindexed videos are ordinary; warning on each would flood the log."""
        reader = SynoIndexMetadataReader(_StubFilesystem(content=None), logger)

        reader.read("/media/album/video.mp4")

        assert logger.warnings == []
        assert len(logger.debugs) == 1

    def test_unreadable_index_returns_none(self, logger):
        """A legacy-encoded path makes read_file raise; the chain must continue."""
        error = UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
        reader = SynoIndexMetadataReader(_StubFilesystem(error=error), logger)

        assert reader.read("/media/album/video.mp4") is None

    def test_unreadable_index_is_logged_as_a_warning(self, logger):
        error = OSError("permission denied")
        reader = SynoIndexMetadataReader(_StubFilesystem(error=error), logger)

        reader.read("/media/album/video.mp4")

        assert len(logger.warnings) == 1

    def test_unparseable_content_returns_none(self, logger):
        reader = SynoIndexMetadataReader(_StubFilesystem(content="garbage"), logger)

        assert reader.read("/media/album/video.mp4") is None

    def test_unparseable_content_is_logged_as_a_warning(self, logger):
        """An index that exists but does not parse is worth surfacing."""
        reader = SynoIndexMetadataReader(_StubFilesystem(content="garbage"), logger)

        reader.read("/media/album/video.mp4")

        assert len(logger.warnings) == 1

    def test_implausible_content_returns_none(self, logger):
        """The parser's plausibility gate must reach the caller as 'unknown'."""
        record = "0 0 0 0 8 /x.mp4 " + " ".join(["0"] * 54)
        content = f"22 serialization::archive 19 0 0 0 0 2 1 1\n{record}\n"
        reader = SynoIndexMetadataReader(_StubFilesystem(content=content), logger)

        assert reader.read("/media/album/video.mp4") is None
