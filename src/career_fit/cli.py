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
