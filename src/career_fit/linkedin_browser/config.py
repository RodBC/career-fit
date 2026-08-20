"""Session config for Camoufox persistent profile (no end-user password in API)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import ROOT

_DEFAULT_PROFILE = ROOT / "data" / "camoufox_profile"
# Legacy Chrome profile — still reported so founders can migrate once
_LEGACY_CHROME_PROFILE = ROOT / "data" / "chrome_profile"


@dataclass
class SessionConfig:
    user_data_dir: str = ""
    nav_pause_sec: float = 1.5
    headless: bool = False
    humanize: bool = True


def load_session_config(override: dict[str, Any] | None = None) -> SessionConfig:
    """Load from env and optional gitignored data/linkedin_session.yaml."""
    data: dict[str, Any] = {}
    cfg_path = ROOT / "data" / "linkedin_session.yaml"
    if cfg_path.exists():
        try:
            import yaml

            loaded = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            if isinstance(loaded, dict):
                data.update(loaded)
        except Exception:  # noqa: BLE001
            pass

    env_map = {
        "user_data_dir": "CAREER_FIT_CAMOUFOX_USER_DATA",
        "nav_pause_sec": "CAREER_FIT_NAV_PAUSE",
    }
    for key, env in env_map.items():
        val = os.environ.get(env)
        if val:
            data[key] = val

    # Legacy env still accepted for profile dir during migration
    legacy = os.environ.get("CAREER_FIT_CHROME_USER_DATA")
    if legacy and not data.get("user_data_dir"):
        data["user_data_dir"] = legacy

    if override:
        data.update({k: v for k, v in override.items() if v not in (None, "")})

    user_data = str(data.get("user_data_dir") or "") or str(_DEFAULT_PROFILE)
    # Camoufox cannot reuse Chrome user-data-dir — migrate legacy default path
    if "chrome_profile" in user_data.replace("\\", "/") and not os.environ.get(
        "CAREER_FIT_CAMOUFOX_USER_DATA"
    ):
        user_data = str(_DEFAULT_PROFILE)
    headless_env = os.environ.get("CAREER_FIT_CAMOUFOX_HEADLESS", "1").strip().lower()
    # Default ON (headless) for zero-friction product UI
    headless = headless_env not in ("0", "false", "no", "off")
    if "headless" in data:
        headless = bool(data.get("headless"))

    return SessionConfig(
        user_data_dir=user_data,
        nav_pause_sec=float(data.get("nav_pause_sec") or 1.5),
        headless=headless,
        humanize=bool(data.get("humanize", True)),
    )


def session_ready_report(cfg: SessionConfig | None = None) -> dict[str, Any]:
    """Diagnose why live LinkedIn map would 503."""
    cfg = cfg or load_session_config()
    profile_path = Path(cfg.user_data_dir)
    profile_ok = profile_path.exists()
    # Camoufox/Firefox persistent dirs usually contain cookies.sqlite or storage
    cookie_hints = [
        profile_path / "cookies.sqlite",
        profile_path / "cookies.sqlite-wal",
        profile_path / "storage",
        profile_path / "Default" / "cookies.sqlite",
    ]
    logged_in_hint = any(p.exists() for p in cookie_hints)
    camoufox_ok = _camoufox_importable()
    return {
        "engine": "camoufox",
        "camoufox_ok": camoufox_ok,
        "chrome_ok": camoufox_ok,  # back-compat for UI that checks chrome_ok
        "user_data_dir": cfg.user_data_dir,
        "profile_ok": profile_ok,
        "logged_in_hint": logged_in_hint,
        "ready": camoufox_ok,
        "legacy_chrome_profile_exists": _LEGACY_CHROME_PROFILE.exists(),
        "hint": (
            "OK — try live map"
            if camoufox_ok and logged_in_hint
            else (
                "Session cold — ops: career-fit linkedin-burner-login (or paste secrets in chat for the agent)"
                if camoufox_ok
                else "Install: pip install -e '.[linkedin]' && python -m camoufox fetch"
            )
        ),
    }


def _camoufox_importable() -> bool:
    try:
        import camoufox  # noqa: F401

        return True
    except ImportError:
        return False
