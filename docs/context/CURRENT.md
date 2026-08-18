# CURRENT context — Career Fit

> **AIs: read this fully before coding. Update this file before you end a session with meaningful changes.**

**Last updated:** 2026-08-18  
**Repo:** `/home/decastro/studies/career-fit` (own git, public-bound)  
**Related private corpus:** `/home/decastro/studies/curriculumn` (LaTeX source of angle IP — do not publish PII)

## Goal

Ship a profitable SaaS that turns a deep candidate profile + a job into **tailored CV + decision-maker outreach**, with optional career tutoring. Loop:

`profile → job → angle → CV → recruiter message → (later) interview tutoring`

## What exists now

- Playbook: `playbook/angles.yaml`, `rewrite-rules.md`, `structure.md`  
- Core Python: classify / tailor / render / outreach / recruiters / jobs  
- API: FastAPI on `:8787` (`career-fit serve`)  
- UI: Vite React on `:5173` (`web/`)  
- AI contract: `AGENTS.md`, `.cursor/rules/`, `.cursor/skills/`  
- Entrep learnings captured in `docs/entrep-transfer.md` + `docs/sources.yaml`

## Decisions locked

| Decision | Rationale |
|----------|-----------|
| No automated LinkedIn scraper in public core | ToS, bans, fragility; wrong moat |
| Deterministic tailor before LLM | Fast, cheap, controllable; LLM is polish |
| Manual send of DMs/emails | Quality + compliance; product is drafts not spam |
| Paste-first job & recruiter intake | Same user outcome without red-tier harvesting |
| Context must live in git | Chat is ephemeral; SaaS iteration needs memory |

## Active priorities (P0 → P2)

1. **P0** Profile form in UI (reduce YAML friction)  
2. **P0** Keep context/skills discipline as default agent behavior  
3. **P1** Import tagged profile from `curriculumn` corpus  
4. **P1** Better JD normalizers (LinkedIn/Gupy/inHire paste)  
5. **P2** Optional LLM polish behind rewrite-rules  
6. **P2** Interview prep generator  
7. **Later** Green-tier job feeds; user-assisted browser capture (not headless LinkedIn farm)

## Open questions

- Pricing exact numbers (Pro band $19–39 draft)  
- Whether coach/team tier ships before or after LLM polish  
- Browser-extension assisted capture: build in private fork first?

## Do not regress

- Inventing career facts  
- Shipping LinkedIn credential stuffing / session hijack  
- Letting README go vague — stay decisive  

## Session handoff template

When updating this file, keep sections above and add under **Last session**:

```
### Last session
- Date:
- Done:
- Blocked:
- Next exact task:
```

### Last session

- Date: 2026-08-18  
- Done: Decisive README/PRODUCT/AGENTS; cursor rules+skills; context system; entrep transfer notes; sources.yaml  
- Blocked: none  
- Next exact task: Profile form in Vite UI (no YAML required for happy path)  
