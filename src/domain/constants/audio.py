"""Audio-related constants and enums."""
from enum import Enum
from typing import Optional


class AudioEncoder(Enum):
    """Audio encoders for FFmpeg."""
    AAC = "libfdk_aac"
    MP3 = "libmp3lame"
    AC3 = "ac3"
    EAC3 = "eac3"
    PCM_S16LE = "pcm_s16le"
    OPUS = "libopus"
    VORBIS = "libvorbis"
    FLAC = "flac"


class AudioCodec(str, Enum):
    """Supported audio codecs."""
    AAC = "aac"
    MP3 = "mp3"
    AC3 = "ac3"
    EAC3 = "eac3"
    PCM_S16LE = "pcm_s16le"
    OPUS = "opus"
    VORBIS = "vorbis"
    FLAC = "flac"
    
    @classmethod
    def from_str(cls, value: str) -> "AudioCodec":
        """
        Creates an AudioCodec from a string value.
        
        Args:
            value: Codec name (case insensitive)
            
        Returns:
            AudioCodec enum value (defaults to AAC if invalid or empty)
        """
        if not value:
            return cls.AAC
        
        value_lower = value.lower()
        
        # Map common aliases
        if value_lower == "aac":
            return cls.AAC
        
        try:
            return cls(value_lower)
        except ValueError:
            return cls.AAC
    
    def encoder(self) -> str:
        """
        Gets the encoder name for this audio codec.
        
        Returns:
            Encoder name string (e.g., 'aac', 'libmp3lame')
        """
        encoder_map = {
            AudioCodec.AAC: "aac",
            AudioCodec.MP3: "libmp3lame",
            AudioCodec.AC3: "ac3",
            AudioCodec.EAC3: "eac3",
            AudioCodec.PCM_S16LE: "pcm_s16le",
            AudioCodec.OPUS: "libopus",
            AudioCodec.VORBIS: "libvorbis",
            AudioCodec.FLAC: "flac",
        }
        return encoder_map.get(self, "aac")  # Default to aac


class AACProfile(str, Enum):
    """AAC audio profiles."""
    LC = "aac_lc"
    HE = "aac_he"
    HE_V2 = "aac_he_v2"
    
    @classmethod
    def from_str(cls, value: str) -> Optional["AACProfile"]:
        """
        Gets or creates an AACProfile from a string value.
        
        Args:
            value: Profile name (case insensitive, e.g., 'aac_lc', 'aac_he', 'aac_he_v2')
            
        Returns:
            AACProfile enum value or None if invalid or empty
        """
        if not value:
            return None
        
        value_lower = value.lower().strip()
        
        # Map common aliases
        alias_map = {
            "aac_low": cls.LC,
            "aac_lc": cls.LC,
            "aac_he": cls.HE,
            "aac_he_v2": cls.HE_V2,
            "he_v2": cls.HE_V2,
        }
        
        if value_lower in alias_map:
            return alias_map[value_lower]
        
        try:
            return cls(value_lower)
        except ValueError:
            return None
