"""Composition-root smoke test: dashboard is wired and started before the scheduler."""
from unittest.mock import Mock, patch

import pytest

import main
from domain.models.app_config import DashboardConfig
from domain.models.hardware import CPUVendor


@pytest.fixture(autouse=True)
def reset_shutdown_flag():
    """Ensure each test starts with a fresh `_shutdown_requested`."""
    main._shutdown_requested = False
    yield
    main._shutdown_requested = False


def _stub_config(*, dashboard_port: int = 9201) -> Mock:
    """Returns a Mock posing as `Config.load()`'s return value."""
    config = Mock()
    config.database = Mock()
    config.paths = Mock()
    config.paths.media_path = "/test/media"
    config.dashboard = DashboardConfig(
        port=dashboard_port,
        user="admin",
        password="secret",
        secret_key="key123",
        cookie_secure=False,
    )
    config.log_config = Mock()
    return config


def _trigger_shutdown_on_first_sleep():
    """Returns a side_effect for `time.sleep` that flips `_shutdown_requested`.

    The first call (inside the scheduler's `while not _shutdown_requested`
    loop) sets the flag so the loop terminates after one tick.
    """
    state = {"called": 0}

    def _side_effect(_seconds):
        state["called"] += 1
        if state["called"] == 1:
            main._shutdown_requested = True

    return _side_effect


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
class TestDashboardWiring:
    """End-to-end smoke for `main()` with all I/O mocked out."""

    def _wire_hardware(self, mock_hardware_info_cls):
        instance = mock_hardware_info_cls.return_value
        cpu_mock = Mock()
        cpu_mock.vendor = CPUVendor.INTEL
        instance.cpu = cpu_mock
        instance.video_acceleration = None
        return instance

    def test_dashboard_app_started_before_scheduler_first_tick(
        self,
        mock_config,
        mock_logger,
        mock_path,
        mock_db,
        mock_settings_repo,
        mock_video_repo,
        mock_filesystem,
        mock_hardware_info,
        mock_transcoder_factory,
        mock_process_use_case,
        mock_main_controller,
        mock_sleep,
        mock_signal,
        mock_schedule,
        mock_run_processing,
        mock_build_routers,
        mock_create_app,
        mock_run_in_thread,
    ):
        events = []

        sentinel_app = Mock(name="dashboard_app")
        mock_create_app.return_value = sentinel_app
        mock_settings_repo.return_value.load.return_value = Mock(startup_delay=0, execution_interval=60)

        def _record_run_in_thread(*_args, **_kwargs):
            events.append("run_in_thread")
            return Mock(name="dashboard_thread")

        def _record_run_processing(*_args, **_kwargs):
            events.append("run_processing")

        mock_run_in_thread.side_effect = _record_run_in_thread
        mock_run_processing.side_effect = _record_run_processing
        mock_sleep.side_effect = _trigger_shutdown_on_first_sleep()

        mock_config.load.return_value = _stub_config()
        mock_logger.get_logger.return_value = Mock()
        self._wire_hardware(mock_hardware_info)

        main.main()

        assert "run_in_thread" in events
        assert "run_processing" in events
        assert events.index("run_in_thread") < events.index("run_processing"), (
            f"run_in_thread must precede the first scheduled run; got {events}"
        )

    def test_create_app_receives_dashboard_use_case_config_routers_logger(
        self,
        mock_config,
        mock_logger,
        mock_path,
        mock_db,
        mock_settings_repo,
        mock_video_repo,
        mock_filesystem,
        mock_hardware_info,
        mock_transcoder_factory,
        mock_process_use_case,
        mock_main_controller,
        mock_sleep,
        mock_signal,
        mock_schedule,
        mock_run_processing,
        mock_build_routers,
        mock_create_app,
        mock_run_in_thread,
    ):
        stub_config = _stub_config()
        mock_config.load.return_value = stub_config
        mock_settings_repo.return_value.load.return_value = Mock(startup_delay=0, execution_interval=60)
        stub_logger = Mock()
        mock_logger.get_logger.return_value = stub_logger
        self._wire_hardware(mock_hardware_info)
        mock_sleep.side_effect = _trigger_shutdown_on_first_sleep()

        main.main()

        mock_create_app.assert_called_once()
        kwargs = mock_create_app.call_args.kwargs
        assert kwargs["config"] is stub_config.dashboard
        assert kwargs["routers"] == []
        assert kwargs["logger"] is stub_logger
        # The use case must be the DashboardStatsUseCase wrapping the SQL repo.
        from application.dashboard_stats_use_case import DashboardStatsUseCase
        assert isinstance(kwargs["use_case"], DashboardStatsUseCase)

    def test_run_in_thread_uses_dashboard_port_from_config(
        self,
        mock_config,
        mock_logger,
        mock_path,
        mock_db,
        mock_settings_repo,
        mock_video_repo,
        mock_filesystem,
        mock_hardware_info,
        mock_transcoder_factory,
        mock_process_use_case,
        mock_main_controller,
        mock_sleep,
        mock_signal,
        mock_schedule,
        mock_run_processing,
        mock_build_routers,
        mock_create_app,
        mock_run_in_thread,
    ):
        sentinel_app = Mock(name="dashboard_app")
        mock_create_app.return_value = sentinel_app
        mock_settings_repo.return_value.load.return_value = Mock(startup_delay=0, execution_interval=60)
        mock_config.load.return_value = _stub_config(dashboard_port=9301)
        mock_logger.get_logger.return_value = Mock()
        self._wire_hardware(mock_hardware_info)
        mock_sleep.side_effect = _trigger_shutdown_on_first_sleep()

        main.main()

        mock_run_in_thread.assert_called_once()
        kwargs = mock_run_in_thread.call_args.kwargs
        args = mock_run_in_thread.call_args.args
        called_app = args[0] if args else kwargs.get("app")
        assert called_app is sentinel_app
        assert kwargs.get("host") == "0.0.0.0"
        assert kwargs.get("port") == 9301
