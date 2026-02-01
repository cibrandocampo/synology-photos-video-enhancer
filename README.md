# Synology Photos – Intermediate Video Quality Enhancer

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/cibrandocampo/synology-photos-video-enhancer)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Image-blue?logo=docker)](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cibrandocampo/synology-photos-video-enhancer)](https://github.com/cibrandocampo/synology-photos-video-enhancer/releases)
[![Python](https://img.shields.io/badge/python-3.14-blue?logo=python)](https://www.python.org/)
[![Docker Pulls](https://img.shields.io/docker/pulls/cibrandocampo/synology-photos-video-enhancer)](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer)
[![Codecov](https://codecov.io/gh/cibrandocampo/synology-photos-video-enhancer/graph/badge.svg)](https://codecov.io/gh/cibrandocampo/synology-photos-video-enhancer)

![Grafana Dashboard](https://raw.githubusercontent.com/cibrandocampo/synology-photos-video-enhancer/master/docs/images/small_grafana_dashboard.png)

Synology Photos, like YouTube and other streaming platforms, automatically generates lower-quality versions of uploaded videos. These intermediate videos are used for adaptive playback when the connection is not sufficient for the original file, or when the device does not support the original video's codec or resolution (for example, browsers without native HEVC support or devices such as Chromecast V1 that do not support 4K).

The problem is that Synology Photos generates these intermediate videos with very poor quality, especially when videos are uploaded via the web interface. The transcodes are created using **H.264 baseline profile** and a framerate of only **15 fps**. The result is files that take up more space than necessary, look noticeably bad, and can even cause playback issues. Imagine trying to play your videos on a Chromecast and seeing them stutter because of the 15 fps limitation — it's simply not acceptable.

This tool solves that problem by automatically improving the quality of those intermediate videos. It retranscodes them into more efficient and modern formats (**H.264 High Profile** or **H.265/HEVC**), using hardware acceleration when available. The result is a significant improvement in visual quality while keeping file sizes efficient. Optionally, the transcoding process and its statistics can be monitored using **Grafana dashboards**.

## TL;DR

Synology Photos creates very low-quality intermediate videos (15 fps, H.264 baseline).
This tool automatically re-transcodes them to modern formats with hardware acceleration, fixing playback issues and improving visual quality.

## Features

- **Automatic transcoding**: Detects and processes videos automatically
- **Hardware acceleration**: Supports QSV (Intel), VAAPI (Intel/AMD), and V4L2M2M (ARM)
- **Multi-architecture**: Docker images for amd64 and arm64
- **Periodic execution**: Runs automatically at configurable intervals
- **Smart detection**: Only transcodes videos that haven't been processed yet
- **Comprehensive logging**: Detailed logging system with configurable levels
- **High test coverage**: 95% code coverage ensuring reliability

## Prerequisites

- APP: Synology Photos > 1.8
- SO: Synology DSM > 7.1
- Docker: Version > 20 | It is recommended to use Synology's "Container Manager" as it greatly facilitates management. Version > 24
- Intel CPUs Only: SynoCli Video Drivers package > 1.3 | Provides video driver support for Intel GPU acceleration (DSM6-7), including OpenCL (DSM7.1+ only). **Note:** AMD CPUs have drivers included by default, this package is only required for Intel processors. Available from [SynoCommunity](https://synocommunity.com/).

## Quick Start

1. **Create directory structure** on your NAS (e.g. `/volume1/docker/photo/photo-video-enhancer/`)
2. **Copy `docker-compose.yml`** and edit volume mounts to point to your photo directories
3. **Create `.env`** from `env.example` and adjust settings (codec, resolution, bitrate, etc.)
4. **Deploy** via Synology Container Manager or `docker compose up -d`

For step-by-step instructions and the full environment variables reference, see the **[Configuration Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/configuration.md)**.

## How It Works

1. **Periodic Scanning**: The application runs periodically (configurable via `EXECUTION_INTERVAL`)
2. **Video Detection**: Recursively scans all subdirectories under `/media` for video files
3. **Metadata Reading**: Reads original video metadata from Synology's `SYNOINDEX_MEDIA_INFO` files
4. **Transcoding Check**: Verifies if video has already been transcoded
5. **Smart Transcoding**: Only transcodes videos that haven't been processed before
6. **Output Storage**: Saves transcoded videos to `@eaDir/[video_name]/SYNOPHOTO_FILM_H.mp4` in the same directory as the original video
7. **Database Tracking**: Maintains a SQLite database of all transcoding operations

## Monitoring and Logs

After each execution, the application logs a summary:

```
2025-01-04T12:01:35+0000 (video-enhancer) INFO | Processing results:
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Total processed: 514
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Already transcoded: 239
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Transcoded: 275
2025-01-04T12:01:35+0000 (video-enhancer) INFO |   - Errors: 0
```

View logs with `docker logs synology-photos-video-enhancer` or via Container Manager in DSM.

For optional Grafana dashboards, see the **[Grafana Setup Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/grafana-setup.md)**.

## Development

```bash
make dev      # Development mode (hot reload)
make debug    # Debug mode (with breakpoints)
make test     # Run all tests
```

For detailed development instructions, see the [Development Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/dev/README.md).

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

For architecture details, see the [Architecture Documentation](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/src/README.md). For tests, see the [Testing Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/tests/README.md).

## Documentation

| Document | Description |
|----------|-------------|
| [Configuration Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/configuration.md) | Directory setup, docker-compose, environment variables |
| [Supported Formats](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/supported-formats.md) | Video/audio codecs, hardware acceleration, resolutions |
| [Grafana Setup](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/grafana-setup.md) | Optional monitoring dashboards |
| [Grafana Queries](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/grafana-queries.md) | Ready-to-use SQL queries for dashboards |
| [SQLite Schema](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/sqlite-schema.md) | Database schema documentation |
| [Docker Build](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/DOCKER.md) | Multi-architecture Docker build guide |
| [Architecture](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/src/README.md) | Hexagonal architecture and data flow |
| [Development Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/dev/README.md) | Local development, debugging, Docker dev setup |
| [Testing Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/tests/README.md) | Test structure, fixtures, coverage |

## Software Architecture

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
- **[Grafana](https://grafana.com/)**: The open-source analytics and monitoring platform that enables optional visualization of transcoding statistics and results. We use Grafana with the [frser-sqlite-datasource](https://github.com/fr-ser/grafana-sqlite-datasource) plugin to connect to the SQLite database.
- **[Python](https://www.python.org/)**: The programming language that powers this application.
  - **[Pydantic](https://pydantic.dev/)** (>=2.12.0): For data validation and settings management
  - **[SQLAlchemy](https://www.sqlalchemy.org/)** (>=2.0.0): For database operations
  - **[py-cpuinfo](https://github.com/workhorsy/py-cpuinfo)** (>=9.0.0): For CPU information and hardware detection
  - **[schedule](https://github.com/dbader/schedule)** (>=1.2.0): For periodic task execution

## Support

- **Issues**: Open an issue in the [GitHub repository](https://github.com/cibrandocampo/synology-photos-video-enhancer/issues)
- **Email**: For questions or doubts, feel free to send an email to [hello@cibran.es](mailto:hello@cibran.es)

## License

Licensed under the **MIT License**. See [LICENSE](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/LICENSE) for details.

**Note on Dependencies:**
- This project uses Jellyfin FFmpeg binaries, which are licensed under LGPL-3.0/GPL-2.0/GPL-3.0 (see [jellyfin-ffmpeg license](https://github.com/jellyfin/jellyfin-ffmpeg)). The FFmpeg binaries are used as external tools and are not modified or statically linked, which is compatible with the MIT license of this project.
- Grafana (optional monitoring component) is licensed under AGPL-3.0 (see [Grafana license](https://github.com/grafana/grafana/blob/main/LICENSE)). Grafana is used as an external service via Docker and is not modified or statically linked, which is compatible with the MIT license of this project.
