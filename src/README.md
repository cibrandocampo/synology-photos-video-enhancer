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
│   ├── constants/            # Enums and constants
│   ├── models/               # Domain entities
│   └── ports/                # Interfaces (contracts)
└── infrastructure/            # Infrastructure adapters (implementations)
    ├── config/               # Configuration loader
    ├── db/                   # Database implementation
    ├── filesystem/           # Filesystem operations
    ├── hardware/             # Hardware detection
    ├── transcoder/           # Video transcoding
    └── logger.py             # Logging system
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

### `infrastructure/config/config.py` - Configuration Loader

**Responsibility**: Load configuration from environment variables

- Reads environment variables
- Returns `AppConfig` domain model
- **No other module reads os.environ directly**
- The domain model (`AppConfig`) is in `domain/models/app_config.py`
- Uses lazy loading: each section is loaded only when accessed

### `controllers/main_controller.py` - Main Controller

**Responsibility**: Entry-point orchestration — launch the use case

- Launches the use case
- Returns the result

**The controller does NOT**:
- List directories
- Execute ffmpeg
- Touch database
- Detect hardware

### `application/process_videos_use_case.py` - Use Case

**Responsibility**: Orchestrate the complete video processing workflow

This is the **heart of the application**. It orchestrates:

1. List videos from filesystem
2. For each video:
   - Check if already transcoded (via repository)
   - Read video metadata (via filesystem)
   - Determine transcoding parameters
   - Create transcoder (via factory) and transcode
   - Update transcoding status using immutable domain methods
   - Persist result (via repository)

**Depends ONLY on interfaces (ports)**, not concrete implementations.

### `domain/models/` - Domain Entities

**Responsibility**: Represent domain concepts

- `video.py` - Video entity with metadata
- `transcoding.py` - Transcoding entity with status
- `hardware.py` - Hardware-related models (CPUVendor, HardwareVideoAcceleration)

**No infrastructure concerns here** - pure domain logic.

**Does NOT execute anything** - only makes decisions.

### `domain/ports/` - Interfaces (Ports)

These are **contracts**, not implementations:

- `video_repository.py` - Video persistence operations
- `filesystem.py` - Filesystem operations (find videos, read files, ensure directories)
- `hardware_info.py` - Hardware information
- `transcoder.py` - Video transcoding operations
- `transcoder_factory.py` - Factory for creating transcoder instances
- `logger.py` - Application logging interface

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
- Reads file contents
- Ensures directories exist

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

- Builds ffmpeg commands for each hardware backend (QSV, VAAPI, V4L2M2M, software)
- Executes transcoding process
- Handles process errors

**Implements** `domain/ports/transcoder.py`

### `infrastructure/transcoder/ffmpeg_transcoder_factory.py`

**Responsibility**: Create FFmpegTranscoder instances

- Receives hardware info and logger via dependency injection
- Creates transcoders with the correct dependencies

**Implements** `domain/ports/transcoder_factory.py`

### `infrastructure/logger.py`

**Responsibility**: Logging

- Configures the root Python logger
- Provides `EnhancedLogger` with `title()` and `subtitle()` methods
- Auto-detects calling module name for log messages

**Implements** `domain/ports/logger.py`

**The domain never sees ffmpeg directly.**

## Data Flow

```
main.py (bootstrap)
    ↓
MainController
    ↓
ProcessVideosUseCase
    ↓
    ├─→ Filesystem (port)         → LocalFilesystem (implementation)
    ├─→ VideoRepository (port)    → VideoRepositorySQL (implementation)
    ├─→ TranscoderFactory (port)  → FFmpegTranscoderFactory → FFmpegTranscoder
    └─→ AppLogger (port)          → EnhancedLogger (implementation)
```

## Key Principles

### 1. Dependency Inversion

- High-level modules (use cases) don't depend on low-level modules (infrastructure)
- Both depend on abstractions (ports/interfaces)
- Infrastructure implements domain interfaces

### 2. Single Responsibility

Each module has one clear responsibility:
- `main.py` → Composition
- `infrastructure/config/config.py` → Configuration loading
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
| Read configuration | `main.py` + `infrastructure/config/config.py` |
| Detect hardware | `HardwareInfo` (infrastructure) |
| Connect to database | `main.py` + `DatabaseConnection` (infrastructure) |
| Create tables | `DatabaseConnection` (infrastructure) |
| List directories | `Filesystem` (infrastructure) |
| Read files / ensure dirs | `Filesystem` (infrastructure) |
| Verify transcodings | `VideoRepository` (infrastructure) |
| Create transcoders | `TranscoderFactory` (infrastructure) |
| Execute ffmpeg | `Transcoder` (infrastructure) |
| Logging | `AppLogger` (port) / `EnhancedLogger` (infrastructure) |
| Orchestrate everything | `ProcessVideosUseCase` |

## Usage

### Running the Application

```bash
python main.py
```

## Configuration

Infrastructure settings are loaded from environment variables. See `env.example` in the root directory for the full reference.

### Main Environment Variables

**Paths:**
- `MEDIA_APP_PATH` - Path inside container where media is mounted (default: `/media`)
- `DATABASE_APP_PATH` - Path inside container where database is stored (default: `data/transcodings.db`)

**Scheduling:**
- `STARTUP_DELAY` - Minutes to wait before first execution (default: 30)
- `EXECUTION_INTERVAL` - Minutes between periodic executions (default: 240)

**Logger:**
- `LOGGER_NAME` - Logger name (default: synology-photos-video-enhancer)
- `LOGGER_LEVEL` - Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)

**Transcoding settings** (codec, bitrate, resolution, threads, hardware acceleration, etc.) are stored in the SQLite database and managed at runtime via the built-in dashboard. They are not read from environment variables.

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
