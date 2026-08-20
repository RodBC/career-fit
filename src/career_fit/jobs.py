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


_STRUCTURED_URL_SOURCES = {
    "public_job_url",
    "linkedin_camoufox_guest",
    "linkedin_camoufox",
}

_SECTION_HEADINGS = {
    "about the job",
    "about the role",
    "job description",
    "responsibilities",
    "requirements",
    "qualifications",
    "sobre a vaga",
    "descrição da vaga",
    "responsabilidades",
    "requisitos",
}


def is_complete_job(parsed: ParsedJob, *, min_description_chars: int = 80) -> bool:
    """A mapped URL is usable only when its core facts were actually observed."""
    title = parsed.title.strip()
    company = parsed.company.strip()
    description = parsed.description.strip()
    return bool(
        title
        and title != "Untitled role"
        and company
        and len(description) >= min_description_chars
    )


def parse_job_text(raw: str, source: str = "paste") -> ParsedJob:
    """
    Normalize pasted JD text from LinkedIn / Gupy / inHire / anywhere.
    Heuristic only — good enough for tailor; user can edit fields in UI.
    """
    text = raw.strip()
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    title = ""
    company = ""

    # Structured URL fetches commonly return: title\n\ncompany\n\ndescription.
    if source in _STRUCTURED_URL_SOURCES and len(lines) >= 2:
        if len(lines[0]) < 120 and not lines[0].lower().startswith("http"):
            title = lines[0]
        company_candidate = lines[1]
        candidate_low = company_candidate.lower().rstrip(":")
        if (
            1 < len(company_candidate) < 80
            and len(company_candidate.split()) <= 10
            and not candidate_low.startswith("http")
            and candidate_low not in _SECTION_HEADINGS
        ):
            company = company_candidate

    # Common patterns
    # "Role at Company" on first lines
    for ln in lines[:8]:
        if title and company:
            break
        m = re.match(r"^(.{3,90}?)\s+(?:at|@|na)\s+(.{2,60})$", ln, re.I)
        if m and not title:
            title = m.group(1).strip()
            company = company or m.group(2).strip(" -|·")
            break

    for ln in lines[:12]:
        if title and company:
            break
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
