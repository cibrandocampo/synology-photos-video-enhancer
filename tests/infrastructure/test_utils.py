"""Tests for infrastructure utilities."""
import pytest
from infrastructure.utils import to_int


class TestToInt:
    """Tests for to_int utility function."""
    
    def test_to_int_valid_string(self):
        """Test to_int converts valid string to int."""
        assert to_int("123") == 123
        assert to_int("0") == 0
        assert to_int("-5") == -5
    
    def test_to_int_with_default(self):
        """Test to_int returns default for invalid input."""
        assert to_int("invalid", default=42) == 42
        assert to_int(None, default=10) == 10
        assert to_int("", default=99) == 99
    
    def test_to_int_without_default(self):
        """Test to_int returns 0 when no default provided."""
        assert to_int("invalid") == 0
        assert to_int(None) == 0
