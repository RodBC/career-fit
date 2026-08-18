# AI build map — how / where / why

> **Audience:** every AI agent touching this repo.  
> **Purpose:** durable memory of *what was built*, *which files own it*, and *why that shape* — so the next agent extends the right layer instead of inventing a parallel path.  
> **Read with:** [`docs/context/CURRENT.md`](context/CURRENT.md) (live state) → this file (code archaeology) → skill matching your task.

Chat is ephemeral. This map + `CURRENT.md` + daily logs are the handoff.

---

## 1. Commit ledger (oldest → newest)

History is short and intentional. Treat each commit as a **layer**, not a random dump.

| Commit | Title | Layer introduced | Why |
|--------|-------|------------------|-----|
| `ff33743` | `feat: bootstrap Career Fit playbook and local tailor CLI` | **Core IP + CLI** | Encode multi-angle resume craft as playbook + deterministic assemble. Prove value without an API or LLM. |
| `3da2325` | `first commit` | *(noise)* | Empty/placeholder README commit; ignore for product archaeology. |
| `5f181f1` | `feat: add Vite UI, API, and recruiter paste flow` | **Distribution surface** | Expose the same core over FastAPI + Vite so a human can paste JD/recruiters without YAML CLI gymnastics. Still no scraping. |
| `f613de8` | `docs: decisive product framing and mandatory AI context loop` | **Agent operating system** | Force every AI to read/write durable SaaS state (`AGENTS.md`, `CURRENT.md`, skills, source tiers). Stop chat-only memory. |
| `f89082d` | `docs: lock ecosystem vision for career CRM and coach loop` | **North-star expansion** | Document Phase B/C (tracker + suggestions) so agents plan retention without boiling the ocean before the wedge converts. |
| *(uncommitted)* | `feat: guided profile + resume intake` | **Phase A intake** | Form + rules-first resume parse → tailor-ready profile; UI wizard before workspace. |

**Invariant across all layers:** paste/CSV intake · deterministic tailor first · user sends messages · no LinkedIn harvester in public core.

When you add a meaningful feature, **extend this ledger** in the same table (one row, commit hash after push if known).

---

## 2. Layer cake (dependency direction)

```
playbook/ + profile/ + corpus/ + prompts/     ← IP & rules (edit carefully)
        ↓
src/career_fit/{models,angle,tailor,render,outreach}   ← assemble path
        ↓
src/career_fit/{jobs,recruiters,intake}         ← paste normalizers (JD / contacts / resume)
        ↓
src/career_fit/{cli,api}                     ← entrypoints (same core)
        ↓
web/                                         ← UX only; calls API
        ↓
docs/ + AGENTS.md + .cursor/                 ← product memory & agent contract
```

**Rule:** never put angle/bullet logic in the UI. UI calls API; API calls core; core reads playbook/profile.

---

## 3. Directory map — where things live

| Path | Owns | Why it exists | Do not |
|------|------|---------------|--------|
| `playbook/angles.yaml` | Angle IDs, keywords, weights | Deterministic classify signals | Invent angles without eval cases |
| `playbook/rewrite-rules.md` | Anti-AI-smell craft | Constrains any future LLM polish | Bypass when “just generating” |
| `playbook/structure.md` | CV section shape | Keeps LaTeX/md consistent | Free-form whole-CV rewrite |
| `playbook/corpus-index.yaml` | Pointers into example corpus | Grounds craft in examples | Copy private PII from `/curriculumn` |
| `profile/schema.yaml` | Profile contract | Tags (`bullets_by_angle`, etc.) | Untagged free prose as source of truth |
| `profile/example.profile.yaml` | Safe demo profile | UI/API default when no `data/profile.yaml` | Commit real PII here |
| `data/` | Local runtime outputs + optional private profile | gitignored user data | Commit `profile.yaml` |
| `corpus/examples/` | Anonymized craft samples | Teaching + eval grounding | Treat as live user data |
| `prompts/` | Optional LLM prompt shells | Polish/interview later; not on critical path today | Call LLM from core without rules |
| `evals/cases.yaml` | Angle classify regression | Guard keyword/angle edits | Skip `career-fit eval` after angle changes |
| `src/career_fit/` | All product logic | Single Python package | Duplicate logic in `web/` |
| `web/` | Vite React tailor workspace | Human happy path for paste → artifacts | Business rules or scrapers |
| `docs/` | Product + architecture + this map | Durable decisions | Leave decisions only in chat |
| `docs/context/` | Live handoff (`CURRENT.md` + logs) | Multi-agent continuity | Delete historical log entries |
| `.cursor/rules/` + `.cursor/skills/` | Always-on + task skills | Encode conventions agents must follow | Invent conflicting one-off rules |
| `templates/` + `resume.cls` | LaTeX class assets | Render target for `.tex` | Redesign without `structure.md` |

Private corpus (not in this repo): `/home/decastro/studies/curriculumn` — LaTeX angle IP source. Import tagged facts later; never publish PII.

---

## 4. Python module map (`src/career_fit/`)

| Module | Responsibility | Key symbols | Why separate |
|--------|----------------|-------------|--------------|
| `models.py` | Shared types + YAML load + `ROOT` | `Job`, `TailoredResume`, `load_yaml` | One truth for CLI/API |
| `angle.py` | Score JD → primary angle | `classify_angle`, `load_angles` | Pure, fast, eval-friendly |
| `tailor.py` | Assemble resume from tagged profile | `tailor` | Deterministic; picks locale/summary/skills/bullets by angle |
| `render.py` | Emit markdown + LaTeX | `render_markdown`, `render_latex` | Presentation only |
| `outreach.py` | Company-level short message | `build_outreach` | One generic HM/company draft from proof |
| `jobs.py` | JD paste → fields | `parse_job_text`, `ParsedJob` | Normalize LinkedIn/Gupy/inHire **text** without fetch |
| `recruiters.py` | Contact paste/CSV → ranked drafts | `parse_contacts_*`, `score_title`, `enrich_with_messages` | People enter via user paste; title ranking is the value |
| `intake.py` | Guided form + resume text → profile | `parse_resume_text`, `build_profile_from_intake` | Rules-first; same facts on every angle until user tags; no invented employers |
| `cli.py` | argparse commands | `classify`, `tailor`, `eval`, `recruiters`, `serve`, `fit-brief` | Power-user + scripts |
| `api.py` | FastAPI on `:8787` | `/api/tailor`, `/api/intake`, … | Thin HTTP over the same functions as CLI |
| `__main__.py` | `python -m career_fit` | — | Package entry |

### Critical assemble path (do not fork)

```
Job (+ optional raw_paste)
  → jobs.parse_job_text (if paste incomplete)
  → angle.classify_angle
  → tailor.tailor(profile, job, angle)
  → render_* + outreach.build_outreach
```

Recruiter path reuses tailor for proof line, then:

```
contacts_text → parse_contacts_text|csv → enrich_with_messages → ranked Contact[]
```

Intake path (before tailor):

```
identity + career_tutoring + targets + resume_text
  → intake.build_profile_from_intake
  → profile (facts.experience[].bullets_by_angle, summaries_by_angle, …)
  → (UI) localStorage · then tailor path above
```

### HTTP surface (`api.py`) — keep thin

| Method | Path | Core call |
|--------|------|-----------|
| GET | `/api/health` | liveness |
| GET | `/api/example-profile` | load example YAML |
| POST | `/api/parse-job` | `parse_job_text` |
| POST | `/api/classify` | `classify_angle` |
| POST | `/api/tailor` | tailor + render + outreach |
| POST | `/api/recruiters` | tailor proof + recruiter enrich |
| POST | `/api/upload-profile` | YAML/JSON validate → return profile (no server persist) |
| POST | `/api/parse-resume` | `parse_resume_text` (preview) |
| POST | `/api/intake` | `build_profile_from_intake` |

CORS allows Vite `:5173` only. Adding a new capability: implement in a core module first, then expose CLI + one API route + `web/src/api.ts` helper.

---

## 5. Web map (`web/`)

| File | Role | Why |
|------|------|-----|
| `src/App.tsx` | View switch: intake ↔ tailor workspace | Steps 1–4; persists profile via `api.storeProfile` |
| `src/Intake.tsx` | Guided 5-step interview (You → Work → Targets → Resume → Review) | Progressive disclosure; calls `/api/intake`; YAML shortcut still available |
| `src/api.ts` | Typed `fetch` + `localStorage` profile helpers | No business logic; mirror API contracts |
| `src/styles.css` | Local MVP styling + intake step chrome | Extend existing calm palette |
| `vite.config.ts` | Dev server | Proxies `/api` → `:8787` |

**UI status:** Phase A intake + tailor + recruiter drafts. No applications tracker, no suggestion home — Phase B/C (`docs/ECOSYSTEM.md`). Next UI: richer resume tagging UI and/or Phase B application objects. PDF resume parse still deferred (open question).

---

## 6. Docs & agent contract map

| Doc / asset | When to read | When to write |
|-------------|--------------|---------------|
| `AGENTS.md` | Every session | When operating contract changes |
| `docs/context/CURRENT.md` | Before non-trivial work | End of meaningful session |
| `docs/context/log/YYYY-MM-DD.md` | Optional history | Append after meaningful work |
| `docs/PRODUCT.md` | Scope / pricing / moat fights | Product decision changes |
| `docs/ECOSYSTEM.md` | Tracker / coach / UX phases | Ecosystem phase shifts |
| `docs/ARCHITECTURE.md` | Build order & LinkedIn stance | Priority table changes |
| `docs/AI_BUILD_MAP.md` (this file) | Before editing code layout | After new modules/layers land |
| `docs/sources.yaml` | Any ingest/scrape idea | New source tier decisions |
| `docs/entrep-transfer.md` | “Can we steal from entrep?” | New steal/reject rows |
| `.cursor/skills/career-fit-*` | Task-matched skill | New durable convention |

### Skills → code ownership

| Skill | Edit these first |
|-------|------------------|
| `career-fit-tailor` | `playbook/*`, `angle.py`, `tailor.py`, `render.py`, `evals/`, `prompts/tailor_cv.md` |
| `career-fit-sources` | `jobs.py`, `recruiters.py`, `intake.py`, `docs/sources.yaml`, future `sources/` |
| `career-fit-product` | `PRODUCT.md`, `ECOSYSTEM.md`, `CURRENT.md` — not random features |
| `career-fit-context` | `CURRENT.md` + daily log |

---

## 7. Where to change what (cheat sheet)

| User-facing need | Edit here | Not here |
|------------------|-----------|----------|
| New resume angle | `playbook/angles.yaml` + `evals/cases.yaml` + example profile tags | Hardcoded strings in UI |
| Better anti-AI wording rules | `playbook/rewrite-rules.md` | Unconstrained LLM prompt only |
| JD paste quality (LinkedIn/Gupy) | `jobs.py` (+ later per-source notes) | Headless login scraper |
| Recruiter ranking / email extract | `recruiters.py` | LinkedIn API scrape |
| Outreach tone | `outreach.py` / `recruiters.draft_recruiter_message` | Auto-send servers |
| New API capability | core module → `api.py` → `web/src/api.ts` → `App.tsx` | UI-only duplicate of Python logic |
| Persist applications / people | **new** models + store (Phase B) — design in ARCHITECTURE/ECOSYSTEM first | Stuff into `TailoredResume` |
| Suggestion cards | Phase C engine — after tracker objects exist | Spammy home widgets before intake delight |
| Import from private corpus | profile import path / guided intake | Commit `/curriculumn` files |
| Resume text parse quality | `intake.py` | LLM inventing employers; PDF until decided |
| Intake form copy / steps | `web/src/Intake.tsx` | Duplicating assemble logic in React |

---

## 8. Explicit non-builds (already decided)

Documented so agents stop re-proposing them:

1. Automated LinkedIn profile/job harvesting in this public repo  
2. Mass DM / auto-apply from our servers  
3. Inventing employers, metrics, or tools absent from the profile  
4. Rewriting the whole CV when `bullets_by_angle` / `summaries_by_angle` exist  
5. Full CRM UI before guided intake + tailor are delightful  
6. Suggestion flood before Phase B tracker objects  

Rationale lives in `ARCHITECTURE.md` (LinkedIn) and `PRODUCT.md` / `ECOSYSTEM.md` (phasing).

---

## 9. How to extend this map (mandatory for AIs)

After you add a **new module**, **new HTTP route**, **new Phase B/C object**, or **new ingest backend**:

1. Add a row to §1 (commit ledger) and/or §4–5 tables.  
2. Update `docs/context/CURRENT.md` → What exists / Last session.  
3. Append `docs/context/log/YYYY-MM-DD.md`.  
4. If the convention is reusable, encode it in the matching `.cursor/skills/` file.

If you only polish copy inside an existing function, skip the ledger — still update CURRENT if priorities or behavior change.

---

## 10. Quick verification commands

```bash
career-fit eval              # angle regressions
career-fit serve             # API :8787
cd web && npm run dev        # UI :5173
# happy path: example profile → paste JD → Tailor → paste recruiters
```

Do not claim a layer is “done” in CURRENT without these working for the paths you touched.
