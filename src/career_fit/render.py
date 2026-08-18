from __future__ import annotations

from .models import SECTION_LABELS, TailoredResume


def _esc(text: str) -> str:
    """Minimal LaTeX escaping for common characters."""
    repl = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    out = []
    for ch in text:
        out.append(repl.get(ch, ch))
    return "".join(out)


def render_markdown(resume: TailoredResume) -> str:
    labels = SECTION_LABELS.get(resume.locale, SECTION_LABELS["en"])
    idn = resume.identity
    lines: list[str] = []
    lines.append(f"# {idn.get('name', '')}")
    contact = " | ".join(
        x
        for x in [
            idn.get("city"),
            idn.get("phone"),
            idn.get("email"),
            idn.get("linkedin"),
        ]
        if x
    )
    lines.append(contact)
    lines.append("")
    lines.append(f"## {labels['summary']}")
    lines.append(resume.summary)
    lines.append("")
    lines.append(f"## {labels['skills']}")
    for s in resume.skills:
        lines.append(f"- {s}")
    lines.append("")
    lines.append(f"## {labels['experience']}")
    for role in resume.experience:
        end = "Present" if role["end"] == "present" and resume.locale == "en" else (
            "atual" if role["end"] == "present" else role["end"]
        )
        lines.append(f"### {role['title']} — {role['company']} ({role['start']} – {end})")
        if role.get("location"):
            lines.append(f"*{role['location']}*")
        for b in role["bullets"]:
            lines.append(f"- {b}")
        lines.append("")
    if resume.projects:
        lines.append(f"## {labels['projects']}")
        for p in resume.projects:
            lines.append(f"### {p['name']}")
            for b in p["bullets"]:
                lines.append(f"- {b}")
            lines.append("")
    lines.append(f"## {labels['education']}")
    for edu in resume.education:
        lines.append(f"- **{edu.get('degree', '')}**, {edu.get('school', '')} ({edu.get('dates', '')})")
    if resume.languages:
        lines.append(f"- **Languages**: {', '.join(resume.languages)}")
    if resume.certifications:
        lines.append(f"- **Certifications**: {', '.join(resume.certifications)}")
    if resume.availability_line:
        lines.append(f"- {resume.availability_line}")
    lines.append("")
    lines.append(f"_angle: {resume.angle}_")
    return "\n".join(lines)


def render_latex(resume: TailoredResume) -> str:
    """Compact LaTeX matching the corpus skeleton (uses resume.cls)."""
    labels = SECTION_LABELS.get(resume.locale, SECTION_LABELS["en"])
    idn = resume.identity
    name = _esc(idn.get("name", ""))
    city = _esc(idn.get("city", ""))
    phone = _esc(idn.get("phone", ""))
    email = idn.get("email", "")
    linkedin = idn.get("linkedin", "")
    linkedin_url = linkedin if linkedin.startswith("http") else f"https://www.{linkedin}"

    parts: list[str] = []
    parts.append(r"\documentclass{resume}")
    parts.append(r"\usepackage[left=0.4in,top=0.32in,right=0.4in,bottom=0.32in]{geometry}")
    parts.append(r"\usepackage[final]{microtype}")
    parts.append(r"\usepackage{enumitem}")
    parts.append(r"\usepackage[hidelinks]{hyperref}")
    parts.append(r"\renewcommand{\baselinestretch}{0.92}")
    parts.append(r"\setlist[itemize]{itemsep=0pt, topsep=0pt, parsep=0pt, partopsep=0pt}")
    parts.append(rf"\name{{{name}}}")
    address = (
        rf"{city} \;|\; {phone} \;|\; "
        rf"\href{{mailto:{email}}}{{{_esc(email)}}} \;|\; "
        rf"\href{{{linkedin_url}}}{{{_esc(linkedin)}}}"
    )
    parts.append(rf"\address{{{address}}}")
    parts.append(r"\begin{document}")
    parts.append(r"\small")

    parts.append(rf"\begin{{rSection}}{{{labels['summary']}}}")
    parts.append(_esc(resume.summary))
    parts.append(r"\end{rSection}")

    parts.append(rf"\begin{{rSection}}{{{labels['skills']}}}")
    parts.append(r"\begin{itemize}")
    for s in resume.skills:
        # skills already contain **bold** markdown — convert lightly
        latex_s = _esc(s).replace(r"\*\*", r"\textbf{").replace("**:", "}:")
        # naive: **Bucket**: → \textbf{Bucket}:
        if s.startswith("**") and "**" in s[2:]:
            end = s.find("**", 2)
            bucket = _esc(s[2:end])
            rest = _esc(s[end + 2 :].lstrip(": ").lstrip(":"))
            latex_s = rf"\textbf{{{bucket}}}: {rest}"
        parts.append(rf"    \item {latex_s}")
    parts.append(r"\end{itemize}")
    parts.append(r"\end{rSection}")

    parts.append(rf"\begin{{rSection}}{{{labels['experience']}}}")
    for role in resume.experience:
        end = "Present" if role["end"] == "present" and resume.locale == "en" else (
            "atual" if role["end"] == "present" else _esc(str(role["end"]))
        )
        parts.append(
            rf"{{\large \textbf{{{_esc(role['title'])}}}}} \hfill {_esc(str(role['start']))} -- {end}\\"
        )
        parts.append(
            rf"{{\small {_esc(role['company'])} \hfill \textit{{{_esc(role.get('location', ''))}}}}}\\[-4pt]"
        )
        parts.append(r"\begin{itemize}")
        for b in role["bullets"]:
            parts.append(rf"    \item {_esc(b)}")
        parts.append(r"\end{itemize}")
        parts.append("")
    parts.append(r"\end{rSection}")

    if resume.projects:
        parts.append(rf"\begin{{rSection}}{{{labels['projects']}}}")
        parts.append(r"\begin{itemize}")
        for p in resume.projects:
            bullet = " ".join(p["bullets"])
            parts.append(rf"    \item \textbf{{{_esc(p['name'])}}} --- {_esc(bullet)}")
        parts.append(r"\end{itemize}")
        parts.append(r"\end{rSection}")

    parts.append(rf"\begin{{rSection}}{{{labels['education']}}}")
    for edu in resume.education:
        parts.append(
            rf"{{\bf {_esc(edu.get('degree', ''))}}}, {_esc(edu.get('school', ''))} "
            rf"\hfill {{{_esc(edu.get('dates', ''))}}}\\"
        )
    if resume.languages:
        parts.append(rf"\textbf{{Languages}}: {_esc(', '.join(resume.languages))}\\")
    if resume.certifications:
        parts.append(rf"\textbf{{Certifications}}: {_esc(', '.join(resume.certifications))}\\")
    parts.append(r"\end{rSection}")
    parts.append(r"\normalsize")
    parts.append(r"\end{document}")
    return "\n".join(parts)
