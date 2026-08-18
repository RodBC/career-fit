from __future__ import annotations

from typing import Any

from .models import Job, TailoredResume


def _pick_locale(profile: dict, job: Job, angle: str) -> str:
    if job.locale in ("en", "pt"):
        return job.locale
    targets = profile.get("targets", {})
    locales = targets.get("locales") or ["en"]
    # Prefer pt summaries when angle block only has pt, etc.
    summaries = profile.get("summaries_by_angle", {}).get(angle, {})
    if isinstance(summaries, dict):
        if locales[0] in summaries:
            return locales[0]
        if "en" in summaries:
            return "en"
        if "pt" in summaries:
            return "pt"
    return locales[0]


def _summary_for(profile: dict, angle: str, locale: str) -> str:
    block = profile.get("summaries_by_angle", {}).get(angle, {})
    if isinstance(block, dict):
        return block.get(locale) or block.get("en") or block.get("pt") or ""
    if isinstance(block, str):
        return block
    return ""


def _skills_for(profile: dict, angle: str) -> list[str]:
    return list(profile.get("skills_by_angle", {}).get(angle, []))


def _bullets(item: dict, angle: str, fallback_angles: list[str] | None = None) -> list[str]:
    by = item.get("bullets_by_angle") or {}
    if angle in by:
        return list(by[angle])
    for alt in fallback_angles or []:
        if alt in by:
            return list(by[alt])
    # any available
    for v in by.values():
        return list(v)
    return []


def tailor(profile: dict, job: Job, angle: str) -> TailoredResume:
    """Assemble resume from pre-tagged profile facts — no LLM required."""
    locale = _pick_locale(profile, job, angle)
    identity = profile.get("identity", {})
    facts = profile.get("facts", {})

    experience_out: list[dict[str, Any]] = []
    for role in facts.get("experience", []):
        bullets = _bullets(role, angle, fallback_angles=["gtm", "ops", "backend"])
        if not bullets:
            continue
        experience_out.append(
            {
                "id": role.get("id"),
                "title": role.get("title", ""),
                "company": role.get("company", ""),
                "location": role.get("location", ""),
                "start": role.get("start", ""),
                "end": role.get("end", ""),
                "bullets": bullets,
            }
        )

    projects_out: list[dict[str, Any]] = []
    for proj in facts.get("projects", []):
        bullets = _bullets(proj, angle)
        if not bullets:
            continue
        projects_out.append({"name": proj.get("name", ""), "bullets": bullets})

    return TailoredResume(
        angle=angle,
        locale=locale,
        summary=_summary_for(profile, angle, locale),
        skills=_skills_for(profile, angle),
        experience=experience_out,
        projects=projects_out[:2],
        identity=identity,
        education=list(facts.get("education", [])),
        certifications=list(facts.get("certifications", [])),
        languages=list(identity.get("languages", [])),
    )
