from __future__ import annotations

from .models import Job, TailoredResume


def build_outreach(profile: dict, job: Job, resume: TailoredResume) -> str:
    idn = profile.get("identity", {})
    name = idn.get("name", "")
    project = resume.projects[0] if resume.projects else None
    proof = ""
    if project:
        detail = project["bullets"][0] if project["bullets"] else ""
        proof = f"Um exemplo concreto é o {project['name']}: {detail}"
        if resume.locale == "en":
            proof = f"One concrete example is {project['name']}: {detail}"

    tutoring = profile.get("career_tutoring", {})
    diff = (tutoring.get("positive_differentials") or [""])[0]

    if resume.locale == "pt":
        company = job.company or "a equipe"
        body = (
            f"Olá, equipe {company}!\n\n"
            f"Sou o/a {name} e me candidatei à vaga de {job.title}.\n\n"
            f"{resume.summary}\n\n"
            f"{proof}\n\n"
            f"{diff}\n\n"
            f"Fico à disposição para conversar!\n\n"
            f"Abraço,\n{name}\n"
        )
    else:
        company = job.company or "the team"
        body = (
            f"Hi {company} team,\n\n"
            f"I'm {name} — I applied for the {job.title} role.\n\n"
            f"{resume.summary}\n\n"
            f"{proof}\n\n"
            f"{diff}\n\n"
            f"Happy to chat if useful.\n\n"
            f"Best,\n{name}\n"
        )

    for key in ("phone", "email", "linkedin"):
        if idn.get(key):
            body += f"{idn[key]}\n"
    return body.strip() + "\n"
