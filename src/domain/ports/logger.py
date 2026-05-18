"""Port for application logging."""
from abc import ABC, abstractmethod


class AppLogger(ABC):
    """Interface for application logging."""

    @abstractmethod
    def info(self, msg: str, *args, **kwargs) -> None:
        """Logs an informational message."""
        pass  # pragma: no cover

    @abstractmethod
    def warning(self, msg: str, *args, **kwargs) -> None:
        """Logs a warning message."""
        pass  # pragma: no cover

    @abstractmethod
    def error(self, msg: str, *args, **kwargs) -> None:
        """Logs an error message."""
        pass  # pragma: no cover

    @abstractmethod
    def title(self, text: str, char: str = "=") -> None:
        """Logs a title with automatic border calculation."""
        pass  # pragma: no cover

    @abstractmethod
    def subtitle(self, text: str, char: str = "-") -> None:
        """Logs a subtitle with automatic border calculation."""
        pass  # pragma: no cover
