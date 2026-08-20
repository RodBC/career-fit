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
- Done: Ported warm-bridge OTP parse + App Password preflight; updated account password in secrets (gitignored); docs/README/skills; commit + push Camoufox stack  
- Note: If IMAP AUTH fails, regenerate App Password while logged into the burner Gmail + enable IMAP  
- Next: Founder dogfood http://127.0.0.1:5173  
