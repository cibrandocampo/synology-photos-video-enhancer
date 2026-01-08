"""Port for filesystem operations."""
from abc import ABC, abstractmethod
from typing import List


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
