"""Tests for main.py."""
from unittest.mock import Mock, patch


class TestSignalHandler:
    """Tests for signal handler."""
    
    def test_signal_handler_sets_shutdown_flag(self):
        """Test that signal handler sets _shutdown_requested flag."""
        # Import main module
        import main
        
        # Reset flag using the module's global
        main._shutdown_requested = False
        
        # Call signal handler
        main._signal_handler(signum=2, frame=None)
        
        assert main._shutdown_requested is True


class TestRunProcessing:
    """Tests for _run_processing function."""
    
    def test_run_processing_success(self):
        """Test _run_processing with successful execution."""
        import main
        from application.process_result import ProcessResult

        mock_controller = Mock()
        # ProcessResult is a dataclass, create it properly
        result = ProcessResult(
            total_processed=10,
            transcoded=5,
            already_transcoded=3,
            errors=0  # No errors = success
        )
        mock_controller.run.return_value = result
        mock_logger = Mock()
        
        main._run_processing(mock_controller, mock_logger)
        
        mock_controller.run.assert_called_once()
        mock_logger.subtitle.assert_called()
        # Should call info for success (errors == 0)
        mock_logger.info.assert_called()
    
    def test_run_processing_failure(self):
        """Test _run_processing with failed execution."""
        import main
        from application.process_result import ProcessResult

        mock_controller = Mock()
        # ProcessResult with errors
        result = ProcessResult(
            total_processed=10,
            transcoded=0,
            already_transcoded=5,
            errors=5  # Has errors
        )
        mock_controller.run.return_value = result
        mock_logger = Mock()
        
        main._run_processing(mock_controller, mock_logger)
        
        mock_controller.run.assert_called_once()
        # Should call warning when errors > 0
        mock_logger.warning.assert_called()
    
    def test_run_processing_exception(self):
        """Test _run_processing handles exceptions."""
        import main

        mock_controller = Mock()
        mock_controller.run.side_effect = Exception("Test error")
        mock_logger = Mock()
        
        main._run_processing(mock_controller, mock_logger)
        
        # Should log error when exception occurs
        assert mock_logger.error.call_count >= 2  # Error message + traceback
        # Verify error message was logged
        assert any("Error during video processing" in str(call) for call in mock_logger.error.call_args_list)


class TestMain:
    """Tests for main() function."""
    
    @patch('main.run_in_thread')
    @patch('main.Config')
    @patch('main.DatabaseConnection')
    @patch('main.SettingsRepositorySQL')
    @patch('main.VideoRepositorySQL')
    @patch('main.LocalFilesystem')
    @patch('main.LocalHardwareInfo')
    @patch('main.FFmpegTranscoderFactory')
    @patch('main.ProcessVideosUseCase')
    @patch('main.MainController')
    @patch('main.signal.signal')
    @patch('main.schedule')
    @patch('main.time.sleep')
    def test_main_shutdown_during_startup_delay(self, mock_sleep, mock_schedule, mock_signal,
                                                mock_main_controller, mock_use_case,
                                                mock_transcoder_factory,
                                                mock_hardware_info, mock_filesystem,
                                                mock_repository, mock_settings_repo,
                                                mock_db, mock_config, mock_run_in_thread):
        """Test main() handles shutdown during startup delay."""
        import main

        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.paths.media_path = "/test"
        mock_config.load.return_value = mock_config_instance

        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance

        mock_settings_repo.return_value.load.return_value = Mock(startup_delay=1, execution_interval=60)

        # Mock hardware_info properties for logging in main()
        mock_hw_instance = Mock()
        mock_hw_instance.cpu.vendor = Mock()
        mock_hw_instance.video_acceleration = None
        mock_hardware_info.return_value = mock_hw_instance

        # Set shutdown flag after first sleep
        def side_effect_sleep(seconds):
            main._shutdown_requested = True
        mock_sleep.side_effect = side_effect_sleep

        # Reset shutdown flag
        main._shutdown_requested = False

        main.main()

        # Should have called signal handlers
        assert mock_signal.call_count == 2  # SIGTERM and SIGINT

    @patch('main.run_in_thread')
    @patch('main.Config')
    @patch('main.DatabaseConnection')
    @patch('main.SettingsRepositorySQL')
    @patch('main.VideoRepositorySQL')
    @patch('main.LocalFilesystem')
    @patch('main.LocalHardwareInfo')
    @patch('main.FFmpegTranscoderFactory')
    @patch('main.ProcessVideosUseCase')
    @patch('main.MainController')
    @patch('main.signal.signal')
    @patch('main.schedule')
    @patch('main.time.sleep')
    def test_main_keyboard_interrupt(self, mock_sleep, mock_schedule, mock_signal,
                                     mock_main_controller, mock_use_case,
                                     mock_transcoder_factory,
                                     mock_hardware_info, mock_filesystem,
                                     mock_repository, mock_settings_repo,
                                     mock_db, mock_config, mock_run_in_thread):
        """Test main() handles KeyboardInterrupt."""
        import main

        # Setup mocks
        mock_config_instance = Mock()
        mock_config_instance.paths.media_path = "/test"
        mock_config.load.return_value = mock_config_instance

        mock_db_instance = Mock()
        mock_db.return_value = mock_db_instance

        mock_settings_repo.return_value.load.return_value = Mock(startup_delay=0, execution_interval=60)

        # Mock hardware_info properties for logging in main()
        mock_hw_instance = Mock()
        mock_hw_instance.cpu.vendor = Mock()
        mock_hw_instance.video_acceleration = None
        mock_hardware_info.return_value = mock_hw_instance

        # Make schedule.run_pending raise KeyboardInterrupt
        mock_schedule.run_pending.side_effect = KeyboardInterrupt()

        # Reset shutdown flag
        main._shutdown_requested = False

        main.main()

        # Should have handled KeyboardInterrupt gracefully
        assert True  # If we get here, exception was handled

    @patch('main.Config')
    @patch('main.DatabaseConnection')
    @patch('main.VideoRepositorySQL')
    @patch('main.LocalFilesystem')
    @patch('main.LocalHardwareInfo')
    @patch('main.FFmpegTranscoderFactory')
    @patch('main.ProcessVideosUseCase')
    @patch('main.MainController')
    @patch('main.signal.signal')
    @patch('main.schedule')
    @patch('main.time.sleep')
    @patch('sys.exit')
    def test_main_exception_handling(self, mock_exit, mock_sleep, mock_schedule, mock_signal,
                                     mock_main_controller, mock_use_case,
                                     mock_transcoder_factory,
                                     mock_hardware_info, mock_filesystem,
                                     mock_repository, mock_db, mock_config):
        """Test main() handles exceptions and exits."""
        import main

        # Setup mocks
        mock_config.load.side_effect = Exception("Config error")

        # Reset shutdown flag
        main._shutdown_requested = False

        main.main()

        # Should have called sys.exit(1)
        mock_exit.assert_called_once_with(1)

