from __future__ import annotations

from typing import Any

import yaml
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .angle import classify_angle
from .jobs import parse_job_text
from .models import ROOT, Job, load_yaml
from .outreach import build_outreach
from .recruiters import (
    contacts_as_dicts,
    enrich_with_messages,
    parse_contacts_csv,
    parse_contacts_text,
)
from .render import render_latex, render_markdown
from .tailor import tailor

app = FastAPI(title="Career Fit API", version="0.2.0")

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


def run() -> None:
    import uvicorn

    uvicorn.run("career_fit.api:app", host="127.0.0.1", port=8787, reload=True)


if __name__ == "__main__":
    run()
