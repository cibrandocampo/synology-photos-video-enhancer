"""Main entry point - composition root."""
import sys
import signal
import time
from pathlib import Path
import schedule

from infrastructure.config.config import Config
from infrastructure.logger import Logger
from infrastructure.db.connection import DatabaseConnection
from infrastructure.db.video_repository_sql import VideoRepositorySQL
from infrastructure.filesystem.local_filesystem import LocalFilesystem
from infrastructure.hardware.local_hardware_info import LocalHardwareInfo, HW_ACCELERATION_DEVICE_PATH
from infrastructure.transcoder.ffmpeg_transcoder_factory import FFmpegTranscoderFactory
from application.process_videos_use_case import ProcessVideosUseCase
from controllers.main_controller import MainController
from domain.constants.container import get_video_extensions
from domain.models.hardware import CPUVendor


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
        # Parse CLI arguments
        args = MainController.parse_args()
        
        # Execute
        logger.subtitle("Starting video processing...")
        result = controller.run(args)
        logger.subtitle("Video processing completed")
        
        # Check if execution was successful
        if result.is_success:
            logger.info("Process completed successfully")
        else:
            logger.warning(f"Process completed with {result.errors} error(s)")
        
        # Show waiting message if interval is provided
        if execution_interval is not None:
            logger.info(f"Waiting {execution_interval} minute(s) until next execution...")
        
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
        config.log_config(logger)
        
        # 2. Initialize infrastructure adapters (once, reused across all executions)
        logger.info("Initializing infrastructure adapters...")
        
        # Database connection
        db_connection = DatabaseConnection(config.database, logger)
        db_connection.initialize()
        
        # Repository
        video_repository = VideoRepositorySQL(db_connection)
        
        # Filesystem
        filesystem = LocalFilesystem(get_video_extensions())
        
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
        hw_accel_verbose = video_accel.value if video_accel else 'Disabled'
        logger.info(f"  - Hardware acceleration: {hw_accel_verbose}")

        # Transcoder factory
        transcoder_factory = FFmpegTranscoderFactory(hardware_info, logger)

        # 3. Build use case (reused across all executions)
        use_case = ProcessVideosUseCase(
            video_repository=video_repository,
            filesystem=filesystem,
            transcoder_factory=transcoder_factory,
            logger=logger,
            video_config=config.transcoding.video,
            audio_config=config.transcoding.audio,
            video_input_path=config.paths.media_path,
            execution_threads=config.transcoding.execution_threads
        )
        
        # 4. Build controller (reused across all executions)
        controller = MainController(use_case, logger=logger)
        
        logger.info("Infrastructure adapters initialized successfully")
        
        startup_delay = config.transcoding.startup_delay
        execution_interval = config.transcoding.execution_interval
        
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
            execution_interval=execution_interval
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


if __name__ == "__main__":
    main()
