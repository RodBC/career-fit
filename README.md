# Career Fit

**Profile → angle → tailored CV + outreach message.**

Open-source core of a career pipeline that worked in practice: reaching decision-makers beats mass applications. This repo packages the hard-won part — how to reframe the *same* biography for different roles **without** smelling like AI wrote it for that JD.

## Why this exists

Applying cold at scale underperforms. What worked:

1. Find the role  
2. Find the decision-maker  
3. Ship a **credible** tailored CV (LaTeX)  
4. Send a short DM/email with one proof  

Later vision: deep career tutoring (likes, differentials, gaps, networking, hates, challenges) so matching is about *fit*, not keyword spam.

This v0 ships the **IP layer** extracted from a real multi-resume corpus + a fast local assembler. Scraping LinkedIn/jobs is intentionally out of scope for the public repo.

## What's in the box

| Path | Purpose |
|------|---------|
| `playbook/` | Angles, rewrite rules, CV skeleton — the product moat |
| `corpus/examples/` | Sanitized before/after patterns (ops, frontend, backend, data, GTM, sales eng, outreach, interview prep) |
| `profile/` | Deep profile schema + fictional example |
| `prompts/` | LLM prompts for classify / tailor / outreach / interview prep |
| `evals/` | Local classification regression cases |
| `templates/resume.cls` | Minimal LaTeX class used by the corpus |
| `src/career_fit/` | Fast path: classify + assemble CV/message **without** an API call |

### Performance idea

Don't regenerate a whole CV from scratch every time.

1. Classify **angle** (deterministic keywords)  
2. Select pre-tagged `bullets_by_angle` / summaries / skills from the profile  
3. Render Markdown + LaTeX  
4. Optionally polish with an LLM using `prompts/` + `playbook/rewrite-rules.md`

## Quick start

```bash
cd career-fit
python -m venv .venv && source .venv/bin/activate
pip install -e .

# Classify a JD
career-fit classify --title "GTM Engineer" --description "HubSpot Salesforce funnel CRM automation"

# Build tailored CV + outreach (uses profile/example.profile.yaml)
career-fit tailor \
  --title "Content Engineer" \
  --company "ExampleCo" \
  --description "High-volume publishing pipeline, QA before scale, monitoring" \
  --locale en

# Show tutoring / fit brief
career-fit profile

# Run evals
career-fit eval
```

Outputs land in `data/out/` (gitignored): `.md`, `.tex`, `-message.txt`.

### Your private profile

```bash
cp profile/example.profile.yaml data/profile.yaml
# edit facts + bullets_by_angle + career_tutoring
```

`data/profile.yaml` is gitignored — keep PII off GitHub.

## Angles (same bio, different lens)

| Angle | Lens |
|-------|------|
| `ops` | High-volume workflows, QA before scale, escalation |
| `frontend` | React/TS, UI flows, REST consumption |
| `backend` | APIs, auth, ingestion, SQL, production |
| `data` | Pipelines, modeling, gold layers, job observability |
| `gtm` | CRM/MAP, funnel, hygiene, RevOps automations |
| `sales_eng` | Discovery, demos, Sales↔Eng bridge |
| `fullstack` | End-to-end UI + API |

Rules that matter live in `playbook/rewrite-rules.md`.

## Roadmap (platform)

- [ ] Job ingest adapters (manual paste first; scrapers private/local)  
- [ ] Decision-maker helpers (user-supplied LinkedIn notes; no ToS-hostile scraping in core)  
- [ ] Optional LLM provider for polish  
- [ ] Interview-prep generator wired to `prompts/interview_prep.md`  
- [ ] Web UI for tutoring intake  

## Public repo hygiene

- Example profile is **fictional**  
- Corpus examples are **sanitized patterns**, not full personal CVs  
- Put real identity only in `data/profile.yaml`

## License

MIT
# career-fit
