"""Tests for MainController."""
import pytest
from unittest.mock import Mock, MagicMock
from application.process_videos_use_case import ProcessVideosUseCase
from application.process_result import ProcessResult
from controllers.main_controller import MainController


class TestMainController:
    """Tests for MainController."""
    
    @pytest.fixture
    def mock_use_case(self):
        """Creates a mock ProcessVideosUseCase."""
        mock = Mock(spec=ProcessVideosUseCase)
        mock.execute.return_value = ProcessResult(
            total_processed=10,
            transcoded=5,
            already_transcoded=3,
            errors=2
        )
        return mock
    
    @pytest.fixture
    def mock_logger(self):
        """Creates a mock logger."""
        return Mock()
    
    @pytest.fixture
    def controller(self, mock_use_case, mock_logger):
        """Creates a MainController instance for testing."""
        return MainController(mock_use_case, logger=mock_logger)
    
    def test_run_executes_use_case(self, controller, mock_use_case):
        """Test that run executes the use case."""
        result = controller.run()
        
        mock_use_case.execute.assert_called_once()
        assert isinstance(result, ProcessResult)
    
    def test_run_returns_process_result(self, controller):
        """Test that run returns ProcessResult."""
        result = controller.run()
        
        assert isinstance(result, ProcessResult)
        assert result.total_processed == 10
        assert result.transcoded == 5
    
    def test_parse_args_default(self, monkeypatch):
        """Test parsing arguments with defaults."""
        import sys
        # Mock sys.argv to have no arguments (just script name)
        monkeypatch.setattr(sys, "argv", ["main.py"])
        args = MainController.parse_args()
        
        assert args is not None
        assert args.dry_run is False
        assert args.verbose is False
        assert args.only_new is False
    
    def test_parse_args_with_flags(self, monkeypatch):
        """Test parsing arguments with flags."""
        import sys
        monkeypatch.setattr(sys, "argv", ["main.py", "--dry-run", "--verbose", "--only-new"])
        args = MainController.parse_args()
        
        assert args.dry_run is True
        assert args.verbose is True
        assert args.only_new is True
    
    def test_display_results(self, controller, mock_logger):
        """Test that _display_results logs correctly."""
        result = ProcessResult(
            total_processed=10,
            transcoded=5,
            already_transcoded=3,
            errors=2
        )
        
        controller._display_results(result)
        
        # Verify logger was called
        assert mock_logger.info.called
