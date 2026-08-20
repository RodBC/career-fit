"""Offline fixtures for map-job / map-profile mock."""

from __future__ import annotations

# Role-family templates for sample-pack (never invent employer facts on CV)
_ROLE_FAMILIES: list[tuple[tuple[str, ...], str, str]] = [
    (
        ("data", "analytics engineer", "etl", "spark", "dbt", "warehouse"),
        "Senior Data Engineer",
        (
            "own Spark pipelines, Kafka streams, and a warehouse layer with dbt. "
            "Partner with analytics and platform on reliable batch + streaming jobs.\n\n"
            "Responsibilities\n"
            "- Design and operate Spark and Kafka data pipelines\n"
            "- Model warehouse tables with dbt and strong data quality checks\n"
            "- Collaborate with backend and GTM on metrics definitions\n"
            "- Mentor engineers on observability and cost control\n\n"
            "Requirements\n"
            "- 5+ years data engineering\n"
            "- Strong Python and SQL\n"
            "- Experience with Spark, Kafka, dbt, cloud warehouses\n"
            "- Clear written communication with stakeholders"
        ),
    ),
    (
        ("frontend", "front-end", "react", "ui "),
        "Frontend Engineer",
        (
            "ship polished React product surfaces with strong TypeScript habits "
            "and clear design-system collaboration.\n\n"
            "Responsibilities\n"
            "- Build accessible React + TypeScript UI flows\n"
            "- Partner with design on component systems\n"
            "- Improve performance and reliability of client apps\n"
            "- Write clear handoffs for backend contracts\n\n"
            "Requirements\n"
            "- Strong React and TypeScript\n"
            "- Experience with modern CSS and testing\n"
            "- Comfortable owning ambiguous product problems\n"
            "- Clear written communication"
        ),
    ),
    (
        ("gtm", "revops", "sales engineer", "solutions engineer", "revenue"),
        "GTM Engineer",
        (
            "connect product signals to GTM systems and keep partner workflows reliable.\n\n"
            "Responsibilities\n"
            "- Automate CRM and partner sync workflows\n"
            "- Build small FastAPI/services for integrations\n"
            "- Partner with sales ops on metrics definitions\n"
            "- Document runbooks for handoffs\n\n"
            "Requirements\n"
            "- Python and SQL comfort\n"
            "- Experience with CRM/ops tooling\n"
            "- Clear stakeholder communication\n"
            "- Bias to ship simple durable automations"
        ),
    ),
    (
        ("backend", "api", "fastapi", "software", "full stack", "fullstack", "associate"),
        "Backend Engineer",
        (
            "own FastAPI services with clear partner contracts and reliable integrations.\n\n"
            "Responsibilities\n"
            "- Design and ship FastAPI services with auth and validation\n"
            "- Build reliable import/preview pipelines against business rules\n"
            "- Partner with stakeholders to turn requirements into UI flows\n"
            "- Improve observability and operational runbooks\n\n"
            "Requirements\n"
            "- Strong Python\n"
            "- Experience with SQL and API design\n"
            "- Comfortable owning ambiguous problems end-to-end\n"
            "- Clear written communication with partners"
        ),
    ),
]


def mock_job_text_for_role(role_title: str = "", url: str = "") -> str:
    """Build a mock JD shaped around a role title (sample-pack / offline dogfood)."""
    title = (role_title or "").strip() or "Software Engineer"
    slug = (url or "").rstrip("/").split("/")[-1] or "career-fit-sample"
    blob = title.lower()
    body = (
        "ship reliable product and data workflows with strong Python habits "
        "and clear partner communication.\n\n"
        "Responsibilities\n"
        "- Own end-to-end delivery for a product surface\n"
        "- Write clear APIs and operational checks\n"
        "- Partner with stakeholders on requirements\n"
        "- Mentor peers on quality and observability\n\n"
        "Requirements\n"
        "- Strong Python or TypeScript\n"
        "- Experience shipping production systems\n"
        "- Clear written communication\n"
        "- Comfortable with ambiguous problems"
    )
    for tokens, default_title, family_body in _ROLE_FAMILIES:
        if any(tok in blob for tok in tokens):
            body = family_body
            if not role_title.strip():
                title = default_title
            break
    return f"""{title} at Northwind Analytics
https://www.linkedin.com/jobs/view/{slug}

About the job
We are hiring a {title} to {body}

About the company
Northwind Analytics builds decision systems for mid-market operators.
"""


def mock_job_text(url: str = "") -> str:
    slug = (url or "").rstrip("/").split("/")[-1] or "demo"
    return mock_job_text_for_role("Senior Data Engineer", url=f"https://www.linkedin.com/jobs/view/{slug}")


def mock_profile_snapshot(url: str = "") -> dict:
    """Offline fixture for map-profile — observed-shaped fields only."""
    slug = (url or "").rstrip("/").split("/")[-1] or "alex-example"
    parts = [p for p in slug.replace("_", "-").split("-") if p][:3]
    guess = " ".join(p.capitalize() for p in parts)
    name = guess if len(parts) >= 2 else "Alex Rivera"
    if slug in {"career-fit-mock", "alex-example", "demo"}:
        name = "Alex Rivera"
    return {
        "linkedin_url": f"https://www.linkedin.com/in/{slug}",
        "name": name,
        "headline": "Associate Engineer · Northwind Health",
        "location": "São Paulo, Brazil",
        "about": (
            "I turn messy operational workflows into simple automations and "
            "ship FastAPI services with clear partner contracts. Bilingual "
            "(PT/EN). Comfortable owning ambiguous problems end-to-end."
        ),
        "experience_text": (
            "Experience\n"
            "Associate Engineer at Northwind Health — Mar 2026 - Present\n"
            "- Monitor integration pipelines daily; validate against business rules.\n"
            "- Build FastAPI services with auth and import/preview validation.\n"
            "- Partner with stakeholders to turn requirements into UI flows.\n\n"
            "Projects\n"
            "Pipeline dashboard\n"
            "- Built daily health checks for failed jobs.\n\n"
            "Skills\n"
            "Python, FastAPI, SQL, React, TypeScript, HubSpot ops, AWS basics"
        ),
    }
