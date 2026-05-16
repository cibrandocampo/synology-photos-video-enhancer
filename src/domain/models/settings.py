"""Settings domain model."""
from typing import Optional
from pydantic import BaseModel, model_validator

from domain.constants.audio import AACProfile, AudioCodec
from domain.constants.resolution import VideoResolution
from domain.constants.video import VideoCodec, VideoProfile
from domain.models.app_config import AudioConfig, VideoConfig


class TranscodingSettings(BaseModel):
    hw_transcoding: bool = True
    execution_threads: int = 2
    startup_delay: int = 30
    execution_interval: int = 240
    video_codec: str = VideoCodec.H264.value
    video_bitrate: int = 2000
    video_resolution: str = VideoResolution.P720.value
    video_profile: Optional[str] = None
    audio_codec: str = AudioCodec.AAC.value
    audio_bitrate: int = 128
    audio_channels: int = 2
    audio_profile: Optional[str] = None

    @model_validator(mode="after")
    def aac_he_v2_requires_stereo(self) -> "TranscodingSettings":
        if self.audio_profile == "aac_he_v2" and self.audio_channels != 2:
            self.audio_channels = 2
        return self

    def to_video_config(self) -> VideoConfig:
        codec = VideoCodec.from_str(self.video_codec)
        resolution = VideoResolution.from_str(self.video_resolution)
        if self.video_profile and codec.supports_profile():
            profile = VideoProfile.from_str(self.video_profile, codec)
        else:
            profile = VideoProfile.get_default(codec) if codec.supports_profile() else None
        return VideoConfig(
            codec=codec,
            bitrate=self.video_bitrate,
            resolution=resolution,
            width=resolution.width,
            height=resolution.height,
            profile=profile,
        )

    def to_audio_config(self) -> AudioConfig:
        codec = AudioCodec.from_str(self.audio_codec)
        aac_profile = None
        if self.audio_profile and codec == AudioCodec.AAC:
            aac_profile = AACProfile.from_str(self.audio_profile)
        return AudioConfig(
            codec=codec,
            bitrate=self.audio_bitrate,
            channels=self.audio_channels,
            profile=aac_profile,
        )
