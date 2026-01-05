"""Port for video repository operations."""
from abc import ABC, abstractmethod
from typing import Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.models.transcoding import Transcoding


class VideoRepository(ABC):
    """Interface for video repository operations."""
    
    @abstractmethod
    def find_by_original_path(self, original_path: str) -> Optional["Transcoding"]:
        """
        Finds a transcoding by original video path.
        
        Args:
            original_path: Path to the original video
            
        Returns:
            Transcoding if found, None otherwise
        """
        pass
    
    @abstractmethod
    def exists_by_original_path(self, original_path: str) -> bool:
        """
        Checks if a transcoding exists for the given original video path.
        
        Args:
            original_path: Path to the original video
            
        Returns:
            True if exists, False otherwise
        """
        pass
    
    @abstractmethod
    def save(self, transcoding: "Transcoding") -> "Transcoding":
        """
        Saves or updates a transcoding.
        
        Args:
            transcoding: Transcoding to save
            
        Returns:
            Saved transcoding
        """
        pass
