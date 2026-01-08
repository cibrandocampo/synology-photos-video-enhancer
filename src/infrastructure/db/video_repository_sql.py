"""SQL implementation of video repository."""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from domain.models.transcoding import Transcoding, TranscodingStatus
from domain.ports.video_repository import VideoRepository
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.models import TranscodingModel


class VideoRepositorySQL(VideoRepository):
    """SQL implementation of video repository."""
    
    def __init__(self, db_connection: DatabaseConnection):
        """
        Initializes the repository.
        
        Args:
            db_connection: Database connection instance
        """
        self.db_connection = db_connection
    
    def _model_to_domain(self, model: TranscodingModel) -> Transcoding:
        """Converts SQLAlchemy model to domain Transcoding."""
        # This is a simplified conversion - in a real implementation,
        # you'd need to reconstruct the Video objects from the stored paths
        # For now, we'll need to adapt this based on your actual domain model structure
        from domain.models.video import Video
        from domain.models.video import VideoTrack, AudioTrack, Container
        
        # Parse resolution
        width, height = map(int, model.transcoded_video_resolution.split('x'))
        
        # Create video objects (simplified - you may need to read actual metadata)
        original_video = Video(
            path=model.original_video_path,
            video_track=VideoTrack(width=0, height=0, codec_name="", framerate=0),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        transcoded_video = Video(
            path=model.transcoded_video_path,
            video_track=VideoTrack(
                width=width,
                height=height,
                codec_name=model.transcoded_video_codec,
                framerate=0
            ),
            audio_track=AudioTrack(),
            container=Container(format="mp4")
        )
        
        return Transcoding(
            original_video=original_video,
            transcoded_video=transcoded_video,
            status=TranscodingStatus(model.status),
            error_message=model.error_message
        )
    
    def _domain_to_model(self, transcoding: Transcoding) -> TranscodingModel:
        """Converts domain Transcoding to SQLAlchemy model."""
        resolution = f"{transcoding.transcoded_video.video_track.width}x{transcoding.transcoded_video.video_track.height}"
        
        # Get status value - it's already a string due to use_enum_values=True
        status_value = transcoding.status if isinstance(transcoding.status, str) else transcoding.status.value
        
        return TranscodingModel(
            original_video_path=transcoding.original_video.path,
            transcoded_video_path=transcoding.transcoded_video.path,
            transcoded_video_resolution=resolution,
            transcoded_video_codec=transcoding.transcoded_video.video_track.codec_name,
            status=status_value,
            error_message=transcoding.error_message
        )
    
    def find_by_original_path(self, original_path: str) -> Optional[Transcoding]:
        """Finds a transcoding by original video path."""
        session: Session = self.db_connection.get_session()
        try:
            model = session.query(TranscodingModel).filter_by(
                original_video_path=original_path
            ).first()
            return self._model_to_domain(model) if model else None
        finally:
            session.close()
    
    def exists_by_original_path(self, original_path: str) -> bool:
        """Checks if a transcoding exists for the given original video path."""
        return self.find_by_original_path(original_path) is not None
    
    def save(self, transcoding: Transcoding) -> Transcoding:
        """Saves or updates a transcoding."""
        session: Session = self.db_connection.get_session()
        try:
            existing = session.query(TranscodingModel).filter_by(
                original_video_path=transcoding.original_video.path
            ).first()
            
            if existing:
                # Update existing
                model = self._domain_to_model(transcoding)
                for key, value in model.__dict__.items():
                    if not key.startswith('_'):
                        setattr(existing, key, value)
                session.commit()
                session.refresh(existing)
                return self._model_to_domain(existing)
            else:
                # Create new
                model = self._domain_to_model(transcoding)
                session.add(model)
                session.commit()
                session.refresh(model)
                return self._model_to_domain(model)
        except IntegrityError as e:
            session.rollback()
            raise
        finally:
            session.close()
