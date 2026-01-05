# syntax=docker/dockerfile:1.6

ARG PY_IMAGE=python:3.14-slim-bookworm

# Stage 1: Build Python wheels (optimizes build cache for dependencies)
FROM ${PY_IMAGE} AS python-deps

WORKDIR /install
RUN pip install --upgrade pip && mkdir -p /install/wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /install/wheels -r requirements.txt

# Stage 2: Runtime image
FROM ${PY_IMAGE}

ARG TARGETARCH

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gnupg \
  && rm -rf /var/lib/apt/lists/*

# Add Jellyfin repository and install custom FFmpeg build (includes VAAPI drivers)
RUN install -d -m 0755 /etc/apt/keyrings \
  && curl -fsSL https://repo.jellyfin.org/jellyfin_team.gpg.key \
     | gpg --dearmor -o /etc/apt/keyrings/jellyfin.gpg \
  && printf "Types: deb\nURIs: https://repo.jellyfin.org/debian\nSuites: bookworm\nComponents: main\nSigned-By: /etc/apt/keyrings/jellyfin.gpg\n" \
     > /etc/apt/sources.list.d/jellyfin.sources

RUN apt-get update && \
    case "$TARGETARCH" in \
      amd64|arm64) apt-get install -y --no-install-recommends jellyfin-ffmpeg7 ;; \
      *) echo "Unsupported architecture: $TARGETARCH" && exit 1 ;; \
    esac \
  && rm -rf /var/lib/apt/lists/*

# Use Jellyfin FFmpeg binaries (located in /usr/lib/jellyfin-ffmpeg)
ENV PATH="/usr/lib/jellyfin-ffmpeg:${PATH}"

COPY --from=python-deps /install/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

WORKDIR /app
COPY ./src /app

ENTRYPOINT ["python", "main.py"]
