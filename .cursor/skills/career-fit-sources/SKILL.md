---
name: career-fit-sources
description: >-
  Job and recruiter source policy for Career Fit. Use when adding ingest
  adapters, scrapers, LinkedIn/Gupy/inHire integrations, or contact parsers.
  Triggers: scrape, LinkedIn, Gupy, inHire, recruiter, JobSource, sources.yaml.
---

# Career Fit — sources skill

## Policy

Read `docs/sources.yaml` and `docs/entrep-transfer.md`.

| Tier | Meaning | Action |
|------|---------|--------|
| green | User-owned or official | Build freely |
| yellow | Public cautious | Paste first; HTTP later with rate limits + block detection |
| red | ToS-hostile / fragile | Do not ship in public core |

LinkedIn automated scrape = **red**.

## Preferred architecture (from entrep, adapted)

```python
# Conceptual — implement when adding feeds
class ContactSource(Protocol):
    def fetch(self, company: str) -> list[Contact]: ...
```

Backends: `PasteSource` (done), `CsvSource` (done), later `LinkedInExportSource`, `BrowserAssistSource`.

Ownership of `jobs.py` / `recruiters.py`: `docs/AI_BUILD_MAP.md` §4.

## Recruiter messaging

Use `recruiters.py`: score titles, extract emails from **provided** text only, draft per-contact messages. User sends.
