from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ParsedJob:
    title: str
    company: str
    description: str
    source: str
    locale_hint: str | None = None


def parse_job_text(raw: str, source: str = "paste") -> ParsedJob:
    """
    Normalize pasted JD text from LinkedIn / Gupy / inHire / anywhere.
    Heuristic only — good enough for tailor; user can edit fields in UI.
    """
    text = raw.strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = ""
    company = ""

    # Common patterns
    # "Role at Company" on first lines
    for ln in lines[:8]:
        m = re.match(r"^(.{3,90}?)\s+(?:at|@|na)\s+(.{2,60})$", ln, re.I)
        if m and not title:
            title = m.group(1).strip()
            company = company or m.group(2).strip(" -|·")
            break

    for ln in lines[:12]:
        low = ln.lower()
        if not title and len(ln) < 120 and not low.startswith("http"):
            if any(
                k in low
                for k in (
                    "engineer",
                    "developer",
                    "desenvolvedor",
                    "analista",
                    "recruiter",
                    "manager",
                    "especialista",
                    "gtm",
                    "frontend",
                    "front-end",
                    "backend",
                    "full",
                )
            ):
                title = ln
                continue
        if not company:
            m = re.search(r"(?:at|@|na|empresa[:\s]+)\s*(.+)$", ln, re.I)
            if m and len(m.group(1)) < 80:
                company = m.group(1).strip(" -|·")
                continue
            if low.startswith("company:") or low.startswith("empresa:"):
                company = ln.split(":", 1)[-1].strip()

    if not title and lines:
        title = lines[0][:120]
    if not company:
        for ln in lines[:15]:
            if ln.lower().startswith("about the company") or "sobre a empresa" in ln.lower():
                break
            # LinkedIn often has Company on its own line near top after title
        # fallback empty — UI asks user

    locale_hint = None
    sample = text[:800].lower()
    pt_hits = sum(1 for w in ("desenvolvedor", "experiência", "requisitos", "empresa", "vaga") if w in sample)
    en_hits = sum(1 for w in ("requirements", "responsibilities", "experience", "about the job") if w in sample)
    if pt_hits > en_hits:
        locale_hint = "pt"
    elif en_hits > pt_hits:
        locale_hint = "en"

    return ParsedJob(
        title=title or "Untitled role",
        company=company,
        description=text,
        source=source,
        locale_hint=locale_hint,
    )
