# Configuration Guide

Configuration is loaded **only from environment variables** (`.env` + volume mounts in `docker-compose.yml`). Both `env.example` and `docker-compose.yml` files are provided with detailed information.

## 1. Create Directory Structure

Create the main directory for the project (you can choose any location):
- **Main directory** (example): `/volume1/docker/photo/photo-video-enhancer`

Create subdirectories for Docker volumes:
- **Database volume** (example): `{main_directory}/volumes/database`
- **Grafana volume** (optional, only if using Grafana, example): `{main_directory}/volumes/grafana`

**Example structure:**
```
/volume1/docker/photo/photo-video-enhancer/
├── docker-compose.yml
├── .env
└── volumes/
    ├── database/
    └── grafana/  (optional)
```

**Note**: If you have multiple volumes on your Synology NAS, you can use any volume path (e.g., `/volume1/`, `/volume2/`, `/volume3/`, etc.).

## 2. Create docker-compose.yml

Choose one of the following options:

**Option A: With Grafana monitoring (recommended for monitoring statistics)**
- Copy the `docker-compose.yml` file and modify it according to your needs
- This includes both the video enhancer and Grafana services
- Configure Grafana variables in `.env` if you want to customize the default settings

**Option B: Without Grafana (simpler setup)**
- Copy the `docker-compose-without-grafana.yml` file and rename it to `docker-compose.yml`
- This only includes the video enhancer service
- No Grafana configuration needed

The application needs access to all photo directories. You must mount:
- **Common photos folder** (shared by all users): `/volume1/photo`
- **Individual user photo folders**: `/volume1/homes/USERNAME/Photos` for each user (normally `/volume1/` as most users have a single volume; if you have multiple volumes, check the correct volume path)

**Important:**
- The `docker-compose.yml` file has clear sections indicating what **MUST be modified** and what doesn't need changes
- **1. Common photos folder:** If you have a shared photos folder, modify the path `/volume1/photo` according to your Synology configuration. If you don't have a common folder, delete this line
- **2. Individual user folders:** Replace `user1`, `user2`, etc. with your actual Synology usernames. Add or remove lines according to the number of users
- All other configuration (database, hardware acceleration, Grafana) is handled via the `.env` file

## 3. Create .env File

Based on `env.example`, create a `.env` file that must be saved on the NAS at the same level as `docker-compose.yml`. Modify the necessary variables according to your needs.

## Environment Variables

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
| **Grafana Configuration (Optional)** |
| `GRAFANA_DOCKER_VERSION` | `12.3` | Grafana Docker image version. **Only needed if using Grafana monitoring** |
| `GRAFANA_PORT` | `3000` | Port where Grafana web interface will be accessible. **Only needed if using Grafana monitoring** |
| `GRAFANA_USER` | `admin` | Grafana admin username. **Only needed if using Grafana monitoring** |
| `GRAFANA_PASSWORD` | `admin` | Grafana admin password. **Only needed if using Grafana monitoring** |
| `GRAFANA_PERSISTENCE_PATH` | `./grafana-data` | Path on the HOST where Grafana data (dashboards, users, etc.) will be stored. **Only needed if using Grafana monitoring** |
| **Logger Configuration** |
| `LOGGER_NAME` | `video-enhancer` | Logger name (used in log messages) |
| `LOGGER_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| **Advanced/Development Configuration** |
| `MEDIA_APP_PATH` | `/media` | **Internal container path** where media folders are mounted. **Do not modify** unless for development/debugging. The application automatically scans all subdirectories under this path |
| `DATABASE_APP_PATH` | `/app/data` | Path inside the container where the database file is stored. Can be a directory or full path to the database file. If directory, `transcodings.db` will be appended automatically. **Do not modify** unless for development/debugging |

**Note:**
- Advanced configuration variables (`MEDIA_APP_PATH`, `DATABASE_APP_PATH`) are typically not needed and should be left at their default values unless you have specific development or debugging requirements.
- Grafana configuration variables are **optional** and only required if you want to use Grafana for monitoring transcoding statistics. If you don't need monitoring, you can use `docker-compose-without-grafana.yml` instead.

## Execution

### Synology Container Manager (Recommended)

1. **Open Container Manager** in DSM

2. **Create a new project:**
   - Click **Project** -> **Create**
   - Name: `synology-photos-video-enhancer` (or any name you prefer)
   - Path: Choose a location (e.g., `/volume1/docker/video-enhancer`)

3. **Add docker-compose.yml:**
   - **Note:** Container Manager usually detects `docker-compose.yml` automatically if it exists in the project directory. You typically don't need to add it manually.
   - If needed, in the project, click **Edit** -> **Add File**

4. **Deploy:**
   - Click **Deploy** to start the container

### Manual Execution with Docker Compose

1. **Navigate to your project directory:**

```bash
cd /volume1/docker/video-enhancer
```

2. **Ensure your `docker-compose.yml` and `.env` files are configured** (see sections above)

3. **Run:**

```bash
docker compose up -d
```

**Note:** If using `docker-compose.yml` with Grafana, you can start only the video enhancer without Grafana by using:
```bash
docker compose up -d video-enhancer
```

Or start both services (default):
```bash
docker compose up -d
```
