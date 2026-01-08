"""Constantes relacionadas con hardware de transcodificación."""
from enum import Enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from domain.models.hardware import HardwareVideoAcceleration


class CPUVendor(str, Enum):
    """Fabricantes de CPU soportados."""
    INTEL = "intel"
    AMD = "amd"
    ARM = "arm"
    UNKNOWN = "desconocido"


class HardwareBackend(str, Enum):
    """Backends de aceleración por hardware."""
    QSV = "qsv"  # Intel Quick Sync Video
    VAAPI = "vaapi"  # Video Acceleration API (Intel/AMD)
    V4L2M2M = "v4l2m2m"  # Video4Linux2 Memory-to-Memory (ARM)
    NONE = "none"  # Sin aceleración por hardware
    
    def device_path(self) -> Optional[str]:
        """
        Gets the device path for this hardware backend.
        
        Returns:
            Device path string or None if backend is NONE
        """
        device_paths = {
            self.QSV: "/dev/dri/renderD128",
            self.VAAPI: "/dev/dri/renderD128",
            self.V4L2M2M: "/dev/video10",
            self.NONE: None,
        }
        return device_paths.get(self)
    
    @classmethod
    def from_hardware_acceleration(
        cls,
        hardware_acceleration: Optional["HardwareVideoAcceleration"]
    ) -> "HardwareBackend":
        """
        Converts HardwareVideoAcceleration to HardwareBackend.
        
        Args:
            hardware_acceleration: HardwareVideoAcceleration enum value or None
            
        Returns:
            HardwareBackend enum value (NONE if input is None)
        """
        if hardware_acceleration is None:
            return cls.NONE
        
        # Import here to avoid circular dependencies
        from domain.models.hardware import HardwareVideoAcceleration
        
        # Direct mapping since both enums have the same values
        mapping = {
            HardwareVideoAcceleration.QSV: cls.QSV,
            HardwareVideoAcceleration.VAAPI: cls.VAAPI,
            HardwareVideoAcceleration.V4L2M2M: cls.V4L2M2M,
        }
        
        return mapping.get(hardware_acceleration, cls.NONE)

