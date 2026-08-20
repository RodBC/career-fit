"""Compatibility shim — prefer `career_fit.linkedin_browser`.

Selenium + Chrome-for-Testing retired; Camoufox is the engine.
"""

from __future__ import annotations

from ..linkedin_browser import (  # noqa: F401
    BrowserJobError,
    SeleniumJobError,
    SessionConfig,
    bootstrap_burner_session,
    load_session_config,
    map_job_url,
    map_profile_url,
    normalize_job_url,
    normalize_profile_url,
    parsed_as_dict,
    run_linkedin_login_session,
    search_job_openings,
    session_ready_report,
    snapshot_to_profile,
)
from ..linkedin_browser import mock as mock  # noqa: F401
from ..linkedin_browser.public_fetch import fetch_public_job_text  # noqa: F401

__all__ = [
    "BrowserJobError",
    "SeleniumJobError",
    "SessionConfig",
    "bootstrap_burner_session",
    "fetch_public_job_text",
    "load_session_config",
    "map_job_url",
    "map_profile_url",
    "normalize_job_url",
    "normalize_profile_url",
    "parsed_as_dict",
    "run_linkedin_login_session",
    "search_job_openings",
    "session_ready_report",
    "snapshot_to_profile",
]
