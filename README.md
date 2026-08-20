# Career Fit

**We help ambitious candidates get interviews — then keep advancing their career — with a workspace that tracks outreach and suggests the next high-leverage move. Not Easy Apply spam.**

Career Fit is a SaaS. The **wedge** is proven:

1. Capture who you are (deep profile) **and** your current resume  
2. Lock onto a role  
3. Produce a **non-AI-smelling** tailored CV (LaTeX)  
4. Draft short messages to recruiters / hiring managers  
5. You send. We do not spray.

Full map: [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md).

## What ships today (local MVP)

| Capability | Status |
|------------|--------|
| Multi-angle resume playbook | ✅ |
| Deterministic tailor (no LLM required) | ✅ |
| Guided profile + resume intake | ✅ |
| Job URL → public HTTP / Camoufox map + role insights | ✅ |
| Guest-first Camoufox + warm burner session (headless) | ✅ |
| Ops burner login + Gmail IMAP App Password OTP | ✅ |
| Home shell + pipeline + people tracker | ✅ |
| Today coach + soft Free/Pro ($29) | ✅ |
| Recruiter paste → ranked drafts | ✅ |
| Vite UI + FastAPI | ✅ |
| Stripe / network graph | 🧭 later |
| Mass LinkedIn harvest / end-user password-in-API | ❌ red |

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[linkedin]"
python -m camoufox fetch
cd web && npm i && cd ..

career-fit dev            # API :8787 + UI :5173
# open http://127.0.0.1:5173 — only UI the founder should see
```

Camoufox stays **headless** on the product path. Ops cold start:

```bash
# paste LinkedIn email/password + Gmail App Password (16 chars) to the agent
career-fit linkedin-burner-login   # headless + IMAP OTP
career-fit session-status
```

See [`docs/LINKEDIN_JOB_SESSION.md`](docs/LINKEDIN_JOB_SESSION.md) (aligned with warm-bridge).

## Non-negotiables

- **Moat = playbook quality + career graph**, not scrapers.  
- **No headless LinkedIn harvester** / multi-account farm.  
- **You send / you post** — we draft and track.  
- **AIs must read/update context** — [`AGENTS.md`](AGENTS.md).

## Docs map (AIs start here)

| Doc | Purpose |
|-----|---------|
| [`AGENTS.md`](AGENTS.md) | Mandatory AI operating contract |
| [`docs/context/CURRENT.md`](docs/context/CURRENT.md) | Live product state |
| [`docs/AI_BUILD_MAP.md`](docs/AI_BUILD_MAP.md) | Commit ledger + module ownership |
| [`docs/LINKEDIN_JOB_SESSION.md`](docs/LINKEDIN_JOB_SESSION.md) | Camoufox + burner OTP |
| [`docs/PRODUCT.md`](docs/PRODUCT.md) | SaaS vision, tiers, moat |
| [`docs/ECOSYSTEM.md`](docs/ECOSYSTEM.md) | Tracker + coach end-state |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Build order |
| [`playbook/`](playbook/) | Angle IP & anti-AI-smell rules |

## License

MIT
