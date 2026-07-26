"""Video frame rate constants and enums."""
from enum import Enum
from fractions import Fraction


class FrameRate(Enum):
    """Video frame rates using exact fractional values for NTSC rates."""
    # Cine
    FPS_23_976 = Fraction(24000, 1001)
    FPS_24 = Fraction(24, 1)
    FPS_25 = Fraction(25, 1)
    
    # Broadcast / NTSC
    FPS_29_97 = Fraction(30000, 1001)
    FPS_30 = Fraction(30, 1)
    FPS_50 = Fraction(50, 1)
    FPS_59_94 = Fraction(60000, 1001)
    FPS_60 = Fraction(60, 1)
    
    # High frame rate / gaming / slow motion
    FPS_120 = Fraction(120, 1)
    FPS_144 = Fraction(144, 1)
    FPS_240 = Fraction(240, 1)
    
    def to_float(self) -> float:
        """Converts the frame rate to a float value."""
        return float(self.value)
    
    @classmethod
    def from_rate(cls, framerate: float) -> "FrameRate":
        """
        Finds the closest FrameRate to a measured rate.

        Takes the exact value: 29.97 resolves to FPS_29_97 rather than being
        rounded to 30 first. The members are stored as exact fractions for
        precisely this reason, so quantising the input before comparing would
        discard what they exist to represent.

        Args:
            framerate: Measured frames per second, fractional rates included

        Returns:
            Closest FrameRate enum value, or FPS_30 as default
        """
        if framerate <= 0:
            return cls.FPS_30

        closest = cls.FPS_30
        min_diff = abs(framerate - cls.FPS_30.to_float())

        for fps in cls:
            diff = abs(framerate - fps.to_float())
            if diff < min_diff:
                min_diff = diff
                closest = fps

        return closest
    
    @classmethod
    def get_framerate_for_light_videos(cls, original_framerate: "FrameRate") -> "FrameRate":
        """
        Gets the optimal frame rate for light videos (low bitrate/compression).
        
        Reduces high frame rates to lower values to optimize bitrate and file size
        while maintaining acceptable quality for mobile/streaming use cases.
        
        Conversion rules:
        - FPS_50 => FPS_25
        - FPS_59_94 => FPS_29_97
        - FPS_60 => FPS_30
        - FPS_120 => FPS_30
        - FPS_144 => FPS_24
        - FPS_240 => FPS_30
        
        For other frame rates, returns the same value.
        
        Args:
            framerate: Original FrameRate
            
        Returns:
            FrameRate optimized for light videos
        """
        conversion_map = {
            cls.FPS_50: cls.FPS_25,
            cls.FPS_59_94: cls.FPS_29_97,
            cls.FPS_60: cls.FPS_30,
            cls.FPS_120: cls.FPS_30,
            cls.FPS_144: cls.FPS_24,
            cls.FPS_240: cls.FPS_30,
        }
        
        return conversion_map.get(original_framerate, original_framerate)
