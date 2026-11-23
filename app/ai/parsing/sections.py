"""Split resume text into sections using heading lines. Offsets refer to the normalised text."""
import re
from dataclasses import dataclass, field

HEADINGS = {
    "summary": ["summary", "professional summary", "profile", "objective", "career objective", "about me", "about"],
    "education": ["education", "academic background", "academics", "educational qualifications",
                  "academic qualifications", "qualifications"],
    "experience": ["experience", "work experience", "professional experience", "employment",
                   "employment history", "work history"],
    "internships": ["internship", "internships", "internship experience"],
    "skills": ["skills", "technical skills", "key skills", "core competencies", "technologies",
               "tools", "tools and technologies", "technical proficiency", "it skills"],
    "projects": ["projects", "academic projects", "personal projects", "key projects", "project work"],
    "certifications": ["certifications", "certificates", "licenses", "licences", "courses",
                       "training", "certifications and training"],
    "achievements": ["achievements", "awards", "honors", "honours", "accomplishments",
                     "awards and achievements", "publications", "extracurricular activities"],
}
_LOOKUP = {alias: name for name, aliases in HEADINGS.items() for alias in aliases}


@dataclass
class Line:
    text: str
    start: int


@dataclass
class Section:
    name: str
    start: int
    lines: list = field(default_factory=list)
    end: int = 0


def heading_name(line: str):
    cleaned = re.sub(r"[:\-_|•·▪●◦*#=]+", " ", line).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace("&", "and")
    if 0 < len(cleaned) <= 40 and len(line.strip()) <= 50:
        return _LOOKUP.get(cleaned)
    return None


def segment_sections(text: str) -> list:
    sections = [Section("header", 0)]
    offset = 0
    for raw in text.split("\n"):
        name = heading_name(raw)
        if name:
            sections[-1].end = offset
            sections.append(Section(name, offset))
        elif raw.strip():
            sections[-1].lines.append(Line(raw, offset))
        offset += len(raw) + 1
    sections[-1].end = len(text)
    return sections


def section_at(sections: list, pos: int) -> str:
    for s in sections:
        if s.start <= pos < s.end:
            return s.name
    return "header"
