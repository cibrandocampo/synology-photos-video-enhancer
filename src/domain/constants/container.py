"""Container format constants and enums."""
from enum import Enum


class ContainerFormat(str, Enum):
    """Supported container formats."""
    MP4 = "mp4"
    MOV = "mov"
    M4V = "m4v"
    MKV = "mkv"
    AVI = "avi"
    WMV = "wmv"
    FLV = "flv"
    F4V = "f4v"
    TS = "ts"
    MTS = "mts"
    M2TS = "m2ts"
    THREE_GP = "3gp"
    
    @classmethod
    def from_str(cls, value: str) -> "ContainerFormat":
        """
        Creates a ContainerFormat from a string value.
        
        Args:
            value: Container format name (case insensitive)
            
        Returns:
            ContainerFormat enum value (defaults to MP4 if invalid or empty)
        """
        if not value:
            return cls.MP4
        
        value_lower = value.lower().strip()
        
        try:
            return cls(value_lower)
        except ValueError:
            return cls.MP4


def get_video_extensions() -> list[str]:
    """
    Gets all video file extensions from supported container formats.
    
    Returns a list of extensions in both lowercase and uppercase for compatibility.
    
    Returns:
        Sorted list of video extensions (e.g., ['3gp', '3GP', 'avi', 'AVI', ...])
    """
    extensions = []
    for container_format in ContainerFormat:
        ext = container_format.value
        extensions.append(ext.lower())
        extensions.append(ext.upper())
    return sorted(set(extensions))
