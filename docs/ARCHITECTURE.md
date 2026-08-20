# Architecture & critical path

> AIs: also read `docs/context/CURRENT.md` and update it when this file’s priorities change.  
> For **where code lives and why** (commit ledger, module ownership, extension cheat sheet), read [`docs/AI_BUILD_MAP.md`](AI_BUILD_MAP.md).

## Product thesis

Mass apply loses. The loop that works:

**job → decision-maker → tailored CV → short message → (later) interview tutoring**

The hard IP is already here: multi-angle resume reframing without AI smell. Everything else is distribution and UX. We are building a **profitable SaaS** around that loop (`docs/PRODUCT.md`).

## What to build next (ordered)

| Priority | Build | Why |
|----------|-------|-----|
| **P0** | ~~Guided intake (profile form + resume upload)~~ ✅ | Ecosystem starts with a rich career graph |
| **P0** | ~~App shell + Phase B pipeline/people + soft Pro~~ ✅ | Retention + WTP |
| **P0** | AI context discipline (`AGENTS.md` + `docs/context/`) | Multi-agent production speed |
| **P0** | Job URL → session map → role insights (Craft) | Warm Bridge pattern; paste is fallback |
| **P1** | Per-angle bullet tagging after intake | Intake currently mirrors facts across angles |
| **P1** | Live Selenium job DOM harden + Gupy/inHire URL | After mock UX dogfoods |
| **P1** | Import tagged profile from private corpus | Founder becomes power user |
| **P1** | `JobSource` / `ContactSource` protocols | Session + paste + CSV backends |
| **P2** | Richer suggestion engine (Phase C full) | Courses, posts, projects, people, hackathons |
| **P2** | Optional LLM polish + interview prep; PDF parse | After deterministic assemble is solid |
| **Later** | Auth + Stripe; network bridges; partner APIs | Prefer OAuth when available |

Ecosystem map: `docs/ECOSYSTEM.md`. Source policy: `docs/sources.yaml`. Session how-to: `docs/LINKEDIN_JOB_SESSION.md`.

## LinkedIn intake — owner lock (2026-08-19)

Aligned with Warm Bridge: **yellow session Selenium is primary** for job URLs the candidate chooses. **Red** = multi-account / password-in-API / mass harvest.

| Need | Approach in Career Fit |
|------|-------------------------|
| Map a job | Paste **job URL** → local Chrome LinkedIn session → JD text → insights → tailor (`linkedin_selenium_job`) |
| Offline / CI | `CAREER_FIT_SELENIUM_MOCK=1` or Craft “Use mock JD” |
| Session down | Paste full JD (`user_paste_jd`) |
| Recruiters | Paste cards/CSV; session people scrape later if needed |
| Never | Invent JD or resume facts; headless blast; mass DM |

Moat remains angle playbook + anti-AI craft — session map is distribution, not the IP.

## System sketch

```
┌─────────────┐     ┌──────────────┐     ┌────────────────────────────┐
│  Vite Craft │────▶│  FastAPI     │────▶│  map-job → insights →      │
│  URL / paste│     │  /map-job    │     │  angle → tailor → outreach │
│  Home shell │     │  /tailor     │     │  tracker shapes            │
└─────────────┘     └──────────────┘     └────────────────────────────┘
```

## Non-goals (for now)

- Multi-account / password-in-API LinkedIn farming (red)  
- Mass DM sending from the app (user sends manually)  
- Claiming “AI applies for you”  

Manual send is a feature: quality over spray.
