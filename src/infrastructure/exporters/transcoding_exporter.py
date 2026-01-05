from typing import Optional
from domain.models.transcoding import Transcoding
from infrastructure.persistence import PersistentTranscoding
from infrastructure.repositories import TranscodingRepository


class TranscodingExporter:
    """Exports domain Transcoding entities to SQLite database."""
    
    def __init__(self, repository: TranscodingRepository):
        self.repository = repository
    
    def export(self, transcoding: Transcoding) -> PersistentTranscoding:
        """
        Exports a domain Transcoding to the database.
        
        Args:
            transcoding: Domain Transcoding entity
            
        Returns:
            PersistentTranscoding that was saved
        """
        # Convert domain entity to persistent representation
        persistent = PersistentTranscoding.from_domain(transcoding)
        
        # Save to database
        return self.repository.save(persistent)
    
    def exists(self, original_video_path: str) -> bool:
        """
        Checks if a transcoding exists for the given original video path.
        
        Args:
            original_video_path: Path to the original video
            
        Returns:
            True if exists, False otherwise
        """
        return self.repository.exists_by_original_path(original_video_path)
    
    def find_by_original_path(self, original_video_path: str) -> Optional[PersistentTranscoding]:
        """
        Finds a transcoding by original video path.
        
        Args:
            original_video_path: Path to the original video
            
        Returns:
            PersistentTranscoding if found, None otherwise
        """
        return self.repository.find_by_original_path(original_video_path)

