"""Suggest LinkedIn job searches that look like the candidate's path.

Uses observed titles/headline only — never invents employers on their CV.
Links are LinkedIn Jobs *search* URLs (real, always valid). Live job-card
scraping can replace search links later via session (yellow).
"""

from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus


# Adjacent next-step titles keyed by tokens found in past titles/headline
_ADJACENT: list[tuple[tuple[str, ...], list[str]]] = [
    (
        ("data engineer", "analytics engineer", "etl", "spark", "dbt"),
        ["Senior Data Engineer", "Analytics Engineer", "Data Platform Engineer"],
    ),
    (
        ("backend", "api engineer", "fastapi", "software engineer", "associate engineer"),
        ["Backend Engineer", "Senior Software Engineer", "API Engineer"],
    ),
    (
        ("frontend", "front-end", "react", "ui engineer"),
        ["Frontend Engineer", "Senior Frontend Engineer", "Full Stack Engineer"],
    ),
    (
        ("gtm", "revops", "sales engineer", "solutions engineer", "ops"),
        ["GTM Engineer", "Sales Engineer", "Revenue Operations"],
    ),
    (
        ("full stack", "fullstack", "full-stack"),
        ["Full Stack Engineer", "Senior Full Stack Engineer"],
    ),
]


def linkedin_jobs_search(keywords: str, location: str = "") -> str:
    q = quote_plus(keywords.strip())
    url = f"https://www.linkedin.com/jobs/search/?keywords={q}"
    if location.strip():
        url += f"&location={quote_plus(location.strip())}"
    return url


# Back-compat alias
_linkedin_jobs_search = linkedin_jobs_search


def _titles_from_profile(profile: dict[str, Any], headline: str = "") -> list[str]:
    out: list[str] = []
    if headline.strip():
        out.append(headline.split("·")[0].split("|")[0].strip())
    for role in (profile.get("facts") or {}).get("experience") or []:
        t = (role.get("title") or "").strip()
        if t:
            out.append(t)
    for r in (profile.get("targets") or {}).get("roles_wanted") or []:
        if isinstance(r, str) and r.strip():
            out.append(r.strip())
    # dedupe preserve order
    seen: set[str] = set()
    uniq: list[str] = []
    for t in out:
        key = t.lower()
        if key and key not in seen:
            seen.add(key)
            uniq.append(t)
    return uniq


def suggest_roles_from_profile(
    profile: dict[str, Any],
    *,
    headline: str = "",
    location: str = "",
    limit: int = 4,
) -> list[dict[str, Any]]:
    """Return role suggestion cards with LinkedIn Jobs search links."""
    city = location or (profile.get("identity") or {}).get("city") or ""
    titles = _titles_from_profile(profile, headline=headline)
    blob = " ".join(titles).lower()
    if headline:
        blob = f"{blob} {headline.lower()}"

    suggestions: list[dict[str, Any]] = []

    # 1) Direct: search for roles they already held / headline
    for title in titles[:2]:
        suggestions.append(
            {
                "id": f"path-{len(suggestions)}",
                "title": title,
                "kind": "like_your_path",
                "why": f"Matches a role on your profile: “{title}”.",
                "linkedin_url": linkedin_jobs_search(title, city),
            }
        )

    # 2) Adjacent next steps from keyword families
    for tokens, next_titles in _ADJACENT:
        if any(tok in blob for tok in tokens):
            for nt in next_titles:
                if any(nt.lower() == s["title"].lower() for s in suggestions):
                    continue
                suggestions.append(
                    {
                        "id": f"next-{len(suggestions)}",
                        "title": nt,
                        "kind": "next_step",
                        "why": f"Common next step near your experience ({', '.join(titles[:2]) or 'your path'}).",
                        "linkedin_url": linkedin_jobs_search(nt, city),
                    }
                )
                if len(suggestions) >= limit:
                    break
        if len(suggestions) >= limit:
            break

    # 3) Fallback if profile was thin
    if not suggestions:
        for nt in ("Software Engineer", "Backend Engineer", "Data Engineer"):
            suggestions.append(
                {
                    "id": f"explore-{len(suggestions)}",
                    "title": nt,
                    "kind": "explore",
                    "why": "Starter search until we know more of your path.",
                    "linkedin_url": linkedin_jobs_search(nt, city),
                }
            )
            if len(suggestions) >= limit:
                break

    return suggestions[:limit]
