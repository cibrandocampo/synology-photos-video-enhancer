"""Port for transcoder factory."""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.models.transcoding import Transcoding
    from domain.ports.transcoder import Transcoder


class TranscoderFactory(ABC):
    """Interface for creating transcoder instances."""

    @abstractmethod
    def create(self, transcoding: "Transcoding") -> "Transcoder":
        """
        Creates a transcoder for the given transcoding.

        Args:
            transcoding: Transcoding object containing all necessary information

        Returns:
            A configured Transcoder instance
        """
        pass
