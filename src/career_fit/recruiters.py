from __future__ import annotations

import csv
import io
import re
from dataclasses import asdict, dataclass, field


RECRUITER_TITLE_HINTS = (
    "recruiter",
    "talent acquisition",
    "talent partner",
    "people partner",
    "hiring manager",
    "head of talent",
    "technical recruiter",
    "sourcer",
    "hr business partner",
    "people operations",
    "staffing",
)

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(\+?\d[\d\s().-]{7,}\d)")


@dataclass
class Contact:
    name: str
    title: str = ""
    company: str = ""
    linkedin_url: str = ""
    email: str = ""
    phone: str = ""
    about: str = ""
    source: str = "paste"
    score: float = 0.0
    rationale: str = ""
    draft_message: str = ""


def score_title(title: str) -> tuple[float, str]:
    t = title.lower()
    for hint in RECRUITER_TITLE_HINTS:
        if hint in t:
            # Prefer explicit recruiter / TA over generic HR
            boost = 1.0 if "recruit" in hint or "talent" in hint or "hiring manager" in hint else 0.7
            return boost, f"title matched “{hint}”"
    if any(x in t for x in ("engineer", "developer", "designer")):
        return 0.15, "peer role — warm intro possible, not primary recruiter"
    return 0.35, "unknown title — keep if company-matched"


def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text or "")
    return m.group(0) if m else ""


def extract_phone(text: str) -> str:
    m = PHONE_RE.search(text or "")
    return m.group(0).strip() if m else ""


def parse_paste_block(block: str, company: str = "") -> Contact:
    """
    Accept free-form pasted LinkedIn-ish text.
    First non-empty line ≈ name; line with | or · often has title; rest = about.
    """
    lines = [ln.strip() for ln in block.strip().splitlines() if ln.strip()]
    name = lines[0] if lines else "Unknown"
    title = ""
    about_parts: list[str] = []
    linkedin_url = ""

    for ln in lines[1:]:
        low = ln.lower()
        if "linkedin.com/in/" in low:
            linkedin_url = ln if ln.startswith("http") else f"https://{ln}"
            continue
        if not title and (any(h in low for h in RECRUITER_TITLE_HINTS) or " at " in low or " · " in ln or " | " in ln):
            title = ln.replace("·", "|").split("|")[0].strip()
            continue
        about_parts.append(ln)

    about = "\n".join(about_parts)
    blob = "\n".join(lines)
    email = extract_email(blob)
    phone = extract_phone(blob)
    score, rationale = score_title(title or about[:80])
    return Contact(
        name=name,
        title=title,
        company=company,
        linkedin_url=linkedin_url,
        email=email,
        phone=phone,
        about=about,
        source="paste",
        score=score,
        rationale=rationale,
    )


def parse_contacts_text(text: str, company: str = "") -> list[Contact]:
    """Split on blank lines into contact cards."""
    chunks = re.split(r"\n\s*\n", text.strip())
    contacts = [parse_paste_block(c, company=company) for c in chunks if c.strip()]
    contacts.sort(key=lambda c: c.score, reverse=True)
    return contacts


def parse_contacts_csv(content: str, company: str = "") -> list[Contact]:
    reader = csv.DictReader(io.StringIO(content))
    contacts: list[Contact] = []
    for row in reader:
        # flexible headers
        def g(*keys: str) -> str:
            for k in keys:
                for rk, rv in row.items():
                    if rk and rk.strip().lower() == k:
                        return (rv or "").strip()
            return ""

        name = g("name", "full name", "nome")
        title = g("title", "headline", "cargo")
        about = g("about", "info", "summary", "sobre")
        email = g("email", "e-mail") or extract_email(about)
        url = g("linkedin", "linkedin_url", "url", "profile")
        score, rationale = score_title(title)
        contacts.append(
            Contact(
                name=name or "Unknown",
                title=title,
                company=company or g("company", "empresa"),
                linkedin_url=url,
                email=email,
                about=about,
                source="csv",
                score=score,
                rationale=rationale,
            )
        )
    contacts.sort(key=lambda c: c.score, reverse=True)
    return contacts


def draft_recruiter_message(
    *,
    candidate_name: str,
    contact: Contact,
    job_title: str,
    company: str,
    angle_summary: str,
    proof_line: str,
    locale: str = "en",
) -> str:
    channel = "email" if contact.email else "dm"
    first = contact.name.split()[0] if contact.name else ""

    if locale == "pt":
        greeting = f"Olá, {first}!" if first else "Olá!"
        channel_note = "Segue um resumo rápido" if channel == "email" else "Vi seu perfil e queria ser direto"
        return (
            f"{greeting}\n\n"
            f"{channel_note}: me candidatei à vaga de {job_title} na {company}.\n\n"
            f"{angle_summary}\n\n"
            f"{proof_line}\n\n"
            f"Se fizer sentido, toparia uma conversa rápida.\n\n"
            f"Abraço,\n{candidate_name}\n"
        )

    greeting = f"Hi {first}," if first else "Hi,"
    channel_note = "Quick note" if channel == "email" else "Saw your profile — keeping this short"
    return (
        f"{greeting}\n\n"
        f"{channel_note}: I applied for the {job_title} role at {company}.\n\n"
        f"{angle_summary}\n\n"
        f"{proof_line}\n\n"
        f"Happy to chat if useful.\n\n"
        f"Best,\n{candidate_name}\n"
    )


def enrich_with_messages(
    contacts: list[Contact],
    *,
    candidate_name: str,
    job_title: str,
    company: str,
    angle_summary: str,
    proof_line: str,
    locale: str = "en",
) -> list[Contact]:
    out: list[Contact] = []
    for c in contacts:
        msg = draft_recruiter_message(
            candidate_name=candidate_name,
            contact=c,
            job_title=job_title,
            company=company,
            angle_summary=angle_summary,
            proof_line=proof_line,
            locale=locale,
        )
        enriched = Contact(**{**asdict(c), "draft_message": msg})
        out.append(enriched)
    return out


def contacts_as_dicts(contacts: list[Contact]) -> list[dict]:
    return [asdict(c) for c in contacts]
