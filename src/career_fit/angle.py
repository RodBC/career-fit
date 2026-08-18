from __future__ import annotations

from dataclasses import dataclass

from .models import ROOT, Job, load_yaml


@dataclass
class AngleResult:
    angle: str
    score: float
    scores: dict[str, float]
    rationale: str


def load_angles() -> dict:
    return load_yaml(ROOT / "playbook" / "angles.yaml")


def classify_angle(job: Job, angles_doc: dict | None = None) -> AngleResult:
    """Deterministic keyword scorer — fast path, no LLM."""
    doc = angles_doc or load_angles()
    angles = doc["angles"]
    text = job.text
    scores: dict[str, float] = {}

    for name, meta in angles.items():
        hits = 0
        signals = meta.get("keyword_signals", [])
        for signal in signals:
            if signal.lower() in text:
                hits += 1
        # Normalize by signal count so large lists don't dominate unfairly
        scores[name] = hits / max(len(signals), 1)

    # Light priors: if title contains a strong role word, boost
    title = job.title.lower()
    boosts = {
        "frontend": ["front-end", "frontend", "front end", "react"],
        "backend": ["backend", "back-end", "back end", "api engineer"],
        "data": ["data engineer", "data platform", "analytics engineer"],
        "gtm": ["gtm", "revops", "marketing technology", "martech"],
        "sales_eng": ["sales engineer", "solutions engineer", "pre-sales", "presales"],
        "ops": ["content engineer", "operations", "ops "],
        "fullstack": ["full-stack", "fullstack", "full stack"],
    }
    for angle, words in boosts.items():
        if any(w in title for w in words):
            scores[angle] = scores.get(angle, 0) + 0.35

    fallback = doc.get("defaults", {}).get("fallback_angle", "gtm")
    best = max(scores, key=scores.get) if scores else fallback
    if scores.get(best, 0) == 0:
        best = fallback

    rationale = f"highest keyword score among playbook angles ({scores.get(best, 0):.2f})"
    return AngleResult(angle=best, score=scores.get(best, 0), scores=scores, rationale=rationale)
