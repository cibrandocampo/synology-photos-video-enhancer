"""SQLAlchemy database models."""
from sqlalchemy import Boolean, Column, Integer, String, Text, Index

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


class SettingsModel(Base):
    """Single-row table storing transcoding settings configured via the UI."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, default=1)
    hw_transcoding = Column(Boolean, nullable=False, default=True)
    execution_threads = Column(Integer, nullable=False, default=2)
    startup_delay = Column(Integer, nullable=False, default=30)
    execution_interval = Column(Integer, nullable=False, default=240)
    video_codec = Column(String(20), nullable=False, default="h264")
    video_bitrate = Column(Integer, nullable=False, default=2048)
    video_resolution = Column(String(10), nullable=False, default="720p")
    video_profile = Column(String(30), nullable=True)
    audio_codec = Column(String(20), nullable=False, default="aac")
    audio_bitrate = Column(Integer, nullable=False, default=128)
    audio_channels = Column(Integer, nullable=False, default=2)
    audio_profile = Column(String(20), nullable=True)
