"""Module for querying FFmpeg codecs and hardware acceleration capabilities."""
import subprocess
import shutil
from typing import List, Optional


def get_available_hw_codecs() -> List[str]:
    """
    Gets the list of hardware-accelerated codecs available in FFmpeg.
    
    Returns:
        List of hardware codec names (e.g., ['h264_qsv', 'h264_vaapi', 'h264_v4l2m2m'])
    """
    if not shutil.which("ffmpeg"):
        return []
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        codecs = []
        for line in result.stdout.splitlines():
            # Line format: " V..... h264_qsv           Intel QSV H.264 encoder"
            # Look for hardware codecs (usually contain _qsv, _vaapi, _v4l2m2m, _nvenc)
            if any(marker in line for marker in ["_qsv", "_vaapi", "_v4l2m2m", "_nvenc"]):
                parts = line.split()
                if len(parts) >= 2:
                    codec_name = parts[1]
                    if codec_name not in codecs:
                        codecs.append(codec_name)
        
        return codecs
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return []


def get_available_hwaccels() -> List[str]:
    """
    Gets the list of hardware acceleration methods available in FFmpeg.
    
    Returns:
        List of hardware acceleration method names (e.g., ['qsv', 'vaapi', 'v4l2m2m'])
    """
    if not shutil.which("ffmpeg"):
        return []
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-hwaccels"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        hwaccels = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line or line.lower().startswith("hardware acceleration methods"):
                continue
            hwaccels.append(line)
        
        return hwaccels
    except (FileNotFoundError, subprocess.TimeoutExpired, Exception):
        return []


def has_codec(codec_name: str) -> bool:
    """
    Checks if a specific codec is available in FFmpeg.
    
    Args:
        codec_name: Name of the codec to check (e.g., 'h264_qsv')
        
    Returns:
        True if the codec is available
    """
    available_codecs = get_available_hw_codecs()
    return codec_name in available_codecs
