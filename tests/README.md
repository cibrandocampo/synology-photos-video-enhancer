# Test Suite

Test suite for Synology Photos Video Enhancer following Hexagonal Architecture principles.

## Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── domain/
│   ├── test_constants_video.py
│   ├── test_constants_audio.py
│   └── test_models_transcoding.py
├── application/
│   └── test_process_videos_use_case.py
├── infrastructure/
│   ├── test_config.py
│   └── test_transcoder.py
└── controllers/
    └── test_main_controller.py
```

## Running Tests

Los tests deben ejecutarse dentro de Docker. Hay un docker-compose específico para tests.

### Ejecutar Tests en Docker

```bash
# Construir y ejecutar tests
docker-compose -f dev/docker-compose.test.yml up --build

# O solo ejecutar (si ya está construido)
docker-compose -f dev/docker-compose.test.yml up
```

Esto:
1. Construye la imagen con todas las dependencias
2. Instala las dependencias de desarrollo (pytest, pytest-cov, etc.)
3. Ejecuta todos los tests con coverage
4. Genera reportes en `htmlcov/` y `coverage.xml`

### Ejecutar Tests Interactivamente

Si necesitas ejecutar tests de forma interactiva o con opciones personalizadas:

```bash
# Entrar al contenedor
docker-compose -f dev/docker-compose.test.yml run --rm video-enhancer-test /bin/sh

# Dentro del contenedor, instalar dependencias y ejecutar
pip install -r ../dev/requirements-dev.txt
pytest tests/ -v
```

### Opciones de Pytest

Para ejecutar con opciones personalizadas, puedes modificar el comando en `dev/docker-compose.test.yml` o ejecutar interactivamente:

```bash
# Ejecutar un test específico
pytest tests/domain/test_constants_video.py::TestVideoCodec::test_from_str_valid

# Ejecutar sin coverage
pytest tests/ -v --no-cov

# Ejecutar con más verbosidad
pytest tests/ -vv

# Ejecutar solo tests marcados
pytest tests/ -m unit
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
- `mock_filesystem`: Mock Filesystem
- `mock_hardware_info`: Mock HardwareInfo
- `mock_transcoder`: Mock Transcoder
- `sample_video`: Sample Video object
- `sample_transcoding_configuration`: Sample TranscodingConfiguration

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
