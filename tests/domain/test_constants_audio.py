"""Tests for audio-related constants."""
import pytest
from domain.constants.audio import AudioCodec, AACProfile, AudioEncoder


class TestAudioCodec:
    """Tests for AudioCodec enum."""
    
    def test_from_str_valid(self):
        """Test creating AudioCodec from valid string."""
        assert AudioCodec.from_str("aac") == AudioCodec.AAC
        assert AudioCodec.from_str("MP3") == AudioCodec.MP3
        assert AudioCodec.from_str("opus") == AudioCodec.OPUS
    
    def test_from_str_invalid(self):
        """Test creating AudioCodec from invalid string defaults to AAC."""
        assert AudioCodec.from_str("invalid") == AudioCodec.AAC
        assert AudioCodec.from_str("") == AudioCodec.AAC
    
    def test_from_str_case_insensitive(self):
        """Test that from_str is case insensitive."""
        assert AudioCodec.from_str("AAC") == AudioCodec.AAC
        assert AudioCodec.from_str("OpUs") == AudioCodec.OPUS
    
    def test_encoder(self):
        """Test encoder method returns correct encoder."""
        # Note: AudioCodec.encoder() returns simple codec names, not AudioEncoder values
        assert AudioCodec.AAC.encoder() == "aac"
        assert AudioCodec.MP3.encoder() == "libmp3lame"


class TestAACProfile:
    """Tests for AACProfile enum."""
    
    def test_from_str_valid(self):
        """Test creating AACProfile from valid string."""
        assert AACProfile.from_str("aac_lc") == AACProfile.LC
        assert AACProfile.from_str("aac_he") == AACProfile.HE
        assert AACProfile.from_str("aac_he_v2") == AACProfile.HE_V2
        assert AACProfile.from_str("he_v2") == AACProfile.HE_V2  # Alias
    
    def test_from_str_invalid(self):
        """Test creating AACProfile from invalid string returns None."""
        assert AACProfile.from_str("invalid") is None
        assert AACProfile.from_str("") is None


class TestAudioEncoder:
    """Tests for AudioEncoder enum."""
    
    def test_encoder_values(self):
        """Test that encoder values are correct."""
        assert AudioEncoder.AAC.value == "libfdk_aac"
        assert AudioEncoder.MP3.value == "libmp3lame"
        assert AudioEncoder.OPUS.value == "libopus"
