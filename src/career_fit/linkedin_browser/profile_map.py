"""Candidate LinkedIn profile URL → observed snapshot → profile draft."""

from __future__ import annotations

import os
import re
from typing import Any

from ..intake import build_profile_from_intake
from .config import SessionConfig, load_session_config
from .errors import BrowserJobError as SeleniumJobError
from .mock import mock_profile_snapshot

_PROFILE_URL_RE = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/([A-Za-z0-9\-_%]+)/?",
    re.I,
)


def normalize_profile_url(raw: str) -> str:
    text = (raw or "").strip()
    if not text:
        return ""
    m = _PROFILE_URL_RE.search(text)
    if m:
        slug = m.group(1).strip("/")
        return f"https://www.linkedin.com/in/{slug}"
    # bare slug
    if re.fullmatch(r"[A-Za-z0-9\-_%]{3,}", text) and " " not in text:
        return f"https://www.linkedin.com/in/{text}"
    return ""


def _use_mock(explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    return os.environ.get("CAREER_FIT_SELENIUM_MOCK", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def stub_profile_snapshot(url: str = "") -> dict:
    """Name + LinkedIn URL only — never invent employer/headline (live-fail path)."""
    profile_url = normalize_profile_url(url) or (url or "").strip()
    slug = profile_url.rstrip("/").split("/")[-1] if profile_url else "you"
    raw_parts = [p for p in slug.replace("_", "-").split("-") if p]
    # Drop trailing LinkedIn id fragments like 536b85209
    parts = [
        p
        for p in raw_parts
        if not re.fullmatch(r"[0-9a-f]{6,}", p, re.I) and not re.fullmatch(r"\d{5,}", p)
    ]
    name = " ".join(p.capitalize() for p in parts) if parts else "Candidate"
    return {
        "linkedin_url": profile_url or f"https://www.linkedin.com/in/{slug}",
        "name": name,
        "headline": "",
        "location": "",
        "about": "",
        "experience_text": "",
        "stub": True,
    }


def snapshot_to_profile(snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build a tailor-ready profile from observed LinkedIn fields only."""
    name = (snapshot.get("name") or "").strip() or "Candidate"
    headline = (snapshot.get("headline") or "").strip()
    about = (snapshot.get("about") or "").strip()
    location = (snapshot.get("location") or "").strip()
    linkedin = (snapshot.get("linkedin_url") or "").strip()
    experience_text = (snapshot.get("experience_text") or "").strip()

    tutoring: dict[str, Any] = {}
    if about:
        tutoring["positive_differentials"] = [about]
    if headline:
        tutoring["technical_knowledge"] = [headline]

    roles: list[str] = []
    if headline:
        # Light target hint from headline — user can edit later
        roles = [headline.split("·")[0].split("|")[0].strip()[:80]]

    resume_bits = []
    if about:
        resume_bits.append(f"Summary\n{about}")
    if experience_text:
        resume_bits.append(experience_text)
    resume_text = "\n\n".join(resume_bits)

    result = build_profile_from_intake(
        identity={
            "name": name,
            "email": "",
            "city": location,
            "linkedin": linkedin,
            "languages": [],
        },
        career_tutoring=tutoring,
        targets={"roles_wanted": roles, "locales": ["en"], "remote": True},
        resume_text=resume_text,
        base_profile=None,
    )
    # Attach journey metadata for UI (not inventing facts)
    result["_journey"] = {
        "source": "linkedin_profile_map",
        "headline": headline,
        "needs_email": True,
        "light": True,
        "stub": bool(snapshot.get("stub")),
    }
    return result


def map_profile_url(
    url: str,
    session_cfg: SessionConfig | None = None,
    *,
    mock: bool | None = None,
    stub: bool = False,
) -> dict[str, Any]:
    """Return `{snapshot, profile, meta}`. Never invents experience."""
    cfg = session_cfg or load_session_config()
    profile_url = normalize_profile_url(url)
    if not profile_url:
        raise SeleniumJobError(
            "Paste your LinkedIn profile URL (linkedin.com/in/you)",
            status=400,
        )

    if stub:
        snapshot = stub_profile_snapshot(profile_url)
        profile = snapshot_to_profile(snapshot)
        return {
            "snapshot": snapshot,
            "profile": profile,
            "meta": {
                "source": "linkedin_url_stub",
                "url": profile_url,
                "mock": False,
                "stub": True,
            },
        }

    use_mock = _use_mock(mock)
    if use_mock:
        snapshot = mock_profile_snapshot(profile_url)
        profile = snapshot_to_profile(snapshot)
        return {
            "snapshot": snapshot,
            "profile": profile,
            "meta": {
                "source": "linkedin_selenium_mock",
                "url": profile_url,
                "mock": True,
            },
        }

    if not cfg.user_data_dir:
        raise SeleniumJobError(
            "LinkedIn session not configured. Set data/linkedin_session.yaml "
            "or CAREER_FIT_CAMOUFOX_USER_DATA, or try mock. "
            "See docs/LINKEDIN_JOB_SESSION.md",
            status=503,
        )

    try:
        from .fetch import fetch_profile_snapshot
    except ImportError as e:
        raise SeleniumJobError(
            "Camoufox extra not installed. Run: pip install -e '.[linkedin]' "
            "&& python -m camoufox fetch — or use mock.",
            status=503,
        ) from e

    try:
        snapshot = fetch_profile_snapshot(profile_url, cfg)
    except SeleniumJobError:
        raise
    except Exception as e:  # noqa: BLE001 — driver/session failures
        raise SeleniumJobError(
            f"LinkedIn session failed ({e}). Use mock for now, or fix Camoufox profile "
            "(see docs/LINKEDIN_JOB_SESSION.md).",
            status=503,
        ) from e
    if not (snapshot.get("name") or snapshot.get("experience_text") or snapshot.get("about")):
        raise SeleniumJobError(
            "Profile page returned empty fields (login wall or DOM change). "
            "Try mock or paste resume later.",
            status=503,
        )
    snapshot["linkedin_url"] = profile_url
    profile = snapshot_to_profile(snapshot)
    return {
        "snapshot": snapshot,
        "profile": profile,
        "meta": {
            "source": "linkedin_browser",
            "url": profile_url,
            "mock": False,
        },
    }
