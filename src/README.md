# Synology Photos Video Enhancer

Video enhancement application for Synology Photos following Hexagonal Architecture principles.

## Architecture Overview

This application follows **Hexagonal Architecture** (also known as Ports and Adapters), which separates business logic from infrastructure concerns. The architecture is organized into clear layers with well-defined responsibilities.

```
src/
├── main.py                    # Composition root - bootstrap & dependency injection
├── controllers/               # Interface adapters (CLI, future: API, Web)
├── application/               # Use cases - orchestration layer
├── domain/                    # Business logic - core of the application
│   ├── models/               # Domain entities
│   └── ports/                # Interfaces (contracts)
└── infrastructure/            # Infrastructure adapters (implementations)
    ├── config/               # Configuration loader
    ├── db/                   # Database implementation
    ├── filesystem/           # Filesystem operations
    ├── hardware/             # Hardware detection
    └── transcoder/           # Video transcoding
```

## Directory Structure

### `main.py` - Composition Root

**Responsibility**: Bootstrap and dependency injection

- Loads configuration
- Initializes database connection
- Creates database tables
- Builds all infrastructure adapters
- Wires dependencies to use cases
- Launches the controller

**Never contains business logic** - only composition and initialization.

### `infrastructure/config/settings.py` - Configuration Loader

**Responsibility**: Load configuration from environment variables

- Reads environment variables
- Returns `AppConfig` domain model
- **No other module reads os.environ directly**
- The domain model (`AppConfig`) is in `domain/models/app_config.py`

### `controllers/main_controller.py` - Main Controller

**Responsibility**: Parse CLI arguments and launch use case

- Parses command-line arguments (`--dry-run`, `--verbose`, `--only-new`)
- Validates input format
- Launches the use case
- Displays output

**The controller does NOT**:
- List directories
- Execute ffmpeg
- Touch database
- Detect hardware

### `application/process_videos_use_case.py` - Use Case

**Responsibility**: Orchestrate the complete video processing workflow

This is the **heart of the application**. It orchestrates:

1. Get hardware information
2. Decide transcoding policy
3. List videos from filesystem
4. For each video:
   - Check if already transcoded (via repository)
   - If not, determine transcoding parameters
   - Transcode video
   - Persist result

**Depends ONLY on interfaces (ports)**, not concrete implementations.

### `domain/models/` - Domain Entities

**Responsibility**: Represent domain concepts

- `video.py` - Video entity with metadata
- `transcoding.py` - Transcoding entity with status
- `hardware.py` - Hardware-related enums (CPUVendor, HardwareBackend)

**No infrastructure concerns here** - pure domain logic.

**Does NOT execute anything** - only makes decisions.

### `domain/ports/` - Interfaces (Ports)

These are **contracts**, not implementations:

- `video_repository.py` - Video persistence operations
- `filesystem.py` - Filesystem operations
- `hardware_info.py` - Hardware information
- `transcoder.py` - Video transcoding operations

The use case only knows about these interfaces, making it testable and independent of infrastructure.

### `infrastructure/db/` - Database Implementation

**Responsibility**: Concrete database operations

- `connection.py` - Database connection management
- `models.py` - SQLAlchemy models
- `video_repository_sql.py` - SQL implementation of VideoRepository

**Only place where SQL/ORM code exists.**

### `infrastructure/filesystem/local_filesystem.py`

**Responsibility**: Local filesystem operations

- Lists directories recursively
- Finds video files
- Filters Synology directories (@eaDir, #recycle)
- Finds transcoded videos in @eaDir structure

**Implements** `domain/ports/filesystem.py`

### `infrastructure/hardware/local_hardware_info.py`

**Responsibility**: Detect real hardware on the system

- CPU vendor detection
- GPU detection (NVIDIA/AMD)
- Available hardware acceleration backends
- Best backend selection

**Implements** `domain/ports/hardware_info.py`

### `infrastructure/transcoder/ffmpeg_transcoder.py`

**Responsibility**: Execute ffmpeg commands

- Builds ffmpeg commands
- Executes transcoding process
- Handles process errors
- Reads video metadata via ffprobe

**Implements** `domain/ports/transcoder.py`

**The domain never sees ffmpeg directly.**

## Data Flow

```
main.py (bootstrap)
    ↓
MainController
    ↓
ProcessVideosUseCase
    ↓
    ├─→ Filesystem (port) → LocalFilesystem (implementation)
    ├─→ VideoRepository (port) → VideoRepositorySQL (implementation)
    ├─→ HardwareInfo (port) → LocalHardwareInfo (implementation)
    └─→ Transcoder (port) → FFmpegTranscoder (implementation)
```

## Key Principles

### 1. Dependency Inversion

- High-level modules (use cases) don't depend on low-level modules (infrastructure)
- Both depend on abstractions (ports/interfaces)
- Infrastructure implements domain interfaces

### 2. Single Responsibility

Each module has one clear responsibility:
- `main.py` → Composition
- `infrastructure/config/settings.py` → Configuration loading
- `domain/models/app_config.py` → Configuration structure
- `main_controller.py` → Main entry point controller
- `process_videos_use_case.py` → Orchestration
- Infrastructure → Implementation

### 3. Testability

- Use cases depend on interfaces, not implementations
- Easy to mock ports for testing
- Business logic isolated from infrastructure

### 4. Flexibility

- Can swap implementations (e.g., different database, different filesystem)
- Can add new interfaces (e.g., cloud storage, different transcoder)
- Domain logic remains unchanged

## Responsibilities Matrix

| Requirement | Who Does It |
|------------|-------------|
| Read configuration | `main.py` + `infrastructure/config/settings.py` |
| Detect hardware | `HardwareInfo` (infrastructure) |
| Connect to database | `main.py` |
| Create tables | `main.py` (or migrations) |
| List directories | `Filesystem` (infrastructure) |
| Verify transcodings | `VideoRepository` (infrastructure) |
| Execute ffmpeg | `Transcoder` (infrastructure) |
| Orchestrate everything | `ProcessVideosUseCase` |

## Usage

### Running the Application

```bash
python main.py
```

### CLI Options

```bash
python main.py --dry-run      # Show what would be done
python main.py --verbose      # Enable verbose output
python main.py --only-new      # Only process new videos
```

## Configuration

Configuration is loaded from:
1. Environment variables (takes precedence)
2. Configuration file (default: `photo-enhancer/video_quality_enhancer.conf`)

### Environment Variables

- `CONFIG_FILE_PATH` - Path to configuration file
- `DATABASE_PATH` - Path to SQLite database
- `LOGGER_NAME` - Logger name
- `LOGGER_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

### Configuration File

```ini
[InputFolders]
VIDEO_PATH = /data

[OutputVideo]
VIDEO_CODEC = h264
VIDEO_BITRATE = 2048k
VIDEO_MAX_H_W = 720
AUDIO_CODEC = aac
AUDIO_BITRATE = 128k
AUDIO_CHANNELS = 1
```

## Adding New Features

### Adding a New Use Case

1. Create new file in `application/`
2. Depend only on ports (interfaces)
3. Wire in `main.py`

### Adding a New Infrastructure Implementation

1. Create implementation in appropriate `infrastructure/` subdirectory
2. Implement the corresponding port interface
3. Wire in `main.py`

### Adding a New Port

1. Define interface in `domain/ports/`
2. Create implementation in `infrastructure/`
3. Update use case to use the new port
4. Wire in `main.py`

## Testing Strategy

- **Unit tests**: Test domain use cases with mocked ports
- **Integration tests**: Test infrastructure implementations
- **E2E tests**: Test complete flow with real (or test) infrastructure

## Future Enhancements

- API controller (REST/GraphQL)
- Web interface controller
- Cloud storage filesystem implementation
- Different transcoder implementations
- Migration system for database schema
- Queue system for async transcoding
