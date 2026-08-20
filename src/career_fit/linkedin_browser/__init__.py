"""LinkedIn job URL → JD text via Camoufox (Warm Bridge yellow pattern).

Layers: public HTTP → guest Camoufox → warm profile → ops burner OTP.
Never invent JD text. Never accept end-user LinkedIn passwords in the API.
"""

from __future__ import annotations

import os
import re
from typing import Any

from ..jobs import ParsedJob, is_complete_job, parse_job_text
from .config import SessionConfig, load_session_config, session_ready_report
from .errors import BrowserJobError, SeleniumJobError
from .mock import mock_job_text
from .profile_map import map_profile_url, normalize_profile_url, snapshot_to_profile

__all__ = [
    "BrowserJobError",
    "SeleniumJobError",
    "SessionConfig",
    "load_session_config",
    "session_ready_report",
    "map_job_url",
    "map_profile_url",
    "normalize_job_url",
    "normalize_profile_url",
    "parsed_as_dict",
    "snapshot_to_profile",
    "search_job_openings",
    "run_linkedin_login_session",
    "bootstrap_burner_session",
]


def run_linkedin_login_session(
    session_cfg: SessionConfig | None = None,
    *,
    wait_sec: float = 300,
) -> dict[str, Any]:
    from .fetch import run_linkedin_login_session as _run

    return _run(session_cfg, wait_sec=wait_sec)


def bootstrap_burner_session(
    *,
    headless: bool = False,
    session_cfg: SessionConfig | None = None,
) -> dict[str, Any]:
    from .burner_login import bootstrap_burner_session as _run

    return _run(headless=headless, cfg=session_cfg)

_JOB_URL_RE = re.compile(
    r"https?://(?:www\.)?linkedin\.com/jobs/(?:view|collections)/[^\s]+",
    re.I,
)
_VIEW_ID_RE = re.compile(r"linkedin\.com/jobs/view/(\d+)", re.I)
_CURRENT_JOB_ID_RE = re.compile(r"[?&]currentJobId=(\d+)", re.I)


def normalize_job_url(raw: str) -> str:
    """Accept LinkedIn jobs/view, search?currentJobId=, or any https careers URL."""
    text = (raw or "").strip()
    if not text:
        return ""
    m = _VIEW_ID_RE.search(text)
    if m:
        return f"https://www.linkedin.com/jobs/view/{m.group(1)}"
    m = _CURRENT_JOB_ID_RE.search(text)
    if m:
        return f"https://www.linkedin.com/jobs/view/{m.group(1)}"
    m = _JOB_URL_RE.search(text)
    if m:
        return m.group(0).split("?")[0]
    if text.startswith("http://") or text.startswith("https://"):
        return text.split()[0]
    return ""


def _use_mock(explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    return os.environ.get("CAREER_FIT_SELENIUM_MOCK", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ) or os.environ.get("CAREER_FIT_BROWSER_MOCK", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def map_job_url(
    url: str,
    session_cfg: SessionConfig | None = None,
    *,
    mock: bool | None = None,
) -> dict[str, Any]:
    """Return `{parsed, meta}` from a job URL (public fetch first, Camoufox if needed).

    Never fabricates a posting. Empty/fail → BrowserJobError.
    """
    cfg = session_cfg or load_session_config()
    job_url = normalize_job_url(url)
    if not job_url:
        raise BrowserJobError(
            "Paste a job URL (LinkedIn /jobs/view/… or company careers link)",
            status=400,
        )

    use_mock = _use_mock(mock)
    if use_mock:
        raw = mock_job_text(job_url)
        parsed = parse_job_text(raw, source="linkedin_browser_mock")
        return {
            "parsed": parsed,
            "meta": {
                "source": "linkedin_browser_mock",
                "url": job_url,
                "mock": True,
            },
        }

    found_incomplete = False

    # L1: Public HTTP — no LinkedIn login
    try:
        from .public_fetch import fetch_public_job_text

        public_raw = fetch_public_job_text(job_url)
    except Exception:  # noqa: BLE001
        public_raw = ""
    if public_raw and len(public_raw.strip()) >= 80:
        parsed = parse_job_text(public_raw, source="public_job_url")
        if is_complete_job(parsed):
            return {
                "parsed": parsed,
                "meta": {
                    "source": "public_job_url",
                    "url": job_url,
                    "mock": False,
                },
            }
        found_incomplete = True

    # L2: Guest Camoufox
    try:
        from .fetch import fetch_job_page_text

        raw = fetch_job_page_text(job_url, cfg, guest=True)
        if raw and len(raw.strip()) >= 40:
            parsed = parse_job_text(raw, source="linkedin_camoufox_guest")
            if is_complete_job(parsed):
                return {
                    "parsed": parsed,
                    "meta": {
                        "source": "linkedin_camoufox_guest",
                        "url": job_url,
                        "mock": False,
                    },
                }
            found_incomplete = True
    except BrowserJobError:
        pass
    except Exception:  # noqa: BLE001
        pass

    # L4: Warm persistent profile
    if cfg.user_data_dir:
        try:
            from .fetch import fetch_job_page_text

            raw = fetch_job_page_text(job_url, cfg, guest=False)
            if raw and len(raw.strip()) >= 40:
                parsed = parse_job_text(raw, source="linkedin_camoufox")
                if is_complete_job(parsed):
                    return {
                        "parsed": parsed,
                        "meta": {
                            "source": "linkedin_camoufox",
                            "url": job_url,
                            "mock": False,
                        },
                    }
                found_incomplete = True
        except BrowserJobError:
            pass
        except Exception:  # noqa: BLE001
            pass

    if found_incomplete:
        raise BrowserJobError(
            "The page was reachable, but Career Fit could not verify the title, "
            "company, and full job description. Try a public careers / Greenhouse / "
            "Lever link, or a publicly viewable LinkedIn jobs/view URL.",
            status=422,
        )

    raise BrowserJobError(
        "Could not read that job URL (login wall or empty page). "
        "Use a public careers / Greenhouse / Lever link, or a LinkedIn "
        "jobs/view URL that is publicly viewable. Ops: career-fit linkedin-burner-login",
        status=503,
    )


def parsed_as_dict(parsed: ParsedJob) -> dict[str, Any]:
    return {
        "title": parsed.title,
        "company": parsed.company,
        "description": parsed.description,
        "source": parsed.source,
        "locale_hint": parsed.locale_hint,
    }


def search_job_openings(
    keywords: str,
    *,
    location: str = "",
    limit: int = 8,
    mock: bool | None = None,
) -> dict[str, Any]:
    """Live LinkedIn job search → complete /jobs/view cards only."""
    if mock or os.environ.get("CAREER_FIT_SELENIUM_MOCK", "").strip().lower() in (
        "1",
        "true",
        "yes",
    ):
        raise BrowserJobError(
            "Live job search required — mock openings are disabled for the journey. "
            "Paste a real LinkedIn jobs/view URL instead.",
            status=400,
        )
    from .fetch import fetch_job_search_openings

    openings = fetch_job_search_openings(
        keywords,
        location=location,
        limit=limit,
    )
    return {
        "openings": openings,
        "meta": {
            "source": "linkedin_jobs_search",
            "keywords": keywords,
            "mock": False,
            "count": len(openings),
            "engine": "camoufox",
        },
    }
