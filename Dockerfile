# syntax=docker/dockerfile:1.6

ARG PY_IMAGE=python:3.13-slim-bookworm

# Stage 1: FFmpeg builder
FROM ${PY_IMAGE} AS ffmpeg-builder

ARG TARGETPLATFORM
ARG TARGETARCH
ARG TARGETVARIANT

# Build dependencies
# Use separate cache per stage to avoid lock conflicts in parallel builds
RUN --mount=type=cache,target=/var/cache/apt,id=ffmpeg-builder-apt \
    apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends \
    build-essential nasm yasm cmake git wget pkg-config \
    libtool autoconf automake \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Architecture-specific build dependencies
RUN --mount=type=cache,target=/var/cache/apt,id=ffmpeg-builder-apt \
    set -eux; \
    apt-get update -o Acquire::Retries=3; \
    if [ "$TARGETARCH" = "amd64" ]; then \
        apt-get install -y --no-install-recommends libva-dev libdrm-dev libmfx-dev; \
    elif [ "$TARGETARCH" = "arm64" ] || { [ "$TARGETARCH" = "arm" ] && [ "$TARGETVARIANT" = "v7" ]; }; then \
        apt-get install -y --no-install-recommends libv4l-dev v4l-utils; \
    fi; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /tmp/ffmpeg-build

ENV PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/local/lib64/pkgconfig:/usr/lib/pkgconfig:/usr/lib64/pkgconfig

# x264
RUN git clone --depth 1 https://code.videolan.org/videolan/x264.git && \
    cd x264 && \
    ./configure --enable-static --enable-pic && \
    make -j"$(nproc)" && make install

# x265 (HEVC encoder)
# Note: x265 doesn't generate .pc file when built as static, so we create it manually
RUN git clone --depth 1 https://bitbucket.org/multicoreware/x265_git.git && \
    cd x265_git/build/linux && \
    cmake -G "Unix Makefiles" \
        -DCMAKE_INSTALL_PREFIX=/usr/local \
        -DENABLE_SHARED=off \
        -DENABLE_PIC=on \
        ../../source && \
    make -j"$(nproc)" && make install && \
    mkdir -p /usr/local/lib/pkgconfig && \
    printf 'prefix=/usr/local\nexec_prefix=${prefix}\nlibdir=${exec_prefix}/lib\nincludedir=${prefix}/include\n\nName: x265\nDescription: H.265/HEVC video encoder\nVersion: 3.5\nLibs: -L${libdir} -lx265\nLibs.private: -lstdc++ -lm -lrt -ldl\nCflags: -I${includedir}\n' > /usr/local/lib/pkgconfig/x265.pc

# libvpx
RUN git clone --depth 1 https://chromium.googlesource.com/webm/libvpx.git && \
    cd libvpx && \
    ./configure --enable-static --enable-pic && \
    make -j"$(nproc)" && make install

# fdk-aac
RUN git clone --depth 1 https://github.com/mstorsjo/fdk-aac.git && \
    cd fdk-aac && \
    autoreconf -fiv && \
    ./configure --enable-static --enable-pic && \
    make -j"$(nproc)" && make install

# FFmpeg
RUN git clone --depth 1 https://git.ffmpeg.org/ffmpeg.git ffmpeg
WORKDIR /tmp/ffmpeg-build/ffmpeg

# Verify pkg-config can find x265 before configuring FFmpeg
RUN pkg-config --exists x265 || (echo "x265 not found in PKG_CONFIG_PATH: $PKG_CONFIG_PATH" && pkg-config --list-all | grep x265 || find /usr/local -name "x265.pc" || exit 1)

RUN set -eux; \
    if [ "$TARGETARCH" = "amd64" ]; then \
      ./configure \
        --prefix=/usr/local \
        --pkg-config-flags="--static" \
        --extra-cflags="-I/usr/local/include" \
        --extra-ldflags="-L/usr/local/lib" \
        --extra-libs="-lpthread -lm" \
        --enable-gpl --enable-version3 --enable-nonfree \
        --enable-libx264 --enable-libx265 --enable-libvpx --enable-libfdk-aac \
        --enable-vaapi \
        --enable-libmfx \
        --enable-static --disable-shared --enable-pic \
        --disable-doc; \
    else \
      ./configure \
        --prefix=/usr/local \
        --pkg-config-flags="--static" \
        --extra-cflags="-I/usr/local/include" \
        --extra-ldflags="-L/usr/local/lib" \
        --extra-libs="-lpthread -lm" \
        --enable-gpl --enable-version3 --enable-nonfree \
        --enable-libx264 --enable-libx265 --enable-libvpx --enable-libfdk-aac \
        --enable-v4l2-m2m --enable-libv4l2 \
        --enable-static --disable-shared --enable-pic \
        --disable-doc; \
    fi; \
    make -j"$(nproc)" && make install && make distclean

# Stage 2: Python wheels
FROM ${PY_IMAGE} AS python-deps

WORKDIR /install
RUN pip install --upgrade pip && mkdir -p /install/wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /install/wheels -r requirements.txt

# Stage 3: Runtime
FROM ${PY_IMAGE}

ARG TARGETARCH
ARG TARGETVARIANT

# Runtime dependencies
# Compiled libraries (libfdk-aac, libmfx) are copied from builder
# Only system dependencies for VAAPI/V4L2 are needed
# Use separate cache per stage to avoid lock conflicts in parallel builds
RUN --mount=type=cache,target=/var/cache/apt,id=runtime-apt \
    apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends \
    libva2 libva-drm2 libdrm2 \
    libmfx1 \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy FFmpeg and compiled dependencies
COPY --from=ffmpeg-builder /usr/local/bin/ffmpeg /usr/local/bin/ffmpeg
COPY --from=ffmpeg-builder /usr/local/bin/ffprobe /usr/local/bin/ffprobe
COPY --from=ffmpeg-builder /usr/local/lib /usr/local/lib
RUN ldconfig

# Wheels
COPY --from=python-deps /install/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

WORKDIR /app
COPY ./src /app

RUN ffmpeg -version && ffprobe -version
ENTRYPOINT ["python", "main.py"]
