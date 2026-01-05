"""SQLAlchemy database models."""
from sqlalchemy import Column, String, Text, Index

from infrastructure.db.connection import Base


class TranscodingModel(Base):
    """SQLAlchemy model for transcodings table."""
    __tablename__ = "transcodings"

    original_video_path = Column(String(1000), primary_key=True, nullable=False, index=True)
    transcoded_video_path = Column(String(1000), nullable=False)
    transcoded_video_resolution = Column(String(20), nullable=False)  # Format: "widthxheight"
    transcoded_video_codec = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    error_message = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_original_path", "original_video_path"),
        Index("idx_status", "status"),
    )
