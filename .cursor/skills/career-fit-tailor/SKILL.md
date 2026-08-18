---
name: career-fit-tailor
description: >-
  Implements multi-angle resume tailoring without AI smell. Use when editing
  playbook, tailor/render code, LaTeX templates, evals, or prompts for CV
  rewrite. Triggers: resume, CV, LaTeX, angle, tailor, rewrite-rules.
---

# Career Fit — tailor skill

## Rules of craft

Follow `playbook/rewrite-rules.md` and `playbook/structure.md` strictly.

- Same facts, different lens  
- One primary angle  
- Prefer `bullets_by_angle` / `summaries_by_angle` over free generation  
- Human unevenness beats template symmetry  

## Code path

1. `angle.classify_angle` — deterministic  
2. `tailor.tailor` — assemble  
3. `render` — md + latex  
4. Optional LLM only via `prompts/tailor_cv.md` + rewrite rules  

Full ownership map: `docs/AI_BUILD_MAP.md` §4. 

## Evals

Run `career-fit eval` after changing keyword signals or angle definitions.
