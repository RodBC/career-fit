# Career Fit

**We help ambitious candidates get interviews — then keep advancing their career — with a workspace that tracks outreach and suggests the next high-leverage move. Not Easy Apply spam.**

Career Fit is a SaaS. The **wedge** is proven:

1. Capture who you are (deep profile) **and** your current resume  
2. Lock onto a role  
3. Produce a **non-AI-smelling** tailored CV (LaTeX)  
4. Draft short messages to recruiters / hiring managers  
5. You send. We do not spray.

The **ecosystem** we are building next:

- Track applied jobs, recruiters reached, and network people who can help  
- Advance your curriculum (skills, projects, signal)  
- Keep suggesting: post topics, courses, recruiters, peers, hackathons, projects  
- All behind a **friendly, guided UI/UX** — calm home, sharp next actions  

Full map: [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md). Everything we ship either strengthens the wedge→ecosystem path or is cut.

## The problem we solve

Mass applications lose. Personalized reach-out wins — but doing it by hand does not scale, and generic AI CVs get ignored. After the first message, candidates still lack a system: who did I contact? what should I learn? who in my network can open a door?

We productize the craft **and** the ongoing operating rhythm.

## What ships today (local MVP)

| Capability | Status |
|------------|--------|
| Multi-angle resume playbook (ops / frontend / backend / data / GTM / sales eng) | ✅ |
| Deterministic tailor (no LLM required) | ✅ |
| Recruiter paste → ranked contacts + DM/email drafts | ✅ |
| Vite UI + FastAPI | ✅ |
| Career CRM + suggestion engine | 🧭 planned (`docs/ECOSYSTEM.md`) |
| Automated LinkedIn scraping | ❌ by design |

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
career-fit serve          # API :8787
cd web && npm i && npm run dev   # UI :5173
```

## Non-negotiables

- **Moat = playbook quality + career graph**, not scrapers.  
- **No headless LinkedIn harvester** in the public product. Paste / user-assisted capture / official APIs only.  
- **You send / you post** — we draft and track; we do not spray.  
- **AIs working on this repo must read and update context** — see [`AGENTS.md`](AGENTS.md).

## Docs map (start here if you are an AI)

| Doc | Purpose |
|-----|---------|
| [`AGENTS.md`](AGENTS.md) | Mandatory AI operating contract |
| [`docs/context/CURRENT.md`](docs/context/CURRENT.md) | Live product state — **read first, update last** |
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | SaaS vision, tiers, moat |
| [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md) | Tracker + coach + UI/UX end-state |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Build order & technical constraints |
| [`docs/entrep-transfer.md`](docs/entrep-transfer.md) | What we reuse (and reject) from `/entrep` |
| [`playbook/`](playbook/) | Angle IP & anti-AI-smell rules |

## License

MIT
