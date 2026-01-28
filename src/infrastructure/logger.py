"""Logger configuration."""
import inspect
import logging
from typing import Optional

from domain.ports.logger import AppLogger


class EnhancedLogger(AppLogger):
    """Enhanced logger with title and subtitle methods."""

    def __init__(self, logger: logging.Logger):
        """
        Initializes the enhanced logger.

        Args:
            logger: Standard logging.Logger instance
        """
        self._logger = logger

    def __getattr__(self, name):
        """Delegates all other attributes to the underlying logger."""
        return getattr(self._logger, name)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Logs an informational message."""
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Logs a warning message."""
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Logs an error message."""
        self._logger.error(msg, *args, **kwargs)

    def title(self, text: str, char: str = "=") -> None:
        """
        Logs a title with automatic border calculation.

        Args:
            text: Title text
            char: Character to use for border (default: "=")
        """
        border = char * len(text)
        self._logger.info(border)
        self._logger.info(text)
        self._logger.info(border)

    def subtitle(self, text: str, char: str = "-") -> None:
        """
        Logs a subtitle with automatic border calculation.

        Args:
            text: Subtitle text
            char: Character to use for border (default: "-")
        """
        border = char * len(text)
        self._logger.info(border)
        self._logger.info(text)
        self._logger.info(border)


class Logger:
    """Logger utility class."""
    
    _enhanced_loggers: dict[str, EnhancedLogger] = {}
    _root_logger_configured: bool = False
    
    @staticmethod
    def _configure_root_logger(level: str):
        """
        Configures the root logger once with shared handlers.
        All child loggers will inherit this configuration.
        
        Args:
            level: Logging level
        """
        if Logger._root_logger_configured:
            return
        
        # Configure root logger (empty string = root)
        root_logger = logging.getLogger()
        
        # Configure root logger only once
        if not root_logger.handlers:
            formatter = logging.Formatter(
                '%(asctime)s (%(name)s) %(levelname)s | %(message)s',
                datefmt='%Y-%m-%dT%H:%M:%S%z'
            )
            
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
            
            # Set logging level
            try:
                level_int = getattr(logging, level.upper(), logging.INFO)
            except AttributeError:
                level_int = logging.INFO
            root_logger.setLevel(level_int)
        
        Logger._root_logger_configured = True
    
    @staticmethod
    def get_logger(name: str = None, level: str = None) -> EnhancedLogger:
        """
        Gets a configured logger instance with enhanced methods.
        
        Automatically detects the calling module name if name is not provided.
        All loggers share the same root configuration (formatter, handlers, level)
        but each displays its own module name.
        
        Args:
            name: Logger name (optional, will auto-detect from calling module if not provided)
            level: Logging level (defaults to settings)
            
        Returns:
            Enhanced logger instance with title and subtitle methods
        """
        # Use defaults first, then try to get from config if available
        default_level = "INFO"
        default_name = "synology-photos-video-enhancer"
        
        if not level:
            level = default_level
        
        # Configure root logger once (all children inherit this)
        Logger._configure_root_logger(level)
        
        # If no name provided, try to auto-detect or use config/default
        if not name:
            try:
                # Get the frame of the caller (skip this method and get_logger)
                frame = inspect.currentframe()
                if frame:
                    caller_frame = frame.f_back
                    if caller_frame:
                        # Get the module name from the caller's frame
                        module = inspect.getmodule(caller_frame)
                        if module and module.__name__:
                            name = module.__name__
                        else:
                            # Fallback: use filename if module not available
                            filename = caller_frame.f_globals.get('__name__', None)
                            if filename:
                                name = filename
            except Exception:
                pass
            
            # If auto-detection failed, use default
            if not name:
                name = default_name
        
        # Use logger name as cache key - each module gets its own EnhancedLogger
        # but all share the same underlying configuration
        if name not in Logger._enhanced_loggers:
            # Get logger - it will inherit handlers from root
            logger = logging.getLogger(name)
            
            # Set logging level (inherits from root if not set)
            try:
                level_int = getattr(logging, level.upper(), logging.INFO)
            except AttributeError:
                level_int = logging.INFO
            logger.setLevel(level_int)
            
            # Cache the EnhancedLogger instance for this name
            Logger._enhanced_loggers[name] = EnhancedLogger(logger)
        
        return Logger._enhanced_loggers[name]
