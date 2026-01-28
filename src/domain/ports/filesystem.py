"""Port for filesystem operations."""
from abc import ABC, abstractmethod
from typing import List, Optional


class Filesystem(ABC):
    """Interface for filesystem operations."""
    
    @abstractmethod
    def find_videos(self, directory: str) -> List[str]:
        """
        Finds all video files in a directory and subdirectories.
        
        Args:
            directory: Root directory to search
            
        Returns:
            List of full paths to video files
        """
        pass
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """
        Checks if a file exists.
        
        Args:
            path: File path to check
            
        Returns:
            True if file exists, False otherwise
        """
        pass
    
    @abstractmethod
    def read_file(self, path: str) -> Optional[str]:
        """
        Reads the contents of a file.

        Args:
            path: Path to the file

        Returns:
            File contents as string, or None if the file does not exist
        """
        pass

    @abstractmethod
    def ensure_directory(self, path: str) -> None:
        """
        Ensures a directory exists, creating it and parent directories if necessary.

        Args:
            path: Directory path to ensure exists
        """
        pass

    @abstractmethod
    def find_transcoded_video(self, original_video_path: str) -> str:
        """
        Finds the transcoded video file associated with an original video.
        
        In Synology Photo, transcoded videos are located at:
        <original_directory>/@eaDir/<filename>/SYNOPHOTO_FILM_M.mp4 or SYNOPHOTO_FILM_H.mp4
        
        Args:
            original_video_path: Full path to the original video
            
        Returns:
            Path to transcoded video if exists, empty string otherwise
        """
        pass
