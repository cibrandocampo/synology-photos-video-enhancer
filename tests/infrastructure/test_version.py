"""Tests for the build-time version constant."""

import importlib

import infrastructure.version


class TestAppVersion:
    def test_defaults_to_dev_without_build_arg(self, monkeypatch):
        monkeypatch.delenv("APP_VERSION", raising=False)
        module = importlib.reload(infrastructure.version)

        assert module.APP_VERSION == "dev"

    def test_reads_the_value_injected_by_ci(self, monkeypatch):
        monkeypatch.setenv("APP_VERSION", "v4.2.1-2-gbd6bb")
        module = importlib.reload(infrastructure.version)

        assert module.APP_VERSION == "v4.2.1-2-gbd6bb"

    def teardown_method(self):
        # The constant is read at import time and cached by other modules;
        # restore the process-wide default so test order stays irrelevant.
        importlib.reload(infrastructure.version)
