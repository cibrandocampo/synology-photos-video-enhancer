"""Hardware-related domain models."""
from enum import Enum
from pydantic import BaseModel


class CPUVendor(str, Enum):
    """Supported CPU vendors."""
    INTEL = "intel"
    AMD = "amd"
    ARM = "arm"
    UNKNOWN = "unknown"


class CPUInfo(BaseModel):
    """CPU information."""
    vendor: CPUVendor = CPUVendor.UNKNOWN
    name: str = "unknown"
    arch: str = "unknown"
    cores: int = 1
    
    def __str__(self) -> str:
        """Returns a human-readable string representation."""
        return f"{self.vendor.value} ({self.cores} cores) | {self.name}"


class HardwareVideoAcceleration(str, Enum):
    """Hardware acceleration backends."""
    QSV = "qsv"  # Intel Quick Sync Video
    VAAPI = "vaapi"  # Video Acceleration API (Intel/AMD)
    V4L2M2M = "v4l2m2m"  # Video4Linux2 Memory-to-Memory (ARM)


# Mapping from CPU vendor to preferred hardware video acceleration
VENDOR_TO_VIDEO_ACCELERATION: dict[CPUVendor, HardwareVideoAcceleration] = {
    CPUVendor.INTEL: HardwareVideoAcceleration.QSV,
    CPUVendor.AMD: HardwareVideoAcceleration.VAAPI,
    CPUVendor.ARM: HardwareVideoAcceleration.V4L2M2M,
    CPUVendor.UNKNOWN: None,
}
