"""Synology-specific constants."""
from enum import IntEnum


class MetadataIndex(IntEnum):
    """Indexes of metadata fields in Synology's metadata list."""
    DURATION = 31
    AUDIO_BITRATE = 32
    TOTAL_BITRATE = 33
    VIDEO_BITRATE = 34
    FRAMERATE = 35
    SAMPLE_RATE = 37
    CHANNELS = 38
    WIDTH = 39
    HEIGHT = 40
    FILE_SIZE = 41
    VIDEO_CODEC = 47
    CONTAINER = 49
    AUDIO_CODEC = 53


