"""Tests for process result."""
import pytest
from application.process_result import ProcessResult, ProcessStatus


class TestProcessResult:
    """Tests for ProcessResult."""
    
    def test_default_values(self):
        """Test ProcessResult with default values."""
        result = ProcessResult()
        
        assert result.total_processed == 0
        assert result.already_transcoded == 0
        assert result.transcoded == 0
        assert result.errors == 0
    
    def test_is_success_no_errors(self):
        """Test is_success returns True when no errors."""
        result = ProcessResult(errors=0)
        
        assert result.is_success is True
    
    def test_is_success_with_errors(self):
        """Test is_success returns False when there are errors."""
        result = ProcessResult(errors=5)
        
        assert result.is_success is False
    
    def test_str_representation(self):
        """Test string representation of ProcessResult."""
        result = ProcessResult(
            total_processed=10,
            already_transcoded=3,
            transcoded=5,
            errors=2
        )
        
        str_repr = str(result)
        
        assert "10" in str_repr
        assert "3" in str_repr
        assert "5" in str_repr
        assert "2" in str_repr
