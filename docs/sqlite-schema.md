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

