# Docker Build Guide

This project supports multiple architectures with different hardware acceleration options:

- **amd64**: QSV (Intel Quick Sync Video) + VAAPI
- **arm64**: V4L2M2M (Video4Linux2 Memory-to-Memory)

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
docker buildx build --platform linux/amd64 -t synology-photos-video-enhancer:latest-amd64 --load .
```

**ARM64 (V4L2M2M)**:
```bash
docker buildx build --platform linux/arm64 -t synology-photos-video-enhancer:latest-arm64 --load .
```

### Multi-architecture build (all platforms)

```bash
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t synology-photos-video-enhancer:latest \
  --push .
```

**Note**: Multi-architecture builds require `--push` to push to a registry, or you can use `--load` but it will only load one platform at a time.

## Dockerfile Structure

The Dockerfile uses a multi-stage approach:

1. **Stage 1 (python-deps)**: Pre-compiles Python dependencies into wheels for faster builds

2. **Stage 2 (runtime)**: Final image that combines:
   - Python runtime (from base image)
   - Jellyfin FFmpeg 7 (pre-built package with hardware acceleration drivers included)
   - Python dependencies (from wheels)
   - Application code

**Note**: This project uses Jellyfin's pre-built FFmpeg package, which includes all necessary hardware acceleration drivers (VAAPI, QSV, V4L2M2M) pre-configured. This eliminates the need to compile FFmpeg from source.

## Verification

After building, verify that FFmpeg is available and has the required codecs:

```bash
docker run --rm --entrypoint /bin/sh synology-photos-video-enhancer:latest \
  -c "ffmpeg -version && echo '---' && ffmpeg -hide_banner -codecs | grep -E 'h264|hevc|vaapi|v4l2'"
```

To verify hardware acceleration:

**AMD64 (VAAPI/QSV)**:
```bash
docker run --rm --device=/dev/dri:/dev/dri --entrypoint /bin/sh synology-photos-video-enhancer:latest \
  -c "ffmpeg -hide_banner -hwaccels"
```

**ARM64 (V4L2M2M)**:
```bash
docker run --rm --entrypoint /bin/sh synology-photos-video-enhancer:latest \
  -c "ffmpeg -hide_banner -codecs | grep v4l2"
```

**Note**: Jellyfin FFmpeg is located at `/usr/lib/jellyfin-ffmpeg` and is automatically added to PATH. The binaries include hardware acceleration drivers pre-configured.

## Build Times

- **AMD64**: ~5-10 minutes (first time)
- **ARM64**: ~8-15 minutes (first time, with emulation)

Build times are significantly faster since we use pre-built FFmpeg packages instead of compiling from source. Subsequent builds are even faster thanks to Docker cache.

## Troubleshooting

### Error: "platform linux/arm64 not supported"
- Ensure buildx is enabled and QEMU is installed
- Verify with: `docker buildx ls`

### Error: "jellyfin-ffmpeg7 not found"
- Ensure the Jellyfin repository is properly configured
- Check that the architecture (amd64/arm64) is supported
- Verify network connectivity to repo.jellyfin.org

### Build very slow
- Use `--cache-from` to reuse previous layers
- Consider using a registry for shared cache
- The build should be relatively fast since FFmpeg is pre-built

### FFmpeg missing shared libraries
- Jellyfin FFmpeg includes all necessary dependencies
- If issues persist, ensure the container has access to hardware devices (`/dev/dri` for VAAPI/QSV)
