# CURRENT context — Career Fit

> **AIs: read this fully before coding. Update this file before you end a session with meaningful changes.**

**Last updated:** 2026-08-18  
**Repo:** `/home/decastro/studies/career-fit` (own git, public-bound)  
**Related private corpus:** `/home/decastro/studies/curriculumn` (LaTeX source of angle IP — do not publish PII)

## Goal

Ship a profitable **career OS** SaaS. Wedge: deep profile + resume → tailored CV + decision-maker outreach. Ecosystem: track applications/people/network + suggest growth moves (courses, posts, projects, hackathons, contacts) behind friendly UI/UX.

```
intake (profile + resume)
  → tailor + reach-out
  → track jobs / recruiters / network
  → suggest next growth actions
```

See `docs/ECOSYSTEM.md` for the full end-state; do not boil the ocean before the wedge converts.

## What exists now

- Playbook: `playbook/angles.yaml`, `rewrite-rules.md`, `structure.md`  
- Core Python: classify / tailor / render / outreach / recruiters / jobs / **intake**  
- API: FastAPI on `:8787` — includes `/api/intake`, `/api/parse-resume`  
- UI: Vite React on `:5173` — **guided intake wizard** + tailor workspace  
- AI contract: `AGENTS.md`, `.cursor/rules/`, `.cursor/skills/`  
- Product docs: `PRODUCT.md`, `ECOSYSTEM.md`, `entrep-transfer.md`, `sources.yaml`  
- **Code archaeology for AIs:** `docs/AI_BUILD_MAP.md` (commit layers, module map, where-to-edit)

## Decisions locked

| Decision | Rationale |
|----------|-----------|
| No automated LinkedIn scraper in public core | ToS, bans, fragility; wrong moat |
| Deterministic tailor before LLM | Fast, cheap, controllable; LLM is polish |
| Manual send / manual post | Draft + track only; no spam automation |
| Paste-first job & recruiter intake | Same user outcome without red-tier harvesting |
| Context must live in git | Chat is ephemeral; SaaS iteration needs memory |
| Ecosystem after wedge | Tracker (B) before suggestion flood (C); UX stays calm |
| Code archaeology in `AI_BUILD_MAP.md` | Agents extend ownership tables when adding layers — not chat archaeology |
| Resume intake = rules-first text/YAML | No invented employers; PDF deferred |

## Active priorities (P0 → P2)

1. **P0** ~~Guided intake in UI~~ ✅ (form + resume paste; localStorage profile)  
2. **P0** Keep context/skills discipline as default agent behavior  
3. **P1** Import tagged profile from `curriculumn` corpus  
4. **P1** Better JD normalizers (LinkedIn/Gupy/inHire paste)  
5. **P1** Applications + outreach tracker (Phase B objects)  
6. **P1** Per-angle bullet tagging UI (intake currently copies facts to all angles)  
7. **P2** Suggestion cards from profile gaps (Phase C)  
8. **P2** Optional LLM polish + interview prep; PDF resume parse decision  
9. **Later** Network bridges; green-tier feeds; browser-assisted capture  

## Open questions

- Pricing exact numbers (Pro band $19–39 draft)  
- Resume parse: keep rules-first vs add optional LLM for PDF/messy pastes (still no inventing facts)  
- Browser-extension assisted capture: private fork first?  
- How aggressive should “Today” suggestions be (cap at 3?)  

## Do not regress

- Inventing career facts  
- Shipping LinkedIn credential stuffing / session hijack  
- Auto-DM or auto-LinkedIn-post  
- Vague README — stay decisive  
- Building full CRM UI before intake + tailor are delightful  

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
- Done: Guided intake — `intake.py`, `/api/intake` + `/api/parse-resume`, `Intake.tsx` wizard (5 steps), localStorage profile, AI_BUILD_MAP §4–5 updated  
- Blocked: PDF resume parse deferred  
- Next exact task: Phase B applications + outreach tracker objects (or per-angle tagging UI if wedge quality needs it first)  
