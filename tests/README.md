# Test Suite

Test suite for Synology Photos Video Enhancer following Hexagonal Architecture principles.

## Structure

```
tests/
├── __init__.py
├── conftest.py                # Shared fixtures and configuration
├── test_main.py               # Tests for main.py (composition root)
├── domain/
│   ├── test_constants_video.py
│   ├── test_constants_audio.py
│   ├── test_constants_container.py
│   ├── test_constants_framerate.py
│   ├── test_constants_hardware.py
│   ├── test_constants_resolution.py
│   ├── test_models_app_config.py
│   ├── test_models_transcoding.py
│   └── test_models_video.py
├── application/
│   ├── test_process_result.py
│   └── test_process_videos_use_case.py
├── infrastructure/
│   ├── test_config.py
│   ├── test_db_connection.py
│   ├── test_ffmpeg_codecs.py
│   ├── test_filesystem.py
│   ├── test_hardware_info.py
│   ├── test_logger.py
│   ├── test_transcoder.py
│   ├── test_transcoder_factory.py
│   ├── test_utils.py
│   └── test_video_repository.py
└── controllers/
    └── test_main_controller.py
```

## Running Tests

Tests must be executed inside Docker. There is a specific docker-compose file for tests.

### Running Tests in Docker

```bash
# Build and run tests
docker compose -f dev/docker-compose.test.yml up --build

# Or just run (if already built)
docker compose -f dev/docker-compose.test.yml up
```

This will:
1. Build the image with all dependencies
2. Install development dependencies (pytest, pytest-cov, etc.)
3. Run all tests with coverage
4. Display coverage report in the terminal

### Running Tests Interactively

If you need to run tests interactively or with custom options:

```bash
# Enter the container
docker compose -f dev/docker-compose.test.yml run --rm video-enhancer-test /bin/sh

# Inside the container, install dependencies and run
pip install -q -r dev/requirements-dev.txt
python -m pytest tests/ -v
```

### Pytest Options

To run with custom options, you can modify the command in `dev/docker-compose.test.yml` or run interactively:

```bash
# Run a specific test
python -m pytest tests/domain/test_constants_video.py::TestVideoCodec::test_from_str_valid

# Run without coverage
python -m pytest tests/ -v --no-cov

# Run with more verbosity
python -m pytest tests/ -vv

# Run only marked tests
python -m pytest tests/ -m unit
```

## Test Categories

Tests are organized by architectural layer:

- **Domain**: Tests for domain models, constants, and business logic
- **Application**: Tests for use cases (with mocked dependencies)
- **Infrastructure**: Tests for infrastructure adapters
- **Controllers**: Tests for controller layer

## Fixtures

Common fixtures are defined in `conftest.py`:

- `temp_dir`: Temporary directory for test files
- `temp_db_path`: Temporary database path
- `mock_video_repository`: Mock VideoRepository
- `mock_filesystem`: Mock Filesystem (includes `read_file`, `ensure_directory`)
- `mock_hardware_info`: Mock HardwareInfo
- `mock_logger`: Mock AppLogger
- `mock_transcoder`: Mock Transcoder
- `mock_transcoder_factory`: Mock TranscoderFactory
- `sample_video`: Sample Video object
- `sample_transcoding_configuration`: Sample TranscodingConfiguration
- `sample_video_track`: Sample VideoTrack object
- `sample_audio_track`: Sample AudioTrack object
- `sample_container`: Sample Container object

## Writing New Tests

1. Follow the naming convention: `test_*.py` for files, `test_*` for functions
2. Use fixtures from `conftest.py` when possible
3. Mock external dependencies (filesystem, database, hardware)
4. Test both success and failure cases
5. Keep tests isolated and independent

## Coverage Goals

- Domain layer: 100% coverage (pure business logic)
- Application layer: >90% coverage (use cases)
- Infrastructure layer: >80% coverage (adapters)
- Controllers: >80% coverage
