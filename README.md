# Career Fit

**Profile → angle → tailored CV + recruiter outreach drafts.**

Open-source core of a career pipeline that worked in practice: reaching decision-makers beats mass applications. This repo packages the hard-won part — how to reframe the *same* biography for different roles **without** smelling like AI wrote it for that JD — plus a local web UI.

## Critical stance (read this)

**We do not ship automated LinkedIn scrapers** in the public core. They violate LinkedIn ToS, get accounts banned, break constantly, and are not the product moat. Gupy/inHire are useful as **paste sources** for job text.

What users do instead (same outcome, durable product):

1. Paste the JD (LinkedIn / Gupy / inHire / anywhere)  
2. Generate tailored CV + company message  
3. Paste recruiter / hiring-manager profile text (or CSV) from LinkedIn people search  
4. Get ranked contacts + DM/email drafts — **you send manually**

Details: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Quick start (UI)

```bash
cd career-fit
python -m venv .venv && source .venv/bin/activate
pip install -e .

# terminal 1 — API
career-fit serve

# terminal 2 — Vite UI
cd web && npm install && npm run dev
```

Open http://localhost:5173 — upload profile YAML, paste job, generate, then paste recruiters.

## CLI

```bash
career-fit classify --title "GTM Engineer" --description "HubSpot Salesforce funnel CRM"
career-fit tailor --title "Content Engineer" --company ExampleCo --description "..." --locale en
career-fit recruiters --contacts corpus/examples/recruiters-paste.txt --title "Content Engineer" --company ExampleCo
career-fit eval
career-fit profile
```

## Layout

| Path | Purpose |
|------|---------|
| `playbook/` | Angles, rewrite rules, CV skeleton |
| `corpus/examples/` | Sanitized patterns + sample recruiter paste |
| `profile/` | Schema + fictional example |
| `prompts/` | LLM prompts (optional polish later) |
| `evals/` | Classification regression |
| `src/career_fit/` | Core + FastAPI (`api.py`) + recruiters/jobs parsers |
| `web/` | Vite + React UI |
| `docs/ARCHITECTURE.md` | What to build next and why |

### Performance idea

1. Classify **angle** (deterministic)  
2. Select pre-tagged profile bullets  
3. Render MD + LaTeX  
4. Optional LLM polish later  

## Private profile

```bash
cp profile/example.profile.yaml data/profile.yaml
```

`data/profile.yaml` is gitignored.

## License

MIT
