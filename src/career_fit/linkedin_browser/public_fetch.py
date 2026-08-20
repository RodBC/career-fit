"""Fetch a public job posting page without LinkedIn login.

Used for one-shot job URLs (ATS / careers / guest LinkedIn). Never invents text.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser

_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "noscript", "svg"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript", "svg") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        t = data.strip()
        if t:
            self.parts.append(t)


def _strip_html(chunk: str) -> str:
    text = re.sub(r"<[^>]+>", " ", chunk)
    return re.sub(r"\s+", " ", text).strip()


def _json_ld_job_text(html: str) -> str:
    """Pull JobPosting JSON-LD when present (Greenhouse, Lever, many careers pages)."""
    chunks: list[str] = []
    for m in re.finditer(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.I | re.S,
    ):
        raw = m.group(1).strip()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if not isinstance(item, dict):
                continue
            if "@graph" in item and isinstance(item["@graph"], list):
                items.extend(item["@graph"])
                continue
            types = item.get("@type")
            type_l = (
                [types]
                if isinstance(types, str)
                else list(types or [])
                if isinstance(types, list)
                else []
            )
            if "JobPosting" not in type_l:
                continue
            title = str(item.get("title") or "").strip()
            org = item.get("hiringOrganization") or {}
            company = ""
            if isinstance(org, dict):
                company = str(org.get("name") or "").strip()
            desc = _strip_html(str(item.get("description") or ""))
            block = "\n".join(x for x in (title, company, desc) if x)
            if len(block) > 40:
                chunks.append(block)
    return "\n\n".join(chunks)


def _linkedin_guest_job_text(html: str) -> str:
    """Structured text from LinkedIn guest /jobs/view pages (no login)."""
    title = ""
    for pat in (
        r'class="[^"]*top-card-layout__title[^"]*"[^>]*>([^<]+)',
        r'class="[^"]*topcard__title[^"]*"[^>]*>([^<]+)',
    ):
        m = re.search(pat, html, re.I)
        if m:
            title = m.group(1).strip()
            if title:
                break

    company = ""
    m = re.search(
        r'class="[^"]*topcard__org-name-link[^"]*"[^>]*>([^<]+)',
        html,
        re.I,
    )
    if m:
        company = m.group(1).strip()
    if not company:
        m = re.search(r'property="og:title" content="([^"]+)"', html, re.I)
        if m:
            og = re.sub(r"\s*\|\s*LinkedIn\s*$", "", m.group(1)).strip()
            hm = re.match(r"^(.+?)\s+hiring\s+(.+?)(?:\s+in\s+.+)?$", og, re.I)
            if hm:
                company = hm.group(1).strip()
                if not title:
                    title = hm.group(2).strip()

    desc = ""
    m = re.search(
        r'class="[^"]*show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>',
        html,
        re.I | re.S,
    )
    if m:
        desc = _strip_html(m.group(1))
    if len(desc) < 40:
        m = re.search(r'property="og:description" content="([^"]+)"', html, re.I)
        if m:
            desc = m.group(1).strip()

    if not title and not company and len(desc) < 40:
        return ""
    # Line 1 title, line 2 company — parse_job_text picks these up
    parts = [p for p in (title, company, desc) if p]
    return "\n\n".join(parts)


def fetch_public_job_text(url: str) -> str:
    """HTTP GET job URL → visible / JSON-LD text. Empty string if unusable."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": _UA,
            "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read()
            charset = "utf-8"
            ctype = resp.headers.get_content_charset()
            if ctype:
                charset = ctype
            html = raw.decode(charset, errors="replace")
    except (urllib.error.URLError, TimeoutError, ValueError):
        return ""

    if "linkedin.com" in url.lower():
        li = _linkedin_guest_job_text(html)
        if len(li) >= 40:
            return li

    ld = _json_ld_job_text(html)
    if len(ld) >= 80:
        return ld

    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:  # noqa: BLE001
        return ld
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    low = text.lower()
    if "sign in" in low and "linkedin" in low and len(text) < 400:
        return ""
    if len(text) < 80:
        return ld or ""
    return text[:50000]
