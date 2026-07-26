"""Tests for the SYNOINDEX_MEDIA_INFO parser.

Fixtures are anonymised copies of real production records. Their byte layout is what
matters — number of spaces in the path, multibyte characters, declared lengths and
archive version are preserved exactly. Synthetic token lists are deliberately avoided
for the alignment cases: the original defect survived the suite precisely because no
fixture ever contained a path field.
"""
from pathlib import Path

import pytest

from domain.constants.synology import MetadataIndex
from domain.models.video import Video
from domain.parsers.synoindex_media_info import SynoIndexMediaInfo

FIXTURES = Path(__file__).parent.parent / "fixtures" / "synoindex"


def load(name: str) -> str:
    """Reads a fixture file as UTF-8 text."""
    return (FIXTURES / name).read_text(encoding="utf-8")


def record_line(name: str) -> str:
    """Returns line 2 of a fixture — the media record."""
    return load(name).splitlines()[1]


def as_content(record: str) -> str:
    """Wraps a record line in the surrounding archive lines."""
    return f"22 serialization::archive 19 0 0 0 0 2 1 1\n{record}\n"


def with_declared_length(record: str, length) -> str:
    """Rewrites the declared byte length of the path in a record line."""
    parts = record.split(None, 5)
    parts[4] = str(length)
    return " ".join(parts)


def build_record(path: str, width: str = "1920", height: str = "1080",
                 framerate_num: str = "30", framerate_den: str = "1",
                 token_count: int = 60) -> str:
    """Builds a synthetic record with a chosen path and geometry.

    Used only for the plausibility-gate cases, where the point is to control a single
    field exactly. Alignment is covered by the real fixtures.
    """
    tokens = ["0"] * 60
    tokens[MetadataIndex.WIDTH] = width
    tokens[MetadataIndex.HEIGHT] = height
    tokens[MetadataIndex.FRAMERATE_NUMERATOR] = framerate_num
    tokens[MetadataIndex.FRAMERATE_DENOMINATOR] = framerate_den
    tokens = tokens[:token_count]
    tail = " ".join(tokens[6:])
    return f"0 0 0 0 {len(path.encode('utf-8'))} {path} {tail}"


class TestAlignment:
    """The media path must never shift the fields that follow it."""

    def test_path_without_spaces(self):
        """Baseline: a path with no spaces parses correctly."""
        video = SynoIndexMediaInfo.parse("/media/video.mp4", load("no_spaces.txt"))

        assert video is not None
        assert video.video_track.width == 720
        assert video.video_track.height == 1280
        assert video.video_track.framerate == 30
        assert video.video_track.codec_name == "h264"
        assert video.audio_track.channels == 2
        assert video.container.format == "mp4"

    def test_path_with_one_space(self):
        """A single space in the path shifted width into the channels field."""
        video = SynoIndexMediaInfo.parse("/media/2023 Trip.mp4", load("one_space.txt"))

        assert video is not None
        assert video.video_track.width == 1280
        assert video.video_track.height == 720
        assert video.video_track.framerate == 50
        assert video.audio_track.channels == 2

    def test_path_with_one_space_is_not_the_production_corruption(self):
        """Regression: this record used to be stored as 2x1280."""
        video = SynoIndexMediaInfo.parse("/media/2023 Trip.mp4", load("one_space.txt"))

        assert video.video_track.resolution == "1280x720"
        assert video.video_track.resolution != "2x1280"

    def test_path_with_two_spaces(self):
        """Two spaces shifted the audio sample rate into the width field."""
        video = SynoIndexMediaInfo.parse("/media/IMG_0001.MOV", load("two_spaces.txt"))

        assert video is not None
        assert video.video_track.width == 1080
        assert video.video_track.height == 1920
        assert video.video_track.framerate == 25
        assert video.video_track.codec_name == "hevc"
        assert video.audio_track.channels == 1

    def test_path_with_two_spaces_is_not_the_production_corruption(self):
        """Regression: this record used to be stored as 44100x2."""
        video = SynoIndexMediaInfo.parse("/media/IMG_0001.MOV", load("two_spaces.txt"))

        assert video.video_track.resolution == "1080x1920"
        assert video.video_track.resolution != "44100x2"

    def test_accented_path_is_sliced_by_bytes(self):
        """The declared length counts bytes: this path is 76 bytes and 75 characters."""
        video = SynoIndexMediaInfo.parse(
            "/media/VID-20200511-WA0002.mp4", load("accented_path.txt")
        )

        assert video is not None
        assert video.video_track.width == 352
        assert video.video_track.height == 640
        assert video.video_track.framerate == 30
        assert video.audio_track.channels == 2

    def test_video_path_is_the_argument_not_the_embedded_path(self):
        """The embedded path is the indexed location, which may differ from ours."""
        video = SynoIndexMediaInfo.parse("/media/renamed.mp4", load("no_spaces.txt"))

        assert video.path == "/media/renamed.mp4"


class TestFractionalFramerate:
    """The framerate spans two positions: a numerator and a denominator.

    Every fixture used to carry a whole rate, so position 36 looked like a constant
    flag and reading position 35 alone worked by coincidence. In the production
    library 41% of indexed videos carry a fractional rate.
    """

    def test_ntsc_rate_is_evaluated_not_truncated(self):
        video = SynoIndexMediaInfo.parse("/media/clip.MOV", load("ntsc_framerate.txt"))

        assert video is not None
        assert video.video_track.framerate == pytest.approx(30000 / 1001)

    def test_ntsc_rate_is_not_the_bare_numerator(self):
        """Reading position 35 alone gave 30000, which the gate then rejected."""
        video = SynoIndexMediaInfo.parse("/media/clip.MOV", load("ntsc_framerate.txt"))

        assert video.video_track.framerate != 30000

    def test_ntsc_rate_is_not_rounded_to_thirty(self):
        """29.97 must survive; rounding here is what the enum's fractions prevent."""
        video = SynoIndexMediaInfo.parse("/media/clip.MOV", load("ntsc_framerate.txt"))

        assert video.video_track.framerate != 30

    def test_ntsc_sixty_rate(self):
        video = SynoIndexMediaInfo.parse(
            "/media/clip.mp4", load("ntsc_60_framerate.txt")
        )

        assert video.video_track.framerate == pytest.approx(60000 / 1001)

    def test_the_rest_of_the_record_still_aligns(self):
        """Splitting the field must not shift anything after it."""
        video = SynoIndexMediaInfo.parse("/media/clip.MOV", load("ntsc_framerate.txt"))

        assert video.video_track.resolution == "1920x1080"
        assert video.audio_track.channels == 2
        assert video.video_track.codec_name == "hevc"

    @pytest.mark.parametrize(
        "fixture, expected",
        [("no_spaces.txt", 30), ("two_spaces.txt", 25), ("one_space.txt", 50)],
    )
    def test_whole_rates_are_unchanged(self, fixture, expected):
        """A denominator of 1 must behave exactly as before."""
        video = SynoIndexMediaInfo.parse("/media/clip.mp4", load(fixture))

        assert video.video_track.framerate == expected

    def test_zero_denominator_is_rejected(self):
        """A rate of 30/0 must not become a plausible-looking 30 fps.

        The numerator is deliberately one that would pass the plausibility gate on
        its own. With an implausible numerator the gate rejects the record whether
        or not the zero denominator is handled at all, so the test would pass
        against code that defaults the denominator to 1 — pinning nothing.
        """
        record = build_record("/media/video.mp4", framerate_num="30",
                              framerate_den="0")

        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_an_implausible_rate_is_rejected(self):
        """Reading position 35 alone yielded 30000, which the gate must refuse."""
        record = build_record("/media/video.mp4", framerate_num="30000",
                              framerate_den="1")

        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_a_truncated_record_is_rejected(self):
        """Cutting the record at 36 drops the denominator — and width and height.

        The gate refuses it on geometry before the framerate is ever considered, so
        this pins truncation handling, not the denominator rule. That rule is pinned
        in `tests/domain/test_models_video.py`, where no gate can mask it.
        """
        record = build_record("/media/video.mp4", token_count=36)

        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None


class TestFixturesReproduceTheDefect:
    """Proves the fixtures are real regressions rather than tests that always passed.

    Each case parses the fixture the way the code used to — a plain whitespace split —
    and asserts it yields the exact corruption observed in production, then asserts the
    parser does not.
    """

    @staticmethod
    def naive_resolution(fixture: str) -> str:
        """Reproduces the original defect: split line 2 on whitespace, index blindly."""
        tokens = record_line(fixture).split()
        video = Video.from_synology_metadata("/media/video.mp4", tokens)
        return video.video_track.resolution

    def test_one_space_fixture_used_to_yield_2x1280(self):
        assert self.naive_resolution("one_space.txt") == "2x1280"

        video = SynoIndexMediaInfo.parse("/media/video.mp4", load("one_space.txt"))
        assert video.video_track.resolution == "1280x720"

    def test_two_spaces_fixture_used_to_yield_a_sample_rate_as_width(self):
        """The source record is mono, so the shifted width/height pair is 44100x1."""
        assert self.naive_resolution("two_spaces.txt") == "44100x1"

        video = SynoIndexMediaInfo.parse("/media/video.mp4", load("two_spaces.txt"))
        assert video.video_track.resolution == "1080x1920"

    def test_transcoded_record_used_to_yield_44100x2(self):
        """The exact value stored 40 times in production, from the transcoded record."""
        assert self.naive_resolution("two_spaces_transcoded.txt") == "44100x2"

        video = SynoIndexMediaInfo.parse(
            "/media/SYNOPHOTO_FILM_H.mp4", load("two_spaces_transcoded.txt")
        )
        assert video.video_track.resolution == "720x1280"

    def test_accented_fixture_used_to_yield_a_sample_rate_as_width(self):
        """Two spaces and a multibyte character: width became the audio sample rate."""
        assert self.naive_resolution("accented_path.txt") == "48000x2"

        video = SynoIndexMediaInfo.parse("/media/video.mp4", load("accented_path.txt"))
        assert video.video_track.resolution == "352x640"

    def test_no_spaces_fixture_was_never_affected(self):
        """The baseline must parse identically both ways, or it is not a baseline."""
        assert self.naive_resolution("no_spaces.txt") == "720x1280"


class TestArchiveVersions:
    """Field positions are identical across the archive versions observed."""

    @pytest.mark.parametrize(
        "fixture, version, expected_resolution",
        [
            ("no_spaces.txt", "19", "720x1280"),
            ("accented_path.txt", "17", "352x640"),
        ],
    )
    def test_version_is_not_assumed(self, fixture, version, expected_resolution):
        """Both v17 and v19 records parse with the same field positions."""
        content = load(fixture)

        assert content.splitlines()[0].split()[2] == version

        video = SynoIndexMediaInfo.parse("/media/video.mp4", content)
        assert video.video_track.resolution == expected_resolution


class TestMalformedContent:
    """Anything that does not match the expected layout must be reported as unknown."""

    def test_empty_content(self):
        assert SynoIndexMediaInfo.parse("/media/video.mp4", "") is None

    def test_none_content(self):
        assert SynoIndexMediaInfo.parse("/media/video.mp4", None) is None

    def test_single_line_content(self):
        content = "22 serialization::archive 19 0 0 0 0 2 1 1\n"
        assert SynoIndexMediaInfo.parse("/media/video.mp4", content) is None

    def test_record_line_too_short(self):
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content("0 0 0")) is None

    def test_declared_length_is_not_an_integer(self):
        record = with_declared_length(record_line("no_spaces.txt"), "abc")
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_declared_length_is_negative(self):
        record = with_declared_length(record_line("no_spaces.txt"), -1)
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_declared_length_longer_than_the_record(self):
        record = with_declared_length(record_line("no_spaces.txt"), 100000)
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_declared_length_does_not_land_on_a_separator(self):
        """83 is correct for this fixture; 82 lands inside the path."""
        record = with_declared_length(record_line("no_spaces.txt"), 82)
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None


class TestPlausibilityGate:
    """Physically impossible values must be rejected, not persisted."""

    def test_width_from_a_shifted_sample_rate(self):
        """44100 is an audio sample rate, never a width."""
        record = build_record("/media/video.mp4", width="44100")
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_zero_height(self):
        record = build_record("/media/video.mp4", height="0")
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_zero_width(self):
        record = build_record("/media/video.mp4", width="0")
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_framerate_from_a_shifted_bitrate(self):
        """6498826 is a bitrate; read as fps it snapped the output to 30."""
        record = build_record("/media/video.mp4", framerate_num="6498826")
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_zero_framerate(self):
        record = build_record("/media/video.mp4", framerate_num="0")
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_dimension_above_the_upper_bound(self):
        record = build_record("/media/video.mp4", width="20000")
        assert SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record)) is None

    def test_plausible_record_is_accepted(self):
        """The gate must not reject a legitimate record."""
        record = build_record("/media/video.mp4")
        video = SynoIndexMediaInfo.parse("/media/video.mp4", as_content(record))

        assert video is not None
        assert video.video_track.resolution == "1920x1080"
