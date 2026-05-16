"""Domain DTO returned by the dashboard stats use case."""
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.models.transcoding import TranscodingStatus


CANONICAL_STATUSES: tuple[str, ...] = tuple(s.value for s in TranscodingStatus)


class CodecCount(BaseModel):
    """Number of completed transcodings produced with a given codec."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    codec: str
    count: int = Field(ge=0)


class ResolutionCount(BaseModel):
    """Number of completed transcodings produced at a given resolution."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    resolution: str
    count: int = Field(ge=0)


class LatestTranscoding(BaseModel):
    """Lightweight projection of a `transcodings` row for the dashboard list."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    original_video_path: str
    transcoded_video_path: str
    status: str
    transcoded_video_codec: str
    transcoded_video_resolution: str
    error_message: Optional[str] = None


class ErrorCount(BaseModel):
    """Aggregated error message (truncated to 100 chars by the repository)."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    error_summary: str
    count: int = Field(ge=0)


class DashboardStats(BaseModel):
    """Immutable payload consumed by both the HTML and JSON dashboard routes."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    total: int = Field(ge=0)
    status_counts: dict[str, int]
    success_rate: float = Field(ge=0.0, le=100.0)
    codec_distribution: list[CodecCount]
    resolution_distribution: list[ResolutionCount]
    latest_transcodings: list[LatestTranscoding] = Field(max_length=5)
    top_errors: list[ErrorCount] = Field(max_length=5)

    @field_validator("status_counts", mode="after")
    @classmethod
    def normalise_status_counts(cls, value: dict[str, int]) -> dict[str, int]:
        unknown = set(value) - set(CANONICAL_STATUSES)
        if unknown:
            raise ValueError(f"Unknown status keys: {sorted(unknown)}")
        for count in value.values():
            if count < 0:
                raise ValueError("Status counts must be non-negative")
        return {status: value.get(status, 0) for status in CANONICAL_STATUSES}
