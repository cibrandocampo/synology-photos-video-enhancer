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



@patch("main.run_in_thread")
@patch("main.create_app")
@patch("main.build_routers", return_value=[])
@patch("main._run_processing")
@patch("main.schedule")
@patch("main.signal.signal")
@patch("main.time.sleep")
@patch("main.MainController")
@patch("main.ProcessVideosUseCase")
@patch("main.FFmpegTranscoderFactory")
@patch("main.LocalHardwareInfo")
@patch("main.LocalFilesystem")
@patch("main.VideoRepositorySQL")
@patch("main.SettingsRepositorySQL")
@patch("main.DatabaseConnection")
@patch("main.Path")
@patch("main.Logger")
@patch("main.Config")
class TestCompositionRootWiring:
    """The arguments `main()` passes must satisfy the real constructor.

    Every other test in this module patches `main.ProcessVideosUseCase`, so a use
    case that gained a required parameter would keep the suite green while the
    container failed to start. These tests bind the captured arguments against the
    genuine signature instead.
    """

    def _run_main(self, mock_config, mock_logger, mock_hardware_info,
                  mock_settings_repo, mock_sleep):
        """Runs `main()` once with all I/O mocked out."""
        from domain.models.app_config import DashboardConfig
        from domain.models.hardware import CPUVendor
        import main

        config = Mock()
        config.database = Mock()
        config.paths = Mock()
        config.paths.media_path = "/test/media"
        config.dashboard = DashboardConfig(
            port=9201,
            user="admin",
            password="secret",
            secret_key="key123",
            cookie_secure=False,
        )
        config.log_config = Mock()
        mock_config.load.return_value = config

        mock_logger.get_logger.return_value = Mock()
        mock_settings_repo.return_value.load.return_value = Mock(
            startup_delay=0, execution_interval=60
        )

        hardware = mock_hardware_info.return_value
        cpu = Mock()
        cpu.vendor = CPUVendor.INTEL
        hardware.cpu = cpu
        hardware.video_acceleration = None

        state = {"called": 0}

        def _stop_after_first_tick(_seconds):
            state["called"] += 1
            if state["called"] == 1:
                main._shutdown_requested = True

        mock_sleep.side_effect = _stop_after_first_tick

        main._shutdown_requested = False
        main.main()
        main._shutdown_requested = False

    def test_arguments_satisfy_the_real_signature(
        self, mock_config, mock_logger, mock_path, mock_db, mock_settings_repo,
        mock_video_repo, mock_filesystem, mock_hardware_info,
        mock_transcoder_factory, mock_process_use_case, mock_main_controller,
        mock_sleep, mock_signal, mock_schedule, mock_run_processing,
        mock_build_routers, mock_create_app, mock_run_in_thread,
    ):
        """A missing required argument must fail here, not on the NAS."""
        import inspect
        from application.process_videos_use_case import ProcessVideosUseCase

        self._run_main(
            mock_config, mock_logger, mock_hardware_info, mock_settings_repo, mock_sleep
        )

        mock_process_use_case.assert_called_once()
        args, kwargs = mock_process_use_case.call_args

        # Raises TypeError if any required parameter is missing or unknown.
        inspect.signature(ProcessVideosUseCase.__init__).bind(
            Mock(name="self"), *args, **kwargs
        )

    def test_source_reader_is_the_chain(
        self, mock_config, mock_logger, mock_path, mock_db, mock_settings_repo,
        mock_video_repo, mock_filesystem, mock_hardware_info,
        mock_transcoder_factory, mock_process_use_case, mock_main_controller,
        mock_sleep, mock_signal, mock_schedule, mock_run_processing,
        mock_build_routers, mock_create_app, mock_run_in_thread,
    ):
        """Source videos must be probed first, with Synology's index as the fallback.

        The order is a capability question. The index stores only the nominal frame
        rate, so a constant 30 fps source and a variable-rate one both read `30 1`;
        the pipeline now treats those two differently, and only ffprobe can tell them
        apart. Restoring the old order silently disables that distinction, which is
        why the position of each reader is asserted rather than merely their presence.
        """
        from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader
        from infrastructure.metadata.ffprobe_metadata_reader import FFprobeMetadataReader
        from infrastructure.metadata.synoindex_metadata_reader import (
            SynoIndexMetadataReader,
        )

        self._run_main(
            mock_config, mock_logger, mock_hardware_info, mock_settings_repo, mock_sleep
        )

        reader = mock_process_use_case.call_args.kwargs["metadata_reader"]
        assert isinstance(reader, ChainedMetadataReader)
        assert isinstance(reader.readers[0], FFprobeMetadataReader)
        assert isinstance(reader.readers[1], SynoIndexMetadataReader)

    def test_output_reader_is_ffprobe_alone(
        self, mock_config, mock_logger, mock_path, mock_db, mock_settings_repo,
        mock_video_repo, mock_filesystem, mock_hardware_info,
        mock_transcoder_factory, mock_process_use_case, mock_main_controller,
        mock_sleep, mock_signal, mock_schedule, mock_run_processing,
        mock_build_routers, mock_create_app, mock_run_in_thread,
    ):
        """Reading the output through Synology's index is the stale-resolution defect."""
        from infrastructure.metadata.chained_metadata_reader import ChainedMetadataReader
        from infrastructure.metadata.ffprobe_metadata_reader import FFprobeMetadataReader

        self._run_main(
            mock_config, mock_logger, mock_hardware_info, mock_settings_repo, mock_sleep
        )

        reader = mock_process_use_case.call_args.kwargs["output_metadata_reader"]
        assert isinstance(reader, FFprobeMetadataReader)
        assert not isinstance(reader, ChainedMetadataReader)

    def test_readers_are_distinct_collaborators(
        self, mock_config, mock_logger, mock_path, mock_db, mock_settings_repo,
        mock_video_repo, mock_filesystem, mock_hardware_info,
        mock_transcoder_factory, mock_process_use_case, mock_main_controller,
        mock_sleep, mock_signal, mock_schedule, mock_run_processing,
        mock_build_routers, mock_create_app, mock_run_in_thread,
    ):
        """The ffprobe instance is shared, but the source reader is not the output one."""
        self._run_main(
            mock_config, mock_logger, mock_hardware_info, mock_settings_repo, mock_sleep
        )

        kwargs = mock_process_use_case.call_args.kwargs
        assert kwargs["metadata_reader"] is not kwargs["output_metadata_reader"]
        assert kwargs["metadata_reader"].readers[0] is kwargs["output_metadata_reader"]

    def test_a_missing_dri_device_is_warned_about(
        self, mock_config, mock_logger, mock_path, mock_db, mock_settings_repo,
        mock_video_repo, mock_filesystem, mock_hardware_info,
        mock_transcoder_factory, mock_process_use_case, mock_main_controller,
        mock_sleep, mock_signal, mock_schedule, mock_run_processing,
        mock_build_routers, mock_create_app, mock_run_in_thread,
    ):
        """An Intel or AMD CPU with no /dev/dri means silent software encoding.

        Nothing fails when the device is absent — the run just becomes many times
        slower, which is exactly the kind of problem that goes unnoticed without a
        line in the log.
        """
        mock_path.return_value.exists.return_value = False

        self._run_main(
            mock_config, mock_logger, mock_hardware_info, mock_settings_repo, mock_sleep
        )

        logger = mock_logger.get_logger.return_value
        warnings = [str(call.args[0]) for call in logger.warning.call_args_list]
        assert any("DRI device not found" in warning for warning in warnings)
