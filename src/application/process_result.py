"""Result model for video processing use case."""
from dataclasses import dataclass


@dataclass
class ProcessResult:
    """Result of video processing operation."""
    total_processed: int = 0
    already_transcoded: int = 0
    transcoded: int = 0
    errors: int = 0
    
    @property
    def is_success(self) -> bool:
        """
        Checks if the process was successful.
        
        Returns:
            True if no errors occurred, False otherwise
        """
        return self.errors == 0
    
    def __str__(self) -> str:
        """String representation of the result."""
        return (
            f"Processed: {self.total_processed}, "
            f"Already transcoded: {self.already_transcoded}, "
            f"Transcoded: {self.transcoded}, "
            f"Errors: {self.errors}"
        )
