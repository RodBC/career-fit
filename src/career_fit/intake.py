"""Guided intake: build a profile from form fields + rules-first resume text.

No LLM. No inventing employers. Resume facts come only from user-provided text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .angle import load_angles

_BULLET_RE = re.compile(r"^[\s]*[-*•–—]\s+(.+)$")
_DATE_RANGE_RE = re.compile(
    r"(?P<start>(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}(?:-\d{2})?)"
    r"\s*[–—\-to]+\s*"
    r"(?P<end>Present|present|Atual|atual|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|\d{4}(?:-\d{2})?)",
    re.I,
)
_AT_COMPANY_RE = re.compile(
    r"^(?P<title>.+?)\s+(?:at|@|—|-|–|·|\||em)\s+(?P<company>.+)$",
    re.I,
)

_SECTION_MAP: dict[str, tuple[str, ...]] = {
    "summary": ("summary", "profile", "about", "objective", "resumo", "objetivo", "sobre"),
    "experience": (
        "experience",
        "work experience",
        "employment",
        "work history",
        "experiência",
        "experiencia",
        "histórico profissional",
        "historico profissional",
    ),
    "education": ("education", "formação", "formacao", "educação", "educacao", "academic"),
    "projects": ("projects", "project", "projetos", "selected projects"),
    "skills": ("skills", "competências", "competencias", "habilidades", "tech stack", "technologies"),
}


@dataclass
class ParsedResume:
    summary: str = ""
    skills: list[str] = field(default_factory=list)
    experience: list[dict[str, Any]] = field(default_factory=list)
    projects: list[dict[str, Any]] = field(default_factory=list)
    education: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _lines(text: str) -> list[str]:
    return [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]


def _norm_header(line: str) -> str | None:
    raw = line.strip().strip(":").lower()
    if not raw or len(raw) > 48:
        return None
    # Ignore markdown heading markers
    raw = re.sub(r"^#+\s*", "", raw)
    for key, aliases in _SECTION_MAP.items():
        if raw in aliases:
            return key
    return None


def _is_bullet(line: str) -> str | None:
    m = _BULLET_RE.match(line)
    return m.group(1).strip() if m else None


def _split_skills(blob: str) -> list[str]:
    parts = re.split(r"[,;|•·]|\n", blob)
    out: list[str] = []
    for p in parts:
        s = p.strip(" -\t")
        if 1 < len(s) <= 60:
            out.append(s)
    return out


def _parse_role_header(line: str) -> dict[str, str] | None:
    cleaned = line.strip().lstrip("#").strip()
    if not cleaned or _is_bullet(cleaned):
        return None
    dates = _DATE_RANGE_RE.search(cleaned)
    start, end = "", ""
    head = cleaned
    if dates:
        start, end = dates.group("start"), dates.group("end")
        head = (cleaned[: dates.start()] + cleaned[dates.end() :]).strip(" |·—–,")
        head = head.rstrip(" -—–|·,")
    end_norm = end.lower() if end else ""
    if end_norm in ("present", "atual"):
        end = "present"
    at = _AT_COMPANY_RE.match(head)
    if at:
        return {
            "title": at.group("title").strip(" |·"),
            "company": at.group("company").strip(" |·—–-"),
            "start": start,
            "end": end,
        }
    # "Title, Company" or "Title — Company"
    if " — " in head or " - " in head or " – " in head:
        parts = re.split(r"\s+[—–\-]\s+", head, maxsplit=1)
        if len(parts) == 2 and len(parts[0]) < 80:
            return {
                "title": parts[0].strip(),
                "company": parts[1].strip(" |·—–-"),
                "start": start,
                "end": end,
            }
    if dates and head:
        # Treat remaining as title when dates present
        return {"title": head, "company": "", "start": start, "end": end}
    return None


def parse_resume_text(raw: str) -> ParsedResume:
    """Rules-first section/bullet parser. Does not invent employers or metrics."""
    result = ParsedResume()
    if not raw or not raw.strip():
        result.warnings.append("Empty resume text")
        return result

    lines = _lines(raw)
    section = "summary"
    buckets: dict[str, list[str]] = {k: [] for k in _SECTION_MAP}
    current_role: dict[str, Any] | None = None
    current_project: dict[str, Any] | None = None

    def flush_role() -> None:
        nonlocal current_role
        if current_role and (current_role.get("bullets") or current_role.get("title")):
            result.experience.append(current_role)
        current_role = None

    def flush_project() -> None:
        nonlocal current_project
        if current_project and (current_project.get("bullets") or current_project.get("name")):
            result.projects.append(current_project)
        current_project = None

    for line in lines:
        if not line.strip():
            continue
        header = _norm_header(line)
        if header:
            flush_role()
            flush_project()
            section = header
            continue

        bullet = _is_bullet(line)
        if section == "experience":
            if bullet is not None:
                if current_role is None:
                    current_role = {
                        "id": f"role_{len(result.experience) + 1}",
                        "title": "Role",
                        "company": "",
                        "location": "",
                        "start": "",
                        "end": "",
                        "bullets": [],
                    }
                current_role["bullets"].append(bullet)
                continue
            header_role = _parse_role_header(line)
            if header_role:
                flush_role()
                current_role = {
                    "id": f"role_{len(result.experience) + 1}",
                    "title": header_role["title"],
                    "company": header_role["company"],
                    "location": "",
                    "start": header_role.get("start", ""),
                    "end": header_role.get("end", ""),
                    "bullets": [],
                }
                continue
            # Continuation line under current role → treat as soft bullet
            if current_role is not None and len(line.strip()) > 20:
                current_role["bullets"].append(line.strip())
            continue

        if section == "projects":
            if bullet is not None:
                if current_project is None:
                    current_project = {"name": "Project", "bullets": []}
                current_project["bullets"].append(bullet)
                continue
            # Project name line
            flush_project()
            name = line.strip().lstrip("#").strip()
            current_project = {"name": name[:120], "bullets": []}
            continue

        if section == "skills":
            if bullet is not None:
                result.skills.extend(_split_skills(bullet))
            else:
                result.skills.extend(_split_skills(line))
            continue

        if section == "education":
            if bullet is not None:
                result.education.append({"degree": bullet, "school": "", "dates": ""})
            else:
                result.education.append({"degree": line.strip()[:160], "school": "", "dates": ""})
            continue

        # summary / unknown
        if bullet is not None:
            buckets["summary"].append(bullet)
        else:
            buckets["summary"].append(line.strip())

    flush_role()
    flush_project()

    if buckets["summary"]:
        result.summary = " ".join(buckets["summary"][:6]).strip()
    # Dedupe skills
    seen: set[str] = set()
    uniq: list[str] = []
    for s in result.skills:
        key = s.lower()
        if key not in seen:
            seen.add(key)
            uniq.append(s)
    result.skills = uniq[:40]

    if not result.experience and not result.projects and not result.summary:
        # Fallback: treat whole paste as unstructured bullets under one role
        soft = [ln.strip() for ln in lines if ln.strip() and not _norm_header(ln)]
        bullets = []
        for ln in soft:
            b = _is_bullet(ln)
            bullets.append(b if b else ln)
        if bullets:
            result.experience.append(
                {
                    "id": "role_1",
                    "title": "Experience",
                    "company": "",
                    "location": "",
                    "start": "",
                    "end": "",
                    "bullets": bullets[:12],
                }
            )
            result.warnings.append(
                "Could not detect clear sections — stored lines as a single experience block. "
                "Add Experience / Projects headers for better parsing."
            )
    if result.experience and not any(r.get("bullets") for r in result.experience):
        result.warnings.append("Experience headers found but no bullets — add - bullet lines under each role.")
    return result


def _lines_to_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    text = str(value).replace("\r\n", "\n")
    out: list[str] = []
    for ln in text.split("\n"):
        s = ln.strip().lstrip("-•*").strip()
        if s:
            out.append(s)
    return out


def _angle_ids() -> list[str]:
    doc = load_angles()
    return list((doc.get("angles") or {}).keys())


def _bullets_by_angle(bullets: list[str]) -> dict[str, list[str]]:
    """Same facts on every angle until the user tags per-angle later. No invention."""
    clean = [b.strip() for b in bullets if b and b.strip()]
    return {aid: list(clean) for aid in _angle_ids()}


def _starter_summaries(tutoring: dict[str, Any], resume_summary: str, locales: list[str]) -> dict[str, dict[str, str]]:
    parts = _lines_to_list(tutoring.get("positive_differentials"))[:2]
    parts += _lines_to_list(tutoring.get("enjoyed_most"))[:1]
    if resume_summary:
        parts.append(resume_summary[:220])
    en = ". ".join(p.rstrip(".") for p in parts if p).strip()
    if en and not en.endswith("."):
        en += "."
    if not en:
        en = "Operator who ships reliable work and communicates clearly with stakeholders."
    block = {loc: en for loc in (locales or ["en"])}
    if "en" not in block:
        block["en"] = en
    return {aid: dict(block) for aid in _angle_ids()}


def _skills_by_angle(skills: list[str], tutoring: dict[str, Any]) -> dict[str, list[str]]:
    tech = _lines_to_list(tutoring.get("technical_knowledge"))
    merged = list(dict.fromkeys([*skills, *tech]))[:24]
    return {aid: list(merged) for aid in _angle_ids()}


def build_profile_from_intake(
    identity: dict[str, Any] | None = None,
    career_tutoring: dict[str, Any] | None = None,
    targets: dict[str, Any] | None = None,
    resume_text: str = "",
    base_profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a tailor-ready profile. Never invent employers or metrics."""
    identity = dict(identity or {})
    career_tutoring = dict(career_tutoring or {})
    targets = dict(targets or {})
    base = dict(base_profile or {})

    # Normalize list fields
    for key in (
        "enjoyed_most",
        "positive_differentials",
        "improvement_areas",
        "technical_knowledge",
        "networking_notes",
        "hates_doing",
        "challenges_overcome",
    ):
        if key in career_tutoring:
            career_tutoring[key] = _lines_to_list(career_tutoring[key])

    if "languages" in identity and not isinstance(identity["languages"], list):
        identity["languages"] = _lines_to_list(identity["languages"]) or [
            x.strip() for x in str(identity["languages"]).split(",") if x.strip()
        ]

    roles = targets.get("roles_wanted")
    if roles is not None and not isinstance(roles, list):
        targets["roles_wanted"] = _lines_to_list(roles)
    locales = targets.get("locales") or ["en"]
    if isinstance(locales, str):
        locales = [x.strip() for x in locales.split(",") if x.strip()]
    targets["locales"] = locales or ["en"]
    if "remote" in targets:
        targets["remote"] = bool(targets["remote"])

    name = (identity.get("name") or "").strip()
    email = (identity.get("email") or "").strip()
    if not name:
        raise ValueError("identity.name is required")
    if not email:
        raise ValueError("identity.email is required")

    parsed = parse_resume_text(resume_text) if resume_text.strip() else ParsedResume()

    experience = []
    for role in parsed.experience:
        bullets = list(role.get("bullets") or [])
        experience.append(
            {
                "id": role.get("id") or f"role_{len(experience) + 1}",
                "title": role.get("title") or "Role",
                "company": role.get("company") or "",
                "location": role.get("location") or "",
                "start": role.get("start") or "",
                "end": role.get("end") or "",
                "bullets_by_angle": _bullets_by_angle(bullets),
            }
        )

    projects = []
    for proj in parsed.projects:
        bullets = list(proj.get("bullets") or [])
        projects.append(
            {
                "name": proj.get("name") or "Project",
                "bullets_by_angle": _bullets_by_angle(bullets),
            }
        )

    # Prefer intake facts; keep base facts if resume empty
    base_facts = dict(base.get("facts") or {})
    facts: dict[str, Any] = {
        "years_experience": base_facts.get("years_experience"),
        "education": parsed.education or list(base_facts.get("education") or []),
        "certifications": list(base_facts.get("certifications") or []),
        "experience": experience or list(base_facts.get("experience") or []),
        "projects": projects or list(base_facts.get("projects") or []),
    }
    facts = {k: v for k, v in facts.items() if v is not None}

    merged_identity = {**(base.get("identity") or {}), **identity}
    merged_tutoring = {**(base.get("career_tutoring") or {}), **career_tutoring}
    merged_targets = {**(base.get("targets") or {}), **targets}

    profile: dict[str, Any] = {
        "$schema_note": "Built by guided intake (rules-first). Tag bullets_by_angle later for sharper angles.",
        "identity": merged_identity,
        "career_tutoring": merged_tutoring,
        "targets": merged_targets,
        "facts": facts,
        "summaries_by_angle": _starter_summaries(merged_tutoring, parsed.summary, locales),
        "skills_by_angle": _skills_by_angle(parsed.skills, merged_tutoring),
        "intake_meta": {
            "source": "guided_form",
            "resume_warnings": parsed.warnings,
            "parsed_roles": len(experience),
            "parsed_projects": len(projects),
        },
    }
    return profile
