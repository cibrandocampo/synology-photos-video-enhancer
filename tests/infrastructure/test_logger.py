"""Tests for logger."""
import pytest
import logging
from unittest.mock import patch, Mock
from infrastructure.logger import Logger, EnhancedLogger


class TestLogger:
    """Tests for Logger."""
    
    def test_get_logger_returns_enhanced_logger(self):
        """Test that get_logger returns EnhancedLogger instance."""
        logger = Logger.get_logger()
        
        assert isinstance(logger, EnhancedLogger)
    
    def test_get_logger_singleton(self):
        """Test that get_logger returns same instance for same name."""
        logger1 = Logger.get_logger("test-logger")
        logger2 = Logger.get_logger("test-logger")
        
        # Should be same EnhancedLogger instance (wrapping same underlying logger)
        assert logger1._logger is logger2._logger
    
    def test_get_logger_different_names(self):
        """Test that get_logger returns different loggers for different names."""
        logger1 = Logger.get_logger("logger1")
        logger2 = Logger.get_logger("logger2")
        
        # Should be different underlying loggers
        assert logger1._logger is not logger2._logger
    
    def test_get_logger_auto_detects_name(self):
        """Test that get_logger auto-detects module name."""
        # This test verifies that get_logger works without explicit name
        # The actual auto-detection happens internally via inspect
        logger = Logger.get_logger()
        
        # Should return an EnhancedLogger
        assert isinstance(logger, EnhancedLogger)
        assert logger._logger is not None


class TestEnhancedLogger:
    """Tests for EnhancedLogger."""
    
    @pytest.fixture
    def mock_logger(self):
        """Creates a mock standard logger."""
        return Mock()
    
    @pytest.fixture
    def enhanced_logger(self, mock_logger):
        """Creates an EnhancedLogger instance."""
        return EnhancedLogger(mock_logger)
    
    def test_title(self, enhanced_logger, mock_logger):
        """Test title method logs border, text, and border."""
        enhanced_logger.title("Test Title")
        
        # Should log 3 times: border, title, border
        assert mock_logger.info.call_count == 3
        # First and last should be borders
        assert mock_logger.info.call_args_list[0][0][0] == "=" * len("Test Title")
        assert mock_logger.info.call_args_list[2][0][0] == "=" * len("Test Title")
    
    def test_title_custom_char(self, enhanced_logger, mock_logger):
        """Test title method with custom border character."""
        enhanced_logger.title("Test", char="-")
        
        # Should use custom character
        assert mock_logger.info.call_args_list[0][0][0] == "-" * len("Test")
    
    def test_subtitle(self, enhanced_logger, mock_logger):
        """Test subtitle method logs border, text, and border."""
        enhanced_logger.subtitle("Test Subtitle")
        
        # Should log 3 times: border, subtitle, border
        assert mock_logger.info.call_count == 3
        # Should use "-" as default
        assert mock_logger.info.call_args_list[0][0][0] == "-" * len("Test Subtitle")
    
    def test_subtitle_custom_char(self, enhanced_logger, mock_logger):
        """Test subtitle method with custom border character."""
        enhanced_logger.subtitle("Test", char="*")
        
        # Should use custom character
        assert mock_logger.info.call_args_list[0][0][0] == "*" * len("Test")
    
    def test_delegates_to_underlying_logger(self, enhanced_logger, mock_logger):
        """Test that EnhancedLogger delegates other methods to underlying logger."""
        enhanced_logger.info("test message")
        enhanced_logger.warning("test warning")
        enhanced_logger.error("test error")
        enhanced_logger.debug("test debug")
        
        assert mock_logger.info.called
        assert mock_logger.warning.called
        assert mock_logger.error.called
        assert mock_logger.debug.called
    
    def test_get_logger_with_custom_level(self):
        """Test get_logger with custom level."""
        logger = Logger.get_logger("test-level", level="DEBUG")
        
        assert isinstance(logger, EnhancedLogger)
        assert logger._logger.level == logging.DEBUG
    
    def test_get_logger_with_invalid_level(self):
        """Test get_logger with invalid level falls back to INFO."""
        logger = Logger.get_logger("test-invalid", level="INVALID_LEVEL")
        
        assert isinstance(logger, EnhancedLogger)
        # Should default to INFO
        assert logger._logger.level <= logging.INFO
    
    def test_get_logger_auto_detection_fallback(self):
        """Test get_logger auto-detection works."""
        # This test verifies that auto-detection doesn't crash
        # The actual implementation uses inspect which is hard to mock reliably
        logger = Logger.get_logger()
        
        # Should still return a logger (using default or detected name)
        assert isinstance(logger, EnhancedLogger)
    
    @patch('infrastructure.config.config.Config')
    def test_get_logger_config_exception_handling(self, mock_config_class):
        """Test get_logger handles config exceptions gracefully."""
        # Make config raise exception
        mock_config_class.get_instance.side_effect = RuntimeError("Config error")
        
        logger = Logger.get_logger()
        
        # Should still return a logger using defaults
        assert isinstance(logger, EnhancedLogger)
    
    def test_configure_root_logger_idempotent(self):
        """Test _configure_root_logger is idempotent."""
        # Reset the flag
        Logger._root_logger_configured = False
        
        # Call multiple times
        Logger._configure_root_logger("INFO")
        first_call = Logger._root_logger_configured
        
        Logger._root_logger_configured = False
        Logger._configure_root_logger("INFO")
        second_call = Logger._root_logger_configured
        
        # Both should mark as configured
        assert first_call is True
        assert second_call is True
    
    def test_configure_root_logger_with_existing_handlers(self):
        """Test _configure_root_logger when root logger already has handlers."""
        import logging
        
        # Reset the flag
        Logger._root_logger_configured = False
        
        # Get root logger and add a handler
        root_logger = logging.getLogger()
        original_handlers = root_logger.handlers[:]
        
        # Add a handler if none exist
        if not root_logger.handlers:
            root_logger.addHandler(logging.NullHandler())
        
        try:
            Logger._configure_root_logger("INFO")
            # Should mark as configured
            assert Logger._root_logger_configured is True
        finally:
            # Cleanup: remove handlers we added
            for handler in root_logger.handlers[:]:
                if handler not in original_handlers:
                    root_logger.removeHandler(handler)
    
    def test_configure_root_logger_invalid_level(self):
        """Test _configure_root_logger with invalid level."""
        # Reset the flag
        Logger._root_logger_configured = False
        
        # Call with invalid level
        Logger._configure_root_logger("INVALID_LEVEL")
        
        # Should still mark as configured
        assert Logger._root_logger_configured is True
    
    def test_get_logger_with_name_and_level(self):
        """Test get_logger with both name and level."""
        logger = Logger.get_logger("test-named-level", level="DEBUG")
        
        assert isinstance(logger, EnhancedLogger)
        assert logger._logger.level == logging.DEBUG
        assert logger._logger.name == "test-named-level"
    
    def test_get_logger_caching(self):
        """Test that get_logger caches loggers by name."""
        logger1 = Logger.get_logger("cached-test")
        logger2 = Logger.get_logger("cached-test")
        
        # Should be the same EnhancedLogger instance
        assert logger1 is logger2

