from sqlalchemy import create_engine, Column, String, Text, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from infrastructure.config import Config

Base = declarative_base()


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


class Database:
    """Gestor de base de datos SQLite."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config().database_path
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False}  # Necesario para SQLite en threads
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def create_tables(self):
        """Crea todas las tablas en la base de datos."""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Obtiene una sesión de base de datos."""
        return self.SessionLocal()

