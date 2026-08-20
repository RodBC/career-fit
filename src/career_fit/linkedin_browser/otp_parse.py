"""Extract 6-digit LinkedIn OTP from email subject/body (PT/EN) — warm-bridge port."""

from __future__ import annotations

import re

_OTP_RE = re.compile(r"\b(\d{6})\b")
_OTP_PATTERNS = [
    re.compile(r"(?:code|código|verification|verificação)[^\d]{0,40}(\d{6})", re.I),
    re.compile(r"(\d{6})[^\d]{0,20}(?:LinkedIn|linkedin)", re.I),
    _OTP_RE,
]


def _looks_like_year(code: str) -> bool:
    if not (code.startswith("20") and code.isdigit()):
        return False
    try:
        return int(code) > 200000
    except ValueError:
        return False


def pick_code(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    for pat in _OTP_PATTERNS:
        for m in pat.finditer(raw):
            code = m.group(1)
            if len(code) == 6 and code.isdigit() and not _looks_like_year(code):
                return code
    return None


def extract_otp(text: str) -> str | None:
    return pick_code(text)
