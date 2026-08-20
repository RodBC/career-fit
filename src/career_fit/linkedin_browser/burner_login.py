"""Ops-only burner LinkedIn login + OTP bootstrap (never end-user passwords)."""

from __future__ import annotations

import time
from typing import Any

from .browser import launch_persistent, looks_like_login, new_page
from .config import SessionConfig, load_session_config, session_ready_report
from .errors import BrowserJobError
from .gmail_otp import totp_now, wait_for_linkedin_otp
from .secrets import BurnerSecrets, load_burner_secrets


def _body_lower(page: Any, n: int = 2500) -> str:
    try:
        return (page.locator("body").inner_text(timeout=4000) or "").lower()[:n]
    except Exception:  # noqa: BLE001
        return ""


def _detect_challenge(page: Any) -> str:
    """Return email_otp | totp | sms | none | captcha | bad_ creds."""
    url = (page.url or "").lower()
    head = _body_lower(page)
    if "captcha" in head or "unusual activity" in head or "security verification" in head:
        if "enter the code" in head or "verification code" in head or "pin" in head:
            return "email_otp"
        return "captcha"
    if "phone" in head and ("text" in head or "sms" in head or "mobile"):
        return "sms"
    if any(
        x in head
        for x in (
            "authenticator",
            "verification app",
            "google authenticator",
            "enter the code from your authenticator",
        )
    ):
        return "totp"
    if any(
        x in head
        for x in (
            "enter the code",
            "verification code",
            "we emailed you",
            "email you a code",
            "check your email",
            "enter the pin",
            "email verification",
        )
    ) or ("/checkpoint" in url and "challenge" in url):
        return "email_otp"
    if any(
        x in head
        for x in (
            "wrong email or password",
            "couldn’t find a linkedin account",
            "couldn't find a linkedin account",
            "that's not the right password",
            "incorrect password",
        )
    ):
        return "bad_creds"
    return "none"


def _first_visible(page: Any, selector: str):
    loc = page.locator(selector)
    n = loc.count()
    for i in range(n):
        el = loc.nth(i)
        try:
            if el.is_visible():
                return el
        except Exception:  # noqa: BLE001
            continue
    return loc.first if n else None


def _fill_credentials(page: Any, secrets: BurnerSecrets) -> None:
    time.sleep(1.0)
    email_el = _first_visible(page, "input[type='email'], #username, input[name='session_key']")
    if email_el is None:
        raise BrowserJobError("LinkedIn login: email field not found", status=503)
    email_el.click(timeout=5000, force=True)
    email_el.fill(secrets.email, timeout=5000, force=True)

    pw_el = _first_visible(page, "input[type='password'], #password, input[name='session_password']")
    if pw_el is None:
        raise BrowserJobError("LinkedIn login: password field not found", status=503)
    pw_el.click(timeout=5000, force=True)
    pw_el.fill(secrets.password, timeout=5000, force=True)

    time.sleep(0.5)
    # Exact "Entrar" / "Sign in" — not "Entrar com Apple/Microsoft"
    clicked = page.evaluate(
        """() => {
      const buttons = Array.from(document.querySelectorAll('button'));
      const b = buttons.find((x) => {
        const t = (x.innerText || '').trim().toLowerCase();
        const visible = !!(x.offsetWidth || x.offsetHeight);
        return visible && !x.disabled && (t === 'entrar' || t === 'sign in');
      });
      if (!b) return false;
      b.scrollIntoView({block: 'center'});
      b.click();
      return true;
    }"""
    )
    if not clicked:
        pw_el.press("Enter")
    time.sleep(1.5)


def _fill_otp(page: Any, code: str) -> None:
    for sel in (
        "input[name='pin']",
        "input#input__email_verification_pin",
        "input[id*='verification']",
        "input[autocomplete='one-time-code']",
        "input[type='tel']",
        "input[type='text']",
    ):
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.fill(code, timeout=5000)
                break
        except Exception:  # noqa: BLE001
            continue
    for sel in (
        "button[type='submit']",
        "button[data-id='sign-in-form__submit-btn']",
        "button.form__submit",
    ):
        try:
            loc = page.locator(sel)
            if loc.count():
                loc.first.click(timeout=5000)
                return
        except Exception:  # noqa: BLE001
            continue
    page.keyboard.press("Enter")


def _authed_url(url: str) -> bool:
    u = (url or "").lower()
    if any(x in u for x in ("/login", "/uas/", "/checkpoint", "/authwall")):
        return False
    return any(x in u for x in ("/feed", "/in/", "/jobs", "/mynetwork", "/messaging"))


def _wait_feed(page: Any, *, timeout_sec: float = 90) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if _authed_url(page.url or ""):
            return True
        time.sleep(2)
    return False


def _await_post_password(page: Any, *, timeout_sec: float = 45) -> str:
    """After password submit, wait until challenge / feed / error appears."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if _authed_url(page.url or ""):
            return "none"
        ch = _detect_challenge(page)
        if ch != "none":
            return ch
        # Still on login form — keep waiting briefly
        time.sleep(1.5)
    return _detect_challenge(page)


def bootstrap_burner_session(
    *,
    headless: bool = False,
    cfg: SessionConfig | None = None,
    secrets: BurnerSecrets | None = None,
    otp_timeout_sec: float = 120,
) -> dict[str, Any]:
    """Camoufox login + OTP → persist profile. Ops-only. Never call from public API."""
    cfg = cfg or load_session_config()
    secrets = secrets or load_burner_secrets()
    from .secrets import validate_secrets_for_bootstrap

    validate_secrets_for_bootstrap(secrets)
    before = session_ready_report(cfg)
    final_url = ""
    challenge = "none"
    logged_in = False

    with launch_persistent(cfg, headless=headless) as context:
        page = new_page(context)
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=60000)
        time.sleep(1.5)
        t0 = time.time()
        _fill_credentials(page, secrets)
        challenge = _await_post_password(page, timeout_sec=40)

        if challenge == "bad_creds":
            raise BrowserJobError(
                "LinkedIn rejected email/password — check burner secrets",
                status=503,
            )
        if challenge == "captcha":
            raise BrowserJobError(
                "LinkedIn captcha/checkpoint — re-run with: career-fit linkedin-burner-login --headed",
                status=503,
            )
        if challenge == "sms":
            raise BrowserJobError(
                "SMS 2FA is out of scope — switch burner to email OTP or authenticator",
                status=503,
            )

        if challenge == "email_otp":
            code = wait_for_linkedin_otp(
                secrets, after_ts=t0, timeout_sec=otp_timeout_sec
            )
            _fill_otp(page, code)
        elif challenge == "totp":
            if not secrets.totp_secret:
                raise BrowserJobError(
                    "Authenticator challenge but totp_secret missing in burner secrets",
                    status=503,
                )
            _fill_otp(page, totp_now(secrets.totp_secret))

        logged_in = _wait_feed(page, timeout_sec=90)
        if not logged_in:
            challenge = _await_post_password(page, timeout_sec=20)
            if challenge == "email_otp":
                code = wait_for_linkedin_otp(
                    secrets, after_ts=t0, timeout_sec=otp_timeout_sec
                )
                _fill_otp(page, code)
                logged_in = _wait_feed(page, timeout_sec=60)
            elif challenge == "totp" and secrets.totp_secret:
                _fill_otp(page, totp_now(secrets.totp_secret))
                logged_in = _wait_feed(page, timeout_sec=60)

        final_url = page.url or ""
        # Nudge cookie write
        try:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            time.sleep(2)
            final_url = page.url or final_url
            if _authed_url(final_url):
                logged_in = True
        except Exception:  # noqa: BLE001
            pass

    after = session_ready_report(cfg)
    return {
        "ok": True,
        "logged_in": logged_in,
        "challenge": challenge,
        "final_url": final_url,
        "before": before,
        "after": after,
        "hint": (
            "Burner session warm — try search-jobs / suggest-openings."
            if logged_in
            else f"Burner login incomplete (url={final_url!r}, challenge={challenge})."
        ),
    }
