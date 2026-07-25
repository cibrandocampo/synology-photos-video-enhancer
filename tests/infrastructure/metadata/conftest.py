"""Shared stubs for the metadata reader adapter tests."""
from typing import List, Optional

import pytest

from domain.ports.logger import AppLogger


class RecordingLogger(AppLogger):
    """Hand-rolled stub honoring the `AppLogger` port, capturing what was logged."""

    def __init__(self) -> None:
        self.debugs: List[str] = []
        self.infos: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []

    def debug(self, msg: str, *args, **kwargs) -> None:
        self.debugs.append(msg)

    def info(self, msg: str, *args, **kwargs) -> None:
        self.infos.append(msg)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self.warnings.append(msg)

    def error(self, msg: str, *args, **kwargs) -> None:
        self.errors.append(msg)

    def title(self, text: str, char: str = "=") -> None:
        self.infos.append(text)

    def subtitle(self, text: str, char: str = "-") -> None:
        self.infos.append(text)


class StubCompletedProcess:
    """Mimics the subset of subprocess.CompletedProcess the reader uses."""

    def __init__(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class StubRunner:
    """Callable standing in for subprocess.run, capturing the command it received."""

    def __init__(self, result: Optional[StubCompletedProcess] = None,
                 error: Optional[Exception] = None):
        self._result = result
        self._error = error
        self.command: Optional[List[str]] = None
        self.timeout: Optional[int] = None
        self.calls = 0

    def __call__(self, command, **kwargs):
        self.calls += 1
        self.command = command
        self.timeout = kwargs.get("timeout")
        if self._error is not None:
            raise self._error
        return self._result


@pytest.fixture
def logger() -> RecordingLogger:
    """Provides a logger that records every message."""
    return RecordingLogger()
