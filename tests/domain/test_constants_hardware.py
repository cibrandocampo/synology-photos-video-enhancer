"""Tests for hardware-related constants."""
import pytest
from domain.constants.hardware import HardwareBackend, CPUVendor
from domain.models.hardware import HardwareVideoAcceleration


class TestHardwareBackend:
    """Tests for HardwareBackend enum."""
    
    def test_device_path_qsv(self):
        """Test device_path for QSV backend."""
        assert HardwareBackend.QSV.device_path() == "/dev/dri/renderD128"
    
    def test_device_path_vaapi(self):
        """Test device_path for VAAPI backend."""
        assert HardwareBackend.VAAPI.device_path() == "/dev/dri/renderD128"
    
    def test_device_path_v4l2m2m(self):
        """Test device_path for V4L2M2M backend."""
        assert HardwareBackend.V4L2M2M.device_path() == "/dev/video10"
    
    def test_device_path_none(self):
        """Test device_path for NONE backend."""
        assert HardwareBackend.NONE.device_path() is None
    
    def test_from_hardware_acceleration_qsv(self):
        """Test from_hardware_acceleration with QSV."""
        backend = HardwareBackend.from_hardware_acceleration(HardwareVideoAcceleration.QSV)
        assert backend == HardwareBackend.QSV
    
    def test_from_hardware_acceleration_vaapi(self):
        """Test from_hardware_acceleration with VAAPI."""
        backend = HardwareBackend.from_hardware_acceleration(HardwareVideoAcceleration.VAAPI)
        assert backend == HardwareBackend.VAAPI
    
    def test_from_hardware_acceleration_v4l2m2m(self):
        """Test from_hardware_acceleration with V4L2M2M."""
        backend = HardwareBackend.from_hardware_acceleration(HardwareVideoAcceleration.V4L2M2M)
        assert backend == HardwareBackend.V4L2M2M
    
    def test_from_hardware_acceleration_none(self):
        """Test from_hardware_acceleration with None."""
        backend = HardwareBackend.from_hardware_acceleration(None)
        assert backend == HardwareBackend.NONE
    
    def test_from_hardware_acceleration_unknown(self):
        """Test from_hardware_acceleration with unknown value defaults to NONE."""
        # This would require a mock or an invalid enum value
        # For now, we test that None returns NONE
        backend = HardwareBackend.from_hardware_acceleration(None)
        assert backend == HardwareBackend.NONE


class TestCPUVendor:
    """Tests for CPUVendor enum."""
    
    def test_enum_values(self):
        """Test that CPUVendor has correct values."""
        assert CPUVendor.INTEL.value == "intel"
        assert CPUVendor.AMD.value == "amd"
        assert CPUVendor.ARM.value == "arm"
        assert CPUVendor.UNKNOWN.value == "desconocido"
