"""Main entry point - composition root."""

import sys
import signal
import time
from pathlib import Path
import schedule

from domain.constants.container import get_video_extensions
from domain.models.hardware import CPUVendor
from application.dashboard_stats_use_case import DashboardStatsUseCase
from application.process_videos_use_case import ProcessVideosUseCase
from application.retranscode_use_case import RetranscodeUseCase
from application.settings_use_case import SettingsUseCase
from domain.models.settings import TranscodingSettings
from infrastructure.config.config import Config
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.settings_repository_sql import SettingsRepositorySQL
from infrastructure.db.transcoding_stats_repository_sql import (
    TranscodingStatsRepositorySQL,
)
from infrastructure.db.video_repository_sql import VideoRepositorySQL
from infrastructure.filesystem.local_filesystem import LocalFilesystem
from infrastructure.hardware.local_hardware_info import (
    LocalHardwareInfo,
    HW_ACCELERATION_DEVICE_PATH,
)
from infrastructure.logger import Logger
from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader
from infrastructure.metadata.ffprobe_metadata_reader import FFprobeMetadataReader
from infrastructure.metadata.synoindex_metadata_reader import SynoIndexMetadataReader
from infrastructure.transcoder.ffmpeg_transcoder_factory import FFmpegTranscoderFactory
from infrastructure.web.app import create_app
from infrastructure.web.i18n import Translations
from infrastructure.web.server import run_in_thread
from controllers.dashboard import build_routers
from controllers.main_controller import MainController


# Global flag for graceful shutdown
_shutdown_requested = False


def _signal_handler(signum, frame):
    """Handles shutdown signals gracefully."""
    global _shutdown_requested
    logger = Logger.get_logger()
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    _shutdown_requested = True


def _run_processing(controller, logger, execution_interval=None):
    """
    Executes the video processing workflow.

    Args:
        controller: MainController instance (pre-configured)
        logger: Logger instance
        execution_interval: Optional interval in minutes to show waiting message after execution
    """
    try:
        # Execute
        logger.subtitle("Starting video processing...")
        result = controller.run()
        logger.subtitle("Video processing completed")

        # Check if execution was successful
        if result.is_success:
            logger.info("Process completed successfully")
        else:
            logger.warning(f"Process completed with {result.errors} error(s)")

        # Show waiting message if interval is provided
        if execution_interval is not None:
            logger.info(
                f"Waiting {execution_interval} minute(s) until next execution..."
            )

    except Exception as e:
        logger.error(f"Error during video processing: {e}")
        import traceback

        logger.error(traceback.format_exc())


def main():
    """Main application entry point - composition root."""
    global _shutdown_requested

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    logger = Logger.get_logger()
    logger.title("Starting Synology Photos Video Enhancer")

    try:
        # 1. Load configuration
        config = Config.load()

        # 2. Initialize infrastructure adapters (once, reused across all executions)
        logger.info("Initializing infrastructure adapters...")

        # Database connection
        db_connection = DatabaseConnection(config.database, logger)
        db_connection.initialize()

        # Dashboard stats repository + use case (read-only, share the same connection)
        stats_repository = TranscodingStatsRepositorySQL(db_connection)
        dashboard_use_case = DashboardStatsUseCase(stats_repository)

        # Settings repository + use case
        settings_repository = SettingsRepositorySQL(db_connection)
        settings_use_case = SettingsUseCase(settings_repository)
        settings_use_case.seed_defaults()
        db_settings = settings_use_case.load()
        config.log_config(logger, db_settings)

        # Repository
        video_repository = VideoRepositorySQL(db_connection)
        retranscode_use_case = RetranscodeUseCase(
            video_repository=video_repository,
            stats_repository=stats_repository,
        )

        # Filesystem
        filesystem = LocalFilesystem(get_video_extensions())

        # Metadata readers
        # Source videos: probe the file first, and fall back to Synology's index.
        # The order is a capability question, not a preference. The index stores only
        # the nominal frame rate, so a constant 30 fps video and a variable-rate one
        # both read `30 1` and are indistinguishable — and the pipeline now treats the
        # two differently. Only ffprobe can tell them apart.
        # The cost is bounded: metadata is read only for videos not already recorded
        # as completed or not_required, so this is one subprocess per *new* video,
        # not one per video per cycle.
        ffprobe_reader = FFprobeMetadataReader(logger)
        metadata_reader = ChainedMetadataReader(
            [
                ffprobe_reader,
                SynoIndexMetadataReader(filesystem, logger),
            ],
            logger,
        )

        # Hardware info
        hardware_info = LocalHardwareInfo()
        logger.info("Detecting hardware...")
        cpu = hardware_info.cpu
        video_accel = hardware_info.video_acceleration
        if cpu.vendor in (CPUVendor.INTEL, CPUVendor.AMD):
            if not Path(HW_ACCELERATION_DEVICE_PATH).exists():
                logger.warning(f"DRI device not found ({HW_ACCELERATION_DEVICE_PATH})")
        logger.info("Hardware detected successfully")
        logger.info(f"  - CPU: {cpu}")
        hw_accel_verbose = video_accel.value if video_accel else "Disabled"
        logger.info(f"  - Hardware acceleration: {hw_accel_verbose}")

        # Transcoder factory
        transcoder_factory = FFmpegTranscoderFactory(hardware_info, logger)

        # 3. Build use case (reused across all executions)
        _defaults = TranscodingSettings()
        use_case = ProcessVideosUseCase(
            video_repository=video_repository,
            filesystem=filesystem,
            transcoder_factory=transcoder_factory,
            logger=logger,
            video_config=_defaults.to_video_config(),
            audio_config=_defaults.to_audio_config(),
            video_input_path=config.paths.media_path,
            metadata_reader=metadata_reader,
            # Never the chain: Synology's index of the output file still describes
            # the version this run overwrites.
            output_metadata_reader=ffprobe_reader,
            execution_threads=_defaults.execution_threads,
            settings_repository=settings_repository,
        )

        # 4. Build controller (reused across all executions)
        controller = MainController(use_case, logger=logger)

        logger.info("Infrastructure adapters initialized successfully")

        # 5. Build and start the dashboard before the scheduler loop so it
        # remains reachable even during the startup-delay window. Reading
        # `config.dashboard` here is the hard-fail point if DASHBOARD_*
        # env vars are missing — that error must surface at startup, not later.
        dashboard_config = config.dashboard
        translations = Translations()
        dashboard_app = create_app(
            use_case=dashboard_use_case,
            settings_use_case=settings_use_case,
            retranscode_use_case=retranscode_use_case,
            hardware_info=hardware_info,
            translations=translations,
            config=dashboard_config,
            routers=build_routers(),
            logger=logger,
        )
        run_in_thread(
            dashboard_app, host="0.0.0.0", port=dashboard_config.port, logger=logger
        )

        startup_delay = db_settings.startup_delay
        execution_interval = db_settings.execution_interval

        logger.info(f"Waiting {startup_delay} minutes before first execution...")

        # Wait for startup delay: allows container/system to fully initialize before processing videos.
        # This prevents immediate processing on container startup and ensures all services are ready.
        # The delay is checked second-by-second to allow graceful shutdown if requested during this period.
        startup_delay_seconds = startup_delay * 60
        elapsed = 0
        while elapsed < startup_delay_seconds and not _shutdown_requested:
            time.sleep(1)
            elapsed += 1

        if _shutdown_requested:
            logger.info("Shutdown requested during startup delay")
            return

        # Schedule periodic execution (with execution_interval parameter for waiting message)
        schedule.every(execution_interval).minutes.do(
            _run_processing,
            controller=controller,
            logger=logger,
            execution_interval=execution_interval,
        )

        # Run first execution immediately after startup delay
        logger.subtitle("Executing first video processing run...")
        _run_processing(controller, logger, execution_interval=execution_interval)

        # Main loop: run scheduled tasks
        # This loop checks for pending scheduled tasks every second while allowing immediate
        # graceful shutdown via signal handlers. The 1-second sleep prevents CPU spinning while
        # maintaining responsiveness to shutdown signals.
        while not _shutdown_requested:
            schedule.run_pending()
            time.sleep(1)

        logger.info("Shutdown complete")

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
