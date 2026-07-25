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
        pass  # pragma: no cover

    @abstractmethod
    def exists_by_original_path(self, original_path: str) -> bool:
        """
        Checks if a transcoding exists for the given original video path.
        
        Args:
            original_path: Path to the original video
            
        Returns:
            True if exists, False otherwise
        """
        pass  # pragma: no cover

    @abstractmethod
    def save(self, transcoding: "Transcoding") -> "Transcoding":
        """
        Saves or updates a transcoding.

        Args:
            transcoding: Transcoding to save

        Returns:
            Saved transcoding
        """
        pass  # pragma: no cover

    @abstractmethod
    def update_transcoded_metadata(
        self, original_path: str, width: int, height: int, codec: str
    ) -> bool:
        """
        Corrects the recorded description of an already transcoded output file.

        For records whose stored resolution or codec no longer match the file on
        disk, but whose file is correct — re-encoding those would be wasteful.
        Only acts on records whose current status is COMPLETED.

        Args:
            original_path: Path to the original video
            width: Measured width of the transcoded file
            height: Measured height of the transcoded file
            codec: Measured video codec of the transcoded file

        Returns:
            True if the record was updated, False if it did not exist or was not
            in COMPLETED status.
        """
        pass  # pragma: no cover

    @abstractmethod
    def reset_to_pending(self, original_path: str) -> bool:
        """
        Resets a transcoding to PENDING status, clearing any error message.
        Only acts on records whose current status is COMPLETED or FAILED.

        Args:
            original_path: Path to the original video

        Returns:
            True if the record was updated, False if it did not exist or
            was not in an eligible status (completed or failed).
        """
        pass  # pragma: no cover
