# Rewrite rules (anti–AI-smell)

Extracted from iterative fine-tuning across ~15 real tailored resumes.
Goal: **fit without sounding generated for that job**.

## Hard rules

1. **Same facts, different lens** — Employers, titles, dates, and education stay fixed. Only summary, skills clustering, bullet emphasis, and project framing change.
2. **Reframe ≠ invent** — Do not add metrics, stacks, or responsibilities that are not in the source profile. Prefer weaker true phrasing over strong fiction.
3. **One primary angle** — Pick one lens (ops / frontend / backend / data / gtm / sales_eng / fullstack). Blending more than one flattens voice.
4. **Keyword fit by clustering, not stuffing** — Mirror JD language inside natural skill buckets. Avoid comma-salad of every buzzword from the posting.
5. **Density over decoration** — Short bullets, concrete verbs, tools named once where they earn their place. No “passionate”, “synergy”, “leverage cutting-edge”.
6. **Tone matches audience** — PT for BR product teams; EN for global/remote. Keep the same personality: ownership, clarity, remote-ready.
7. **Title soft-align only** — Parentheticals like `(APIs & product interfaces)` are OK; renaming the official job title is not.
8. **Projects as proof** — Promote the project that best proves the angle (UI vs API vs pipelines vs ops dashboards). Demote the rest to one line or drop.
9. **Availability line is contextual** — Only when the JD cares (timezone overlap, remote %). Otherwise omit.
10. **Human unevenness** — Real CVs are slightly uneven: some roles get 3 bullets, older ones 1–2. Perfect symmetry reads as template.

## Soft signals of “AI wrote this for the JD”

Reject or regenerate if output has:

- Opening summary that paraphrases the JD paragraph-for-paragraph
- Every bullet ending with a fabricated `%` or `$` impact
- Identical sentence rhythm across all bullets
- Generic soft-skills block disconnected from tools
- “I am excited to apply…” voice inside the CV body
- Stack lists longer than ~1 line per bucket

## Order of operations (performant path)

1. Classify **angle** from JD keywords (deterministic).
2. Select **skill buckets** + **experience emphasis** for that angle.
3. Pull pre-authored bullet variants from the profile (facts tagged by angle).
4. Only then optionally call an LLM for polish — with these rules in the system prompt.
5. Render LaTeX from structured fields (no free-form whole-CV generation on every run).

This keeps the expensive part rare and reuses the corpus IP as structured data.
