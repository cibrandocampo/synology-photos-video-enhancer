# Synology Photos – Video Quality Enhancer

<p align="center">
  <a href="https://github.com/cibrandocampo/synology-photos-video-enhancer"><img src="https://img.shields.io/badge/Source-GitHub-181717?logo=github&logoColor=white" alt="Source on GitHub"/></a>
  <a href="https://github.com/cibrandocampo/synology-photos-video-enhancer/actions/workflows/ci.yml"><img src="https://github.com/cibrandocampo/synology-photos-video-enhancer/actions/workflows/ci.yml/badge.svg" alt="CI"/></a>
  <a href="https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer"><img src="https://img.shields.io/docker/pulls/cibrandocampo/synology-photos-video-enhancer?logo=docker&color=066da5" alt="Docker Pulls"/></a>
  <a href="https://github.com/cibrandocampo/synology-photos-video-enhancer/releases"><img src="https://img.shields.io/github/v/release/cibrandocampo/synology-photos-video-enhancer" alt="Latest release"/></a>
  <a href="https://codecov.io/gh/cibrandocampo/synology-photos-video-enhancer"><img src="https://codecov.io/gh/cibrandocampo/synology-photos-video-enhancer/graph/badge.svg" alt="Codecov"/></a>
  <a href="https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT"/></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white" alt="Python 3.14"/>
  <img src="https://img.shields.io/badge/FFmpeg-Jellyfin-007808?logo=ffmpeg&logoColor=white" alt="FFmpeg (Jellyfin)"/>
  <img src="https://img.shields.io/badge/platforms-amd64%20·%20arm64-informational" alt="amd64 · arm64"/>
  <img src="https://img.shields.io/badge/HW_accel-QSV%20·%20VAAPI%20·%20V4L2M2M-blueviolet" alt="QSV · VAAPI · V4L2M2M"/>
</p>

<p align="center">
  <img src="https://raw.githubusercontent.com/cibrandocampo/synology-photos-video-enhancer/master/src/infrastructure/web/static/logo.svg" width="96" alt="Synology Photos Video Enhancer logo"/>
  <br/><br/>
  <i>Fix the videos Synology Photos ruins.</i>
  <br/>
  Automatic re-transcoding of Synology Photos intermediate videos — H.264 High Profile or H.265/HEVC, hardware-accelerated, running on your NAS.
</p>

<p align="center">
  <a href="https://video-enhancer.cibran.es"><strong>See the project site →</strong></a>
  <br/>
  <sub>How it works, features, screenshots, codec reference and setup guide</sub>
</p>

---

Synology Photos, like YouTube and other streaming platforms, automatically generates lower-quality versions of uploaded videos. These intermediate videos are used for adaptive playback when the connection is not sufficient for the original file, or when the device does not support the original video's codec or resolution (for example, browsers without native HEVC support or devices such as Chromecast V1 that do not support 4K).

The problem is that Synology Photos generates these intermediate videos with very poor quality, especially when videos are uploaded via the web interface. The transcodes are created using **H.264 baseline profile** and a framerate of only **15 fps**. The result is files that take up more space than necessary, look noticeably bad, and can even cause playback issues. Imagine trying to play your videos on a Chromecast and seeing them stutter because of the 15 fps limitation — it's simply not acceptable.

This tool solves that problem by automatically improving the quality of those intermediate videos. It retranscodes them into more efficient and modern formats (**H.264 High Profile** or **H.265/HEVC**), using hardware acceleration when available. The result is a significant improvement in visual quality while keeping file sizes efficient.

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

- APP: Synology Photos 1.9.1 or later
- SO: Synology DSM 7.3.2 or later
- Docker: Version 24.0.2 or later, via Synology's "Container Manager" (recommended, as it greatly facilitates management)
- Intel CPUs Only: SynoCli Video Drivers package 1.5.8 or later | Provides video driver support for Intel GPU acceleration, including OpenCL. **Note:** AMD CPUs have drivers included by default, this package is only required for Intel processors. Available from [SynoCommunity](https://synocommunity.com/).

## Quick Start

1. **Create directory structure** on your NAS (e.g. `/volume1/docker/photo/photo-video-enhancer/`)
2. **Copy `docker-compose.yml`** and edit volume mounts to point to your photo directories
3. **Create `.env`** from `env.example` and set the required dashboard credentials (`WEB_PASSWORD`, `WEB_SECRET_KEY`). Transcoding settings (codec, resolution, bitrate, etc.) are configured via the dashboard at runtime.
4. **Deploy** via Synology Container Manager or `docker compose up -d`

For step-by-step instructions and the full environment variables reference, see the **[Configuration Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/configuration.md)**.

## How It Works

1. **Periodic Scanning**: The application runs periodically (configurable from the dashboard)
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

## Dashboard

The container ships with a built-in, server-rendered dashboard that runs alongside the scheduler in the same process — no extra container, no JavaScript, no external service.

- **Access**: `http://<NAS-ip>:${WEB_PORT:-9200}/`. Recommended setup: put it behind DSM's reverse proxy with TLS termination.
- **What it shows**: total transcodings, counts per status, success rate, codec distribution, resolution distribution, the latest 5 transcodings, and the top 5 errors. HTML tables and CSS bars only.
- **About failures**: a video whose dimensions cannot be determined — neither from Synology's index nor by probing the file — is recorded as `failed` and left untouched, rather than transcoded with guessed settings. Its path and the reason appear in the error list. Videos Synology never generated a transcoded version for are recorded as `not_required`, which is not a failure.

**Endpoints:**

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET`  | `/` | required | HTML dashboard |
| `GET`  | `/api/stats` | required | JSON payload (same data as the HTML view) |
| `GET`  | `/healthz` | none | `{"status":"ok"}` — used by the Docker `healthcheck:` |
| `GET`  | `/login` | none | Login form |
| `POST` | `/login` | none | Submit credentials |
| `GET`  | `/logout` | required | Clear the session and redirect to `/login` |

**Authentication.** Single user. Username is `WEB_USER` (defaults to `admin`); password is `WEB_PASSWORD` and is **required** — the app refuses to start if it is unset or empty. The session cookie is HMAC-signed with `WEB_SECRET_KEY` (also required). Generate the secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

For the full list of dashboard env vars (port, cookie flags, etc.) see the **[Configuration Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/configuration.md)**.

## Upgrading

Coming from an older version? The **[Upgrading Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/upgrading.md)** covers what needs your attention, each entry starting from something you can observe:

- Odd resolutions such as `44100x2` or `2x1280` in the dashboard — databases written by 4.2.2 or earlier, and how to repair them.
- More failures reported after upgrading to 4.2.3 or later — why that is intended.
- Coming from the Grafana-based dashboard — replaced by the built-in one in 4.0.0.

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
├── controllers/         # Controllers (entry-point orchestration)
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
| [Upgrading Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/upgrading.md) | What needs attention when moving from an older version |
| [Supported Formats](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/supported-formats.md) | Video/audio codecs, hardware acceleration, resolutions |
| [SQLite Schema](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/sqlite-schema.md) | Database schema documentation |
| [Synology Metadata](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/docs/synology-metadata.md) | `SYNOINDEX_MEDIA_INFO` on-disk format and how it is read |
| [Docker Build](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/DOCKER.md) | Multi-architecture Docker build guide |
| [Architecture](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/src/README.md) | Hexagonal architecture and data flow |
| [Development Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/dev/README.md) | Local development, debugging, Docker dev setup |
| [Testing Guide](https://github.com/cibrandocampo/synology-photos-video-enhancer/blob/master/tests/README.md) | Test structure, fixtures, coverage |

## Codec Reference

Use this table to pick the right output settings in the dashboard.

### Video codecs

| Codec | Efficiency | CPU cost | Web | Android | iOS | TV | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| MPEG-4 | ↓ | ×1 | ✗ | ✗ | ✗ | ✓ | Legacy (DivX/Xvid) |
| **H.264 / AVC** ⭐ | = | ×0.2 * | ✓ | ✓ | ✓ | ✓ | **Recommended** — maximum compatibility |
| H.265 / HEVC | ↑ | ×0.4 * | ✗ | ✓ | ✓ | ✓ | Chrome/Firefox don't support it; check NAS CPU for HW encoding |
| AV1 | ↑↑ | ×22 | ✓ | ✗ | ✗ | ✓ | Requires NAS CPU with HW AV1 encoding support |

\* CPU cost with hardware acceleration (QSV/VAAPI). Without HW: H.264 ×5, H.265 ×22.

### Audio codecs

| Codec | Efficiency | Quality † | Web | Android | iOS | TV | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| AC-3 / Dolby Digital | ↓ | 82 | ✗ | ✗ | ✗ | ✓ | Home theater only. Needs ≥192 kbps |
| MP3 | = | 75 | ✓ | ✓ | ✓ | ✓ | Legacy; lower quality than AAC at same bitrate |
| E-AC-3 / Dolby Digital Plus | = | 91 | ✗ | ✗ | ✗ | ✓ | Home theater only. Possible royalty restrictions |
| **AAC LC** ⭐ | ↑ | 88 | ✓ | ✓ | ✓ | ✓ | **Recommended** — maximum compatibility |
| AAC HE | ↑↑ | 82 | ✓ | ✓ | ✓ | ✓ | Ideal for low bitrates (≥48 kbps) |
| AAC HE v2 | ↑↑↑ | 70 | ✓ | ~ | ~ | ✓ | Stereo only; best at ≤48 kbps |

† MUSHRA perceptual quality score at 128 kbps (0–100). ~ = partial support depending on device.

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
