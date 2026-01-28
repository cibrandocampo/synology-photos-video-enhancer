"""Main controller for application entry point."""
import argparse

from application.process_videos_use_case import ProcessVideosUseCase
from application.process_result import ProcessResult
from domain.ports.logger import AppLogger


class MainController:
    """Main controller for application execution."""

    def __init__(self, use_case: ProcessVideosUseCase, logger: AppLogger):
        """
        Initializes the main controller.

        Args:
            use_case: Process videos use case
            logger: Logger instance
        """
        self.use_case = use_case
        self.logger = logger
    
    def run(self, args: argparse.Namespace = None) -> ProcessResult:
        """
        Runs the main controller.
        
        Args:
            args: Parsed command-line arguments (optional)
            
        Returns:
            ProcessResult: Detailed result of the processing operation
        """
        # Execute the use case
        result = self.use_case.execute()
        
        # Display detailed results
        self._display_results(result)
        
        return result
    
    def _display_results(self, result: ProcessResult) -> None:
        """
        Displays the processing results.
        
        Args:
            result: Process result to display
        """
        self.logger.info("Processing results:")
        self.logger.info(f"  - Total processed: {result.total_processed}")
        self.logger.info(f"  - Already transcoded: {result.already_transcoded}")
        self.logger.info(f"  - Transcoded: {result.transcoded}")
        if result.errors > 0:
            self.logger.warning(f"  - Errors: {result.errors}")
        else:
            self.logger.info(f"  - Errors: {result.errors}")
    
    @staticmethod
    def parse_args() -> argparse.Namespace:
        """
        Parses command-line arguments.
        
        Returns:
            Parsed arguments
        """
        parser = argparse.ArgumentParser(
            description="Synology Photos Video Enhancer"
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without actually doing it"
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Enable verbose output"
        )
        parser.add_argument(
            "--only-new",
            action="store_true",
            help="Only process videos that haven't been transcoded"
        )
        return parser.parse_args()
