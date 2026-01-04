# Synology Photos Video Enhancer

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/cibrandocampo/synology-photos-video-enhancer)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Image-blue?logo=docker)](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cibrandocampo/synology-photos-video-enhancer)](https://github.com/cibrandocampo/synology-photos-video-enhancer/releases)
[![Python](https://img.shields.io/badge/python-3.13-blue?logo=python)](https://www.python.org/)
[![Docker Pulls](https://img.shields.io/docker/pulls/cibrandocampo/synology-photos-video-enhancer)](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer)
[![Coverage](https://img.shields.io/badge/coverage-89%25-green)](https://github.com/cibrandocampo/synology-photos-video-enhancer)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A robust and efficient tool for enhancing video quality in Synology Photos by automatically transcoding videos to optimized formats with hardware acceleration support.

Unfortunately, the quality of Synology Photos' built-in transcoding process for medium quality videos (for mobile devices) is poor:
- Videos uploaded from smartphones: H.264 baseline profile
- Videos uploaded via web/SMB: Framerate of 15fps

This tool automatically detects and transcodes videos to higher quality formats (H.264 High Profile or H.265/HEVC) using hardware acceleration when available, significantly improving video quality while maintaining efficient file sizes.

## Features

- **Automatic transcoding**: Detects and processes videos automatically
- **Hardware acceleration**: Supports QSV (Intel), VAAPI (Intel/AMD), and V4L2M2M (ARM)
- **Multi-architecture**: Docker images for amd64, arm64, and arm/v7
- **Periodic execution**: Runs automatically at configurable intervals
- **Smart detection**: Only transcodes videos that haven't been processed yet
- **Comprehensive logging**: Detailed logging system with configurable levels
- **High test coverage**: 89% code coverage ensuring reliability

## Prerequisites

- A Synology NAS with DSM > 7.3 installed and properly configured
- Synology Photos application > 1.8 installed and running
- Hardware acceleration support (VAAPI for AMD/Intel or QSV for Intel) via SynoCli Video Drivers package

### Installing SynoCli Video Drivers (Required for Hardware Acceleration)

This tool requires hardware acceleration support for video transcoding. To enable VAAPI (AMD/Intel) or QSV (Intel) support, you need to install the **SynoCli Video Drivers** package from SynoCommunity.

#### Step 1: Add SynoCommunity Repository

1. Log into your NAS as administrator and go to **Main Menu → Package Center → Settings**
2. Set **Trust Level** to _Synology Inc. and trusted publishers_ (skip this step if you are on DSM7 or later)
3. In the **Package Sources** tab, click **Add**
4. Type _SynoCommunity_ as **Name** and _https://packages.synocommunity.com/_ as **Location**
5. Press **OK** to validate

#### Step 2: Install SynoCli Video Drivers

1. Go back to the **Package Center**
2. Navigate to the **Community** tab
3. Find and install **SynoCli Video Drivers** package

For more information, visit: https://synocommunity.com/#easy-install

## Quick Start

### Docker Image

Pre-built images are available on [Docker Hub](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer). For production use, two tags are recommended:

- **`latest`**: Most up-to-date version passing unit tests
- **`stable`**: Latest version passing both unit and integration tests (recommended for production)

Version-specific tags are also available (e.g., `v1.0.0`).

### Configuration

Configuration is loaded **only from environment variables**. A `.env` file is provided for easy setup with docker-compose.

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| **Media Configuration** |
| `MEDIA_APP_PATH` | `/media` | Path inside container where media folders are mounted |
| **Transcoding Resources** |
| `HW_TRANSCODING` | `True` | Enable hardware transcoding (True/False) |
| `EXECUTION_THREADS` | `2` | Number of threads for FFmpeg transcoding |
| `STARTUP_DELAY` | `30` | Minutes to wait before first execution |
| `EXECUTION_INTERVAL` | `240` | Minutes between periodic executions |
| **Output Video Settings** |
| `VIDEO_CODEC` | `h264` | Video codec: `h264`, `hevc`, `mpeg4`, `mpeg2video`, `vp8`, `vp9`, `av1` |
| `VIDEO_BITRATE` | `2048` | Video bitrate in kbps |
| `VIDEO_RESOLUTION` | `480p` | Resolution: `144p`, `240p`, `360p`, `480p`, `720p`, `1080p`, `1440p`, `2160p` |
| `VIDEO_W` | `854` | Output video width in pixels (fallback if VIDEO_RESOLUTION not set) |
| `VIDEO_H` | `480` | Output video height in pixels (fallback if VIDEO_RESOLUTION not set) |
| `VIDEO_PROFILE` | `high` | Video profile: `baseline`, `main`, `high` (H.264), `main`, `main10` (HEVC) |
| **Output Audio Settings** |
| `AUDIO_CODEC` | `aac` | Audio codec: `aac`, `mp3`, `ac3`, `eac3`, `opus`, `vorbis`, `flac` |
| `AUDIO_BITRATE` | `128` | Audio bitrate in kbps |
| `AUDIO_CHANNELS` | `1` | Number of audio channels (1=mono, 2=stereo) |
| `AUDIO_PROFILE` | - | AAC profile: `aac_lc`, `aac_he`, `aac_he_v2` (only for AAC codec) |
| **Database Configuration** |
| `DATABASE_APP_PATH` | `data/transcodings.db` | Path to SQLite database file inside container |
| **Logger Configuration** |
| `LOGGER_NAME` | `synology-photos-video-enhancer` | Logger name |
| `LOGGER_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |

#### Example .env File

```bash
# Media Configuration
MEDIA_APP_PATH=/media

# Transcoding Resources
HW_TRANSCODING=True
EXECUTION_THREADS=2
STARTUP_DELAY=30
EXECUTION_INTERVAL=240

# Output Video Settings
VIDEO_CODEC=h264
VIDEO_BITRATE=2048
VIDEO_RESOLUTION=720p
VIDEO_PROFILE=high

# Output Audio Settings
AUDIO_CODEC=aac
AUDIO_BITRATE=128
AUDIO_CHANNELS=2
AUDIO_PROFILE=aac_lc

# Database Configuration
DATABASE_APP_PATH=data/transcodings.db

# Logger Configuration
LOGGER_NAME=synology-photos-video-enhancer
LOGGER_LEVEL=INFO
```

### Installation Methods

#### Option A: Manual Execution with Docker Compose

1. **Create `docker-compose.yml`:**

```yaml
version: '3.8'

services:
  video-enhancer:
    image: cibrandocampo/synology-photos-video-enhancer:${DOCKER_VERSION:-stable}
    container_name: synology-photos-video-enhancer
    env_file:
      - .env
    volumes:
      - ${MEDIA_HOST_PATH}:/media:rw
      - ${DATABASE_HOST_PATH:-./data}:/app/data
    devices:
      - /dev/dri:/dev/dri
    restart: unless-stopped
```

2. **Create `.env` file** (see example above)

3. **Set host paths** (add to `.env` or export):

```bash
export MEDIA_HOST_PATH=/volume1/photo
export DATABASE_HOST_PATH=./data
```

4. **Run:**

```bash
docker compose up -d
```

#### Option B: Synology Container Manager

1. **Open Container Manager** in DSM

2. **Create a new project:**
   - Click **Project** → **Create**
   - Name: `synology-photos-video-enhancer`
   - Path: Choose a location (e.g., `/docker/video-enhancer`)

3. **Add docker-compose.yml:**
   - In the project, click **Edit** → **Add File**
   - Create `docker-compose.yml` with the content from Option A above

4. **Add .env file:**
   - Click **Edit** → **Add File**
   - Create `.env` file with your configuration

5. **Configure volumes:**
   - Edit `docker-compose.yml` and update `MEDIA_HOST_PATH` to your Synology Photos path (typically `/volume1/photo` or `/volume1/homes/Photos`)
   - Update `DATABASE_HOST_PATH` to a persistent location (e.g., `/docker/video-enhancer/data`)

6. **Deploy:**
   - Click **Deploy** to start the container

## Supported Formats and Features

### Video Codecs

**Supported Input/Output Codecs:**
- H.264 (AVC) - Hardware accelerated on Intel/AMD/ARM
- H.265/HEVC - Hardware accelerated on Intel/AMD/ARM
- MPEG-4 - Software encoding
- MPEG-2 - Hardware accelerated on Intel/AMD/ARM
- VP8 - Software encoding
- VP9 - Software encoding
- AV1 - Software encoding

### Hardware Acceleration

**Backends:**
- **QSV (Quick Sync Video)**: Intel processors with integrated graphics
- **VAAPI (Video Acceleration API)**: Intel and AMD processors
- **V4L2M2M (Video4Linux2 Memory-to-Memory)**: ARM processors (Raspberry Pi, Synology ARM NAS)

**Automatic Detection:**
- The tool automatically detects available hardware acceleration
- Falls back to software encoding if hardware acceleration is unavailable
- Supports mixed environments (some videos with HW, others with SW)

### Container Formats

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

### Video Resolutions

**Supported Resolutions:**
- 144p (256×144)
- 240p (426×240)
- 360p (640×360)
- 480p (854×480) - Default
- 720p (1280×720) - HD
- 1080p (1920×1080) - Full HD
- 1440p (2560×1440) - 2K
- 2160p (3840×2160) - 4K

### Audio Codecs

**Supported Audio Codecs:**
- AAC (recommended, hardware accelerated)
- MP3
- AC3, EAC3
- Opus, Vorbis
- FLAC (lossless)

**AAC Profiles:**
- LC (Low Complexity) - Default
- HE (High Efficiency)
- HE v2 (High Efficiency v2)

## How It Works

1. **Periodic Scanning**: The application runs periodically (configurable via `EXECUTION_INTERVAL`)
2. **Video Detection**: Scans the configured media path for video files
3. **Metadata Reading**: Reads original video metadata from Synology's `SYNOINDEX_MEDIA_INFO` files
4. **Transcoding Check**: Verifies if video has already been transcoded
5. **Smart Transcoding**: Only transcodes videos that:
   - Haven't been processed before
   - Don't match target codec/resolution
   - Need quality improvement
6. **Output Storage**: Saves transcoded videos to `@eaDir/[video_name]/SYNOPHOTO_FILM_H.mp4`
7. **Database Tracking**: Maintains a SQLite database of all transcoding operations

## Development

### Development Environment

For development, this project includes a complete Docker-based development environment with hot reload, debugging support, and automated testing tools.

**Quick Start:**

```bash
cd dev/
make dev      # Development mode (hot reload)
make debug    # Debug mode (with breakpoints)
```

**Available Commands:**

- `make dev` - Run in development mode with hot reload
- `make debug` - Run in debug mode (waits for debugger connection on port 5678)
- `make test` - Run all tests
- `make test-build` - Build test container
- `make test-run` - Run tests (requires built container)
- `make test-clean` - Clean test containers and volumes

For detailed development instructions, see the [Development README](dev/README.md).

### Project Structure

```
src/
├── application/          # Application logic (use cases)
├── controllers/         # Controllers (CLI interface)
├── domain/              # Domain models and business logic
│   ├── constants/      # Enums and constants
│   ├── models/         # Domain models
│   └── ports/          # Ports (interfaces)
└── infrastructure/      # Infrastructure adapters
    ├── config/         # Configuration management
    ├── db/             # Database adapters
    ├── filesystem/     # Filesystem operations
    ├── hardware/       # Hardware detection
    ├── transcoder/     # FFmpeg transcoding
    └── logger.py       # Logging system
```

### Running Tests

```bash
# Using Make (recommended)
make test

# Or run directly
docker compose -f dev/docker-compose.test.yml up --build
```

### Test Coverage

The project maintains high test coverage to ensure code quality and reliability. Current coverage status:

- **Overall coverage: 89%**
- Domain layer: Comprehensive coverage
- Application layer: >90% coverage
- Infrastructure layer: >85% coverage

Tests are automatically executed in CI/CD pipelines before building Docker images to ensure code quality.

For more details, see the [Testing README](tests/README.md).

## Monitoring and Logs

### Normal Operation Logs

```
2025-01-04T12:01:32+0000 (synology-photos-video-enhancer) INFO | Starting video processing...
2025-01-04T12:01:32+0000 (synology-photos-video-enhancer) INFO | Found 5 videos to process
2025-01-04T12:01:32+0000 (synology-photos-video-enhancer) INFO | Video /media/album/video.mp4 already transcoded, skipping
2025-01-04T12:01:35+0000 (synology-photos-video-enhancer) INFO | Transcoding completed: 3 processed, 1 transcoded, 1 already transcoded
```

### Transcoding Logs

```
2025-01-04T12:01:32+0000 (synology-photos-video-enhancer) INFO | Starting transcoding: /media/album/video.mp4
2025-01-04T12:01:32+0000 (synology-photos-video-enhancer) INFO | Hardware acceleration: QSV detected
2025-01-04T12:01:33+0000 (synology-photos-video-enhancer) INFO | Transcoding completed successfully
```

## Architecture

Uses **Hexagonal Architecture (Ports and Adapters)** pattern to ensure:
- Clear separation between domain logic and infrastructure
- Easy testing with mocked dependencies
- Flexibility to swap implementations (e.g., different filesystems, databases)

## Links

- **GitHub Repository**: https://github.com/cibrandocampo/synology-photos-video-enhancer
- **Docker Hub Image**: https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer

## References

- [Synology Photos Documentation](https://kb.synology.com/en-global/DSM/help/Photos/Photos_desc)
- [FFmpeg Documentation](https://ffmpeg.org/documentation.html)
- [SynoCommunity](https://synocommunity.com/)

## Dependencies

This project is built on top of open source libraries:

- **FFmpeg**: For video transcoding with hardware acceleration
- **Pydantic**: For data validation and settings management
- **SQLAlchemy**: For database operations
- **schedule**: For periodic task execution

## Support

- **Issues**: Open an issue in the [GitHub repository](https://github.com/cibrandocampo/synology-photos-video-enhancer/issues)

## License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
