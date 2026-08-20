# CURRENT context — Career Fit

> **AIs: read this fully before coding. Update this file before you end a session with meaningful changes.**

**Last updated:** 2026-08-20  
**Repo:** `/home/decastro/studies/career-fit`  
**Sibling:** `/home/decastro/studies/warm-bridge` (Camoufox burner + IMAP App Password OTP — same pattern)

## Goal

```
LinkedIn URL → roles → job cards → tailor & save → message → Home
```

Founder sees **only Career Fit UI**. Camoufox headless. Credentials = paste to agent.

## What exists now

- `linkedin_browser`: public HTTP → guest Camoufox → warm profile → ops burner  
- Job URL mapping requires verified title + company + full JD; incomplete reads fall through instead of reaching the UI as false successes
- Burner login (PT “Entrar”, exact button match) + IMAP App Password OTP (warm-bridge port)  
- Secrets: `password` = LinkedIn/Gmail account login; `gmail_app_password` = 16-char App Password only  
- Live search verified with warm session; Intake does not open LinkedIn tabs  

## Decisions locked

| Decision | Rationale |
|----------|-----------|
| Guest-first, burner = ops infra | Least friction / no end-user passwords |
| IMAP App Password ≠ Gmail login password | Google IMAP AUTH (warm-bridge) |
| Headless product path | Founder only sees Career Fit UI |
| Never invent employers | Trust |

## Active priorities

1. **P0** Dogfood UI E2E with warm session  
2. **P1** Harden guest parsers / openings completeness  
3. **Later** Pro / Stripe  

### Last session

- Date: 2026-08-20  
- Done: Fixed Job URL false-success path and moved the destructive workspace reset beside the logo as an explicit “Clear all data” action with confirmation
- Note: A cold LinkedIn session can still require a public URL or burner login, but it now returns an accurate extraction error instead of a missing-company UI error
- Next: Founder dogfood a real public `jobs/view` URL, then harden any newly observed DOM variant
