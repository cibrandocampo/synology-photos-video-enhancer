# Supported Formats and Features

## Video Codecs

**Supported Input/Output Codecs:**
- H.264 (AVC) - Hardware accelerated on Intel/AMD/ARM
- H.265/HEVC - Hardware accelerated on Intel/AMD/ARM
- MPEG-4 - Software encoding
- MPEG-2 - Hardware accelerated on Intel/AMD/ARM
- VP8 - Software encoding
- VP9 - Software encoding
- AV1 - Software encoding

## Hardware Acceleration

**Backends:**
- **QSV (Quick Sync Video)**: Intel processors with integrated graphics
- **VAAPI (Video Acceleration API)**: Intel and AMD processors
- **V4L2M2M (Video4Linux2 Memory-to-Memory)**: ARM processors (Raspberry Pi, Synology ARM NAS)

**Automatic Detection:**
- The tool automatically detects available hardware acceleration
- Falls back to software encoding if hardware acceleration is unavailable
- Supports mixed environments (some videos with HW, others with SW)

## Container Formats

**Supported Containers:**
- MP4 (recommended for Synology Photos)
- MOV, M4V
- MKV, AVI
- WMV, FLV, F4V
- TS, MTS, M2TS
- 3GP

**Output Format:**
- Always MP4 (compatible with Synology Photos)
- Fast-start enabled for web streaming

## Video Resolutions

**Supported Resolutions:**
- 144p (256x144)
- 240p (426x240)
- 360p (640x360)
- 480p (854x480)
- 720p (1280x720) - HD
- 1080p (1920x1080) - Full HD
- 1440p (2560x1440) - 2K
- 2160p (3840x2160) - 4K

**How the target is applied:**

The configured resolution sets a target *height*; the width is derived from the source aspect ratio, so the
original proportions are always preserved.

- **Horizontal videos** use the configured height directly. With 720p selected, a 1920x1080 source becomes
  1280x720.
- **Vertical videos** use the configured width as their height, so a portrait clip keeps a comparable level of
  detail. With 720p selected, a 1080x1920 source becomes 720x1280.
- **The output is never larger than the source.** If the target height exceeds the source height, the source
  height is used instead. With 720p selected, a 480x854 vertical clip stays at 854 rather than being enlarged
  to 720x1280. Enlarging costs space and adds no detail.

Orientation is taken from the video's display geometry, so clips recorded in portrait by a phone — which are
stored rotated, with the rotation held as metadata — are treated as vertical rather than horizontal.

## Frame Rate

Frame rate is not configurable. It is derived from the source, on the principle that the output should cost
less to store without looking different.

**Sources at or below 30 fps keep their rate.** A 25 fps clip stays at 25, a 24 fps clip stays at 24. Rates
that are not whole numbers are preserved exactly: an NTSC source at 29.97 fps comes out at 29.97, not rounded
to 30. Rounding would add roughly one duplicated frame every thirty seconds and slowly drift audio out of
sync against the video.

**Higher rates are halved, to the nearest standard rate:**

| Source | Output |
|--------|--------|
| 50 fps | 25 fps |
| 59.94 fps | 29.97 fps |
| 60 fps | 30 fps |
| 120 fps | 30 fps |
| 144 fps | 24 fps |
| 240 fps | 30 fps |

A 60 fps recording carries twice the frames of a 30 fps one for a difference most people cannot see on a
phone or a TV at normal playback speed. Halving is where most of the size reduction comes from.

**The output rate is never higher than the source's.** A source at a rate with no standard equivalent at or
below it — 29 fps, say — keeps its own rate rather than being pushed up to 29.97 or down to 25. There is no
rate at which inventing frames improves a video.

**Variable-rate sources keep their variable cadence.** Some cameras and most screen recorders spend frames
only where there is motion, holding a still shot at a low rate and rising during movement. That is a
deliberate optimisation, and forcing such a video to a constant rate would either duplicate frames it chose
not to record or discard frames it chose to keep — larger either way, and no better to watch. These files are
re-encoded at their original cadence.

Whether a source varies its rate can only be determined by probing the file. Synology's index records a
single nominal rate, so a constant 30 fps video and a variable one look identical in it — which is why the
tool probes source videos first and falls back to the index. See
[Synology metadata](synology-metadata.md).

## Audio Codecs

**Supported Audio Codecs:**
- AAC (recommended, hardware accelerated)
- MP3
- AC3, EAC3
- Opus, Vorbis
- FLAC (lossless)

**AAC Profiles:**
- LC (Low Complexity)
- HE (High Efficiency)
- HE v2 (High Efficiency v2)
