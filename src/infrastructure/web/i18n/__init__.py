"""Server-side i18n: JSON-based translation loader and Accept-Language detector."""

import json
from pathlib import Path
from typing import Callable

SUPPORTED_LOCALES: frozenset[str] = frozenset({"en", "es", "gl"})
DEFAULT_LOCALE = "en"

_LOCALES_DIR = Path(__file__).parent


def detect_locale(request) -> str:
    """Return the best-supported locale from the Accept-Language header, or 'en'."""
    header = request.headers.get("accept-language", "")
    for part in header.split(","):
        tag = part.split(";")[0].strip().lower()
        lang = tag.split("-")[0]
        if lang in SUPPORTED_LOCALES:
            return lang
    return DEFAULT_LOCALE


class Translations:
    """Loads all locale JSON files once at startup and provides per-locale t() callables."""

    def __init__(self, locales_dir: Path = _LOCALES_DIR) -> None:
        self._data: dict[str, dict[str, str]] = {}
        for locale in SUPPORTED_LOCALES:
            path = locales_dir / f"{locale}.json"
            with open(path, encoding="utf-8") as f:
                self._data[locale] = json.load(f)

    def for_locale(self, locale: str) -> Callable[..., str]:
        """Return a t(key, **kwargs) callable bound to the given locale."""
        data = self._data.get(locale, self._data[DEFAULT_LOCALE])

        def t(key: str, **kwargs: object) -> str:
            value = data.get(key, key)  # fallback: return the key itself
            if kwargs:
                return value.format_map(kwargs)
            return value

        return t
