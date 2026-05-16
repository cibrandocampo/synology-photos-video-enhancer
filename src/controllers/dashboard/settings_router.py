"""Settings page: GET (form) + POST (save)."""
import os
from fastapi import APIRouter, Depends, Form, Request
from starlette.responses import RedirectResponse
from typing import Optional

from domain.models.settings import TranscodingSettings
from infrastructure.web.auth import html_require_session

router = APIRouter()


_VIDEO_MAP: dict[str, tuple[str, str | None]] = {
    "mpeg4":           ("mpeg4", None),
    "mpeg4_simple":    ("mpeg4", "simple"),
    "mpeg4_advsimple": ("mpeg4", "advanced-simple"),
    "h264_baseline":   ("h264", "baseline"),
    "h264_main":       ("h264", "main"),
    "h264_high":       ("h264", "high"),
    "hevc_main":       ("hevc", "main"),
    "hevc_main10":     ("hevc", "main10"),
    "av1":             ("av1", None),
}

_AUDIO_MAP: dict[str, tuple[str, str | None]] = {
    "aac_lc":    ("aac", "aac_lc"),
    "aac_he":    ("aac", "aac_he"),
    "aac_he_v2": ("aac", "aac_he_v2"),
    "mp3":       ("mp3", None),
    "ac3":       ("ac3", None),
    "eac3":      ("eac3", None),
}


def _int(value: str, default: int) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


@router.get("/settings")
async def settings_get(
    request: Request,
    _user: str = Depends(html_require_session),
    saved: str = "",
):
    settings_use_case = request.app.state.settings_use_case
    settings = settings_use_case.load()
    templates = request.app.state.templates
    cpu_count = os.cpu_count() or 1
    return templates.TemplateResponse(
        request=request,
        name="settings.html",
        context={"settings": settings, "saved": saved == "1", "cpu_count": cpu_count},
    )


@router.post("/settings")
async def settings_post(
    request: Request,
    _user: str = Depends(html_require_session),
    hw_transcoding: Optional[str] = Form(None),
    execution_threads: str = Form("2"),
    startup_delay: str = Form("30"),
    execution_interval: str = Form("240"),
    video_codec: str = Form("h264_high"),
    video_bitrate: str = Form("2000"),
    video_resolution: str = Form("720p"),
    audio_codec: str = Form("aac_lc"),
    audio_bitrate: str = Form("128"),
    audio_channels: str = Form("2"),
):
    resolved_video_codec, resolved_video_profile = _VIDEO_MAP.get(video_codec, ("h264", "high"))
    resolved_audio_codec, resolved_audio_profile = _AUDIO_MAP.get(audio_codec, ("aac", "aac_lc"))
    settings = TranscodingSettings(
        hw_transcoding=hw_transcoding is not None,
        execution_threads=_int(execution_threads, 2),
        startup_delay=_int(startup_delay, 30),
        execution_interval=_int(execution_interval, 240),
        video_codec=resolved_video_codec,
        video_bitrate=_int(video_bitrate, 2048),
        video_resolution=video_resolution,
        video_profile=resolved_video_profile,
        audio_codec=resolved_audio_codec,
        audio_bitrate=_int(audio_bitrate, 128),
        audio_channels=_int(audio_channels, 2),
        audio_profile=resolved_audio_profile,
    )
    request.app.state.settings_use_case.save(settings)
    return RedirectResponse(url="/settings?saved=1", status_code=303)
