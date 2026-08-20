"""Live page fetch via Camoufox (guest-first, then persistent session)."""

from __future__ import annotations

import re
import time
from typing import Any
from urllib.parse import quote_plus

from .browser import launch_guest, launch_persistent, looks_like_login, new_page
from .config import SessionConfig, load_session_config, session_ready_report
from .errors import BrowserJobError
from .intercept import attach_job_intercept, openings_from_intercept

_JOB_VIEW_RE = re.compile(r"linkedin\.com/jobs/view/(\d+)", re.I)

_JOB_SELECTORS = [
    ".jobs-description__content",
    ".jobs-box__html-content",
    "#job-details",
    ".description__text",
    ".show-more-less-html__markup",
    "main",
]

_JOB_TITLE_SELECTORS = [
    ".job-details-jobs-unified-top-card__job-title h1",
    ".job-details-jobs-unified-top-card__job-title",
    ".top-card-layout__title",
    ".topcard__title",
    "h1",
]

_JOB_COMPANY_SELECTORS = [
    ".job-details-jobs-unified-top-card__company-name",
    ".jobs-unified-top-card__company-name",
    ".topcard__org-name-link",
]


def _pause(cfg: SessionConfig) -> None:
    time.sleep(max(0.5, cfg.nav_pause_sec))


def _first_text(page: Any, selectors: list[str], *, max_len: int) -> str:
    for sel in selectors:
        try:
            loc = page.locator(sel)
            if not loc.count():
                continue
            text = (loc.nth(0).inner_text(timeout=2000) or "").strip()
            if text:
                return text.splitlines()[0][:max_len].strip()
        except Exception:  # noqa: BLE001
            continue
    return ""


def _page_job_text(page: Any) -> str:
    title = _first_text(page, _JOB_TITLE_SELECTORS, max_len=120)
    company = _first_text(page, _JOB_COMPANY_SELECTORS, max_len=80)
    chunks: list[str] = []
    for sel in _JOB_SELECTORS:
        try:
            loc = page.locator(sel)
            n = min(loc.count(), 2)
            for i in range(n):
                t = (loc.nth(i).inner_text(timeout=2000) or "").strip()
                if len(t) > 80:
                    chunks.append(t)
        except Exception:  # noqa: BLE001
            continue
    if chunks:
        body = "\n\n".join(chunks)
    else:
        try:
            body = (page.locator("body").inner_text(timeout=3000) or "").strip()
        except Exception:  # noqa: BLE001
            body = ""

    # Preserve observed title/company ahead of the JD so the shared parser does
    # not have to guess them from a description-only selector.
    if title and company:
        return f"{title}\n\n{company}\n\n{body}".strip()
    if title:
        return f"{title}\n\n{body}".strip()
    return body


def _normalize_job_view_url(href: str) -> str:
    m = _JOB_VIEW_RE.search(href or "")
    if not m:
        return ""
    return f"https://www.linkedin.com/jobs/view/{m.group(1)}"


def fetch_job_page_text(
    url: str,
    cfg: SessionConfig | None = None,
    *,
    guest: bool = False,
) -> str:
    """Open job URL; return visible text. Guest or persistent profile."""
    cfg = cfg or load_session_config()
    launcher = launch_guest if guest else launch_persistent
    kwargs = {} if guest else {"cfg": cfg}
    with launcher(**kwargs) as browser:
        page = new_page(browser)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        _pause(cfg)
        if looks_like_login(page):
            raise BrowserJobError(
                "LinkedIn login wall — run: career-fit linkedin-session "
                "(or career-fit linkedin-burner-login for ops burner)",
                status=503,
            )
        return _page_job_text(page)


def fetch_profile_snapshot(url: str, cfg: SessionConfig) -> dict[str, Any]:
    """Open /in/… page; return observed name/headline/about/experience text."""
    with launch_persistent(cfg) as context:
        page = new_page(context)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        _pause(cfg)
        if looks_like_login(page):
            raise BrowserJobError(
                "LinkedIn login wall — run: career-fit linkedin-session",
                status=503,
            )
        body = (page.locator("body").inner_text(timeout=5000) or "").strip()
        name = ""
        headline = ""
        location = ""
        about = ""
        try:
            h1 = page.locator("h1")
            if h1.count():
                name = (h1.first.inner_text(timeout=2000) or "").strip()
        except Exception:  # noqa: BLE001
            pass
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        if not name and lines:
            name = lines[0][:80]
        for i, ln in enumerate(lines[:12]):
            if not headline and i >= 1 and 8 < len(ln) < 120 and "contact" not in ln.lower():
                headline = ln
                break
        for ln in lines[:20]:
            low = ln.lower()
            if any(
                x in low
                for x in (
                    "brazil",
                    "remote",
                    "são paulo",
                    "sao paulo",
                    "lisbon",
                    "portugal",
                )
            ):
                location = ln[:80]
                break
        about_idx = next(
            (i for i, ln in enumerate(lines) if ln.lower() in {"about", "sobre"}),
            None,
        )
        if about_idx is not None:
            about = " ".join(lines[about_idx + 1 : about_idx + 6])[:600]
        exp_idx = next(
            (
                i
                for i, ln in enumerate(lines)
                if ln.lower() in {"experience", "experiência", "experiencia"}
            ),
            None,
        )
        experience_text = ""
        if exp_idx is not None:
            chunk = lines[exp_idx : exp_idx + 40]
            experience_text = "Experience\n" + "\n".join(chunk[1:])
        elif lines:
            experience_text = "Experience\n" + "\n".join(lines[:50])
        return {
            "name": name,
            "headline": headline,
            "location": location,
            "about": about,
            "experience_text": experience_text,
            "raw_chars": len(body),
        }


def _dom_search_candidates(page: Any) -> list[dict[str, str]]:
    card_sels = [
        "div.job-card-container",
        "li.jobs-search-results__list-item",
        "div.base-card",
        "div.base-search-card",
        "li.scaffold-layout__list-item",
    ]
    cards = []
    for sel in card_sels:
        try:
            loc = page.locator(sel)
            n = loc.count()
            if n >= 3:
                cards = [loc.nth(i) for i in range(min(n, 40))]
                break
            if n > len(cards):
                cards = [loc.nth(i) for i in range(n)]
        except Exception:  # noqa: BLE001
            continue

    seen_ids: set[str] = set()
    candidates: list[dict[str, str]] = []
    for card in cards:
        try:
            link = ""
            title = ""
            anchors = card.locator("a[href*='/jobs/view/']")
            for i in range(min(anchors.count(), 5)):
                a = anchors.nth(i)
                href = a.get_attribute("href") or ""
                norm = _normalize_job_view_url(href)
                if not norm:
                    continue
                link = norm
                t = (a.inner_text(timeout=1000) or "").strip()
                if not t:
                    t = (a.get_attribute("aria-label") or "").strip()
                if t and len(t) > 2:
                    title = t.split("\n")[0][:120]
                    break
            if not link:
                continue
            jid_m = _JOB_VIEW_RE.search(link)
            if not jid_m or jid_m.group(1) in seen_ids:
                continue
            company = ""
            for sel in (
                ".job-card-container__primary-description",
                ".artdeco-entity-lockup__subtitle",
                ".base-search-card__subtitle",
                "h4",
                ".job-card-list__company-name",
            ):
                try:
                    els = card.locator(sel)
                    if els.count():
                        c = (els.first.inner_text(timeout=800) or "").strip().split("\n")[0][
                            :100
                        ]
                        if c and c.lower() != title.lower() and len(c) > 1:
                            company = c
                            break
                except Exception:  # noqa: BLE001
                    continue
            if not title or not company or not link:
                continue
            seen_ids.add(jid_m.group(1))
            candidates.append(
                {
                    "id": jid_m.group(1),
                    "title": title,
                    "company": company,
                    "linkedin_url": link,
                }
            )
        except Exception:  # noqa: BLE001
            continue
    return candidates


def _verify_and_build_openings(
    page: Any,
    candidates: list[dict[str, str]],
    *,
    limit: int,
    verify_jd: bool,
    cfg: SessionConfig,
) -> list[dict[str, Any]]:
    openings: list[dict[str, Any]] = []
    for cand in candidates:
        if len(openings) >= limit:
            break
        description = ""
        if verify_jd:
            try:
                page.goto(cand["linkedin_url"], wait_until="domcontentloaded", timeout=60000)
                _pause(cfg)
                if looks_like_login(page):
                    continue
                description = _page_job_text(page)
                if len(description) < 80:
                    continue
            except Exception:  # noqa: BLE001
                continue
        blurb = " ".join((description or f"{cand['title']} at {cand['company']}").split())[
            :180
        ]
        openings.append(
            {
                "id": f"li-{cand['id']}",
                "title": cand["title"],
                "company": cand["company"],
                "blurb": blurb + ("…" if len(blurb) >= 180 else ""),
                "description": description
                or f"{cand['title']} at {cand['company']}\n{cand['linkedin_url']}",
                "linkedin_url": cand["linkedin_url"],
                "sample": False,
            }
        )
    return openings


def _search_with_browser(
    browser: Any,
    keywords: str,
    *,
    location: str,
    limit: int,
    verify_jd: bool,
    cfg: SessionConfig,
) -> list[dict[str, Any]]:
    search = f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keywords)}"
    if location.strip():
        search += f"&location={quote_plus(location.strip())}"

    page = new_page(browser)
    captured = attach_job_intercept(page)
    page.goto(search, wait_until="domcontentloaded", timeout=60000)
    _pause(cfg)
    if looks_like_login(page):
        raise BrowserJobError(
            "LinkedIn login wall — run: career-fit linkedin-session "
            "(or career-fit linkedin-burner-login)",
            status=503,
        )

    for _ in range(3):
        try:
            page.evaluate(
                """() => {
                  const el = document.querySelector(
                    '.jobs-search-results-list,div.scaffold-finite-scroll__content,ul'
                  );
                  if (el) el.scrollTop = el.scrollHeight;
                  window.scrollBy(0, 800);
                }"""
            )
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.6)

    candidates = openings_from_intercept(captured, limit=max(limit * 2, 12))
    if len(candidates) < 3:
        for c in _dom_search_candidates(page):
            if c["id"] not in {x["id"] for x in candidates}:
                candidates.append(c)

    return _verify_and_build_openings(
        page, candidates, limit=limit, verify_jd=verify_jd, cfg=cfg
    )


def fetch_job_search_openings(
    keywords: str,
    *,
    location: str = "",
    limit: int = 8,
    cfg: SessionConfig | None = None,
    verify_jd: bool = True,
) -> list[dict[str, Any]]:
    """Scrape LinkedIn Jobs search — guest Camoufox first, then warm profile.

    Completeness rule: skip cards missing title, company, or valid view URL.
    Never invent employers.
    """
    cfg = cfg or load_session_config()
    q = (keywords or "").strip()
    if not q:
        raise BrowserJobError("keywords required for job search", status=400)

    # L3: guest Camoufox (no account)
    try:
        with launch_guest(headless=cfg.headless, humanize=cfg.humanize) as browser:
            openings = _search_with_browser(
                browser,
                q,
                location=location,
                limit=limit,
                verify_jd=verify_jd,
                cfg=cfg,
            )
            if openings:
                return openings
    except BrowserJobError:
        # Fall through to persistent session
        pass
    except Exception:  # noqa: BLE001
        pass

    # L4: warm persistent profile
    with launch_persistent(cfg) as context:
        return _search_with_browser(
            context,
            q,
            location=location,
            limit=limit,
            verify_jd=verify_jd,
            cfg=cfg,
        )


def run_linkedin_login_session(
    cfg: SessionConfig | None = None,
    *,
    wait_sec: float = 300,
) -> dict[str, Any]:
    """Open Camoufox on LinkedIn login; poll until feed or timeout (manual login)."""
    cfg = cfg or load_session_config()
    before = session_ready_report(cfg)
    if not before.get("camoufox_ok"):
        raise BrowserJobError(
            "Camoufox missing. Run: pip install -e '.[linkedin]' && python -m camoufox fetch",
            status=503,
        )
    logged_in = False
    # Force headed for manual login
    with launch_persistent(cfg, headless=False) as context:
        page = new_page(context)
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        deadline = time.time() + max(30.0, wait_sec)
        while time.time() < deadline:
            url = (page.url or "").lower()
            if "/feed" in url or "/in/" in url or "linkedin.com/jobs" in url:
                if "/login" not in url and "/checkpoint" not in url:
                    logged_in = True
                    break
            time.sleep(2)
    after = session_ready_report(cfg)
    return {
        "ok": True,
        "logged_in": logged_in,
        "before": before,
        "after": after,
        "hint": (
            "Looks logged in — Retry live on Start."
            if logged_in or after.get("logged_in_hint")
            else "Timed out or still on login — finish login in Camoufox, then Check session."
        ),
    }
