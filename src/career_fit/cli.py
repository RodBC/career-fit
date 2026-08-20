from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .angle import classify_angle
from .jobs import parse_job_text
from .models import ROOT, Job, load_yaml
from .outreach import build_outreach
from .recruiters import contacts_as_dicts, enrich_with_messages, parse_contacts_csv, parse_contacts_text
from .render import render_latex, render_markdown
from .tailor import tailor


def _resolve_profile(path: str | None) -> Path:
    if path:
        return Path(path)
    local = ROOT / "data" / "profile.yaml"
    if local.exists():
        return local
    return ROOT / "profile" / "example.profile.yaml"


def cmd_classify(args: argparse.Namespace) -> int:
    job = Job(title=args.title, company=args.company or "", description=args.description or "")
    result = classify_angle(job)
    print(json.dumps({"angle": result.angle, "score": result.score, "scores": result.scores, "rationale": result.rationale}, indent=2))
    return 0


def cmd_tailor(args: argparse.Namespace) -> int:
    profile = load_yaml(_resolve_profile(args.profile))
    job = Job(
        title=args.title,
        company=args.company or "",
        description=args.description or "",
        locale=args.locale or "en",
    )
    angle = args.angle or classify_angle(job).angle
    resume = tailor(profile, job, angle)

    out_dir = Path(args.out or ROOT / "data" / "out")
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = (args.company or angle).lower().replace(" ", "-")

    md = render_markdown(resume)
    tex = render_latex(resume)
    msg = build_outreach(profile, job, resume)

    (out_dir / f"{slug}.md").write_text(md, encoding="utf-8")
    (out_dir / f"{slug}.tex").write_text(tex, encoding="utf-8")
    (out_dir / f"{slug}-message.txt").write_text(msg, encoding="utf-8")
    meta = {"angle": angle, "locale": resume.locale, "files": [f"{slug}.md", f"{slug}.tex", f"{slug}-message.txt"]}
    (out_dir / f"{slug}.meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    print(json.dumps(meta, indent=2))
    print(f"wrote outputs to {out_dir}")
    return 0


def cmd_eval(_: argparse.Namespace) -> int:
    cases = load_yaml(ROOT / "evals" / "cases.yaml")["cases"]
    failed = 0
    for case in cases:
        if "expect_angle" not in case:
            continue
        job = Job(title=case["id"], description=case["job"])
        got = classify_angle(job).angle
        ok = got == case["expect_angle"]
        status = "PASS" if ok else "FAIL"
        print(f"{status}  {case['id']}: expected={case['expect_angle']} got={got}")
        if not ok:
            failed += 1
    print(f"\n{len([c for c in cases if 'expect_angle' in c]) - failed} passed, {failed} failed")
    return 1 if failed else 0


def cmd_fit_brief(args: argparse.Namespace) -> int:
    """Print tutoring fields relevant to matching — platform layer preview."""
    profile = load_yaml(_resolve_profile(args.profile))
    tutoring = profile.get("career_tutoring", {})
    targets = profile.get("targets", {})
    print("## Targets")
    print(yaml_dump(targets))
    print("## Enjoyed most")
    for x in tutoring.get("enjoyed_most", []):
        print(f"- {x}")
    print("## Positive differentials")
    for x in tutoring.get("positive_differentials", []):
        print(f"- {x}")
    print("## Improvement areas")
    for x in tutoring.get("improvement_areas", []):
        print(f"- {x}")
    print("## Hates doing")
    for x in tutoring.get("hates_doing", []):
        print(f"- {x}")
    print("## Challenges overcome")
    for x in tutoring.get("challenges_overcome", []):
        print(f"- {x}")
    return 0


def cmd_serve(_: argparse.Namespace) -> int:
    from .api import run

    run()
    return 0


def cmd_map_job(args: argparse.Namespace) -> int:
    from .insights import build_role_insights
    from .linkedin_browser import BrowserJobError, map_job_url, parsed_as_dict

    try:
        mapped = map_job_url(args.url, mock=True if args.mock else None)
    except BrowserJobError as e:
        print(str(e), file=sys.stderr)
        return 1
    parsed = mapped["parsed"]
    profile = None if args.no_profile else load_yaml(_resolve_profile(args.profile))
    insights = build_role_insights(
        parsed.title,
        parsed.company,
        parsed.description,
        profile=profile,
        locale=parsed.locale_hint or "en",
    )
    print(
        json.dumps(
            {"job": parsed_as_dict(parsed), "insights": insights, "meta": mapped["meta"]},
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_map_profile(args: argparse.Namespace) -> int:
    from .linkedin_browser import BrowserJobError, map_profile_url

    try:
        mapped = map_profile_url(args.url, mock=True if args.mock else None)
    except BrowserJobError as e:
        print(str(e), file=sys.stderr)
        return 1
    identity = (mapped["profile"].get("identity") or {})
    print(
        json.dumps(
            {
                "snapshot": mapped["snapshot"],
                "identity": identity,
                "meta": mapped["meta"],
                "parsed_roles": (mapped["profile"].get("intake_meta") or {}).get(
                    "parsed_roles"
                ),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_sample_pack(args: argparse.Namespace) -> int:
    """Offline dogfood: profile + role title → mock JD → insights → tailor."""
    from .api import SamplePackRequest, api_sample_pack

    profile = None if args.no_profile else load_yaml(_resolve_profile(args.profile))
    result = api_sample_pack(
        SamplePackRequest(
            profile=profile,
            role_title=args.role or "Backend Engineer",
            locale=args.locale,
        )
    )
    print(
        json.dumps(
            {
                "job": result["job"],
                "angle": result["pack"]["angle"],
                "summary": result["pack"]["summary"][:200],
                "linkedin_search_url": result["linkedin_search_url"],
                "meta": result["meta"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0


def cmd_session_status(_: argparse.Namespace) -> int:
    from .linkedin_browser import session_ready_report

    print(json.dumps(session_ready_report(), indent=2))
    return 0


def cmd_linkedin_session(_: argparse.Namespace) -> int:
    """Open Camoufox with the Career Fit profile so you can log into LinkedIn once."""
    from .linkedin_browser import BrowserJobError, run_linkedin_login_session, session_ready_report

    report = session_ready_report()
    print(json.dumps(report, indent=2))
    if not report.get("camoufox_ok"):
        print(
            "Camoufox missing. Run: pip install -e '.[linkedin]' && python -m camoufox fetch",
            file=sys.stderr,
        )
        return 1
    print(
        "\nOpening Camoufox — log into LinkedIn in that window.\n"
        "Waiting up to 5 minutes…\n"
    )
    try:
        result = run_linkedin_login_session(wait_sec=300)
    except BrowserJobError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(result.get("hint", ""))
    print(json.dumps(result.get("after") or session_ready_report(), indent=2))
    return 0 if result.get("logged_in") or (result.get("after") or {}).get("logged_in_hint") else 0


def cmd_linkedin_burner_login(args: argparse.Namespace) -> int:
    """Ops only: product burner + Gmail OTP → warm Camoufox profile (headless)."""
    from .linkedin_browser import BrowserJobError, bootstrap_burner_session

    print(
        "Ops burner login (headless) — product-owned account only.\n"
    )
    try:
        # Default headless so founder never sees Camoufox; --headed for debug
        result = bootstrap_burner_session(headless=not bool(args.headed))
    except BrowserJobError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(result.get("hint", ""))
    print(json.dumps({k: result[k] for k in ("ok", "logged_in", "challenge", "after") if k in result}, indent=2))
    return 0 if result.get("logged_in") else 1


def cmd_search_jobs(args: argparse.Namespace) -> int:
    from .linkedin_browser import BrowserJobError, search_job_openings

    try:
        result = search_job_openings(
            args.keywords,
            location=args.location or "",
            limit=args.limit,
        )
    except BrowserJobError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


def cmd_dev(_: argparse.Namespace) -> int:
    """Start API (:8787) + Vite UI (:5173) in one process group."""
    import os
    import signal
    import subprocess
    import time

    web = ROOT / "web"
    if not (web / "package.json").exists():
        print("web/package.json missing — cannot start UI", file=sys.stderr)
        return 1
    if not (web / "node_modules").exists():
        print("web/node_modules missing — run: cd web && npm i", file=sys.stderr)
        return 1

    env = os.environ.copy()
    procs: list[subprocess.Popen[bytes]] = []

    def stop(*_args: object) -> None:
        for p in procs:
            if p.poll() is None:
                p.send_signal(signal.SIGTERM)
        deadline = time.time() + 5
        for p in procs:
            remaining = max(0.0, deadline - time.time())
            try:
                p.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                p.kill()

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    print("Career Fit dev")
    print("  API  http://127.0.0.1:8787")
    print("  UI   http://127.0.0.1:5173")
    print("  Ctrl+C stops both\n")

    procs.append(
        subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "career_fit.api:app", "--host", "127.0.0.1", "--port", "8787", "--reload"],
            cwd=str(ROOT),
            env=env,
        )
    )
    procs.append(
        subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=str(web),
            env=env,
        )
    )

    try:
        while True:
            for p in procs:
                code = p.poll()
                if code is not None:
                    stop()
                    return code
            time.sleep(0.4)
    except KeyboardInterrupt:
        stop()
        return 0


def cmd_recruiters(args: argparse.Namespace) -> int:
    profile = load_yaml(_resolve_profile(args.profile))
    raw_job = Path(args.job_file).read_text(encoding="utf-8") if args.job_file else args.description or ""
    parsed = parse_job_text(raw_job) if raw_job else None
    job = Job(
        title=args.title or (parsed.title if parsed else ""),
        company=args.company or (parsed.company if parsed else ""),
        description=raw_job or args.description or "",
        locale=args.locale or "en",
    )
    angle = args.angle or classify_angle(job).angle
    resume = tailor(profile, job, angle)
    contacts_raw = Path(args.contacts).read_text(encoding="utf-8")
    if contacts_raw.lower().lstrip().startswith("name,"):
        contacts = parse_contacts_csv(contacts_raw, company=job.company)
    else:
        contacts = parse_contacts_text(contacts_raw, company=job.company)
    proof = ""
    if resume.projects and resume.projects[0].get("bullets"):
        proof = f"{resume.projects[0]['name']}: {resume.projects[0]['bullets'][0]}"
    contacts = enrich_with_messages(
        contacts,
        candidate_name=profile.get("identity", {}).get("name", ""),
        job_title=job.title,
        company=job.company or "the company",
        angle_summary=resume.summary,
        proof_line=f"One proof point — {proof}" if proof else "",
        locale=job.locale,
    )
    print(json.dumps({"angle": angle, "contacts": contacts_as_dicts(contacts)}, indent=2, ensure_ascii=False))
    return 0


def yaml_dump(obj: object) -> str:
    import yaml

    return yaml.safe_dump(obj, sort_keys=False, allow_unicode=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="career-fit", description="Career Fit CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_cls = sub.add_parser("classify", help="Classify JD → angle")
    p_cls.add_argument("--title", required=True)
    p_cls.add_argument("--company", default="")
    p_cls.add_argument("--description", default="")
    p_cls.set_defaults(func=cmd_classify)

    p_t = sub.add_parser("tailor", help="Build tailored CV + outreach from profile")
    p_t.add_argument("--title", required=True)
    p_t.add_argument("--company", default="")
    p_t.add_argument("--description", default="")
    p_t.add_argument("--locale", default=None)
    p_t.add_argument("--angle", default=None)
    p_t.add_argument("--profile", default=None)
    p_t.add_argument("--out", default=None)
    p_t.set_defaults(func=cmd_tailor)

    p_e = sub.add_parser("eval", help="Run local eval cases")
    p_e.set_defaults(func=cmd_eval)

    p_f = sub.add_parser("profile", help="Show tutoring/fit brief from profile")
    p_f.add_argument("--profile", default=None)
    p_f.set_defaults(func=cmd_fit_brief)

    p_s = sub.add_parser("serve", help="Run local API for the Vite UI (port 8787)")
    p_s.set_defaults(func=cmd_serve)

    p_d = sub.add_parser("dev", help="Start API + Vite UI together (ports 8787 + 5173)")
    p_d.set_defaults(func=cmd_dev)

    p_m = sub.add_parser("map-job", help="Job URL → session/mock JD + role insights")
    p_m.add_argument("--url", required=True, help="LinkedIn /jobs/view/… URL")
    p_m.add_argument("--mock", action="store_true", help="Use offline fixture JD")
    p_m.add_argument("--profile", default=None)
    p_m.add_argument("--no-profile", action="store_true")
    p_m.set_defaults(func=cmd_map_job)

    p_mp = sub.add_parser("map-profile", help="LinkedIn /in/ URL → light profile draft")
    p_mp.add_argument("--url", required=True, help="linkedin.com/in/you")
    p_mp.add_argument("--mock", action="store_true")
    p_mp.set_defaults(func=cmd_map_profile)

    p_sp = sub.add_parser(
        "sample-pack",
        help="Role title → mock JD + insights + tailor pack (dogfood)",
    )
    p_sp.add_argument("--role", default="Backend Engineer")
    p_sp.add_argument("--profile", default=None)
    p_sp.add_argument("--no-profile", action="store_true")
    p_sp.add_argument("--locale", default="en")
    p_sp.set_defaults(func=cmd_sample_pack)

    p_ss = sub.add_parser("session-status", help="Diagnose Camoufox / LinkedIn session")
    p_ss.set_defaults(func=cmd_session_status)

    p_ls = sub.add_parser(
        "linkedin-session",
        help="Open Camoufox profile to log into LinkedIn (manual, one-time)",
    )
    p_ls.set_defaults(func=cmd_linkedin_session)

    p_bl = sub.add_parser(
        "linkedin-burner-login",
        help="Ops: product burner + Gmail OTP → warm Camoufox profile (headless)",
    )
    p_bl.add_argument(
        "--headed",
        action="store_true",
        help="Show Camoufox window (debug only; default is headless)",
    )
    p_bl.set_defaults(func=cmd_linkedin_burner_login)

    p_sj = sub.add_parser("search-jobs", help="Live LinkedIn job search → real /jobs/view cards")
    p_sj.add_argument("--keywords", required=True)
    p_sj.add_argument("--location", default="")
    p_sj.add_argument("--limit", type=int, default=5)
    p_sj.set_defaults(func=cmd_search_jobs)

    p_r = sub.add_parser("recruiters", help="Parse pasted contacts + draft messages")
    p_r.add_argument("--contacts", required=True, help="Path to pasted profiles or CSV")
    p_r.add_argument("--title", default="")
    p_r.add_argument("--company", default="")
    p_r.add_argument("--description", default="")
    p_r.add_argument("--job-file", default=None)
    p_r.add_argument("--locale", default="en")
    p_r.add_argument("--angle", default=None)
    p_r.add_argument("--profile", default=None)
    p_r.set_defaults(func=cmd_recruiters)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
