# Development Guide

This directory contains development tools and configurations for local development and debugging.

## Structure

```
dev/
├── docker-compose.dev.yml      # Docker Compose for development
├── docker-compose.debug.yml    # Docker Compose for debugging with debugpy
├── requirements-dev.txt        # Development dependencies (for local development)
└── media/                      # Development media files (gitignored)
```

## 🐛 Debugging with Breakpoints (Recommended)

This is the best option for step-by-step debugging with breakpoints.

### Step 1: Start the container in debug mode

```bash
make debug
```

Or directly:

```bash
cd dev && docker compose -f docker-compose.debug.yml up --build
```

The container will keep running and waiting for debugger connections.

### Step 2: Connect the debugger from Cursor/VS Code

1. Open the **Run and Debug** panel (F5 or `Ctrl+Shift+D`)
2. Select the configuration **"Python: Attach to Docker (Remote Debug)"**
3. Press F5 or click "Start Debugging"

The debugger will connect to the container and you can:
- ✅ Set breakpoints on any line
- ✅ View variables in real-time
- ✅ Step through code (F10, F11)
- ✅ Evaluate expressions
- ✅ View the call stack
- ✅ **Restart the debugger** (circular green arrow) - automatically reconnects
- ✅ Container stays running, you only need to connect/reconnect the debugger

**Note**: When you restart the debugger (circular arrow), it will automatically reconnect. If the program has already finished, you'll need to click "Play" to start a new execution.

### How it works

The debug container:
- Installs `debugpy` automatically
- Waits for a debugger connection on port `5678`
- Keeps running in a loop, allowing multiple debug sessions
- Mounts your `src/` directory for live code changes
- Mounts `dev/media/` as the media directory

## 🚀 Development Mode (Without Debugger)

For running the application in development mode without debugging:

```bash
make dev
```

Or directly:

```bash
cd dev && docker compose -f docker-compose.dev.yml up --build
```

This will:
- Mount `src/` as a volume (code changes reflect immediately)
- Mount `dev/media/` as `/media` in the container (or use `MEDIA_HOST_PATH` env var)
- Enable interactive mode
- Run the application directly

## 🔧 Local Development (Without Docker)

If you prefer to run locally without Docker:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r dev/requirements-dev.txt
   ```

2. Set environment variables (see `.env.example`):
   ```bash
   export MEDIA_HOST_PATH=/path/to/media
   export MEDIA_APP_PATH=/media
   export DATABASE_HOST_PATH=/path/to/data
   # ... other variables
   ```

3. Run the application:
   ```bash
   cd src
   python main.py
   ```

4. For debugging locally, select **"Python: Run Locally"** in the debugger and press F5.

## 📁 Development Media

Place test videos in `dev/media/` directory. This directory is gitignored.

The structure should match your Synology Photos structure:
```
dev/media/
└── [album_id]/
    ├── video.mp4
    └── @eaDir/
        └── video.mp4/
            └── SYNOINDEX_MEDIA_INFO
```

## 🔍 Opening a Shell in Container

To open an interactive shell in a running container:

```bash
docker exec -it synology-photos-video-enhancer-dev /bin/sh
```

Or for the debug container:

```bash
docker exec -it synology-photos-video-enhancer-debug /bin/sh
```

## 📝 Environment Variables

See `.env.example` in the root directory for all available environment variables.

Key variables for development:
- `MEDIA_HOST_PATH` - Path to media directory on host (default: `../dev/media`)
- `MEDIA_APP_PATH` - Path inside container (default: `/media`)
- `DATABASE_HOST_PATH` - Path to database directory on host (default: `../data`)
- `LOGGER_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR (default: `INFO`)

## 🛠️ Troubleshooting

### Port 5678 already in use

If you get an error about port 5678 being in use:

```bash
# Find the process using the port
lsof -i :5678

# Kill it if needed
kill -9 <PID>
```

### Container not starting

Check Docker logs:

```bash
docker logs synology-photos-video-enhancer-debug
```

### Debugger not connecting

1. Make sure the container is running and waiting for connections
2. Check that port 5678 is exposed: `docker ps` should show `0.0.0.0:5678->5678/tcp`
3. Verify the path mappings in `.vscode/launch.json` are correct
4. Try restarting the debugger in VS Code/Cursor

### Code changes not reflecting

Make sure `src/` is mounted as a volume. Check `docker-compose.dev.yml` or `docker-compose.debug.yml`:

```yaml
volumes:
  - ../src:/app
```
