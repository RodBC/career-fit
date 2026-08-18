# AGENTS.md — operating contract for every AI on Career Fit

You are building a **profitable SaaS**, not a scraper demo.

## Before you write code

1. Read [`docs/context/CURRENT.md`](docs/context/CURRENT.md)  
2. Read [`docs/PRODUCT.md`](docs/PRODUCT.md) if the task touches product scope  
3. Read [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) if the task touches system design  
4. Skim the relevant skill under [`.cursor/skills/`](.cursor/skills/)

## After you finish meaningful work

1. Update [`docs/context/CURRENT.md`](docs/context/CURRENT.md) (status, decisions, next)  
2. Append a short entry to `docs/context/log/YYYY-MM-DD.md` (create if missing)  
3. If you introduced a durable convention, encode it in a skill or `.cursor/rules/` — do not leave it only in chat

**Chat is ephemeral. Repo context is the source of truth.**

## Product north star

```
profile → job → angle → tailored CV → decision-maker message → (later) interview tutoring
```

If a feature does not tighten this loop or increase willingness to pay, do not build it.

## Hard bans

- Automated LinkedIn profile/job harvesting in the public core  
- “Apply for the user” / mass DM sending from the server  
- Inventing employers, metrics, or tools not present in the user profile  
- Rewriting the whole CV from scratch when tagged bullets already exist  

## Preferred patterns

- Deterministic assemble first; LLM polish optional and constrained by `playbook/rewrite-rules.md`  
- Job/recruiter **intake** via paste, CSV, or green-tier public APIs (`docs/sources.yaml`)  
- Adapter interfaces inspired by entrep scrapers — **without** copying red-tier LinkedIn tactics  

## Skills (project)

| Skill | When |
|-------|------|
| `career-fit-context` | Any session — read/write context |
| `career-fit-product` | Roadmap, pricing, scope fights |
| `career-fit-tailor` | Resume angle / LaTeX / anti-AI-smell work |
| `career-fit-sources` | Job boards, recruiters, ingest adapters |

## Commit hygiene

Conventional commits (`feat`, `fix`, `docs`, `chore`, `refactor`). Keep PRs small. Never commit `data/profile.yaml` or real PII.
