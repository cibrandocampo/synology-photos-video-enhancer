# Configuration Guide

Infrastructure configuration (paths, ports, credentials) is loaded from environment variables (`.env` + volume mounts in `docker-compose.yml`). Transcoding settings (codecs, bitrates, resolution, execution parameters) are configured through the built-in dashboard and stored in the database.

## 1. Create Directory Structure

Create the main directory for the project (you can choose any location):
- **Main directory** (example): `/volume1/docker/photo/photo-video-enhancer`

Create subdirectories for Docker volumes:
- **Database volume** (example): `{main_directory}/volumes/database`

**Example structure:**
```
/volume1/docker/photo/photo-video-enhancer/
├── docker-compose.yml
├── .env
└── volumes/
    └── database/
```

**Note**: If you have multiple volumes on your Synology NAS, you can use any volume path (e.g., `/volume1/`, `/volume2/`, `/volume3/`, etc.).

## 2. Create docker-compose.yml

Copy the `docker-compose.yml` file and modify it according to your needs.

The application needs access to all photo directories. You must mount:
- **Common photos folder** (shared by all users): `/volume1/photo`
- **Individual user photo folders**: `/volume1/homes/USERNAME/Photos` for each user (normally `/volume1/` as most users have a single volume; if you have multiple volumes, check the correct volume path)

**Important:**
- The `docker-compose.yml` file has clear sections indicating what **MUST be modified** and what doesn't need changes
- **1. Common photos folder:** If you have a shared photos folder, modify the path `/volume1/photo` according to your Synology configuration. If you don't have a common folder, delete this line
- **2. Individual user folders:** Replace `user1`, `user2`, etc. with your actual Synology usernames. Add or remove lines according to the number of users
- All other configuration (database, hardware acceleration) is handled via the `.env` file

## 3. Create .env File

Copy `env.example` to `.env` next to `docker-compose.yml` and adjust values for your installation. Two dashboard variables are **required** before the container will start:

- `WEB_PASSWORD` — pick any non-empty value.
- `WEB_SECRET_KEY` — generate one with:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

All other variables have sensible defaults (see the table below).

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| **Docker Configuration** |
| `APP_DOCKER_VERSION` | `stable` | Docker image version for the main APP container (`synology-photos-video-enhancer`). Pre-built images are available on [Docker Hub](https://hub.docker.com/r/cibrandocampo/synology-photos-video-enhancer). Options: `stable` (recommended for production, updated with releases, passes both unit and integration tests), `latest` (most up-to-date version passing unit tests, daily updates from main), or specific version tag (e.g., `v3.0.0`) |
| **Database Configuration** |
| `DATABASE_HOST_PATH` | `./data` | Path on the HOST where the database directory is located. The SQLite database file will be stored in this location. Typically in a `volumes` or `volumes/data/` folder |
| **Dashboard Configuration** |
| `WEB_PORT` | `9200` | Port where the internal dashboard listens (host and container) |
| `WEB_USER` | `admin` | Username for the single dashboard user |
| `WEB_PASSWORD` | _(none)_ | Password for the single dashboard user. **Required** — the app refuses to start if this is empty |
| `WEB_SECRET_KEY` | _(none)_ | HMAC key for signing the session cookie. **Required** — generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `WEB_COOKIE_SECURE` | `false` | Set to `true` if the dashboard serves HTTPS directly. Leave `false` when DSM's reverse proxy terminates TLS (the typical Synology setup) |
| **Logger Configuration** |
| `LOGGER_NAME` | `video-enhancer` | Logger name (used in log messages) |
| `LOGGER_LEVEL` | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| **Advanced/Development Configuration** |
| `MEDIA_APP_PATH` | `/media` | **Internal container path** where media folders are mounted. **Do not modify** unless for development/debugging. The application automatically scans all subdirectories under this path |
| `DATABASE_APP_PATH` | `/app/data` | Path inside the container where the database file is stored. Can be a directory or full path to the database file. If directory, `transcodings.db` will be appended automatically. **Do not modify** unless for development/debugging |

**Note:**
- Advanced configuration variables (`MEDIA_APP_PATH`, `DATABASE_APP_PATH`) are typically not needed and should be left at their default values unless you have specific development or debugging requirements.

## Dashboard

The container runs an internal HTTP dashboard on `${WEB_PORT:-9200}`, exposed by `docker-compose.yml`. After `docker compose up -d`, the dashboard is reachable at:

```
http://<NAS-ip>:${WEB_PORT:-9200}/
```

It serves HTML at `/`, JSON at `/api/stats` (same payload), and an unauthenticated `{"status":"ok"}` probe at `/healthz`. The `healthcheck:` block in `docker-compose.yml` already targets `/healthz`, so `docker ps` will report the container as `healthy` once the dashboard is reachable.

For production use, point DSM's reverse proxy at the dashboard port and let it terminate TLS — the dashboard itself does not serve HTTPS.

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

