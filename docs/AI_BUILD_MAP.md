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
| `92c8048` | `feat: guided profile intake and AI build map` | **Phase A intake** | Form + rules-first resume parse → tailor-ready profile; `AI_BUILD_MAP` for agents. |
| `ec9cfcd` | `feat: Home shell, pipeline tracker, and soft Pro gates` | **Phase B + soft monetization** | App shell Home/Intake/Craft; applications/outreach localStorage; Today cards; Free limits; Pro $29. |
| *(pending)* | `feat: job URL session map + role insights` | **Warm Bridge-aligned intake** | Yellow LinkedIn session primary for job URLs; Craft URL-first; insights before tailor; paste fallback. |
| *(pending)* | `feat: journey sample pack + dogfood harden` | **Minimum-input loop** | Live→mock Start CTA; roles → `/api/sample-pack` into Craft; session yaml + Fresh always on. |
| *(pending)* | `feat: in-product LinkedIn session unlock + wedge aha` | **Sticky real-data wedge** | Start session banner + `/api/linkedin-session`; paste-first when empty; Craft message-first + Today send outreach. |
| `a10c619` | `feat: Camoufox LinkedIn browser + burner OTP` | **Camoufox stack** | Replace Selenium; guest-first + XHR intercept; ops burner + Gmail IMAP App Password OTP (warm-bridge-aligned); `linkedin_browser` owns ingest. |

**Invariant across all layers:** user-chosen URLs via **session** (yellow) or paste/CSV · deterministic tailor first · user sends messages · no red-tier mass harvest.

When you add a meaningful feature, **extend this ledger** in the same table (one row, commit hash after push if known).

---

## 2. Layer cake (dependency direction)

```
playbook/ + profile/ + corpus/ + prompts/     ← IP & rules (edit carefully)
        ↓
src/career_fit/{models,angle,tailor,render,outreach}   ← assemble path
        ↓
src/career_fit/{jobs,recruiters,intake,tracker,insights,linkedin_browser}  ← paste + Camoufox map + CRM
        ↓
src/career_fit/{cli,api}                     ← entrypoints (same core)
        ↓
web/ (Home · Intake · Craft)                 ← UX only; localStorage persist
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
| `jobs.py` | JD paste → fields + mapped-job completeness | `parse_job_text`, `is_complete_job`, `ParsedJob` | Normalize LinkedIn/Gupy/inHire **text** without fetch; never accept a URL result missing title/company/JD |
| `linkedin_browser/` | Job URL → JD via Camoufox (guest → warm → ops burner) | `map_job_url`, `fetch_*`, `bootstrap_burner_session` | Warm Bridge yellow; never invent JD; no end-user passwords |
| `linkedin_selenium/` | Shim re-export of `linkedin_browser` | same public API | Back-compat only |
| `suggest_roles.py` | Role cards from path → LinkedIn search URLs | `suggest_roles_from_profile`, `linkedin_jobs_search` | Yes/no targeting without inventing jobs |
| `recruiters.py` | Contact paste/CSV → ranked drafts | `parse_contacts_*`, `score_title`, `enrich_with_messages` | People enter via user paste; title ranking is the value |
| `intake.py` | Guided form + resume text → profile | `parse_resume_text`, `build_profile_from_intake` | Rules-first; same facts on every angle until user tags; no invented employers |
| `tracker.py` | Applications, artifacts, outreach, limits, Today | `build_application_from_tailor`, `generate_today_cards`, `limits_payload` | Retention + soft Free/Pro; local-first shapes |
| `cli.py` | argparse commands | `classify`, `tailor`, `eval`, `recruiters`, `map-job`, `serve`, `dev`, `fit-brief` | Power-user + scripts |
| `api.py` | FastAPI on `:8787` | `/api/tailor`, `/api/map-job`, `/api/intake`, … | Thin HTTP over the same functions as CLI |
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
| GET | `/api/session-status` | Chrome / LinkedIn session diagnose |
| POST | `/api/linkedin-session` | Open Chrome login (blocks ≤5 min) |
| POST | `/api/map-job` | `map_job_url` + `build_role_insights` |
| POST | `/api/map-profile` | `map_profile_url` (live / mock / stub) + `suggested_roles` |
| POST | `/api/suggest-openings` | live LinkedIn job cards (skip incomplete) |
| POST | `/api/sample-pack` | mock JD for role title → insights → tailor pack |
| POST | `/api/job-insights` | `build_role_insights` (paste path) |
| POST | `/api/classify` | `classify_angle` |
| POST | `/api/tailor` | tailor + render + outreach |
| POST | `/api/recruiters` | tailor proof + recruiter enrich |
| POST | `/api/upload-profile` | YAML/JSON validate → return profile (no server persist) |
| POST | `/api/parse-resume` | `parse_resume_text` (preview) |
| POST | `/api/intake` | `build_profile_from_intake` |
| GET | `/api/tracker/limits` | Free caps + Pro $29 blurb + stages |
| POST | `/api/tracker/save-application` | Application + Artifact bundle |
| POST | `/api/tracker/log-outreach` | Outreach record (+ company→app match) |
| POST | `/api/tracker/today` | Max 3 Today cards |

CORS allows Vite `:5173` only. Adding a new capability: implement in a core module first, then expose CLI + one API route + `web/src/api.ts` helper.

---

## 5. Web map (`web/`)

| File | Role | Why |
|------|------|-----|
| `src/App.tsx` | Shell: nav Home / Start / Craft / Fresh | Returning users → Home; fresh → Start; Fresh always visible |
| `src/Home.tsx` | Pipeline + People + Today + Pro panel | Retention surface; calm, brand-forward |
| `src/Intake.tsx` | You → roles → **paste JD** → tailor confirm | No LinkedIn login on happy path |
| `src/Craft.tsx` | Job + insights + tailor; message-first after save | Aha = company message to send; recruiters collapsed |
| `src/store.ts` | localStorage profile/apps/artifacts/outreach/usage | Client persist until real backend |
| `src/api.ts` | Typed `fetch` to `:8787` | Thin; no business rules |
| `src/styles.css` | Calm teal/ink + Fraunces display | Extend; don’t purple-slop |
| `vite.config.ts` | Dev server | Proxies `/api` → `:8787` |

**UI status:** Phase A intake + Phase B Home/pipeline/people + soft Free gates + Today lite. Next: per-angle tagging, JD normalizers, real auth/billing later.

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
| `career-fit-tracker` | `tracker.py`, `store.ts`, `Home.tsx`, `Craft.tsx`, Free/Pro gates |
| `career-fit-product` | `PRODUCT.md`, `ECOSYSTEM.md`, `CURRENT.md` — not random features |
| `career-fit-context` | `CURRENT.md` + daily log |

---

## 7. Where to change what (cheat sheet)

| User-facing need | Edit here | Not here |
|------------------|-----------|----------|
| New resume angle | `playbook/angles.yaml` + `evals/cases.yaml` + example profile tags | Hardcoded strings in UI |
| Better anti-AI wording rules | `playbook/rewrite-rules.md` | Unconstrained LLM prompt only |
| JD paste quality (LinkedIn/Gupy) | `jobs.py` (+ later per-source notes) | Inventing missing JD sections |
| Job URL session map | `linkedin_selenium/` + Craft Map role | Red mass harvest / password-in-API |
| Role insights bullets | `insights.py` | Skipping to tailor with no why |
| Recruiter ranking / email extract | `recruiters.py` | LinkedIn API scrape |
| Outreach tone | `outreach.py` / `recruiters.draft_recruiter_message` | Auto-send servers |
| New API capability | core module → `api.py` → `web/src/api.ts` → `App.tsx` | UI-only duplicate of Python logic |
| Persist applications / people | **new** models + store (Phase B) — design in ARCHITECTURE/ECOSYSTEM first | Stuff into `TailoredResume` |
| Suggestion cards | Phase C engine — after tracker objects exist | Spammy home widgets before intake delight |
| Import from private corpus | profile import path / guided intake | Commit `/curriculumn` files |
| Resume text parse quality | `intake.py` | LLM inventing employers; PDF until decided |
| Intake form copy / steps | `web/src/Intake.tsx` | Duplicating assemble logic in React |
| Pipeline / outreach / Today / Free caps | `tracker.py` + `store.ts` + `Home.tsx`/`Craft.tsx` | HubSpot-scale CRM; Stripe before sticky loop |

---

## 8. Explicit non-builds (already decided)

Documented so agents stop re-proposing them:

1. Multi-account / password-in-API LinkedIn mass harvest (red) — session URL map is allowed yellow  
2. Mass DM / auto-apply from our servers  
3. Inventing employers, metrics, or tools absent from the profile  
4. Rewriting the whole CV when `bullets_by_angle` / `summaries_by_angle` exist  
5. Full CRM UI before guided intake + tailor are delightful  
6. Suggestion flood before Phase B tracker objects  

Rationale lives in `ARCHITECTURE.md` (session vs red) and `PRODUCT.md` / `ECOSYSTEM.md` (phasing).

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
career-fit map-job --url 'https://www.linkedin.com/jobs/view/1' --mock
python -m pytest -q          # parser + source fallback regressions
career-fit dev               # API :8787 + UI :5173 together
# happy path: Use mock JD → Role insights → Generate → Save to pipeline
```

Do not claim a layer is “done” in CURRENT without these working for the paths you touched.
