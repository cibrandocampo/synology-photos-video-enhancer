# Synology Photos Video Enhancer

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/cibrandocampo/synology-photos-video-enhancer)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Image-blue?logo=docker)](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cibrandocampo/synology-photos-video-enhancer)](https://github.com/cibrandocampo/synology-photos-video-enhancer/releases)
[![Python](https://img.shields.io/badge/python-3.14-blue?logo=python)](https://www.python.org/)
[![Docker Pulls](https://img.shields.io/docker/pulls/cibrandocampo/synology-photos-video-enhancer)](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer)
[![codecov](https://codecov.io/gh/cibrandocampo/synology-photos-video-enhancer/branch/main/graph/badge.svg)](https://codecov.io/gh/cibrandocampo/synology-photos-video-enhancer)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A robust and efficient tool for enhancing video quality in Synology Photos by automatically transcoding videos to optimized formats with hardware acceleration support.

Unfortunately, the quality of Synology Photos' built-in transcoding process for medium quality videos (for mobile devices) is poor:
- Videos uploaded from smartphones: H.264 baseline profile
- Videos uploaded via web/SMB: Framerate of 15fps

This tool automatically detects and transcodes videos to higher quality formats (H.264 High Profile or H.265/HEVC) using hardware acceleration when available, significantly improving video quality while maintaining efficient file sizes.

## Features

- **Automatic transcoding**: Detects and processes videos automatically
- **Hardware acceleration**: Supports QSV (Intel), VAAPI (Intel/AMD), and V4L2M2M (ARM)
- **Multi-architecture**: Docker images for amd64 and arm64
- **Periodic execution**: Runs automatically at configurable intervals
- **Smart detection**: Only transcodes videos that haven't been processed yet
- **Comprehensive logging**: Detailed logging system with configurable levels
- **High test coverage**: 89% code coverage ensuring reliability

## Architecture

The Docker image is built on:
- **Base**: Debian Bookworm (slim)
- **Python**: 3.14
- **FFmpeg**: Jellyfin FFmpeg 7 (custom build with VAAPI drivers included)

The image uses Jellyfin's pre-built FFmpeg package, which includes all necessary hardware acceleration drivers (VAAPI, QSV) pre-configured, eliminating the need to compile FFmpeg from source or install additional driver packages.

## Prerequisites

- APP: Synology Photos > 1.8
- SO: Synology DSM > 7.1
- Intel CPUs Only: SynoCli Video Drivers package > 1.3 | Provides video driver support for Intel GPU acceleration (DSM6-7), including OpenCL (DSM7.1+ only). **Note:** AMD CPUs have drivers included by default, this package is only required for Intel processors. For installation instructions, see [Installing Video Drivers](docs/installing-video-drivers.md).

## Quick Start

Configuration is loaded **only from environment variables** (.env + volumes management in docker-compose). Both `env.example` and `docker-compose.yml` files are provided with detailed information.

### 1. Configuration

#### 1.1 Create Directory

Create a directory for the project (e.g., `/volume1/docker/video-enhancer`)

#### 1.2 Create docker-compose.yml

Copy the `docker-compose.yml` file and modify it according to your needs. The application needs access to all photo directories. You must mount:
- **Common photos folder** (shared by all users): `/volume1/photo`
- **Individual user photo folders**: `/volume1/homes/USERNAME/Photos` for each user

**Important:** 
- The `docker-compose.yml` file has clear sections indicating what **MUST be modified** and what doesn't need changes
- **1. Common photos folder:** If you have a shared photos folder, modify the path `/volume1/photo` according to your Synology configuration. If you don't have a common folder, delete this line
- **2. Individual user folders:** Replace `user1`, `user2`, etc. with your actual Synology usernames. Add or remove lines according to the number of users
- All other configuration (database, hardware acceleration) is handled via the `.env` file

#### 1.3 Create .env File

Based on `env.example`, create a `.env` file that must be saved on the NAS at the same level as `docker-compose.yml`. Modify the necessary variables according to your needs.

**Environment Variables:**

| Variable | Default | Description |
|----------|---------|-------------|
| **Docker Configuration** |
| `DOCKER_VERSION` | `stable` | Docker image version. Pre-built images are available on [Docker Hub](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer). Options: `stable` (recommended for production, updated with releases, passes both unit and integration tests), `latest` (most up-to-date version passing unit tests, daily updates from main), or specific version tag (e.g., `v3.0.0`) |
| **Transcoding Resources** |
| `HW_TRANSCODING` | `True` | Enable hardware transcoding (True/False) |
| `EXECUTION_THREADS` | `2` | Number of threads for FFmpeg transcoding. **Recommended:** Do not exceed half of available CPU cores (e.g., 4 cores = max 2 threads) |
| `STARTUP_DELAY` | `30` | Minutes to wait before first execution after container startup |
| `EXECUTION_INTERVAL` | `240` | Minutes between periodic executions |
| **Output Video Settings** |
| `VIDEO_CODEC` | `h264` | Video codec: `h264`, `hevc`, `mpeg4`, `mpeg2video`, `vp8`, `vp9`, `av1` |
| `VIDEO_BITRATE` | `2048` | Video bitrate in kbps |
| `VIDEO_RESOLUTION` | `720p` | Resolution: `144p`, `240p`, `360p`, `480p`, `720p`, `1080p`, `1440p`, `2160p`. If not set, `VIDEO_W` and `VIDEO_H` can be used as fallback |
| `VIDEO_PROFILE` | `high` | Video profile (codec-specific): H.264: `baseline`, `main`, `high`; HEVC: `main`, `main10`; MPEG2VIDEO: `simple`, `main`, `high`; MPEG4: `simple`, `advanced-simple`. Ignored if codec doesn't support profiles (vp8, vp9, av1). Set to `False` or leave empty if codec doesn't support profiles |
| **Output Audio Settings** |
| `AUDIO_CODEC` | `aac` | Audio codec: `aac`, `mp3`, `ac3`, `eac3`, `opus`, `vorbis`, `flac` |
| `AUDIO_BITRATE` | `128` | Audio bitrate in kbps |
| `AUDIO_CHANNELS` | `2` | Number of audio channels (1=mono, 2=stereo) |
| `AUDIO_PROFILE` | `aac_lc` | AAC profile: `aac_lc`, `aac_he`, `aac_he_v2` (only for AAC codec). Ignored if not using AAC. Set to `False` or leave empty if not using AAC |
| **Database Configuration** |
| `DATABASE_HOST_PATH` | `./data` | Path on the HOST where the database directory is located. The SQLite database file will be stored in this location. Typically in a `volumes` or `volumes/data/` folder |
| **Logger Configuration** |
| `LOGGER_NAME` | `video-enhancer` | Logger name (used in log messages) |
| `LOGGER_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| **Advanced/Development Configuration** |
| `MEDIA_APP_PATH` | `/media` | **Internal container path** where media folders are mounted. **Do not modify** unless for development/debugging. The application automatically scans all subdirectories under this path |
| `DATABASE_APP_PATH` | `/app/data` | Path inside the container where the database file is stored. Can be a directory or full path to the database file. If directory, `transcodings.db` will be appended automatically. **Do not modify** unless for development/debugging |

**Note:** Advanced configuration variables (`MEDIA_APP_PATH`, `DATABASE_APP_PATH`) are typically not needed and should be left at their default values unless you have specific development or debugging requirements.

### 2. Execution

#### 2.1 Synology Container Manager (Recommended)

1. **Open Container Manager** in DSM

2. **Create a new project:**
   - Click **Project** → **Create**
   - Name: `synology-photos-video-enhancer` (or any name you prefer)
   - Path: Choose a location (e.g., `/volume1/docker/video-enhancer`)

3. **Add docker-compose.yml:**
   - **Note:** Container Manager usually detects `docker-compose.yml` automatically if it exists in the project directory. You typically don't need to add it manually.
   - If needed, in the project, click **Edit** → **Add File**

4. **Deploy:**
   - Click **Deploy** to start the container

#### 2.2 Manual Execution with Docker Compose

1. **Navigate to your project directory:**

```bash
cd /volume1/docker/video-enhancer
```

2. **Ensure your `docker-compose.yml` and `.env` files are configured** (see Configuration section above)

3. **Run:**

```bash
docker compose up -d
```

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
2. **Video Detection**: Recursively scans all subdirectories under `/media` for video files
   - Scans `/media/photos` (common folder)
   - Scans `/media/user1`, `/media/user2`, etc. (individual user folders)
   - Automatically discovers all mounted directories
3. **Metadata Reading**: Reads original video metadata from Synology's `SYNOINDEX_MEDIA_INFO` files
4. **Transcoding Check**: Verifies if video has already been transcoded
5. **Smart Transcoding**: Only transcodes videos that:
   - Haven't been processed before
   - Don't match target codec/resolution
   - Need quality improvement
6. **Output Storage**: Saves transcoded videos to `@eaDir/[video_name]/SYNOPHOTO_FILM_H.mp4` in the same directory as the original video
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

### Viewing Transcoding Results

To check the results of video transcoding, simply consult the container logs. After each execution, the application displays a summary with the following information:

- **Total processed**: Total number of videos found and checked
- **Already transcoded**: Videos that were already transcoded and skipped
- **Transcoded**: New videos that were successfully transcoded
- **Errors**: Number of videos that failed to transcode (if any)

You can view the logs using:

```bash
# View logs from Container Manager in DSM
# Or via command line:
docker logs synology-photos-video-enhancer

# Follow logs in real-time:
docker logs -f synology-photos-video-enhancer

# View last 100 lines:
docker logs --tail 100 synology-photos-video-enhancer
```

### Normal Operation Logs

```
2025-01-04T12:01:32+0000 (video-enhancer) INFO | Starting video processing...
2025-01-04T12:01:32+0000 (video-enhancer) INFO | Found 5 videos to process
2025-01-04T12:01:32+0000 (video-enhancer) INFO | Video /media/album/video.mp4 already transcoded, skipping
2025-01-04T12:01:35+0000 (video-enhancer) INFO | Processing results:
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Total processed: 5
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Already transcoded: 2
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Transcoded: 3
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Errors: 0
```

### Transcoding Logs

```
2025-01-04T12:01:32+0000 (video-enhancer) INFO | Starting transcoding: /media/album/video.mp4
2025-01-04T12:01:32+0000 (video-enhancer) INFO | Hardware acceleration: QSV detected
2025-01-04T12:01:33+0000 (video-enhancer) INFO | Transcoding completed successfully
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

## Acknowledgments

This project would not be possible without the following open-source projects:

- **[FFmpeg](https://www.ffmpeg.org/)**: The powerful multimedia framework that enables video transcoding with hardware acceleration. Thank you to the FFmpeg team for their incredible work.
- **[Jellyfin](https://jellyfin.org/)**: Special thanks to the Jellyfin project for providing pre-built FFmpeg binaries with hardware acceleration drivers included. This significantly simplifies Docker image management and ensures reliable hardware acceleration support. Specifically, we use the [jellyfin-ffmpeg](https://github.com/jellyfin/jellyfin-ffmpeg/tree/jellyfin) project.
- **[Python](https://www.python.org/)**: The programming language that powers this application.
  - **[Pydantic](https://pydantic.dev/)** (>=2.12.0): For data validation and settings management
  - **[SQLAlchemy](https://www.sqlalchemy.org/)** (>=2.0.0): For database operations
  - **[py-cpuinfo](https://github.com/workhorsy/py-cpuinfo)** (>=9.0.0): For CPU information and hardware detection
  - **[schedule](https://github.com/dbader/schedule)** (>=1.2.0): For periodic task execution

## Support

- **Issues**: Open an issue in the [GitHub repository](https://github.com/cibrandocampo/synology-photos-video-enhancer/issues)
- **Email**: For questions or doubts, feel free to send an email to [hello@cibran.es](mailto:hello@cibran.es)

## License

Licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

**Note on Dependencies:** This project uses Jellyfin FFmpeg binaries, which are licensed under LGPL-3.0/GPL-2.0/GPL-3.0 (see [jellyfin-ffmpeg license](https://github.com/jellyfin/jellyfin-ffmpeg)). The FFmpeg binaries are used as external tools and are not modified or statically linked, which is compatible with the MIT license of this project.
