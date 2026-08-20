from __future__ import annotations

from types import SimpleNamespace

import pytest

from career_fit.jobs import is_complete_job, parse_job_text
from career_fit.linkedin_browser import BrowserJobError, map_job_url
from career_fit.linkedin_browser import fetch as browser_fetch
from career_fit.linkedin_browser import public_fetch


LONG_JD = (
    "Build and operate production APIs with Python and FastAPI. "
    "Partner with product and platform teams on reliable distributed systems."
)


def test_structured_camoufox_text_keeps_company() -> None:
    parsed = parse_job_text(
        f"Senior Backend Engineer\nAcme Corp\n{LONG_JD}",
        source="linkedin_camoufox_guest",
    )

    assert parsed.title == "Senior Backend Engineer"
    assert parsed.company == "Acme Corp"
    assert is_complete_job(parsed)


def test_section_heading_is_not_mistaken_for_company() -> None:
    parsed = parse_job_text(
        f"Senior Backend Engineer\nAbout the job\n{LONG_JD}",
        source="public_job_url",
    )

    assert parsed.company == ""
    assert not is_complete_job(parsed)


def test_map_job_falls_through_incomplete_public_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        public_fetch,
        "fetch_public_job_text",
        lambda _url: f"Senior Backend Engineer\n{LONG_JD}",
    )
    monkeypatch.setattr(
        browser_fetch,
        "fetch_job_page_text",
        lambda _url, _cfg, guest=False: (
            f"Senior Backend Engineer\nAcme Corp\n{LONG_JD}"
        ),
    )

    result = map_job_url(
        "https://www.linkedin.com/jobs/view/123",
        session_cfg=SimpleNamespace(user_data_dir=None),
        mock=False,
    )

    assert result["meta"]["source"] == "linkedin_camoufox_guest"
    assert result["parsed"].company == "Acme Corp"


def test_map_job_rejects_incomplete_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    incomplete = f"Senior Backend Engineer\nAbout the job\n{LONG_JD}"
    monkeypatch.setattr(public_fetch, "fetch_public_job_text", lambda _url: incomplete)
    monkeypatch.setattr(
        browser_fetch,
        "fetch_job_page_text",
        lambda _url, _cfg, guest=False: incomplete,
    )

    with pytest.raises(BrowserJobError) as caught:
        map_job_url(
            "https://www.linkedin.com/jobs/view/123",
            session_cfg=SimpleNamespace(user_data_dir=None),
            mock=False,
        )

    assert caught.value.status == 422
    assert "could not verify" in str(caught.value)
