# LinkedIn network spike — URL / content-type patterns (no secrets)

Capture via Camoufox `page.on("response")` in `linkedin_browser.intercept`.

## Likely interesting responses

| Pattern (substring) | Use |
|---------------------|-----|
| `voyager/api/jobs` | Job search / posting graph |
| `jobPosting` / `jobPostings` | Posting payloads |
| `jobsSearch` / `job-search` | Search result lists |

Prefer `content-type` containing `json`. DOM card scrape remains the fallback when intercept is thin.

## Completeness

Still require title + company + `/jobs/view/{id}` before keeping a card. Never invent.

## Out of scope

Do not document or store auth cookies, CSRF tokens, or login signatures in this repo.
