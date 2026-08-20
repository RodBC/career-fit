# LinkedIn job session map (Camoufox)

Same ops pattern as sibling **warm-bridge**: you paste credentials → agent writes gitignored secrets → headless login → you only open the Career Fit UI.

```
L1 public HTTP → L2/L3 Camoufox guest (headless) → L4 warm profile → paste fallback
L5 ops: burner + Gmail IMAP App Password OTP (when LinkedIn emails a code)
```

## Credentials — paste to agent (3 fields)

| Field | What it is | What it is NOT |
|-------|------------|----------------|
| **email** | LinkedIn login (Gmail that gets OTP) | — |
| **password** | LinkedIn / Gmail **account** password | Not for IMAP |
| **gmail_app_password** | Google **App Password** (16 chars) | **Not** the normal Gmail password |

**Why App Password?** Gmail IMAP rejects normal passwords (warm-bridge / Google rule).  
Create: Google Account → Security → 2-Step Verification → App passwords → Mail.  
Also enable IMAP in Gmail settings.

Optional: `totp_secret` if the burner uses authenticator instead of email OTP.

Agent writes `data/secrets/linkedin_burner.yaml` (mode 600, gitignored) and runs:

```bash
pip install -e ".[linkedin]"
python -m camoufox fetch
career-fit linkedin-burner-login   # headless
career-fit session-status
career-fit dev                     # UI only → http://127.0.0.1:5173
```

## Product rule

Founder sees **only** Career Fit UI. Camoufox is headless (`CAREER_FIT_CAMOUFOX_HEADLESS=1` default). No password fields in the web API.

## Completeness (openings)

Title + company + `jobs/view/{id}` + non-empty JD when verified — else skip. Never invent employers.

## Policy

| Allowed | Forbidden |
|---------|-----------|
| Product burner + IMAP App Password OTP | End-user password-in-API |
| Headless Camoufox behind UI | Multi-account farm / SMS gateway |
| Job XHR intercept | Shipping “bypass 2FA” as a user feature |
