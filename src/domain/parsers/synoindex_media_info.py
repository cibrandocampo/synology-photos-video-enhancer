"""Parser for Synology's SYNOINDEX_MEDIA_INFO index file."""
from typing import List, Optional

from domain.models.video import Video


class SynoIndexMediaInfo:
    """Parser for Synology's SYNOINDEX_MEDIA_INFO (Boost serialization text archive).

    Line 2 holds the media record. Strings are serialised as `<byte_length> <content>`,
    and the media path is one of them, so splitting the line on whitespace shifts every
    field after the path by the number of spaces the path contains. This parser slices
    the path out by its declared byte length, keeping the remaining fields at the
    positions declared in MetadataIndex.
    """

    # Position of the token holding the declared byte length of the media path.
    _PATH_LENGTH_INDEX = 4
    # The path occupies one token position; nothing downstream reads its value, so it
    # is replaced by a marker. Video.from_synology_metadata receives the real path
    # as a separate argument.
    _PATH_PLACEHOLDER = "<path>"

    # A record whose geometry or framerate falls outside these bounds is not a video.
    # Rejecting it here is what makes callers fall back to another metadata source
    # instead of persisting a nonsensical resolution such as "44100x2".
    _MIN_DIMENSION = 16
    _MAX_DIMENSION = 16384
    _MIN_FRAMERATE = 1
    _MAX_FRAMERATE = 1000

    @classmethod
    def parse(cls, video_path: str, content: str) -> Optional[Video]:
        """
        Parses SYNOINDEX_MEDIA_INFO content into a Video.

        Args:
            video_path: Path of the video the metadata belongs to
            content: Full contents of the SYNOINDEX_MEDIA_INFO file

        Returns:
            Video with the parsed metadata, or None when the content is missing,
            malformed, does not match the expected layout, or yields physically
            impossible values. Callers are expected to fall back to another
            metadata source.
        """
        if not content:
            return None

        lines = content.splitlines()
        if len(lines) < 2:
            return None

        tokens = cls._normalise_tokens(lines[1])
        if tokens is None:
            return None

        video = Video.from_synology_metadata(video_path, tokens)

        return video if cls._is_plausible(video) else None

    @classmethod
    def _normalise_tokens(cls, line: str) -> Optional[List[str]]:
        """
        Splits the record into tokens, keeping the media path as a single token.

        Args:
            line: Line 2 of the SYNOINDEX_MEDIA_INFO file

        Returns:
            Token list aligned with MetadataIndex positions, or None when the line
            does not match the expected layout.
        """
        # Tokens 0-4 plus the remainder; the remainder starts at the first byte of
        # the path because split() consumes the separator run before it.
        parts = line.split(None, cls._PATH_LENGTH_INDEX + 1)
        if len(parts) <= cls._PATH_LENGTH_INDEX + 1:
            return None

        try:
            declared_length = int(parts[cls._PATH_LENGTH_INDEX])
        except ValueError:
            return None

        if declared_length < 0:
            return None

        # The declared length counts bytes, not characters: a path holding a single
        # accented character is one byte longer than it is long in characters, and
        # slicing by characters would leave the shift this parser exists to remove.
        remainder = parts[cls._PATH_LENGTH_INDEX + 1].encode("utf-8")
        if declared_length > len(remainder):
            return None

        separator = remainder[declared_length:declared_length + 1]
        if separator not in (b"", b" "):
            # The slice did not land on a field boundary, so the record does not
            # have the shape assumed here.
            return None

        # Decoding cannot fail here: `remainder` was encoded from a str, and the
        # slice starts right after the separator checked above, so it always begins
        # on a character boundary.
        tail = remainder[declared_length + 1:].decode("utf-8")

        return parts[:cls._PATH_LENGTH_INDEX + 1] + [cls._PATH_PLACEHOLDER] + tail.split()

    @classmethod
    def _is_plausible(cls, video: Video) -> bool:
        """
        Checks that the parsed values could describe a real video.

        Args:
            video: Video built from the parsed tokens

        Returns:
            True when geometry and framerate are within physical bounds.
        """
        track = video.video_track

        return (
            cls._MIN_DIMENSION <= track.width <= cls._MAX_DIMENSION
            and cls._MIN_DIMENSION <= track.height <= cls._MAX_DIMENSION
            and cls._MIN_FRAMERATE <= track.framerate <= cls._MAX_FRAMERATE
        )
