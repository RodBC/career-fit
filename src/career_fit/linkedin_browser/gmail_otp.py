"""Gmail OTP for LinkedIn email 2FA — IMAP App Password first (warm-bridge pattern)."""

from __future__ import annotations

import base64
import email
import imaplib
import time
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

from .errors import BrowserJobError
from .otp_parse import extract_otp
from .secrets import BurnerSecrets

_GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
_QUERY = "from:(linkedin.com OR security-noreply@linkedin.com) newer_than:1d"
_IMAP_HOST = "imap.gmail.com"


def _imap_auth_error_message(exc: BaseException) -> str:
    low = str(exc).lower()
    if any(
        x in low
        for x in (
            "authenticationfailed",
            "invalid credentials",
            "login failed",
            "auth failed",
            "application-specific password",
        )
    ):
        return (
            "Gmail IMAP AUTH failed — need App Password (16 chars), "
            "not normal Gmail password. "
            "Google Account → Security → 2-Step Verification → App passwords. "
            "Also enable IMAP in Gmail settings."
        )
    return f"Gmail IMAP failed: {exc}"


def _imap_search_otp(secrets: BurnerSecrets, *, after_ts: float) -> str | None:
    if not secrets.gmail_app_password:
        return None
    try:
        conn = imaplib.IMAP4_SSL(_IMAP_HOST)
        conn.login(secrets.email, secrets.gmail_app_password)
        conn.select("INBOX")
        typ, data = conn.search(None, '(FROM "linkedin.com")')
        if typ != "OK" or not data or not data[0]:
            conn.logout()
            return None
        for mid in reversed(data[0].split()[-15:]):
            typ, msg_data = conn.fetch(mid, "(RFC822)")
            if typ != "OK" or not msg_data or not msg_data[0]:
                continue
            raw = msg_data[0][1]
            if not isinstance(raw, (bytes, bytearray)):
                continue
            msg = email.message_from_bytes(raw)
            try:
                dt = parsedate_to_datetime(msg.get("Date", ""))
                if dt and dt.timestamp() < after_ts - 5:
                    continue
            except Exception:  # noqa: BLE001
                pass
            chunks: list[str] = [str(msg.get("Subject") or "")]
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() in ("text/plain", "text/html"):
                        try:
                            payload = part.get_payload(decode=True) or b""
                            chunks.append(payload.decode("utf-8", errors="replace"))
                        except Exception:  # noqa: BLE001
                            continue
            else:
                try:
                    payload = msg.get_payload(decode=True) or b""
                    chunks.append(payload.decode("utf-8", errors="replace"))
                except Exception:  # noqa: BLE001
                    pass
            code = extract_otp("\n".join(chunks))
            if code:
                conn.logout()
                return code
        conn.logout()
    except imaplib.IMAP4.error as exc:
        raise BrowserJobError(_imap_auth_error_message(exc), status=503) from exc
    except BrowserJobError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise BrowserJobError(_imap_auth_error_message(exc), status=503) from exc
    return None


def _gmail_service(secrets: BurnerSecrets) -> Any:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as e:
        raise BrowserJobError(
            "Gmail API deps missing — pip install -e '.[linkedin]'",
            status=503,
        ) from e

    creds_path = Path(secrets.gmail_credentials_json)
    token_path = Path(secrets.gmail_token_json)
    if not creds_path.is_file():
        raise BrowserJobError(
            f"Gmail OAuth client JSON missing: {creds_path}",
            status=503,
        )

    creds = None
    if token_path.is_file():
        creds = Credentials.from_authorized_user_file(str(token_path), _GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(creds_path), _GMAIL_SCOPES
            )
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def _message_body_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []

    def walk(node: dict[str, Any]) -> None:
        body = node.get("body") or {}
        data = body.get("data")
        if data:
            try:
                raw = base64.urlsafe_b64decode(data + "==")
                parts.append(raw.decode("utf-8", errors="replace"))
            except Exception:  # noqa: BLE001
                pass
        for child in node.get("parts") or []:
            if isinstance(child, dict):
                walk(child)

    walk(payload)
    headers = {
        h.get("name", "").lower(): h.get("value", "")
        for h in (payload.get("headers") or [])
        if isinstance(h, dict)
    }
    return headers.get("subject", "") + "\n" + "\n".join(parts)


def _api_search_otp(secrets: BurnerSecrets, *, after_ts: float) -> str | None:
    if not secrets.gmail_credentials_json:
        return None
    service = _gmail_service(secrets)
    after_ms = int(after_ts * 1000)
    listed = (
        service.users()
        .messages()
        .list(userId="me", q=_QUERY, maxResults=10)
        .execute()
    )
    for meta in listed.get("messages") or []:
        mid = meta.get("id") or ""
        if not mid:
            continue
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=mid, format="full")
            .execute()
        )
        if int(msg.get("internalDate") or 0) < after_ms - 2000:
            continue
        code = extract_otp(_message_body_text(msg.get("payload") or {}))
        if code:
            return code
    return None


def wait_for_linkedin_otp(
    secrets: BurnerSecrets,
    *,
    after_ts: float,
    timeout_sec: float = 120,
    poll_sec: float = 4.0,
) -> str:
    """Poll Gmail (IMAP App Password preferred) for LinkedIn OTP."""
    if not secrets.gmail_app_password and not secrets.gmail_credentials_json:
        raise BrowserJobError(
            "Need gmail_app_password (16-char App Password) or Gmail OAuth in burner secrets",
            status=503,
        )
    deadline = time.time() + max(15.0, timeout_sec)
    while time.time() < deadline:
        code = _imap_search_otp(secrets, after_ts=after_ts)
        if code:
            return code
        if secrets.gmail_credentials_json:
            try:
                code = _api_search_otp(secrets, after_ts=after_ts)
                if code:
                    return code
            except BrowserJobError:
                if not secrets.gmail_app_password:
                    raise
        time.sleep(max(2.0, poll_sec))

    raise BrowserJobError(
        f"Timed out waiting for LinkedIn OTP ({timeout_sec:.0f}s). "
        "Email may not have arrived, or IMAP App Password is wrong.",
        status=503,
    )


def totp_now(secret: str) -> str:
    try:
        import pyotp
    except ImportError as e:
        raise BrowserJobError(
            "pyotp missing — pip install -e '.[linkedin]'",
            status=503,
        ) from e
    return pyotp.TOTP(secret.replace(" ", "")).now()
