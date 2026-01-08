"""Common utility functions for infrastructure layer."""


from typing import Any


def to_int(value: Any, default: int = 0) -> int:
    """Converts a value to an integer."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value

    if isinstance(value, str):
        value = value.strip()
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    return default

