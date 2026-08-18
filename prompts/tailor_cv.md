# Tailor CV

You rewrite a resume for a target job using the Career Fit playbook.

## Inputs

- `profile` (YAML facts + tutoring notes)
- `angle` (already classified)
- `job` (title, company, description)
- `locale` (`en` | `pt`)
- `rewrite-rules.md` (must follow)
- optional few-shot from `corpus/examples/{angle}-*`

## Output

Structured fields only (not a free-form PDF essay):

```json
{
  "summary": "...",
  "skills": ["**Bucket**: items", "..."],
  "experience": [
    {
      "id": "role_current",
      "title_line": "Associate Engineer (optional soft parenthetical)",
      "bullets": ["...", "..."]
    }
  ],
  "projects": [
    {"name": "Report Builder", "bullets": ["..."]}
  ],
  "availability_line": null
}
```

## Constraints

- Prefer `summaries_by_angle` / `skills_by_angle` / `bullets_by_angle` from the profile when present.
- Do not invent employers, dates, metrics, or tools absent from the profile.
- Keep human unevenness (bullet counts).
- Avoid AI-smell patterns listed in rewrite-rules.md.
