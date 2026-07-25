"""Tests for ChainedMetadataReader."""
from typing import Optional

from domain.models.video import AudioTrack, Container, Video, VideoTrack
from domain.ports.video_metadata_reader import VideoMetadataReader
from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader


class _StubReader(VideoMetadataReader):
    """Hand-rolled stub honoring the `VideoMetadataReader` port."""

    def __init__(self, video: Optional[Video] = None,
                 error: Optional[Exception] = None) -> None:
        self._video = video
        self._error = error
        self.calls = 0

    def read(self, video_path: str) -> Optional[Video]:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._video


def make_video(width: int, height: int) -> Video:
    """Builds a Video with recognisable geometry."""
    return Video(
        path="/media/album/video.mp4",
        video_track=VideoTrack(
            width=width, height=height, codec_name="h264", framerate=30
        ),
        audio_track=AudioTrack(),
        container=Container(format="mp4"),
    )


class TestOrdering:
    """The chain expresses a preference, not a fallback of last resort."""

    def test_first_result_wins(self, logger):
        preferred = _StubReader(make_video(1920, 1080))
        fallback = _StubReader(make_video(640, 480))
        chain = ChainedMetadataReader([preferred, fallback], logger)

        video = chain.read("/media/album/video.mp4")

        assert video.video_track.resolution == "1920x1080"

    def test_later_readers_are_not_consulted_after_a_hit(self, logger):
        """The point of preferring the index is skipping the subprocess."""
        preferred = _StubReader(make_video(1920, 1080))
        fallback = _StubReader(make_video(640, 480))
        chain = ChainedMetadataReader([preferred, fallback], logger)

        chain.read("/media/album/video.mp4")

        assert preferred.calls == 1
        assert fallback.calls == 0

    def test_falls_through_when_the_first_reader_knows_nothing(self, logger):
        preferred = _StubReader(None)
        fallback = _StubReader(make_video(640, 480))
        chain = ChainedMetadataReader([preferred, fallback], logger)

        video = chain.read("/media/album/video.mp4")

        assert video.video_track.resolution == "640x480"
        assert fallback.calls == 1


class TestResilience:
    """A broken source must not hide the ones behind it."""

    def test_raising_reader_does_not_abort_the_chain(self, logger):
        broken = _StubReader(error=RuntimeError("boom"))
        fallback = _StubReader(make_video(640, 480))
        chain = ChainedMetadataReader([broken, fallback], logger)

        video = chain.read("/media/album/video.mp4")

        assert video.video_track.resolution == "640x480"

    def test_raising_reader_is_logged(self, logger):
        broken = _StubReader(error=RuntimeError("boom"))
        chain = ChainedMetadataReader([broken, _StubReader(make_video(640, 480))], logger)

        chain.read("/media/album/video.mp4")

        assert len(logger.warnings) == 1

    def test_returns_none_when_no_reader_can_help(self, logger):
        chain = ChainedMetadataReader([_StubReader(None), _StubReader(None)], logger)

        assert chain.read("/media/album/video.mp4") is None

    def test_returns_none_when_every_reader_raises(self, logger):
        chain = ChainedMetadataReader(
            [_StubReader(error=RuntimeError("a")), _StubReader(error=RuntimeError("b"))],
            logger,
        )

        assert chain.read("/media/album/video.mp4") is None

    def test_empty_chain_returns_none(self, logger):
        assert ChainedMetadataReader([], logger).read("/media/album/video.mp4") is None
