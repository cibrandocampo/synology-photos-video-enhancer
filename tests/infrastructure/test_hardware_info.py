"""Tests for local hardware info."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from domain.models.hardware import CPUInfo, CPUVendor, HardwareVideoAcceleration
from infrastructure.hardware.local_hardware_info import LocalHardwareInfo


class TestLocalHardwareInfo:
    """Tests for LocalHardwareInfo."""
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_init_detects_hardware(self, mock_path_class, mock_cpuinfo):
        """Test that __init__ detects hardware."""
        # Mock CPU info
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel Core i7',
            'arch': 'x86_64'
        }
        
        # Mock Path.exists() to return True for DRI device
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        
        assert hw_info._cpu_info is not None
        assert hw_info._video_acceleration is not None
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_cpu_property_caches(self, mock_path_class, mock_cpuinfo):
        """Test that cpu property caches the result."""
        mock_cpuinfo.return_value = {'vendor_id_raw': 'GenuineIntel', 'brand_raw': 'Intel', 'arch': 'x86_64'}
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        
        # First access
        cpu1 = hw_info.cpu
        # Second access should return same object (cached)
        cpu2 = hw_info.cpu
        
        assert cpu1 is cpu2
        # Note: cpuinfo.get_cpu_info is called during __init__, so call_count >= 1
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_video_acceleration_property_caches(self, mock_path_class, mock_cpuinfo):
        """Test that video_acceleration property caches the result."""
        mock_cpuinfo.return_value = {'vendor_id_raw': 'GenuineIntel', 'brand_raw': 'Intel', 'arch': 'x86_64'}
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        
        # First access
        accel1 = hw_info.video_acceleration
        # Second access should return same object (cached)
        accel2 = hw_info.video_acceleration
        
        assert accel1 is accel2
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_detect_video_acceleration_intel_with_qsv(self, mock_path_class, mock_cpuinfo):
        """Test video acceleration detection for Intel with QSV."""
        mock_cpuinfo.return_value = {'vendor_id_raw': 'GenuineIntel', 'brand_raw': 'Intel Core i7', 'arch': 'x86_64'}
        
        # Mock Path.exists() to return True for DRI device
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        accel = hw_info.video_acceleration
        
        # Should detect QSV for Intel
        assert accel == HardwareVideoAcceleration.QSV
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_detect_video_acceleration_amd_with_vaapi(self, mock_path_class, mock_cpuinfo):
        """Test video acceleration detection for AMD with VAAPI."""
        mock_cpuinfo.return_value = {'vendor_id_raw': 'AuthenticAMD', 'brand_raw': 'AMD Ryzen', 'arch': 'x86_64'}
        
        # Mock Path.exists() to return True for DRI device
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        accel = hw_info.video_acceleration
        
        # Should detect VAAPI for AMD
        assert accel == HardwareVideoAcceleration.VAAPI
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_detect_video_acceleration_arm_with_v4l2m2m(self, mock_path_class, mock_cpuinfo):
        """Test video acceleration detection for ARM with V4L2M2M."""
        mock_cpuinfo.return_value = {'vendor_id_raw': 'ARM', 'brand_raw': 'ARM Processor', 'arch': 'aarch64'}
        
        # Mock Path.exists() - ARM doesn't check for DRI device
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False  # Doesn't matter for ARM
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        accel = hw_info.video_acceleration
        
        # Should detect V4L2M2M for ARM
        assert accel == HardwareVideoAcceleration.V4L2M2M
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_detect_video_acceleration_no_hardware(self, mock_path_class, mock_cpuinfo):
        """Test video acceleration detection when no hardware available."""
        mock_cpuinfo.return_value = {'vendor_id_raw': 'Unknown', 'brand_raw': 'Unknown', 'arch': 'unknown'}
        
        # Mock Path.exists() 
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        accel = hw_info.video_acceleration
        
        # Should return None when vendor is unknown
        assert accel is None
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_info_exception_handling(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_info handles exceptions gracefully."""
        mock_cpuinfo.side_effect = Exception("CPU info error")
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        # Should return default CPUInfo on error
        assert cpu is not None
        assert cpu.vendor.value == "unknown"  # Default vendor
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_cores_various_formats(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_cores handles various CPU info formats."""
        # Test with 'count' key
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel',
            'arch': 'x86_64',
            'count': 8
        }
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        assert cpu.cores == 8
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_cores_fallback(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_cores falls back to 1 on error."""
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel',
            'arch': 'x86_64',
            # No cores information
        }
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        # Should default to 1 core
        assert cpu.cores == 1
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_cores_with_cpu_count_key(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_cores uses 'cpu_count' key."""
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel Core i7',
            'arch': 'x86_64',
            'cpu_count': 8
        }
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        assert cpu.cores == 8
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_cores_with_cores_key(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_cores uses 'cores' key."""
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel Core i7',
            'arch': 'x86_64',
            'cores': 4
        }
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        assert cpu.cores == 4
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_cores_non_integer(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_cores handles non-integer values."""
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel Core i7',
            'arch': 'x86_64',
            'count': 'invalid'
        }
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        # Should default to 1
        assert cpu.cores == 1
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_detect_video_acceleration_no_dri_device(self, mock_path_class, mock_cpuinfo):
        """Test _detect_video_acceleration returns None when DRI device missing."""
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel Core i7',
            'arch': 'x86_64',
            'count': 4
        }
        
        # Mock Path.exists() to return False (DRI device missing)
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = False
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        acceleration = hw_info.video_acceleration
        
        # Should return None when DRI device is missing for Intel/AMD
        assert acceleration is None
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_vendor_detection(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_vendor detects different vendors correctly."""
        # Test Intel detection via vendor_id
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'GenuineIntel',
            'brand_raw': 'Intel Core i7',
            'arch': 'x86_64',
            'count': 4
        }
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        assert cpu.vendor == CPUVendor.INTEL
    
    @patch('infrastructure.hardware.local_hardware_info.cpuinfo.get_cpu_info')
    @patch('infrastructure.hardware.local_hardware_info.Path')
    def test_get_cpu_vendor_amd_detection(self, mock_path_class, mock_cpuinfo):
        """Test _get_cpu_vendor detects AMD."""
        mock_cpuinfo.return_value = {
            'vendor_id_raw': 'AuthenticAMD',
            'brand_raw': 'AMD Ryzen',
            'arch': 'x86_64',
            'count': 8
        }
        mock_path_instance = Mock()
        mock_path_instance.exists.return_value = True
        mock_path_class.return_value = mock_path_instance
        
        hw_info = LocalHardwareInfo()
        cpu = hw_info.cpu
        
        assert cpu.vendor == CPUVendor.AMD

