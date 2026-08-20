---
name: career-fit-sources
description: >-
  Job and recruiter source policy for Career Fit. Use when adding ingest
  adapters, scrapers, LinkedIn/Gupy/inHire integrations, or contact parsers.
  Triggers: scrape, LinkedIn, Gupy, inHire, recruiter, JobSource, sources.yaml,
  map-job, camoufox, selenium, burner, gmail, otp.
---

# Career Fit — sources skill

## Policy

Read `docs/sources.yaml` and `docs/LINKEDIN_JOB_SESSION.md`.  
Sibling pattern: `/home/decastro/studies/warm-bridge` (Camoufox burner + IMAP App Password).

| Tier | Meaning | Action |
|------|---------|--------|
| green | User-owned / official / URL normalize | Build freely |
| yellow | Camoufox guest / warm profile / ops burner | Primary browser path; rate-limit |
| red | Multi-account farm / password-in-API / invent JD | Do not ship |

**Primary intake:** `job_url_public_fetch` then Camoufox guest (`linkedin_browser`).  
Ops burner OTP uses **Gmail App Password (16 chars)** for IMAP — never the normal Gmail login password.

## Secrets fields (gitignored)

| Key | Meaning |
|-----|---------|
| `password` | LinkedIn account password |
| `gmail_app_password` | Google App Password for IMAP OTP only |

## Preferred architecture

```python
map_job_url(url) → parse_job_text → build_role_insights → tailor
# live: pip install -e ".[linkedin]" && python -m camoufox fetch
```

Module: `career_fit.linkedin_browser`. Shim: `career_fit.linkedin_selenium`.  
Never invent JD text. Empty/fail → 400/503 + paste fallback.

## Recruiter messaging

`recruiters.py`: emails from **provided** text only. User sends.
