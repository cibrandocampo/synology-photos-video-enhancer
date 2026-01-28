"""Database connection management."""
import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from domain.models.app_config import DatabaseConfig
from domain.ports.logger import AppLogger

Base = declarative_base()


class DatabaseConnection:
    """Manages database connection."""
    
    def __init__(self, db_config: DatabaseConfig, logger: AppLogger):
        """
        Initializes database connection.

        Args:
            db_config: Database configuration object
            logger: Application logger
        """
        self.config = db_config
        self.logger = logger
        self.engine = create_engine(
            f"sqlite:///{db_config.path}",
            connect_args={"check_same_thread": False}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def is_empty(self) -> bool:
        """
        Checks if the database is empty (doesn't exist or has no tables).
        
        Returns:
            True if database is empty, False otherwise
        """
        # Check if database file exists
        if not os.path.exists(self.config.path):
            return True
        
        # Check if database has any tables
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        return len(tables) == 0
    
    def has_all_tables(self) -> bool:
        """
        Verifies that all required tables exist in the database.
        
        Returns:
            True if all required tables exist, False otherwise
        """
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())
        
        # Get all required tables from Base metadata
        required_tables = set(Base.metadata.tables.keys())
        
        return required_tables.issubset(existing_tables)
    
    def create_tables(self):
        """
        Creates all tables in the database.
        
        Should only be called if database is empty.
        """
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self):
        """Gets a database session."""
        return self.SessionLocal()
    
    def initialize(self):
        """
        Initializes the database connection and ensures tables exist.
        
        Creates tables if database is empty, or verifies all required tables
        exist if database already has data.
        
        Raises:
            RuntimeError: If database exists but is missing required tables
        """
        self.logger.info("Initializing database connection...")

        # Check if database is empty
        if self.is_empty():
            self.logger.info("Database is empty, creating tables...")
            self.create_tables()
            self.logger.info("Tables created successfully")
        else:
            self.logger.info("Database exists, verifying tables...")
            if not self.has_all_tables():
                error_msg = (
                    "Database exists but is missing required tables. "
                    "Please ensure the database schema is correct or use an empty database."
                )
                self.logger.error(error_msg)
                raise RuntimeError(error_msg)
            self.logger.info("All required tables exist")

        # Verify connection
        session = self.get_session()
        session.close()
        self.logger.info("Database connection established successfully")
