"""Port for hardware information."""
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.models.hardware import CPUInfo, HardwareVideoAcceleration


class HardwareInfo(ABC):
    """
    Interface for hardware information.
    
    Provides access to CPU information and hardware video acceleration capabilities.
    Implementations should detect hardware lazily and cache results for performance.
    """
    
    @property
    @abstractmethod
    def cpu(self) -> "CPUInfo":
        """
        Gets CPU information.
        
        Returns:
            CPUInfo object containing:
            - vendor: CPU vendor (Intel, AMD, ARM, or Unknown)
            - name: CPU brand/name
            - arch: CPU architecture
            - cores: Number of CPU cores
        """
        pass
    
    @property
    @abstractmethod
    def video_acceleration(self) -> Optional["HardwareVideoAcceleration"]:
        """
        Gets the hardware video acceleration method available.
        
        The acceleration method is determined based on:
        - CPU vendor (Intel -> QSV, AMD -> VAAPI, ARM -> V4L2M2M)
        - For Intel/AMD: verification that DRI device exists at /dev/dri/renderD128
        
        Returns:
            HardwareVideoAcceleration enum value (QSV, VAAPI, or V4L2M2M) 
            or None if not available (unknown vendor or missing DRI device for Intel/AMD)
        """
        pass
