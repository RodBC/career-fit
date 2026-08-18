# Career Fit

**We help ambitious candidates get interviews by reaching decision-makers with a credible, tailored resume — not by spamming Easy Apply.**

Career Fit is a SaaS product. The wedge is simple and proven in practice:

1. Capture who you are (deep profile)  
2. Lock onto a role  
3. Produce a **non-AI-smelling** tailored CV (LaTeX)  
4. Draft short messages to recruiters / hiring managers  
5. You send. We do not spray.

Everything we build either strengthens that loop or is cut.

## The problem we solve

Mass applications lose. Personalized reach-out wins — but doing it by hand does not scale, and generic AI CVs get ignored.

We productize the craft: **same biography, different angle**, plus outreach that sounds human.

## What ships today (local MVP)

| Capability | Status |
|------------|--------|
| Multi-angle resume playbook (ops / frontend / backend / data / GTM / sales eng) | ✅ |
| Deterministic tailor (no LLM required) | ✅ |
| Recruiter paste → ranked contacts + DM/email drafts | ✅ |
| Vite UI + FastAPI | ✅ |
| Automated LinkedIn scraping | ❌ by design (see below) |

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
career-fit serve          # API :8787
cd web && npm i && npm run dev   # UI :5173
```

## Non-negotiables

- **Moat = playbook quality**, not scrapers.  
- **No headless LinkedIn harvester** in the public product. Paste / user-assisted capture / official APIs only.  
- **You send the message** — quality over spray.  
- **AIs working on this repo must read and update context** — see [`AGENTS.md`](AGENTS.md).

## Docs map (start here if you are an AI)

| Doc | Purpose |
|-----|---------|
| [`AGENTS.md`](AGENTS.md) | Mandatory AI operating contract |
| [`docs/context/CURRENT.md`](docs/context/CURRENT.md) | Live product state — **read first, update last** |
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | SaaS vision, tiers, moat |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Build order & technical constraints |
| [`docs/entrep-transfer.md`](docs/entrep-transfer.md) | What we reuse (and reject) from `/entrep` |
| [`playbook/`](playbook/) | Angle IP & anti-AI-smell rules |

## License

MIT
