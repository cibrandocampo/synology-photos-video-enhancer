from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from domain.models.transcoding import TranscodingStatus
from infrastructure.database import TranscodingModel, Database
from infrastructure.persistence import PersistentTranscoding


class TranscodingRepository:
    """Repository for transcoding persistence operations."""
    
    def __init__(self, database: Database):
        self.database = database
    
    def _model_to_persistent(self, model: TranscodingModel) -> PersistentTranscoding:
        """Converts a SQLAlchemy model to PersistentTranscoding."""
        return PersistentTranscoding(
            original_video_path=model.original_video_path,
            transcoded_video_path=model.transcoded_video_path,
            transcoded_video_resolution=model.transcoded_video_resolution,
            transcoded_video_codec=model.transcoded_video_codec,
            status=TranscodingStatus(model.status),
            error_message=model.error_message
        )
    
    def _persistent_to_model(self, persistent: PersistentTranscoding) -> TranscodingModel:
        """Converts a PersistentTranscoding to SQLAlchemy model."""
        data = persistent.to_dict()
        return TranscodingModel(**data)
    
    def save(self, transcoding: PersistentTranscoding) -> PersistentTranscoding:
        """
        Saves or updates a transcoding.
        
        Args:
            transcoding: PersistentTranscoding to save
            
        Returns:
            PersistentTranscoding: Saved entity
            
        Raises:
            IntegrityError: If there's a uniqueness conflict
        """
        session: Session = self.database.get_session()
        try:
            existing = session.query(TranscodingModel).filter_by(
                original_video_path=transcoding.original_video_path
            ).first()
            
            if existing:
                # Update existing
                data = transcoding.to_dict()
                for key, value in data.items():
                    setattr(existing, key, value)
                session.commit()
                session.refresh(existing)
                return self._model_to_persistent(existing)
            else:
                # Create new
                model = self._persistent_to_model(transcoding)
                session.add(model)
                session.commit()
                session.refresh(model)
                return self._model_to_persistent(model)
        except IntegrityError as e:
            session.rollback()
            raise
        finally:
            session.close()
    
    def find_by_original_path(self, original_path: str) -> Optional[PersistentTranscoding]:
        """
        Finds a transcoding by original video path.
        
        Args:
            original_path: Path to the original video
            
        Returns:
            PersistentTranscoding if exists, None otherwise
        """
        session: Session = self.database.get_session()
        try:
            model = session.query(TranscodingModel).filter_by(
                original_video_path=original_path
            ).first()
            return self._model_to_persistent(model) if model else None
        finally:
            session.close()
    
    def exists_by_original_path(self, original_path: str) -> bool:
        """
        Checks if a transcoding exists for the given original video path.
        
        Args:
            original_path: Path to the original video
            
        Returns:
            True if exists, False otherwise
        """
        return self.find_by_original_path(original_path) is not None

