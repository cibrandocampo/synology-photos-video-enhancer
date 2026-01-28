"""Local filesystem implementation."""
import os
import glob
from typing import List, Optional
from pathlib import Path

from domain.ports.filesystem import Filesystem


class LocalFilesystem(Filesystem):
    """Local filesystem implementation."""
    
    def __init__(self, video_extensions: List[str]):
        """
        Initializes the filesystem.
        
        Args:
            video_extensions: List of video file extensions to search for
        """
        self.video_extensions = video_extensions
    
    def find_videos(self, directory: str) -> List[str]:
        """Finds all video files in a directory and subdirectories."""
        if not os.path.isdir(directory):
            return []
        
        video_files = []
        for extension in self.video_extensions:
            pattern = os.path.join(directory, '**', f'*.{extension}')
            video_files.extend(glob.iglob(pattern, recursive=True))
        
        # Filter out files in @eaDir and #recycle (Synology directories)
        original_video_files = [
            video_path for video_path in video_files
            if '@eaDir' not in video_path and '#recycle' not in video_path
        ]
        
        return sorted(original_video_files)
    
    def file_exists(self, path: str) -> bool:
        """Checks if a file exists."""
        return os.path.isfile(path)

    def read_file(self, path: str) -> Optional[str]:
        """Reads file contents, returns None if file does not exist."""
        if not os.path.isfile(path):
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None

    def ensure_directory(self, path: str) -> None:
        """Ensures directory exists, creating parents if needed."""
        os.makedirs(path, exist_ok=True)
    
    def find_transcoded_video(self, original_video_path: str) -> str:
        """Finds the transcoded video file associated with an original video."""
        video_file = Path(original_video_path)
        ea_dir = video_file.parent / '@eaDir' / video_file.name
        
        if not ea_dir.exists():
            return ""
        
        # Look for common Synology transcoded files
        transcoded_names = ['SYNOPHOTO_FILM_M.mp4', 'SYNOPHOTO_FILM_H.mp4']
        
        for name in transcoded_names:
            transcoded_path = ea_dir / name
            if transcoded_path.exists():
                return str(transcoded_path)
        
        return ""
