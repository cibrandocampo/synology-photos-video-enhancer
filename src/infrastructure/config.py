import os
import configparser
from pathlib import Path
from typing import List, Optional

from domain.constants.container import ContainerFormat


class Config:
    """
    Handles application configuration, including:
    - Environment variables
    - Logger setup
    - Database configuration
    - Video transcoding configuration
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config_parser = None
            self._config_file_path = os.getenv(
                "CONFIG_FILE_PATH",
                "photo-enhancer/video_quality_enhancer.conf"
            )

    def _load_config(self) -> configparser.ConfigParser:
        """Carga el archivo de configuración si no está cargado."""
        if self._config_parser is None:
            self._config_parser = configparser.ConfigParser()
            if os.path.exists(self._config_file_path):
                self._config_parser.read(self._config_file_path)
            else:
                # Crear configuración por defecto si no existe el archivo
                self._config_parser = self._create_default_config()
        return self._config_parser

    def _create_default_config(self) -> configparser.ConfigParser:
        """Crea una configuración por defecto."""
        config = configparser.ConfigParser()
        config['InputFolders'] = {
            'VIDEO_PATH': '/data'
        }
        config['OutputVideo'] = {
            'VIDEO_CODEC': 'h264',
            'VIDEO_BITRATE': '2048k',
            'VIDEO_MAX_H_W': '720',
            'VIDEO_PROFILE': '-profile:v high -level:v 4.1',
            'VIDEO_CONTAINER': 'mp4',
            'AUDIO_CODEC': 'aac',
            'AUDIO_BITRATE': '128k',
            'AUDIO_CHANNELS': '1'
        }
        return config

    @property
    def logger_config(self) -> tuple:
        """
        Retrieves logger configuration from environment variables.

        Returns:
            tuple[str, str]: (logger name, logger level)
        """
        return (
            os.getenv("LOGGER_NAME", "synology-photos-video-enhancer"),
            os.getenv("LOGGER_LEVEL", "INFO").upper(),
        )
    
    @property
    def database_path(self) -> str:
        """
        Retrieves database path from environment variables.
        
        Returns:
            str: Path to SQLite database file
        """
        db_path = os.getenv("DATABASE_PATH", "data/transcodings.db")
        # Asegurar que el directorio existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return db_path

    @property
    def video_input_path(self) -> str:
        """
        Obtiene la ruta de entrada de vídeos desde la configuración.
        
        Returns:
            str: Ruta donde buscar vídeos
        """
        config = self._load_config()
        if config.has_option('InputFolders', 'VIDEO_PATH'):
            return config.get('InputFolders', 'VIDEO_PATH')
        return '/data'  # Default a /data si no hay configuración

    @property
    def video_extensions(self) -> List[str]:
        """
        Obtiene las extensiones de vídeo permitidas desde ContainerFormat.
        
        Returns:
            List[str]: Lista de extensiones (sin punto, incluyendo mayúsculas y minúsculas)
        """
        # Obtener todas las extensiones de los formatos de contenedor soportados
        extensions = []
        for container_format in ContainerFormat:
            ext = container_format.value
            # Incluir tanto mayúsculas como minúsculas para compatibilidad
            extensions.append(ext.lower())
            extensions.append(ext.upper())
        return sorted(set(extensions))  # Eliminar duplicados y ordenar

    @property
    def output_video_codec(self) -> str:
        """Obtiene el codec de vídeo de salida."""
        config = self._load_config()
        return config.get('OutputVideo', 'VIDEO_CODEC', fallback='h264')

    @property
    def output_video_resolution(self) -> int:
        """Obtiene la resolución máxima de vídeo de salida."""
        config = self._load_config()
        return config.getint('OutputVideo', 'VIDEO_MAX_H_W', fallback=720)

    @property
    def output_video_bitrate(self) -> str:
        """Obtiene el bitrate de vídeo de salida."""
        config = self._load_config()
        return config.get('OutputVideo', 'VIDEO_BITRATE', fallback='2048k')

    @property
    def output_audio_codec(self) -> str:
        """Obtiene el codec de audio de salida."""
        config = self._load_config()
        return config.get('OutputVideo', 'AUDIO_CODEC', fallback='aac')