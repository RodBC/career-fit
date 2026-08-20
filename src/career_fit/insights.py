"""Role insights from a parsed JD (+ optional profile gap hints)."""

from __future__ import annotations

import re
from typing import Any

from .angle import classify_angle
from .models import Job


_REQ_HINTS = (
    "require",
    "must have",
    "você terá",
    "requisito",
    "responsib",
    "qualifica",
    "experience",
    "experiência",
    "skill",
)


def _skill_tokens(profile: dict[str, Any] | None) -> set[str]:
    if not profile:
        return set()
    out: set[str] = set()
    skills = profile.get("skills") or {}
    if isinstance(skills, dict):
        for v in skills.values():
            if isinstance(v, list):
                for item in v:
                    out.add(str(item).lower())
            elif isinstance(v, str):
                out.add(v.lower())
    elif isinstance(skills, list):
        for item in skills:
            out.add(str(item).lower())
    for exp in profile.get("facts", {}).get("experience", []) or []:
        for angle_bullets in (exp.get("bullets_by_angle") or {}).values():
            if isinstance(angle_bullets, list):
                for b in angle_bullets:
                    out.update(w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9+.#]{2,}", str(b)))
    return out


def _line_bullets(description: str, limit: int = 6) -> list[str]:
    lines = [ln.strip(" -•*\t") for ln in description.splitlines() if ln.strip()]
    picked: list[str] = []
    for ln in lines:
        low = ln.lower()
        if len(ln) < 20 or len(ln) > 180:
            continue
        if any(h in low for h in _REQ_HINTS) or ln.startswith(("-", "•")):
            picked.append(ln[:160])
        elif re.search(r"\b(python|spark|kafka|react|sql|dbt|aws|java)\b", low):
            picked.append(ln[:160])
        if len(picked) >= limit:
            break
    if len(picked) < 3:
        for ln in lines:
            if 40 <= len(ln) <= 160 and ln not in picked:
                picked.append(ln)
            if len(picked) >= limit:
                break
    return picked[:limit]


_TOOLISH = {
    "spark",
    "kafka",
    "dbt",
    "react",
    "python",
    "java",
    "kubernetes",
    "k8s",
    "aws",
    "gcp",
    "azure",
    "sql",
    "typescript",
    "nodejs",
    "node",
    "golang",
    "rust",
    "airflow",
    "snowflake",
    "databricks",
    "terraform",
    "docker",
}


def build_role_insights(
    title: str,
    company: str,
    description: str,
    profile: dict[str, Any] | None = None,
    locale: str = "en",
) -> dict[str, Any]:
    job = Job(title=title, company=company, description=description, locale=locale)
    angle = classify_angle(job)
    bullets = _line_bullets(description)
    tokens = _skill_tokens(profile)
    desc_lower = description.lower()
    gaps: list[str] = []
    for tool in sorted(_TOOLISH):
        if tool in desc_lower and tool not in tokens and not any(tool in t for t in tokens):
            gaps.append(
                f"Mention evidence for {tool} if you have it (intake), or skip inventing it."
            )
        if len(gaps) >= 3:
            break

    top_scores = sorted(angle.scores.items(), key=lambda x: -x[1])[:3]
    return {
        "angle": angle.angle,
        "angle_score": angle.score,
        "angle_rationale": angle.rationale,
        "top_angles": [{"angle": a, "score": s} for a, s in top_scores],
        "bullets": bullets,
        "gaps": gaps,
        "intake_nudge": (
            "Thin profile vs this JD — edit Intake with real wins before generating."
            if profile is not None and gaps
            else ""
        ),
    }
