# SQLite Database Schema

## Table: `transcodings`

### Fields

| Field | Type | Description | Primary Key | Nullable | Index |
|-------|------|-------------|-------------|----------|--------|
| `original_video_path` | VARCHAR(1000) | Full path to the original video file | ✅ Yes | ❌ No | ✅ Yes |
| `transcoded_video_path` | VARCHAR(1000) | Full path to the transcoded video file | ❌ No | ❌ No | ❌ No |
| `transcoded_video_resolution` | VARCHAR(20) | Resolution in format "widthxheight" (e.g., "1920x1080") | ❌ No | ❌ No | ❌ No |
| `transcoded_video_codec` | VARCHAR(50) | Video codec name (e.g., "h264", "hevc") | ❌ No | ❌ No | ❌ No |
| `status` | VARCHAR(20) | Transcoding status (see Status Values below) | ❌ No | ❌ No | ✅ Yes |
| `error_message` | TEXT | Error message if transcoding failed (NULL if no error) | ❌ No | ✅ Yes | ❌ No |

### Status Values

The `status` field can have the following values:

- **`pending`**: Video is waiting to be processed
- **`in_progress`**: Video is currently being transcoded
- **`completed`**: Video was successfully transcoded
- **`not_required`**: Video is already in the correct format and doesn't need transcoding
- **`failed`**: Transcoding failed (check `error_message` for details)

### Indexes

- Primary key on `original_video_path`
- Index on `original_video_path` (idx_original_path)
- Index on `status` (idx_status)

### Example Data

```sql
SELECT * FROM transcodings LIMIT 1;
```

Example row:
```
original_video_path: /media/photos/vacation/video.mp4
transcoded_video_path: /media/photos/vacation/@eaDir/video.mp4/SYNOPHOTO_FILM_H.mp4
transcoded_video_resolution: 1920x1080
transcoded_video_codec: h264
status: completed
error_message: NULL
```

---

## Table: `settings`

Single-row table (`id = 1`) storing transcoding configuration managed through the dashboard Settings page. Seeded with defaults on first startup.

### Fields

| Field | Type | Nullable | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | INTEGER | ❌ No | — | Always `1` (single-row sentinel) |
| `hw_transcoding` | BOOLEAN | ❌ No | `true` | Enable VAAPI/QSV (amd64) or V4L2M2M (arm64) hardware acceleration |
| `execution_threads` | INTEGER | ❌ No | `2` | FFmpeg thread count; recommended ≤ half of available CPU cores |
| `startup_delay` | INTEGER | ❌ No | `30` | Minutes to wait after container start before first processing run |
| `execution_interval` | INTEGER | ❌ No | `240` | Minutes between periodic processing runs |
| `video_codec` | VARCHAR(20) | ❌ No | `h264` | Output video codec (`h264`, `hevc`, `mpeg4`, `av1`) |
| `video_bitrate` | INTEGER | ❌ No | `2000` | Output video bitrate in kbps |
| `video_resolution` | VARCHAR(10) | ❌ No | `720p` | Output resolution (`144p` … `1080p`) |
| `video_profile` | VARCHAR(30) | ✅ Yes | `NULL` | Codec profile (`baseline`/`main`/`high` for H.264; `main`/`main10` for HEVC; NULL for others) |
| `audio_codec` | VARCHAR(20) | ❌ No | `aac` | Output audio codec (`aac`, `mp3`, `ac3`, `eac3`) |
| `audio_bitrate` | INTEGER | ❌ No | `128` | Output audio bitrate in kbps |
| `audio_channels` | INTEGER | ❌ No | `2` | Output channel count (`1` = mono, `2` = stereo) |
| `audio_profile` | VARCHAR(20) | ✅ Yes | `NULL` | AAC sub-profile (`aac_lc`, `aac_he`, `aac_he_v2`); NULL for non-AAC codecs |

