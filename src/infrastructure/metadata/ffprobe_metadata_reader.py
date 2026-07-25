"""Video metadata reader backed by ffprobe."""
import json
import subprocess
from typing import Any, Callable, Dict, List, Optional

from domain.models.video import AudioTrack, Container, Video, VideoTrack
from domain.ports.logger import AppLogger
from domain.ports.video_metadata_reader import VideoMetadataReader


class FFprobeMetadataReader(VideoMetadataReader):
    """Reads video metadata by invoking ffprobe.

    This is the authority whenever Synology's index cannot be trusted: when it is
    missing or unparseable, and always for files this application has just written,
    whose index still describes the version that was overwritten.
    """

    _BASE_COMMAND = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        "-show_format",
    ]

    def __init__(
        self,
        logger: AppLogger,
        runner: Optional[Callable] = None,
        timeout: int = 60,
    ):
        """
        Initializes the reader.

        Args:
            logger: Application logger
            runner: Callable used to run the probe command; defaults to subprocess.run.
                Injected so tests can supply canned output instead of a real process.
            timeout: Seconds to wait for ffprobe before giving up
        """
        self.logger = logger
        self._runner = runner or subprocess.run
        self._timeout = timeout

    def read(self, video_path: str) -> Optional[Video]:
        """
        Reads metadata by probing the file.

        Args:
            video_path: Full path to the video file

        Returns:
            Video with the probed metadata, or None when the file cannot be probed,
            contains no video stream, or yields output this reader cannot map.
            Never raises: an unknown result must degrade to the next reader.
        """
        try:
            payload = self._probe(video_path)
            if payload is None:
                return None

            return self._to_video(video_path, payload)
        except Exception as error:
            # Output that decodes as JSON but does not have the shape ffprobe documents
            # would otherwise escape as AttributeError or TypeError from the mapping.
            # Reporting "unknown" lets the chain fall through to another reader; letting
            # it propagate would abort the processing cycle for one odd file.
            self.logger.warning(
                f"ffprobe output for {video_path} could not be interpreted: {error}"
            )
            return None

    def _probe(self, video_path: str) -> Optional[Dict[str, Any]]:
        """Runs ffprobe and returns its parsed JSON output, or None on any failure."""
        command = self._BASE_COMMAND + [video_path]

        try:
            result = self._runner(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=self._timeout,
            )
        except Exception as error:
            self.logger.warning(f"ffprobe could not be run for {video_path}: {error}")
            return None

        if result.returncode != 0:
            self.logger.warning(
                f"ffprobe failed for {video_path}: {self._as_text(result.stderr)}"
            )
            return None

        try:
            payload = json.loads(result.stdout)
        except (ValueError, TypeError) as error:
            self.logger.warning(
                f"ffprobe returned unreadable output for {video_path}: {error}"
            )
            return None

        if not isinstance(payload, dict):
            # `-print_format json` always yields an object. Anything else — including
            # the literal `null`, which json.loads decodes to None — is not output this
            # reader can map, and must not reach the mapping code.
            self.logger.warning(
                f"ffprobe returned a JSON {type(payload).__name__} rather than an "
                f"object for {video_path}"
            )
            return None

        return payload

    def _to_video(self, video_path: str, payload: Dict[str, Any]) -> Optional[Video]:
        """Maps ffprobe output onto the domain model."""
        streams = payload.get("streams") or []

        video_stream = self._first_stream(streams, "video")
        if video_stream is None:
            self.logger.warning(f"ffprobe found no video stream in {video_path}")
            return None

        audio_stream = self._first_stream(streams, "audio")
        container = payload.get("format") or {}

        width = self._to_int(video_stream.get("width"))
        height = self._to_int(video_stream.get("height"))
        if self._is_quarter_turned(video_stream):
            # ffprobe reports the coded geometry; a portrait clip recorded by a phone
            # comes back as 1920x1080 with the orientation held as side data. Reporting
            # it unswapped would make callers treat the video as landscape.
            width, height = height, width

        if width <= 0 or height <= 0:
            # A stream whose dimensions are absent or unusable yields 0, which callers
            # already use to mean "geometry unknown". Returning it as if it had been
            # measured would let orientation and scaling be derived from a non-answer,
            # so report unknown and let the chain try another source.
            self.logger.warning(
                f"ffprobe reported no usable geometry ({width}x{height}) for {video_path}"
            )
            return None

        return Video(
            path=video_path,
            video_track=VideoTrack(
                width=width,
                height=height,
                codec_name=video_stream.get("codec_name") or "",
                framerate=self._framerate(video_stream),
                bitrate=self._to_float(video_stream.get("bit_rate")),
            ),
            audio_track=AudioTrack(
                bitrate=self._to_float(audio_stream.get("bit_rate")),
                codec=audio_stream.get("codec_name") or "",
                channels=self._to_int(audio_stream.get("channels")),
            )
            if audio_stream is not None
            else AudioTrack(),
            container=Container(
                format=container.get("format_name") or "",
                duration=self._to_float(container.get("duration")),
                total_bitrate=self._to_float(container.get("bit_rate")),
                file_size=self._to_int(container.get("size")),
            ),
        )

    @staticmethod
    def _first_stream(
        streams: List[Dict[str, Any]], codec_type: str
    ) -> Optional[Dict[str, Any]]:
        """Returns the first stream of the given type, or None."""
        for stream in streams:
            if stream.get("codec_type") == codec_type:
                return stream
        return None

    @classmethod
    def _is_quarter_turned(cls, stream: Dict[str, Any]) -> bool:
        """Reports whether the stream's rotation swaps width and height."""
        return abs(cls._rotation(stream)) % 180 == 90

    @classmethod
    def _rotation(cls, stream: Dict[str, Any]) -> int:
        """Reads the display rotation in degrees, from side data or legacy tags."""
        for side_data in stream.get("side_data_list") or []:
            if "rotation" in side_data:
                return cls._to_int(side_data.get("rotation"))

        tags = stream.get("tags") or {}
        return cls._to_int(tags.get("rotate"))

    @classmethod
    def _framerate(cls, stream: Dict[str, Any]) -> int:
        """Reads the framerate, preferring the average over the base rate."""
        for key in ("avg_frame_rate", "r_frame_rate"):
            framerate = cls._parse_fraction(stream.get(key))
            if framerate:
                return framerate
        return 0

    @staticmethod
    def _parse_fraction(value: Any) -> Optional[int]:
        """Converts an ffprobe `num/den` rate into a rounded integer."""
        if not isinstance(value, str) or "/" not in value:
            return None

        numerator, _, denominator = value.partition("/")
        try:
            denominator_value = float(denominator)
            if denominator_value == 0:
                return None
            return round(float(numerator) / denominator_value)
        except ValueError:
            return None

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        """Converts an ffprobe value to int, tolerating strings and absent keys."""
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        """Converts an ffprobe value to float, tolerating strings and absent keys."""
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _as_text(value: Any) -> str:
        """Decodes ffprobe's stderr for logging."""
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace").strip()
        return str(value or "").strip()
