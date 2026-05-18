"""Tests for MainController."""
import pytest
from unittest.mock import Mock
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
