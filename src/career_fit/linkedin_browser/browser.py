"""Camoufox launch helpers — guest or persistent profile.

Product/API path is headless by default so the founder only sees Career Fit UI.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from .config import SessionConfig, load_session_config
from .errors import BrowserJobError


def _default_headless() -> bool:
    """Headless unless CAREER_FIT_CAMOUFOX_HEADLESS=0 (debug)."""
    raw = os.environ.get("CAREER_FIT_CAMOUFOX_HEADLESS", "1").strip().lower()
    return raw not in ("0", "false", "no", "off")


def _import_camoufox():
    try:
        from camoufox.sync_api import Camoufox
    except ImportError as e:
        raise BrowserJobError(
            "camoufox not installed — pip install -e '.[linkedin]' "
            "&& python -m camoufox fetch",
            status=503,
        ) from e
    return Camoufox


@contextmanager
def launch_guest(
    *,
    headless: bool | None = None,
    humanize: bool = True,
) -> Generator[Any, None, None]:
    """Ephemeral Camoufox browser (no cookies). Yields a Browser."""
    Camoufox = _import_camoufox()
    if headless is None:
        headless = _default_headless()
    kwargs: dict[str, Any] = {"headless": headless, "humanize": humanize}
    try:
        with Camoufox(**kwargs) as browser:
            yield browser
    except BrowserJobError:
        raise
    except Exception as e:  # noqa: BLE001
        raise BrowserJobError(
            f"Could not start Camoufox ({e}). Run: python -m camoufox fetch",
            status=503,
        ) from e


@contextmanager
def launch_persistent(
    cfg: SessionConfig | None = None,
    *,
    headless: bool | None = None,
) -> Generator[Any, None, None]:
    """Persistent Camoufox context (cookies under user_data_dir). Yields BrowserContext."""
    Camoufox = _import_camoufox()
    cfg = cfg or load_session_config()
    Path(cfg.user_data_dir).mkdir(parents=True, exist_ok=True)
    if headless is None:
        # Product path: headless by default (no extra windows)
        headless = True if _default_headless() else cfg.headless
    kwargs: dict[str, Any] = {
        "headless": headless,
        "humanize": cfg.humanize,
        "persistent_context": True,
        "user_data_dir": cfg.user_data_dir,
    }
    try:
        with Camoufox(**kwargs) as context:
            yield context
    except BrowserJobError:
        raise
    except Exception as e:  # noqa: BLE001
        raise BrowserJobError(
            f"Could not start Camoufox profile ({e}). "
            "Warm session: career-fit linkedin-burner-login",
            status=503,
        ) from e


def new_page(browser_or_context: Any) -> Any:
    """Get a page from Browser or persistent BrowserContext."""
    pages = getattr(browser_or_context, "pages", None)
    if pages:
        return pages[0]
    return browser_or_context.new_page()


def looks_like_login(page: Any) -> bool:
    try:
        url = (page.url or "").lower()
        if "/login" in url or "/checkpoint" in url or "/authwall" in url:
            return True
        body = (page.locator("body").inner_text(timeout=3000) or "").lower()
        head = body[:800]
        return "sign in" in head and "password" in head
    except Exception:  # noqa: BLE001
        return False
