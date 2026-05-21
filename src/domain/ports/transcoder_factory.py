"""Port for transcoder factory."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.models.transcoding import Transcoding
    from domain.ports.transcoder import Transcoder


class TranscoderFactory(ABC):
    """Interface for creating transcoder instances."""

    @abstractmethod
    def create(
        self, transcoding: "Transcoding", hw_transcoding: bool = True
    ) -> "Transcoder":
        """
        Creates a transcoder for the given transcoding.

        Args:
            transcoding: Transcoding object containing all necessary information
            hw_transcoding: Whether to use hardware acceleration. When False, software
                encoding is used regardless of available hardware. When True, hardware
                is used if detected, otherwise falls back to software.

        Returns:
            A configured Transcoder instance
        """
        pass  # pragma: no cover
