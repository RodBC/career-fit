# Transfer from `/home/decastro/entrep` (RepHelp)

**Reviewed:** 2026-08-18  
**Stance:** Steal patterns that accelerate Career Fit. Reject anything that pulls us into red-tier scraping theater or a different product.

RepHelp is a **reputation intelligence** SaaS (Reclame Aqui–first Brazil). Career Fit is a **candidate reach-out** SaaS. Overlap is infrastructure craft, not domain.

## Steal (patterns → Career Fit)

| Entrep idea | Career Fit use | Status |
|-------------|----------------|--------|
| `sources.yaml` green/yellow/red tiers | Job & contact sources policy | Adopted → `docs/sources.yaml` |
| Decisive `PRODUCT_PLAN.md` (vision, tiers, moat, exit criteria) | Our `docs/PRODUCT.md` | Adopted |
| `BaseScraper` + `ScrapeResult` adapter shape | Future `JobSource` / `ContactSource` interfaces | Idea → feat when we add feeds |
| `SCRAPER_NOTES.md` URL patterns + blockers | `docs/JOB_SOURCE_NOTES.md` for paste/URL quirks | Idea (create when first adapter ships) |
| `compliance/sanitize.py` PII redaction | Sanitize logs / shared coach views; never leak pasted recruiter emails into public demos | Feat candidate |
| Rate limit + `looks_blocked()` helpers | Only for **green/yellow public** pages we choose to fetch | Idea |
| Cold-email “send them their own proof” wedge | Our CV quality is the proof; keep drafts human, user sends | Product lesson |
| `.agents/skills/` project skills | `.cursor/skills/` here | Adopted |

## Reject / do not port

| Entrep asset | Why reject for Career Fit |
|--------------|---------------------------|
| Google Maps / TripAdvisor / Yelp scrapers | Wrong domain; CAPTCHA war; not our loop |
| Reclame Aqui / consumidor.gov pipelines | Different SaaS |
| Residential proxy / GECKO for hostile sites | Normalizes “beat the wall” culture we refuse for LinkedIn |
| Hospitality multi-location architecture | Irrelevant |
| Streamlit dashboard stack | We already chose Vite + FastAPI |

## Creative synthesis (keep aim)

1. **Treat LinkedIn like Glassdoor in entrep’s `sources.yaml`:** `tier: red` for automated harvest — document why, move on.  
2. **Treat Gupy/inHire public job pages as yellow** — paste now; polite public fetch later if ToS allows and page is useful without login.  
3. **Build `ContactSource` adapters** the way entrep builds scrapers: one interface, many backends (paste, CSV, LinkedIn export ZIP, future extension). First backend = paste (done).  
4. **Moat discipline from RepHelp:** they chose RA because data is viable + culturally canonical. We choose **playbook quality** because scrapers are not durable advantage in recruiting.

## Feat backlog spawned from this review

- [ ] `JobSource` / `ContactSource` protocol in `src/career_fit/sources/`  
- [ ] Port a slim `redact_text` for demo mode / coach multi-tenant later  
- [ ] Per-source notes file when first HTTP adapter lands  
