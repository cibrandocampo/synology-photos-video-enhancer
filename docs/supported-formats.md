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
