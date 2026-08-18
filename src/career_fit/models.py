from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]


def load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Job:
    title: str
    company: str = ""
    description: str = ""
    locale: str = "en"

    @property
    def text(self) -> str:
        return f"{self.title}\n{self.company}\n{self.description}".lower()


@dataclass
class TailoredResume:
    angle: str
    locale: str
    summary: str
    skills: list[str]
    experience: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    availability_line: str | None = None
    identity: dict[str, Any] = field(default_factory=dict)
    education: list[dict[str, Any]] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)


SECTION_LABELS = {
    "en": {
        "summary": "SUMMARY",
        "skills": "CORE SKILLS",
        "experience": "PROFESSIONAL EXPERIENCE",
        "projects": "PROJECTS",
        "education": "EDUCATION & ADDITIONAL",
    },
    "pt": {
        "summary": "RESUMO",
        "skills": "COMPETÊNCIAS",
        "experience": "EXPERIÊNCIA PROFISSIONAL",
        "projects": "PROJETOS",
        "education": "FORMAÇÃO & INFORMAÇÕES ADICIONAIS",
    },
}
