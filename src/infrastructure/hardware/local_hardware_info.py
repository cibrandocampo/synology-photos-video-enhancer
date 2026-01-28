"""Local hardware information implementation."""
import cpuinfo
from pathlib import Path
from typing import Optional

from domain.models.hardware import CPUInfo, CPUVendor, HardwareVideoAcceleration, VENDOR_TO_VIDEO_ACCELERATION
from domain.ports.hardware_info import HardwareInfo

HW_ACCELERATION_DEVICE_PATH = "/dev/dri/renderD128"


class LocalHardwareInfo(HardwareInfo):
    """
    Local hardware information implementation.
    """

    def __init__(self):
        """
        Initializes hardware info with lazy detection (no side effects).
        """
        self._cpu_info: Optional[CPUInfo] = None
        self._video_acceleration: Optional[HardwareVideoAcceleration] = None

    @property
    def cpu(self) -> CPUInfo:
        """
        Gets CPU information.
        """
        if self._cpu_info is None:
            self._cpu_info = self._get_cpu_info()
        return self._cpu_info

    @property
    def video_acceleration(self) -> Optional[HardwareVideoAcceleration]:
        """
        Gets the hardware video acceleration method available.
        """
        if self._video_acceleration is None:
            self._video_acceleration = self._detect_video_acceleration()
        return self._video_acceleration
    
   
    def _get_cpu_info(self) -> CPUInfo:
        """
        Gets CPU information using py-cpuinfo, caching the result to avoid multiple calls.
        
        Detects:
        - CPU vendor (Intel, AMD, ARM, or Unknown)
        - CPU name/brand
        - CPU architecture
        - Number of CPU cores
        """
        if self._cpu_info is None:
            try:
                raw_cpu_info = cpuinfo.get_cpu_info()
            except Exception:
                # Use default values from CPUInfo model
                self._cpu_info = CPUInfo()
                return self._cpu_info
            else:
                arch = raw_cpu_info.get('arch', 'unknown')
                name = raw_cpu_info.get('brand_raw', 'unknown')
                vendor = self._get_cpu_vendor(
                    arch=arch.lower(),
                    vendor_id=raw_cpu_info.get('vendor_id_raw', '').lower(),
                    name=name.lower()
                )
                self._cpu_info = CPUInfo(
                    vendor=vendor,
                    name=name,
                    arch=arch,
                    cores=self._get_cpu_cores(raw_cpu_info)
                )
                return self._cpu_info
        
        return self._cpu_info
    
    def _get_cpu_vendor(self, arch: str, vendor_id: str, name: str) -> CPUVendor:
        """
        Detects the CPU vendor.
        """
        # Detect Intel
        if 'intel' in vendor_id or 'intel' in name or 'genuineintel' in vendor_id:
            return CPUVendor.INTEL
        
        # Detect AMD
        if 'amd' in vendor_id or 'amd' in name or 'authenticamd' in vendor_id:
            return CPUVendor.AMD
        
        # Detect ARM
        if 'arm' in arch or 'aarch64' in arch or 'arm' in vendor_id or 'arm' in name:
            return CPUVendor.ARM
        
        return CPUVendor.UNKNOWN
    
    def _get_cpu_cores(self, raw_cpu_info: dict) -> int:
        """
        Detects the number of CPU cores from CPU information.
        """
        try:
            # Try different keys that py-cpuinfo might use
            cores = raw_cpu_info.get('count', raw_cpu_info.get('cpu_count', raw_cpu_info.get('cores', 1)))
            return cores if isinstance(cores, int) else 1
        except Exception:
            return 1
    
    
    def _detect_video_acceleration(self) -> Optional[HardwareVideoAcceleration]:
        """
        Detects the hardware video acceleration method based on CPU vendor.
        
        For Intel and AMD, also verifies that the DRI device exists at 
        /dev/dri/renderD128. If the device doesn't exist, returns None.
        """

        preferred_acceleration = VENDOR_TO_VIDEO_ACCELERATION.get(self.cpu.vendor)
        
        if self.cpu.vendor in (CPUVendor.INTEL, CPUVendor.AMD):
            if not Path(HW_ACCELERATION_DEVICE_PATH).exists():
                return None

        return preferred_acceleration

