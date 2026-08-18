---
name: career-fit-context
description: >-
  Reads and updates Career Fit durable context (docs/context/CURRENT.md and daily
  logs). Use at session start/end, after product decisions, architecture changes,
  or whenever another AI must inherit state. Triggers: context, CURRENT.md,
  handoff, session log, AGENTS.md.
---

# Career Fit — context skill

## At session start

1. Open and read `docs/context/CURRENT.md`  
2. If the task touches code (modules, API, UI, playbook wiring), also read `docs/AI_BUILD_MAP.md`  
3. If the task is product/roadmap, also read `docs/PRODUCT.md`  
4. If the task is systems/ingest, also read `docs/ARCHITECTURE.md` and `docs/entrep-transfer.md`  

## During work

- When you make a decision that should outlive chat, write it immediately into CURRENT (Decisions locked or Open questions).  
- Do not rely on “I’ll remember.”

## At session end (or after a meaningful commit)

1. Update **Last updated** date on `docs/context/CURRENT.md`  
2. Refresh **What exists now** / **Active priorities** if changed  
3. Fill **Last session** (Done / Blocked / Next exact task)  
4. If modules/routes/layers changed, update `docs/AI_BUILD_MAP.md`  
5. Append a bullet list to `docs/context/log/YYYY-MM-DD.md` (create file if needed):

```markdown
## HH:MM — short title
- Done: …
- Decisions: …
- Next: …
```

## Never

- Delete historical log entries  
- Store secrets or real `data/profile.yaml` PII in context docs  
