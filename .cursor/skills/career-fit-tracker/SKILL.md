---
name: career-fit-tracker
description: >-
  Phase B career CRM: applications, artifacts, outreach, soft Free/Pro limits,
  Today cards. Use when editing tracker.py, pipeline/Home UI, save-to-pipeline,
  or monetization gates. Triggers: pipeline, application, outreach, Today,
  Free tier, Pro, tracker, Home.
---

# Career Fit — tracker skill

## Aim

Retention + willingness to pay: **memory** (pipeline + people) before suggestion flood.

## Code ownership

| Piece | Where |
|-------|--------|
| Domain shapes + Today + limits | `src/career_fit/tracker.py` |
| HTTP | `api.py` → `/api/tracker/*` |
| Browser persist | `web/src/store.ts` (localStorage) |
| Home / Craft UI | `web/src/Home.tsx`, `Craft.tsx`, `App.tsx` shell |

## Rules

- Soft Free: 3 tailor/mo, 5 applications — Pro working price **$29/mo** (no Stripe yet)
- Human stage labels (`Ready to send`), not CRM jargon
- Today: max **3** cards; cite why; never auto-DM
- Persist locally first; server only shapes/validates records
- Update `docs/AI_BUILD_MAP.md` + `CURRENT.md` when adding tracker objects

## Do not

- Build HubSpot-scale CRM UI  
- Unlock Free limits silently without a clear Pro story  
- Auto-send messages from the server  
