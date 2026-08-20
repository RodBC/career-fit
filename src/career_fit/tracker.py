"""Phase B tracker: applications, artifacts, outreach, soft Free limits, Today cards.

Local-first: API shapes records; UI persists in localStorage. No inventing career facts.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

Stage = Literal["saved", "applied", "waiting", "interviewing", "offer", "rejected"]

STAGES: list[Stage] = ["saved", "applied", "waiting", "interviewing", "offer", "rejected"]

STAGE_HUMAN: dict[str, str] = {
    "saved": "Ready to send",
    "applied": "Applied — waiting on them",
    "waiting": "Waiting on a reply",
    "interviewing": "Interviewing",
    "offer": "Offer",
    "rejected": "Closed — rejected",
}

# Soft Free tier (no Stripe yet) — Pro story at $29/mo working price
FREE_TAILOR_PER_MONTH = 3
FREE_APPLICATION_CAP = 5
PRO_PRICE_USD = 29


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


@dataclass
class Artifact:
    id: str
    application_id: str
    markdown: str
    latex: str
    company_message: str
    summary: str = ""
    proof: str = ""
    created_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Application:
    id: str
    title: str
    company: str
    stage: Stage = "saved"
    angle: str = ""
    locale: str = "en"
    job_description: str = ""
    next_action: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)
    artifact_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Outreach:
    id: str
    name: str
    title: str = ""
    company: str = ""
    channel: Literal["dm", "email"] = "dm"
    draft_message: str = ""
    email: str = ""
    linkedin_url: str = ""
    application_id: str | None = None
    sent: bool = False
    reply: bool = False
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TodayCard:
    id: str
    title: str
    why: str
    action: str  # craft | people | intake | pipeline
    application_id: str | None = None
    outreach_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def limits_payload() -> dict[str, Any]:
    return {
        "free_tailor_per_month": FREE_TAILOR_PER_MONTH,
        "free_application_cap": FREE_APPLICATION_CAP,
        "pro_price_usd": PRO_PRICE_USD,
        "pro_blurb": (
            f"Pro (${PRO_PRICE_USD}/mo) unlocks unlimited craft, full pipeline, "
            "and the Today coach — keep every CV and conversation in one place."
        ),
        "stages": [{"id": s, "label": STAGE_HUMAN[s]} for s in STAGES],
    }


def build_application_from_tailor(
    *,
    title: str,
    company: str,
    angle: str,
    locale: str,
    job_description: str,
    markdown: str,
    latex: str,
    company_message: str,
    summary: str = "",
    proof: str = "",
) -> dict[str, Any]:
    app_id = new_id("app")
    art_id = new_id("art")
    app = Application(
        id=app_id,
        title=title or "Untitled role",
        company=company or "",
        stage="saved",
        angle=angle or "",
        locale=locale or "en",
        job_description=job_description or "",
        next_action="Send outreach or paste recruiters",
        artifact_id=art_id,
    )
    art = Artifact(
        id=art_id,
        application_id=app_id,
        markdown=markdown or "",
        latex=latex or "",
        company_message=company_message or "",
        summary=summary or "",
        proof=proof or "",
    )
    return {"application": app.to_dict(), "artifact": art.to_dict()}


def build_outreach_from_contact(
    contact: dict[str, Any],
    *,
    application_id: str | None = None,
    sent: bool = False,
) -> dict[str, Any]:
    email = (contact.get("email") or "").strip()
    channel: Literal["dm", "email"] = "email" if email else "dm"
    o = Outreach(
        id=new_id("out"),
        name=str(contact.get("name") or "Contact"),
        title=str(contact.get("title") or ""),
        company=str(contact.get("company") or ""),
        channel=channel,
        draft_message=str(contact.get("draft_message") or ""),
        email=email,
        linkedin_url=str(contact.get("linkedin_url") or ""),
        application_id=application_id,
        sent=sent,
        reply=False,
    )
    return o.to_dict()


def match_application_id(company: str, applications: list[dict[str, Any]]) -> str | None:
    c = (company or "").strip().lower()
    if not c:
        return None
    for app in applications:
        if (app.get("company") or "").strip().lower() == c:
            return app.get("id")
    for app in applications:
        ac = (app.get("company") or "").strip().lower()
        if ac and (ac in c or c in ac):
            return app.get("id")
    return None


def generate_today_cards(
    profile: dict[str, Any] | None,
    applications: list[dict[str, Any]],
    outreach: list[dict[str, Any]],
    *,
    dismissed_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Deterministic max-3 cards. Cite why. No auto-send."""
    dismissed = set(dismissed_ids or [])
    cards: list[TodayCard] = []

    open_apps = [
        a
        for a in applications
        if a.get("stage") not in ("offer", "rejected")
    ]
    saved = [a for a in open_apps if a.get("stage") == "saved"]
    waiting = [a for a in open_apps if a.get("stage") in ("applied", "waiting")]

    if saved:
        a = saved[0]
        cards.append(
            TodayCard(
                id=f"today_send_{a['id']}",
                title=f"Send outreach for {a.get('company') or a.get('title')}",
                why=(
                    "Pack just saved — copy the company message and send it yourself. "
                    f"({STAGE_HUMAN.get(a.get('stage', ''), 'Ready to send')})"
                ),
                action="craft",
                application_id=a.get("id"),
            )
        )

    unsent = [o for o in outreach if not o.get("sent")]
    if unsent and len(cards) < 3:
        o = unsent[0]
        cards.append(
            TodayCard(
                id=f"today_log_{o['id']}",
                title=f"Mark outreach to {o.get('name')} as sent — or send it now",
                why="Drafts only help after they leave the app. You send; we track.",
                action="people",
                outreach_id=o.get("id"),
                application_id=o.get("application_id"),
            )
        )

    if waiting and len(cards) < 3:
        a = waiting[0]
        cards.append(
            TodayCard(
                id=f"today_follow_{a['id']}",
                title=f"Follow up on {a.get('company') or a.get('title')}",
                why=STAGE_HUMAN.get(a.get("stage", ""), "Waiting on a reply"),
                action="pipeline",
                application_id=a.get("id"),
            )
        )

    tutoring = (profile or {}).get("career_tutoring") or {}
    gaps = tutoring.get("improvement_areas") or []
    if gaps and len(cards) < 3 and not any(c.action == "intake" for c in cards):
        gap = gaps[0] if isinstance(gaps[0], str) else str(gaps[0])
        cards.append(
            TodayCard(
                id="today_gap_intake",
                title="Close one named gap in your profile",
                why=f"You listed: “{gap[:80]}”. Update intake or add a proof project later.",
                action="intake",
            )
        )

    if not open_apps and len(cards) < 3:
        cards.append(
            TodayCard(
                id="today_craft_first",
                title="Craft your first tailored role pack",
                why="Pipeline is empty — paste a JD and generate a CV + message.",
                action="craft",
            )
        )

    out = [c.to_dict() for c in cards if c.id not in dismissed]
    return out[:3]
