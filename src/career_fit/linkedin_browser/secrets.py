"""Load gitignored burner secrets (ops/infra only).

password          = LinkedIn login password (same mailbox login if Gmail)
gmail_app_password = Google App Password (16 alphanumeric) for IMAP OTP only
                    — NEVER the normal Gmail password (warm-bridge rule)
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..models import ROOT
from .errors import BrowserJobError

DEFAULT_SECRETS = ROOT / "data" / "secrets" / "linkedin_burner.yaml"


@dataclass
class BurnerSecrets:
    email: str
    password: str
    totp_secret: str = ""
    gmail_app_password: str = ""
    gmail_credentials_json: str = ""
    gmail_token_json: str = ""


def looks_like_gmail_app_password(raw: str) -> bool:
    """Google App Passwords are 16 alphanumeric chars (optional spaces)."""
    cleaned = (raw or "").replace(" ", "").strip()
    if len(cleaned) != 16:
        return False
    return cleaned.isalnum()


def validate_secrets_for_bootstrap(sec: BurnerSecrets) -> None:
    """Preflight — reject normal Gmail password used as IMAP secret."""
    if not sec.email or not sec.password:
        raise BrowserJobError(
            "Burner secrets need email + password (ops only)",
            status=503,
        )
    if sec.totp_secret and not sec.gmail_app_password and not sec.gmail_credentials_json:
        return
    if sec.gmail_app_password and not looks_like_gmail_app_password(sec.gmail_app_password):
        raise BrowserJobError(
            "Need Gmail App Password (16 chars), not login password. "
            "Google Account → Security → 2-Step Verification → App passwords.",
            status=503,
        )
    if not sec.gmail_app_password and not sec.gmail_credentials_json and not sec.totp_secret:
        # Allow login without OTP path if LinkedIn does not challenge — warn only via hint
        return


def load_burner_secrets(path: Path | None = None) -> BurnerSecrets:
    """Load data/secrets/linkedin_burner.yaml — never log password contents."""
    cfg_path = path or DEFAULT_SECRETS
    if not cfg_path.is_file():
        raise BrowserJobError(
            f"Burner secrets missing at {cfg_path}. Create gitignored YAML "
            "(see docs/LINKEDIN_JOB_SESSION.md). Ops only.",
            status=503,
        )
    try:
        import yaml

        data = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    except Exception as e:  # noqa: BLE001
        raise BrowserJobError(f"Could not read burner secrets: {e}", status=503) from e
    if not isinstance(data, dict):
        raise BrowserJobError("Burner secrets must be a YAML mapping", status=503)

    email = str(data.get("email") or "").strip()
    password = str(data.get("password") or "")
    if not email or not password:
        raise BrowserJobError(
            "Burner secrets need email + password (product burner only)",
            status=503,
        )

    def _abs(p: str) -> str:
        if not p:
            return ""
        path_p = Path(p)
        if path_p.is_absolute():
            return str(path_p)
        return str(ROOT / path_p)

    sec = BurnerSecrets(
        email=email,
        password=password,
        totp_secret=str(data.get("totp_secret") or "").strip(),
        gmail_app_password=str(
            data.get("gmail_app_password") or data.get("app_password") or ""
        ).replace(" ", ""),
        gmail_credentials_json=_abs(str(data.get("gmail_credentials_json") or "")),
        gmail_token_json=_abs(
            str(data.get("gmail_token_json") or "data/secrets/gmail_token.json")
        ),
    )
    return sec


def secrets_example() -> dict[str, Any]:
    return {
        "email": "you@gmail.com",
        "password": "LINKEDIN_LOGIN_PASSWORD",
        "gmail_app_password": "xxxx xxxx xxxx xxxx",
        "totp_secret": "",
    }


def write_burner_secrets(
    *,
    email: str,
    password: str,
    gmail_app_password: str = "",
    totp_secret: str = "",
    path: Path | None = None,
) -> Path:
    """Write gitignored secrets file. Never commit."""
    import yaml

    app_pw = gmail_app_password.replace(" ", "").strip()
    if app_pw and not looks_like_gmail_app_password(app_pw):
        raise BrowserJobError(
            "Need Gmail App Password (16 chars), not login password. "
            "Google Account → Security → 2-Step Verification → App passwords.",
            status=503,
        )

    cfg_path = path or DEFAULT_SECRETS
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "email": email.strip(),
        "password": password,
        "gmail_app_password": app_pw,
    }
    if totp_secret.strip():
        payload["totp_secret"] = totp_secret.strip()
    cfg_path.write_text(
        yaml.safe_dump(payload, default_flow_style=False, allow_unicode=True),
        encoding="utf-8",
    )
    try:
        cfg_path.chmod(0o600)
    except OSError:
        pass
    return cfg_path
