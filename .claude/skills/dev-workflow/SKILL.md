---
name: dev-workflow
description: Development workflow and Docker commands for synology-photos-video-enhancer. Use when setting up the environment, running tests, debugging the FFmpeg transcoder, or building production images. Triggers when the user asks about development setup, Docker builds, multi-arch, or running the app locally.
---

# Development Workflow — synology-photos-video-enhancer

## Golden rule

**Don't run Python directly on the host.** The repo is built around Docker so that FFmpeg + Jellyfin codecs + hardware acceleration are reproducible across machines. Use the compose files in `dev/`. Bind mounts make code changes visible without rebuilds.

The root `Dockerfile` and `docker-compose.yml` are the **production** artefacts (COPY, no bind mounts, ships to Docker Hub). The `dev/` folder is for development.

## Layout

```
dev/
├── docker-compose.test.yml    # CI test runner
├── docker-compose.dev.yml     # Run app locally with bind mounts
├── docker-compose.debug.yml   # Run app with debugpy on :5678
├── requirements-dev.txt       # pytest, debugpy, etc.
└── media/                     # Test video fixtures (gitignored)
```

## Make targets

`Makefile` provides shortcuts. **Note**: a few targets currently reference `docker compose.X.yml` (with a space) instead of `docker-compose.X.yml` (with a hyphen). The targets are broken until that typo is fixed — when in doubt, run the explicit `docker compose -f dev/docker-compose.X.yml ...` command shown below.

```bash
make help        # list targets
make test        # build + run full test suite
make test-build  # build only
make test-run    # run only (requires built image)
make test-clean  # remove containers and volumes
make dev         # run app in development mode (live reload)
make debug       # run app with debugpy attached
```

## Running the test suite

The canonical command (also what CI runs):

```bash
docker compose -f dev/docker-compose.test.yml build
docker compose -f dev/docker-compose.test.yml run --rm \
  -v "$(pwd)/coverage:/app/coverage" \
  video-enhancer-test
```

What this does:

- Builds the production `Dockerfile` (so tests run against the same Python and FFmpeg as prod).
- Mounts `src/`, `tests/`, `dev/` into the container.
- Mounts `tests/data/` and `tests/media/` read-only.
- Installs `dev/requirements-dev.txt` (pytest, pytest-mock, pytest-cov, debugpy).
- Runs `pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=xml:coverage/coverage.xml`.

Output: ~260 tests, ~2 s, coverage XML in `./coverage/`.

### Running a single test

```bash
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test \
  python -m pytest tests/application/test_process_videos_use_case.py::TestProcessVideosUseCase::test_read_video_metadata_invalid_format -v
```

Override the entrypoint by passing the full pytest command after the service name. The compose file's default `command` is replaced.

### Running with markers

`pytest.ini` defines `unit`, `integration`, `slow` markers. Tests aren't widely tagged, but the infrastructure is there:

```bash
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test \
  python -m pytest tests/ -v -m "not slow"
```

## Running the app for development

```bash
cd dev && docker compose -f docker-compose.dev.yml up --build
```

Mounts `src/` so code changes reflect on next `python main.py` invocation. Uses `dev/media/` as the media dir by default — drop test videos there with the Synology layout:

```
dev/media/
└── <album_id>/
    ├── video.mp4
    └── @eaDir/
        └── video.mp4/
            └── SYNOINDEX_MEDIA_INFO
```

The `.env` file in the repo root is loaded automatically. Override `MEDIA_HOST_PATH`, `DATABASE_HOST_PATH`, etc. there.

## Debugging with breakpoints

```bash
cd dev && docker compose -f docker-compose.debug.yml up --build
```

The container installs `debugpy` and waits for a debugger on `:5678`. From VS Code / Cursor:

1. Open **Run and Debug** (F5).
2. Select **"Python: Attach to Docker (Remote Debug)"**.
3. Press F5 — the debugger connects to the running container.

The container loops on debugger reconnect, so you can disconnect and re-attach without restarting.

## Building production images

The release pipeline (`.github/workflows/build-push.yml`) handles this on tags. To do it locally:

### Single arch (current platform)

```bash
docker build -t synology-photos-video-enhancer:dev .
```

### Multi-arch (amd64 + arm64)

Requires buildx + QEMU (see `DOCKER.md`):

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --build-arg PY_IMAGE=python:3.14-slim-bookworm \
  -t synology-photos-video-enhancer:dev \
  --load .
```

`--load` only loads one platform at a time. `--push` is the usual choice for multi-arch — only relevant when releasing.

### Verifying FFmpeg + hwaccel in a built image

```bash
docker run --rm --entrypoint /bin/sh synology-photos-video-enhancer:dev \
  -c "ffmpeg -version && ffmpeg -hide_banner -hwaccels"
```

For VAAPI / QSV (amd64): pass `--device /dev/dri:/dev/dri`. For V4L2M2M (arm64): no extra device needed, but the host kernel must expose `/dev/video*`.

## Hardware acceleration matrix

| Arch  | Backend  | Encoder source                    | Test on host |
|-------|----------|-----------------------------------|--------------|
| amd64 | QSV      | Intel iGPU via `/dev/dri`         | macOS / dev: software fallback |
| amd64 | VAAPI    | AMD or Intel GPU via `/dev/dri`   | Linux only   |
| arm64 | V4L2M2M  | Synology DS220+ class hardware    | Synology only |

`HW_TRANSCODING=False` in `.env` forces software encoding. Use that for fast iterations on a dev laptop.

## Project structure

```
src/                          # Application code (hexagonal)
├── domain/                   # Pure domain — no I/O, no framework
│   ├── models/               # Video, Transcoding, Hardware, AppConfig
│   ├── ports/                # Interfaces (Filesystem, Transcoder, ...)
│   └── constants/            # Codecs, resolutions, framerates, etc.
├── application/              # Use cases (orchestration)
├── infrastructure/           # Adapters: SQL, FFmpeg, py-cpuinfo, logger
├── controllers/              # Entry-point routing (CLI args)
└── main.py                   # Composition root

tests/                        # Mirrors src/ structure; one test file per source module
```

The hexagonal split is enforced by import direction: `domain` imports nothing application/infra; `application` imports only `domain`; `infrastructure` and `controllers` are the only places that import third-party libraries.

## Logs and troubleshooting

```bash
docker logs synology-photos-video-enhancer        # production container
docker logs synology-photos-video-enhancer-dev    # dev mode
docker logs synology-photos-video-enhancer-debug  # debug mode
```

Set `LOGGER_LEVEL=DEBUG` in `.env` for verbose output. Useful when diagnosing why a video isn't being picked up (find_videos pattern, @eaDir filter, SYNOINDEX_MEDIA_INFO read).

## Environment variables

`env.example` is the source of truth. Copy to `.env` and edit. Variables used during development:

- `MEDIA_HOST_PATH` — where your test videos live (default: `../dev/media`).
- `MEDIA_APP_PATH` — path inside container (default: `/media`). Don't change unless tests fail because of it.
- `DATABASE_HOST_PATH` — SQLite location on the host (default: `../data`).
- `LOGGER_LEVEL` — `DEBUG` for development.
- `EXECUTION_INTERVAL` / `STARTUP_DELAY` — set both low (e.g., `1`) for fast iteration.
- `HW_TRANSCODING` — `False` on dev laptops without QSV/VAAPI.
