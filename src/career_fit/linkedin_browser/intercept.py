"""Capture LinkedIn SPA job JSON via page.on('response')."""

from __future__ import annotations

import json
import re
from typing import Any

_JOB_VIEW_RE = re.compile(r"linkedin\.com/jobs/view/(\d+)", re.I)
_INTERESTING = re.compile(
    r"(jobPosting|job-search|jobsSearch|voyager/api/jobs|jobPostings)",
    re.I,
)


def attach_job_intercept(page: Any) -> list[dict[str, Any]]:
    """Register response listener; returns a mutable list of captured payloads."""
    captured: list[dict[str, Any]] = []

    def _on_response(response: Any) -> None:
        try:
            url = response.url or ""
            if not _INTERESTING.search(url):
                return
            ctype = (response.headers or {}).get("content-type", "")
            if "json" not in ctype.lower() and "javascript" not in ctype.lower():
                # Still try — LinkedIn sometimes omits useful content-type
                if "voyager" not in url and "job" not in url.lower():
                    return
            body = response.text()
            if not body or len(body) < 20:
                return
            data = json.loads(body)
            captured.append({"url": url, "data": data})
        except Exception:  # noqa: BLE001
            return

    page.on("response", _on_response)
    return captured


def openings_from_intercept(
    captured: list[dict[str, Any]],
    *,
    limit: int = 8,
) -> list[dict[str, str]]:
    """Best-effort extract title/company/view-url from intercepted JSON."""
    out: list[dict[str, str]] = []
    seen: set[str] = set()

    def _walk(obj: Any) -> None:
        if len(out) >= limit:
            return
        if isinstance(obj, dict):
            title = str(
                obj.get("title")
                or obj.get("jobPostingTitle")
                or obj.get("normalizedTitle")
                or ""
            ).strip()
            company = ""
            company_details = obj.get("companyDetails") or obj.get("company") or {}
            if isinstance(company_details, dict):
                company = str(
                    company_details.get("name")
                    or company_details.get("companyName")
                    or ""
                ).strip()
            if not company:
                company = str(
                    obj.get("companyName") or obj.get("secondaryDescription") or ""
                ).strip()
            jid = str(
                obj.get("jobPostingId")
                or obj.get("entityUrn")
                or obj.get("jobId")
                or ""
            )
            m = re.search(r"(\d{8,})", str(jid))
            if not m:
                for key in ("jobPostingUrl", "url", "navigationUrl", "*elements"):
                    val = obj.get(key)
                    if isinstance(val, str):
                        vm = _JOB_VIEW_RE.search(val)
                        if vm:
                            m = vm
                            break
            if title and company and m:
                jid_s = m.group(1)
                if jid_s not in seen:
                    seen.add(jid_s)
                    out.append(
                        {
                            "id": jid_s,
                            "title": title[:120],
                            "company": company.split("\n")[0][:100],
                            "linkedin_url": f"https://www.linkedin.com/jobs/view/{jid_s}",
                        }
                    )
            for v in obj.values():
                _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    for item in captured:
        _walk(item.get("data"))
        if len(out) >= limit:
            break
    return out[:limit]
