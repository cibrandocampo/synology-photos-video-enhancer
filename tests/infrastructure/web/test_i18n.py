"""Unit tests for the i18n infrastructure (detect_locale + Translations)."""

from unittest.mock import Mock

import pytest

from infrastructure.web.i18n import DEFAULT_LOCALE, Translations, detect_locale


def _req(accept_language=None):
    """Build a minimal mock request with the given Accept-Language header."""
    mock = Mock()
    mock.headers = {"accept-language": accept_language} if accept_language else {}
    return mock


class TestDetectLocale:
    def test_exact_match_es(self):
        assert detect_locale(_req("es")) == "es"

    def test_exact_match_gl(self):
        assert detect_locale(_req("gl")) == "gl"

    def test_subtag_match(self):
        assert detect_locale(_req("es-ES")) == "es"

    def test_quality_order_picks_first_supported(self):
        # fr is not supported; es is → returns 'es'
        assert detect_locale(_req("fr,es;q=0.8,en;q=0.5")) == "es"

    def test_unknown_language_fallback(self):
        assert detect_locale(_req("fr")) == DEFAULT_LOCALE

    def test_missing_header_fallback(self):
        assert detect_locale(_req()) == DEFAULT_LOCALE

    def test_en_explicit(self):
        assert detect_locale(_req("en")) == "en"

    def test_case_insensitive(self):
        assert detect_locale(_req("ES-ES")) == "es"


class TestTranslations:
    @pytest.fixture
    def trans(self):
        return Translations()

    def test_loads_without_error(self, trans):
        assert trans is not None

    def test_simple_key_en(self, trans):
        t = trans.for_locale("en")
        assert t("nav.dashboard") == "Dashboard"

    def test_simple_key_es(self, trans):
        t = trans.for_locale("es")
        # es.json is a stub in T006 (same as en); T007 fills real translations
        assert isinstance(t("nav.dashboard"), str)

    def test_interpolation(self, trans):
        t = trans.for_locale("en")
        result = t("dashboard.table.show_more", count=3)
        assert "3" in result

    def test_missing_key_returns_key_itself(self, trans):
        t = trans.for_locale("en")
        assert t("nonexistent.key") == "nonexistent.key"

    def test_unknown_locale_falls_back_to_en(self, trans):
        t = trans.for_locale("fr")
        assert t("nav.dashboard") == "Dashboard"

    def test_for_locale_returns_callable(self, trans):
        t = trans.for_locale("en")
        assert callable(t)
