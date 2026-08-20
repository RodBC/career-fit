from __future__ import annotations

import re
from typing import Any

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .angle import classify_angle
from .insights import build_role_insights
from .intake import build_profile_from_intake, parse_resume_text
from .jobs import parse_job_text
from .linkedin_browser import (
    BrowserJobError as SeleniumJobError,
    map_job_url,
    map_profile_url,
    parsed_as_dict,
    run_linkedin_login_session,
    search_job_openings,
    session_ready_report,
)
from .linkedin_browser.mock import mock_job_text_for_role
from .models import ROOT, Job, load_yaml
from .outreach import build_outreach
from .recruiters import (
    contacts_as_dicts,
    enrich_with_messages,
    parse_contacts_csv,
    parse_contacts_text,
)
from .render import render_latex, render_markdown
from .suggest_roles import linkedin_jobs_search, suggest_roles_from_profile
from .tailor import tailor
from .tracker import (
    build_application_from_tailor,
    build_outreach_from_contact,
    generate_today_cards,
    limits_payload,
    match_application_id,
)

app = FastAPI(title="Career Fit API", version="0.4.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobIn(BaseModel):
    title: str = ""
    company: str = ""
    description: str = ""
    locale: str | None = None
    raw_paste: str | None = None
    source: str = "paste"


class TailorRequest(BaseModel):
    profile: dict[str, Any] | None = None
    job: JobIn
    angle: str | None = None


class RecruitersRequest(BaseModel):
    profile: dict[str, Any] | None = None
    job: JobIn
    contacts_text: str = ""
    angle: str | None = None
    locale: str | None = None


class IntakeRequest(BaseModel):
    identity: dict[str, Any] = {}
    career_tutoring: dict[str, Any] = {}
    targets: dict[str, Any] = {}
    resume_text: str = ""
    base_profile: dict[str, Any] | None = None


class ParseResumeRequest(BaseModel):
    text: str = ""


class SaveApplicationRequest(BaseModel):
    title: str = ""
    company: str = ""
    angle: str = ""
    locale: str = "en"
    job_description: str = ""
    markdown: str = ""
    latex: str = ""
    company_message: str = ""
    summary: str = ""
    proof: str = ""


class LogOutreachRequest(BaseModel):
    contact: dict[str, Any]
    application_id: str | None = None
    applications: list[dict[str, Any]] = []
    sent: bool = True


class TodayRequest(BaseModel):
    profile: dict[str, Any] | None = None
    applications: list[dict[str, Any]] = []
    outreach: list[dict[str, Any]] = []
    dismissed_ids: list[str] = []


class MapJobRequest(BaseModel):
    url: str = ""
    profile: dict[str, Any] | None = None
    mock: bool | None = None
    locale: str | None = None


class MapProfileRequest(BaseModel):
    url: str = ""
    mock: bool | None = None
    stub: bool = False


class SuggestRolesRequest(BaseModel):
    profile: dict[str, Any] | None = None
    headline: str = ""
    location: str = ""
    limit: int = 4


class SuggestOpeningsRequest(BaseModel):
    role_titles: list[str] = []
    keywords: str = ""
    location: str = ""
    limit: int = 6


class SamplePackRequest(BaseModel):
    profile: dict[str, Any] | None = None
    role_title: str = ""
    locale: str | None = None


def _default_profile() -> dict[str, Any]:
    path = ROOT / "data" / "profile.yaml"
    if not path.exists():
        path = ROOT / "profile" / "example.profile.yaml"
    return load_yaml(path)


def _resolve_job(job_in: JobIn) -> Job:
    title, company, description, locale = job_in.title, job_in.company, job_in.description, job_in.locale
    if job_in.raw_paste and (not title or not description):
        parsed = parse_job_text(job_in.raw_paste, source=job_in.source)
        title = title or parsed.title
        company = company or parsed.company
        description = description or parsed.description
        if not locale:
            locale = parsed.locale_hint
    return Job(
        title=title or "Untitled role",
        company=company or "",
        description=description or job_in.raw_paste or "",
        locale=locale or "en",
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/example-profile")
def example_profile() -> dict[str, Any]:
    return load_yaml(ROOT / "profile" / "example.profile.yaml")


@app.post("/api/parse-job")
def api_parse_job(payload: dict[str, str]) -> dict[str, Any]:
    raw = payload.get("raw") or payload.get("text") or ""
    source = payload.get("source") or "paste"
    if not raw.strip():
        raise HTTPException(400, "raw job text required")
    parsed = parse_job_text(raw, source=source)
    return {
        "title": parsed.title,
        "company": parsed.company,
        "description": parsed.description,
        "source": parsed.source,
        "locale_hint": parsed.locale_hint,
    }


@app.post("/api/map-job")
def api_map_job(req: MapJobRequest) -> dict[str, Any]:
    """Job URL → session/mock JD → parse → role insights."""
    try:
        mapped = map_job_url(req.url, mock=req.mock)
    except SeleniumJobError as e:
        raise HTTPException(e.status, str(e)) from e
    parsed = mapped["parsed"]
    locale = req.locale or parsed.locale_hint or "en"
    insights = build_role_insights(
        parsed.title,
        parsed.company,
        parsed.description,
        profile=req.profile,
        locale=locale,
    )
    return {
        "ok": True,
        "job": parsed_as_dict(parsed),
        "insights": insights,
        "meta": mapped["meta"],
    }


@app.post("/api/map-profile")
def api_map_profile(req: MapProfileRequest) -> dict[str, Any]:
    """Candidate LinkedIn URL → session/mock/stub snapshot → light profile draft."""
    try:
        mapped = map_profile_url(req.url, mock=req.mock, stub=req.stub)
    except SeleniumJobError as e:
        raise HTTPException(e.status, str(e)) from e
    profile = mapped["profile"]
    snap = mapped["snapshot"]
    roles = suggest_roles_from_profile(
        profile,
        headline=str(snap.get("headline") or ""),
        location=str(snap.get("location") or ""),
        limit=4,
    )
    return {
        "ok": True,
        "snapshot": snap,
        "profile": profile,
        "suggested_roles": roles,
        "meta": mapped["meta"],
    }


@app.post("/api/suggest-roles")
def api_suggest_roles(req: SuggestRolesRequest) -> dict[str, Any]:
    profile = req.profile or _default_profile()
    roles = suggest_roles_from_profile(
        profile,
        headline=req.headline,
        location=req.location,
        limit=max(1, min(req.limit, 6)),
    )
    return {"ok": True, "roles": roles}


@app.get("/api/session-status")
def api_session_status() -> dict[str, Any]:
    return {"ok": True, **session_ready_report()}


@app.post("/api/linkedin-session")
def api_linkedin_session() -> dict[str, Any]:
    """Open Camoufox for one-time LinkedIn login (blocks until feed or ~5 min)."""
    try:
        return run_linkedin_login_session(wait_sec=300)
    except SeleniumJobError as e:
        raise HTTPException(e.status, str(e)) from e


@app.post("/api/suggest-openings")
def api_suggest_openings(req: SuggestOpeningsRequest) -> dict[str, Any]:
    """Live LinkedIn openings only — skip incomplete cards; never invent employers."""
    titles: list[str] = [t.strip() for t in req.role_titles if t and str(t).strip()]
    kw = (req.keywords or "").strip()
    if kw:
        for part in re.split(r"[,;\n]+", kw):
            p = part.strip()
            if p and p.lower() not in {t.lower() for t in titles}:
                titles.append(p)
    if not titles:
        raise HTTPException(
            400,
            "Provide role titles or keywords to search real LinkedIn jobs.",
        )
    # Search the strongest signal first (joined keywords), then fill from singles
    primary = " OR ".join(titles[:3]) if len(titles) > 1 else titles[0]
    # LinkedIn search uses space-separated keywords better than OR in many locales
    primary = " ".join(titles[:2])
    limit = max(1, min(req.limit, 8))
    try:
        result = search_job_openings(
            primary,
            location=req.location or "",
            limit=limit,
        )
    except SeleniumJobError as e:
        raise HTTPException(e.status, str(e)) from e
    openings = result["openings"]
    # If thin results, try next title (still live only)
    if len(openings) < min(3, limit) and len(titles) > 1:
        for title in titles[1:]:
            if len(openings) >= limit:
                break
            try:
                more = search_job_openings(
                    title,
                    location=req.location or "",
                    limit=limit - len(openings),
                )
            except SeleniumJobError:
                break
            seen = {o["linkedin_url"] for o in openings}
            for o in more["openings"]:
                if o["linkedin_url"] not in seen:
                    openings.append(o)
                    seen.add(o["linkedin_url"])
    if not openings:
        raise HTTPException(
            503,
            "No complete LinkedIn job cards found (bad/empty postings skipped). "
            "Paste a jobs/view URL, or run: career-fit linkedin-session",
        )
    return {
        "ok": True,
        "openings": openings[:limit],
        "note": (
            "Live LinkedIn openings — incomplete or unavailable links were skipped. "
            "Paste another jobs/view URL anytime."
        ),
        "meta": result.get("meta") or {},
    }


@app.post("/api/sample-pack")
def api_sample_pack(req: SamplePackRequest) -> dict[str, Any]:
    """Profile + role title → mock JD → insights → tailor pack (dogfood loop)."""
    profile = req.profile or _default_profile()
    title = (req.role_title or "").strip() or "Software Engineer"
    raw = mock_job_text_for_role(title)
    parsed = parse_job_text(raw, source="mock")
    # Prefer the requested title over parser guess
    job_title = title or parsed.title
    company = parsed.company or "Northwind Analytics"
    description = parsed.description or raw
    locale = req.locale or parsed.locale_hint or "en"
    insights = build_role_insights(
        job_title,
        company,
        description,
        profile=profile,
        locale=locale,
    )
    job = Job(
        title=job_title,
        company=company,
        description=description,
        locale=locale,
    )
    angle = insights.get("angle") or classify_angle(job).angle
    resume = tailor(profile, job, angle)
    company_msg = build_outreach(profile, job, resume)
    city = str((profile.get("identity") or {}).get("city") or "")
    return {
        "ok": True,
        "job": {
            "title": job_title,
            "company": company,
            "description": description,
            "source": "mock",
            "locale_hint": locale,
        },
        "insights": insights,
        "pack": {
            "angle": angle,
            "locale": resume.locale,
            "markdown": render_markdown(resume),
            "latex": render_latex(resume),
            "company_message": company_msg,
            "summary": resume.summary,
            "proof": (
                resume.projects[0]["bullets"][0]
                if resume.projects and resume.projects[0].get("bullets")
                else ""
            ),
            "project_name": (resume.projects[0]["name"] if resume.projects else ""),
        },
        "linkedin_search_url": linkedin_jobs_search(job_title, city),
        "meta": {"source": "sample_pack", "mock": True, "role_title": title},
    }


@app.post("/api/job-insights")
def api_job_insights(payload: dict[str, Any]) -> dict[str, Any]:
    """Insights from already-pasted JD text (fallback path)."""
    raw = (payload.get("raw") or payload.get("description") or "").strip()
    title = (payload.get("title") or "").strip()
    company = (payload.get("company") or "").strip()
    if not raw and not title:
        raise HTTPException(400, "job text or title required")
    if raw and (not title or not company):
        parsed = parse_job_text(raw, source=payload.get("source") or "paste")
        title = title or parsed.title
        company = company or parsed.company
        raw = raw or parsed.description
    locale = payload.get("locale") or "en"
    insights = build_role_insights(
        title,
        company,
        raw,
        profile=payload.get("profile"),
        locale=locale,
    )
    return {
        "ok": True,
        "job": {
            "title": title,
            "company": company,
            "description": raw,
            "source": payload.get("source") or "paste",
            "locale_hint": None,
        },
        "insights": insights,
    }


@app.post("/api/classify")
def api_classify(job: JobIn) -> dict[str, Any]:
    j = _resolve_job(job)
    result = classify_angle(j)
    return {
        "angle": result.angle,
        "score": result.score,
        "scores": result.scores,
        "rationale": result.rationale,
        "job": {"title": j.title, "company": j.company, "locale": j.locale},
    }


@app.post("/api/tailor")
def api_tailor(req: TailorRequest) -> dict[str, Any]:
    profile = req.profile or _default_profile()
    job = _resolve_job(req.job)
    angle = req.angle or classify_angle(job).angle
    resume = tailor(profile, job, angle)
    company_msg = build_outreach(profile, job, resume)
    return {
        "angle": angle,
        "locale": resume.locale,
        "markdown": render_markdown(resume),
        "latex": render_latex(resume),
        "company_message": company_msg,
        "summary": resume.summary,
        "proof": (resume.projects[0]["bullets"][0] if resume.projects and resume.projects[0].get("bullets") else ""),
        "project_name": (resume.projects[0]["name"] if resume.projects else ""),
    }


@app.post("/api/recruiters")
def api_recruiters(req: RecruitersRequest) -> dict[str, Any]:
    if not req.contacts_text.strip():
        raise HTTPException(400, "Paste recruiter profiles or CSV text")
    profile = req.profile or _default_profile()
    job = _resolve_job(req.job)
    angle = req.angle or classify_angle(job).angle
    resume = tailor(profile, job, angle)
    locale = req.locale or resume.locale
    proof = ""
    if resume.projects:
        p = resume.projects[0]
        proof = f"{p['name']}: {p['bullets'][0]}" if p.get("bullets") else p.get("name", "")

    text = req.contacts_text.strip()
    if text.lower().startswith("name,") or "\nname," in text.lower()[:80]:
        contacts = parse_contacts_csv(text, company=job.company)
    else:
        contacts = parse_contacts_text(text, company=job.company)

    contacts = enrich_with_messages(
        contacts,
        candidate_name=profile.get("identity", {}).get("name", ""),
        job_title=job.title,
        company=job.company or "the company",
        angle_summary=resume.summary,
        proof_line=f"One proof point — {proof}" if proof else "",
        locale=locale,
    )
    return {
        "angle": angle,
        "count": len(contacts),
        "contacts": contacts_as_dicts(contacts),
        "note": (
            "Contacts come from text you pasted. Career Fit does not scrape LinkedIn. "
            "Copy recruiter cards / About sections yourself, then generate drafts here."
        ),
    }


@app.post("/api/upload-profile")
async def upload_profile(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    try:
        text = raw.decode("utf-8")
        data = yaml.safe_load(text)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, f"Invalid YAML/JSON profile: {exc}") from exc
    if not isinstance(data, dict):
        raise HTTPException(400, "Profile must be a YAML/JSON object")
    if "identity" not in data:
        raise HTTPException(400, "Profile needs an identity block")
    return {"ok": True, "profile": data}


@app.post("/api/parse-resume")
def api_parse_resume(req: ParseResumeRequest) -> dict[str, Any]:
    if not req.text.strip():
        raise HTTPException(400, "resume text required")
    parsed = parse_resume_text(req.text)
    return {
        "summary": parsed.summary,
        "skills": parsed.skills,
        "experience": parsed.experience,
        "projects": parsed.projects,
        "education": parsed.education,
        "warnings": parsed.warnings,
    }


@app.post("/api/intake")
def api_intake(req: IntakeRequest) -> dict[str, Any]:
    try:
        profile = build_profile_from_intake(
            identity=req.identity,
            career_tutoring=req.career_tutoring,
            targets=req.targets,
            resume_text=req.resume_text,
            base_profile=req.base_profile,
        )
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    meta = profile.get("intake_meta") or {}
    return {
        "ok": True,
        "profile": profile,
        "warnings": meta.get("resume_warnings") or [],
        "parsed_roles": meta.get("parsed_roles", 0),
        "parsed_projects": meta.get("parsed_projects", 0),
    }


@app.get("/api/tracker/limits")
def api_tracker_limits() -> dict[str, Any]:
    return limits_payload()


@app.post("/api/tracker/save-application")
def api_save_application(req: SaveApplicationRequest) -> dict[str, Any]:
    if not (req.title or req.company or req.job_description):
        raise HTTPException(400, "Need a role title, company, or job description to save")
    bundle = build_application_from_tailor(
        title=req.title,
        company=req.company,
        angle=req.angle,
        locale=req.locale,
        job_description=req.job_description,
        markdown=req.markdown,
        latex=req.latex,
        company_message=req.company_message,
        summary=req.summary,
        proof=req.proof,
    )
    return {"ok": True, **bundle}


@app.post("/api/tracker/log-outreach")
def api_log_outreach(req: LogOutreachRequest) -> dict[str, Any]:
    if not req.contact.get("name"):
        raise HTTPException(400, "contact.name required")
    app_id = req.application_id or match_application_id(
        str(req.contact.get("company") or ""),
        req.applications,
    )
    outreach = build_outreach_from_contact(
        req.contact,
        application_id=app_id,
        sent=req.sent,
    )
    return {"ok": True, "outreach": outreach}


@app.post("/api/tracker/today")
def api_today(req: TodayRequest) -> dict[str, Any]:
    cards = generate_today_cards(
        req.profile,
        req.applications,
        req.outreach,
        dismissed_ids=req.dismissed_ids,
    )
    return {"cards": cards, "max": 3}


def run() -> None:
    import uvicorn

    uvicorn.run("career_fit.api:app", host="127.0.0.1", port=8787, reload=True)


if __name__ == "__main__":
    run()
