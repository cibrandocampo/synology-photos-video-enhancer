"""Synology-specific constants."""
from enum import IntEnum


class MetadataIndex(IntEnum):
    """Indexes of metadata fields in Synology's metadata list."""
    DURATION = 31
    AUDIO_BITRATE = 32
    TOTAL_BITRATE = 33
    VIDEO_BITRATE = 34
    # The framerate is a rational, not a single number. Reading position 35 alone
    # returns 30000 for an NTSC video, where the rate is 30000/1001 = 29.97.
    FRAMERATE_NUMERATOR = 35
    FRAMERATE_DENOMINATOR = 36
    SAMPLE_RATE = 37
    CHANNELS = 38
    WIDTH = 39
    HEIGHT = 40
    FILE_SIZE = 41
    VIDEO_CODEC = 47
    CONTAINER = 49
    AUDIO_CODEC = 53


