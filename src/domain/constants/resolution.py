"""Video resolution constants and enums."""
from enum import Enum


class VideoResolution(str, Enum):
    """Standard video resolutions."""
    P144 = "144p"  # 256 × 144 - Very low SD
    P240 = "240p"  # 426 × 240 - Low SD
    P360 = "360p"  # 640 × 360 - nHD
    P480 = "480p"  # 854 × 480 - SD (FWVGA)
    P720 = "720p"  # 1280 × 720 - HD
    P1080 = "1080p"  # 1920 × 1080 - Full HD (FHD)
    P1440 = "1440p"  # 2560 × 1440 - Quad HD (QHD / 2K)
    P2160 = "2160p"  # 3840 × 2160 - Ultra HD / 4K
    
    @classmethod
    def from_str(cls, value: str) -> "VideoResolution":
        """
        Creates a VideoResolution from a string value.
        
        Args:
            value: Resolution name (case insensitive, e.g., '720p', '1080p')
            
        Returns:
            VideoResolution enum value (defaults to P480 if invalid or empty)
        """
        if not value:
            return cls.P480
        
        value_lower = value.lower().strip()
        
        try:
            return cls(value_lower)
        except ValueError:
            return cls.P480
    
    @property
    def width(self) -> int:
        """Gets the width in pixels for this resolution."""
        resolutions = {
            VideoResolution.P144: 256,
            VideoResolution.P240: 426,
            VideoResolution.P360: 640,
            VideoResolution.P480: 854,
            VideoResolution.P720: 1280,
            VideoResolution.P1080: 1920,
            VideoResolution.P1440: 2560,
            VideoResolution.P2160: 3840,
        }
        return resolutions[self]
    
    @property
    def height(self) -> int:
        """Gets the height in pixels for this resolution."""
        resolutions = {
            VideoResolution.P144: 144,
            VideoResolution.P240: 240,
            VideoResolution.P360: 360,
            VideoResolution.P480: 480,
            VideoResolution.P720: 720,
            VideoResolution.P1080: 1080,
            VideoResolution.P1440: 1440,
            VideoResolution.P2160: 2160,
        }
        return resolutions[self]
    
    @property
    def name(self) -> str:
        """Gets the common name of the resolution."""
        return self.value
