# Architecture & critical path

> AIs: also read `docs/context/CURRENT.md` and update it when this file’s priorities change.

## Product thesis

Mass apply loses. The loop that works:

**job → decision-maker → tailored CV → short message → (later) interview tutoring**

The hard IP is already here: multi-angle resume reframing without AI smell. Everything else is distribution and UX. We are building a **profitable SaaS** around that loop (`docs/PRODUCT.md`).

## What to build next (ordered)

| Priority | Build | Why |
|----------|-------|-----|
| **P0** | Profile form in Vite (no YAML required) | Remove power-user friction |
| **P0** | AI context discipline (`AGENTS.md` + `docs/context/`) | Multi-agent production speed |
| **P1** | Import tagged profile from private corpus | Founder becomes power user |
| **P1** | Job paste adapters (LinkedIn / Gupy / inHire **text**) | Normalize paste → fields |
| **P1** | `JobSource` / `ContactSource` protocols | Entrep-style adapters; paste/CSV first |
| **P2** | Optional LLM polish | After deterministic assemble is solid |
| **P2** | Interview prep generator | Tutoring layer |
| **Later** | Green/yellow feeds; browser-assisted capture | Never red-tier LinkedIn harvest |

Source policy: `docs/sources.yaml`. Entrep review: `docs/entrep-transfer.md`.


## LinkedIn scraping — critical take

**Do not ship an automated LinkedIn scraper in the public core.**

Reasons:

1. **ToS** — automated collection of LinkedIn profiles/jobs violates LinkedIn’s user agreement; a public GitHub scraper invites bans, DMCA/ToS complaints, and account loss for users.
2. **Fragility** — LinkedIn actively breaks scrapers (auth walls, captchas, DOM churn). Maintenance cost explodes; product looks broken weekly.
3. **Wrong moat** — Competitors can copy a scraper. They cannot easily copy your **angle playbook + anti-AI rewrite craft**.
4. **Legal/reputation risk** for a public product aimed at job seekers.

### What we do instead (same user outcome)

| Need | Approach in Career Fit |
|------|-------------------------|
| Find jobs | User pastes JD (LinkedIn / Gupy / inHire). Later: optional **public** job-board RSS/APIs, never session hijacking. |
| Find recruiters at company | User pastes recruiter list / profile “About” / CSV export they obtained themselves. UI ranks titles (Recruiter, TA, Hiring Manager). |
| Email from About | Parser extracts `mailto` / obvious emails from **user-provided** profile text. |
| Scale later | Private **browser-assisted** capture (user logged in, user initiates) or official partner APIs — never a headless harvester in OSS. |

Gupy / inHire remain useful as **paste sources** (and later public listing adapters). LinkedIn stays primary for **people**, but people enter the app via **user-controlled** input.

## System sketch

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────┐
│  Vite web   │────▶│  FastAPI     │────▶│  career_fit core   │
│  upload/paste│     │  /tailor     │     │  angle→assemble    │
│  recruiters  │     │  /recruiters │     │  outreach messages │
└─────────────┘     └──────────────┘     └────────────────────┘
```

## Non-goals (for now)

- Headless LinkedIn/Gupy login automation  
- Mass DM sending from the app (user sends manually — safer, more human)  
- Claiming “AI applies for you”  

Manual send is a feature: quality over spray.
