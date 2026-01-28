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
