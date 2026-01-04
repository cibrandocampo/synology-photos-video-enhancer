# Docker Build Guide

This project supports multiple architectures with different hardware acceleration options:

- **amd64**: QSV (Intel Quick Sync Video) + VAAPI
- **arm64/armv7**: V4L2M2M (Video4Linux2 Memory-to-Memory)

## Prerequisites

### For multi-architecture builds

1. **Enable buildx**:
```bash
docker buildx create --name multiarch --use
docker buildx inspect --bootstrap
```

2. **Install QEMU** (for cross-compilation):
```bash
# Ubuntu/Debian
sudo apt-get install qemu-user-static

# Or use the official container
docker run --privileged --rm tonistiigi/binfmt --install all
```

## Building Images

### Build for current platform
```bash
docker build -t synology-photos-video-enhancer:latest .
```

### Build for specific architecture

**AMD64 (QSV + VAAPI)**:
```bash
make build-amd64
# Or manually:
docker buildx build --platform linux/amd64 -t synology-photos-video-enhancer:latest-amd64 --load .
```

**ARM64 (V4L2M2M)**:
```bash
make build-arm64
# Or manually:
docker buildx build --platform linux/arm64 -t synology-photos-video-enhancer:latest-arm64 --load .
```

**ARMv7 (V4L2M2M)**:
```bash
make build-armv7
# Or manually:
docker buildx build --platform linux/arm/v7 -t synology-photos-video-enhancer:latest-armv7 --load .
```

### Multi-architecture build (all platforms)

```bash
make build-all
# Or manually:
docker buildx build \
  --platform linux/amd64,linux/arm64,linux/arm/v7 \
  -t synology-photos-video-enhancer:latest \
  --push .
```

**Note**: Multi-architecture builds require `--push` to push to a registry, or you can use `--load` but it will only load one platform at a time.

## Dockerfile Structure

The Dockerfile uses a multi-stage approach:

1. **Stage 1 (ffmpeg-builder)**: Compiles FFmpeg with hardware support based on architecture
   - AMD64: Enables QSV (libmfx) and VAAPI
   - ARM: Enables V4L2M2M

2. **Stage 2 (python-deps)**: Pre-compiles Python dependencies into wheels

3. **Stage 3 (final)**: Combines compiled FFmpeg + Python + application

## Verification

After building, verify that FFmpeg has the required codecs:

```bash
docker run --rm --entrypoint /bin/sh synology-photos-video-enhancer:latest \
  -c "ffmpeg -hide_banner -codecs | grep -E 'h264|hevc|vaapi|v4l2'"
```

To verify hardware acceleration:

**AMD64 (VAAPI)**:
```bash
docker run --rm --device=/dev/dri:/dev/dri --entrypoint /bin/sh synology-photos-video-enhancer:latest \
  -c "ffmpeg -hide_banner -hwaccels"
```

**ARM (V4L2M2M)**:
```bash
docker run --rm --entrypoint /bin/sh synology-photos-video-enhancer:latest \
  -c "ffmpeg -hide_banner -codecs | grep v4l2"
```

## Build Times

- **AMD64**: ~30-45 minutes (first time)
- **ARM64**: ~45-60 minutes (first time, with emulation)
- **ARMv7**: ~45-60 minutes (first time, with emulation)

Subsequent builds are faster thanks to Docker cache.

## Troubleshooting

### Error: "platform linux/arm64 not supported"
- Ensure buildx is enabled and QEMU is installed
- Verify with: `docker buildx ls`

### Error: "libmfx not found" (AMD64)
- Ensure `libmfx-dev` is installed in the build stage

### Build very slow
- Use `--cache-from` to reuse previous layers
- Consider using a registry for shared cache

### FFmpeg missing shared libraries
- Ensure runtime dependencies are installed: `libva2`, `libva-drm2`, `libdrm2`, `libmfx1`
- Compiled libraries are copied from the builder stage
