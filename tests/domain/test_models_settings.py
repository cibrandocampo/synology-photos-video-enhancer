"""Tests for TranscodingSettings domain model."""

from domain.models.settings import TranscodingSettings
from domain.constants.audio import AudioCodec, AACProfile
from domain.constants.video import VideoCodec, VideoProfile
from domain.constants.resolution import VideoResolution


class TestTranscodingSettingsDefaults:
    def test_default_values(self):
        s = TranscodingSettings()

        assert s.hw_transcoding is True
        assert s.execution_threads == 2
        assert s.startup_delay == 30
        assert s.execution_interval == 240
        assert s.video_codec == VideoCodec.H264.value
        assert s.video_bitrate == 2000
        assert s.video_resolution == VideoResolution.P720.value
        assert s.video_profile is None
        assert s.audio_codec == AudioCodec.AAC.value
        assert s.audio_bitrate == 128
        assert s.audio_channels == 2
        assert s.audio_profile is None


class TestAacHeV2RequiresStereoValidator:
    def test_aac_he_v2_non_stereo_is_forced_to_stereo(self):
        s = TranscodingSettings(audio_profile="aac_he_v2", audio_channels=6)

        assert s.audio_channels == 2

    def test_aac_he_v2_already_stereo_unchanged(self):
        s = TranscodingSettings(audio_profile="aac_he_v2", audio_channels=2)

        assert s.audio_channels == 2

    def test_other_profile_keeps_original_channels(self):
        s = TranscodingSettings(audio_profile="aac_lc", audio_channels=6)

        assert s.audio_channels == 6

    def test_no_profile_keeps_original_channels(self):
        s = TranscodingSettings(audio_profile=None, audio_channels=6)

        assert s.audio_channels == 6


class TestToVideoConfig:
    def test_h264_with_profile_produces_correct_config(self):
        s = TranscodingSettings(
            video_codec="h264",
            video_bitrate=2048,
            video_resolution="720p",
            video_profile="high",
        )
        cfg = s.to_video_config()

        assert cfg.codec == VideoCodec.H264
        assert cfg.bitrate == 2048
        assert cfg.profile == VideoProfile.HIGH
        assert cfg.resolution == VideoResolution.P720

    def test_hevc_with_profile(self):
        s = TranscodingSettings(video_codec="hevc", video_profile="main")
        cfg = s.to_video_config()

        assert cfg.codec == VideoCodec.HEVC
        assert cfg.profile == VideoProfile.MAIN

    def test_av1_no_profile_returns_none(self):
        s = TranscodingSettings(video_codec="av1", video_profile=None)
        cfg = s.to_video_config()

        assert cfg.codec == VideoCodec.AV1
        assert cfg.profile is None

    def test_codec_without_profile_field_gets_none(self):
        s = TranscodingSettings(video_codec="av1", video_profile="high")
        cfg = s.to_video_config()

        assert cfg.profile is None

    def test_h264_without_explicit_profile_gets_default(self):
        s = TranscodingSettings(video_codec="h264", video_profile=None)
        cfg = s.to_video_config()

        assert cfg.codec == VideoCodec.H264
        assert cfg.profile is not None

    def test_resolution_dimensions_are_populated(self):
        s = TranscodingSettings(video_resolution="720p")
        cfg = s.to_video_config()

        assert cfg.width > 0
        assert cfg.height > 0


class TestToAudioConfig:
    def test_aac_with_profile(self):
        s = TranscodingSettings(
            audio_codec="aac", audio_profile="aac_lc", audio_channels=2
        )
        cfg = s.to_audio_config()

        assert cfg.codec == AudioCodec.AAC
        assert cfg.profile == AACProfile.LC
        assert cfg.channels == 2

    def test_aac_without_profile_returns_none_profile(self):
        s = TranscodingSettings(audio_codec="aac", audio_profile=None)
        cfg = s.to_audio_config()

        assert cfg.codec == AudioCodec.AAC
        assert cfg.profile is None

    def test_mp3_ignores_profile_field(self):
        s = TranscodingSettings(audio_codec="mp3", audio_profile="aac_lc")
        cfg = s.to_audio_config()

        assert cfg.codec == AudioCodec.MP3
        assert cfg.profile is None

    def test_bitrate_and_channels_forwarded(self):
        s = TranscodingSettings(audio_codec="aac", audio_bitrate=192, audio_channels=2)
        cfg = s.to_audio_config()

        assert cfg.bitrate == 192
        assert cfg.channels == 2
