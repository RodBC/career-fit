# CURRENT context — Career Fit

> **AIs: read this fully before coding. Update this file before you end a session with meaningful changes.**

**Last updated:** 2026-08-18  
**Repo:** `/home/decastro/studies/career-fit` (own git, public-bound)  
**Related private corpus:** `/home/decastro/studies/curriculumn` (LaTeX source of angle IP — do not publish PII)

## Goal

Ship a profitable **career OS** SaaS. Wedge: deep profile + resume → tailored CV + decision-maker outreach. Ecosystem: track applications/people/network + suggest growth moves behind friendly UI/UX.

```
intake → tailor + reach-out → track applications/people → suggest next moves
```

Roadmap slices: see progressive plan S0–S6 (Home → pipeline → people → soft Pro → Today → craft quality).

## What exists now

- Playbook + deterministic tailor / outreach / recruiters / jobs / intake  
- **Tracker:** `tracker.py` — Application, Artifact, Outreach, Free limits, Today cards  
- API `:8787` — `/api/intake`, `/api/tracker/*`  
- UI `:5173` — shell **Home / Intake / Craft**; localStorage persistence  
- Soft Free: **3 tailor/mo**, **5 applications**; Pro working price **$29/mo** (no Stripe yet)  
- Skills: context, product, tailor, sources, **tracker**  
- Docs: `AI_BUILD_MAP.md`, PRODUCT, ECOSYSTEM, ARCHITECTURE  

## Decisions locked

| Decision | Rationale |
|----------|-----------|
| No automated LinkedIn scraper in public core | ToS, bans, fragility; wrong moat |
| Deterministic tailor before LLM | Fast, cheap, controllable |
| Manual send / manual post | Draft + track only |
| Paste-first job & recruiter intake | Same outcome without red-tier harvest |
| Context must live in git | Chat ephemeral |
| Ecosystem after wedge | Tracker before suggestion flood |
| Code archaeology in `AI_BUILD_MAP.md` | Agents extend ownership tables |
| Resume intake = rules-first text/YAML | No invented employers; PDF deferred |
| Phase B Home before angle-tagging UI | Retention/pay before craft polish |
| Pro working price **$29/mo** | Inside $19–39 band; Stripe later |
| Soft Free gates (local counters) | Teach WTP before auth/billing |
| Today max 3 cards | Calm coach; cite why |

## Active priorities (P0 → P2)

1. ~~Guided intake~~ ✅  
2. ~~App shell Home + Phase B pipeline/people~~ ✅  
3. ~~Soft Free/Pro gates + Today lite~~ ✅  
4. **P1** Per-angle bullet tagging UI (intake still mirrors facts across angles)  
5. **P1** Better JD normalizers (LinkedIn/Gupy/inHire paste)  
6. **P1** Import tagged profile from `curriculumn` (founder dogfood)  
7. **P2** Richer suggestion taxonomy (courses/posts/projects) — only after tracker habit  
8. **P2** PDF resume parse decision; optional LLM polish (no inventing facts)  
9. **Later** Real auth + Stripe; network bridges; green-tier feeds  

## Open questions

- Stripe / auth timing (after dogfood proves sticky Home loop)  
- Resume PDF: rules extract→confirm vs deferred  
- Browser-extension assisted capture: private fork first?  

## Do not regress

- Inventing career facts  
- LinkedIn harvest / auto-DM  
- HubSpot-anxiety CRM UI  
- Unlocking Free limits without a Pro story  
- Skipping `CURRENT` / `AI_BUILD_MAP` / skills updates  

### Last session

- Date: 2026-08-18  
- Done: S0 commit intake; S1–S5 lite — Home shell, tracker module/API, Save to pipeline, Log outreach, soft Free gates, Today cards, tracker skill, docs  
- Blocked: none  
- Next exact task: Per-angle bullet tagging UI (S6 craft) **or** JD paste normalizers — pick by dogfood pain  
