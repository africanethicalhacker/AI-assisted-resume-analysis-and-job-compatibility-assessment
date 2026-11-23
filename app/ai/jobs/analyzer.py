"""Job-description analysis. A requirement is 'mandatory' only when the text supports it."""
import re

from ..parsing.extractor import CERT_RE, DEGREE_RE, _clean_bullet

_REQ = ["requirements", "qualifications", "required qualifications", "required skills", "must have",
        "must haves", "what you need", "what we require", "minimum qualifications", "essential",
        "essential skills", "what you bring", "skills required", "eligibility", "required"]
_PREF = ["preferred qualifications", "preferred skills", "preferred", "nice to have", "good to have",
         "desirable", "bonus", "bonus points", "plus", "desired skills", "desired qualifications"]
_RESP = ["responsibilities", "key responsibilities", "duties", "what you will do", "what you'll do",
         "role and responsibilities", "job responsibilities", "the role"]
_IGNORE = ["about us", "about the company", "benefits", "perks", "we offer", "what we offer", "how to apply",
           "equal opportunity", "about the role", "overview", "job description", "company overview"]
_SECTION = {**{a: "mandatory" for a in _REQ}, **{a: "preferred" for a in _PREF},
            **{a: "responsibility" for a in _RESP}, **{a: "ignore" for a in _IGNORE}}

_OPTIONAL_CUE = re.compile(r"\b(optional|not\s+(?:strictly\s+)?(?:required|mandatory|necessary))\b", re.I)
_PREF_CUE = re.compile(r"\b(preferred|nice\s+to\s+have|good\s+to\s+have|desirable|desired|bonus|a\s+plus|an\s+advantage|advantageous|is\s+a\s+plus|would\s+be\s+(?:a\s+)?(?:plus|an?\s+advantage|beneficial))\b", re.I)
_MAND_CUE = re.compile(r"\b(must|required|requirements?|essential|mandatory|minimum|should\s+have|need\s+to\s+have|needs?)\b", re.I)
_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:(?:-|to)\s*\d{1,2}\s*)?(?:years?|yrs?)\b", re.I)
_EDU_WORDS = re.compile(r"\b(bachelor|master|degree|graduate|b\.?\s?tech|m\.?\s?tech|b\.?\s?sc|m\.?\s?sc|diploma|ph\.?d|b\.?\s?e\b)", re.I)
_STRENGTH_RANK = {"mandatory": 3, "preferred": 2, "optional": 1}


def _heading(line: str):
    cleaned = re.sub(r"[:\-_|•·▪●◦*#=]+", " ", line).strip().lower()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if 0 < len(cleaned) <= 40 and len(line.strip()) <= 50:
        return _SECTION.get(cleaned)
    return None


def _line_strength(line: str, section_default):
    if _OPTIONAL_CUE.search(line):
        return "optional", "cue"
    if _PREF_CUE.search(line):
        return "preferred", "cue"
    if _MAND_CUE.search(line):
        return "mandatory", "cue"
    if section_default == "mandatory":
        return "mandatory", "section"
    if section_default == "preferred":
        return "preferred", "section"
    return None, None


def analyze_job(text: str, matcher) -> dict:
    lines = [l for l in text.split("\n")]
    title = organization = None
    for l in lines:
        s = l.strip()
        m = re.match(r"(?i)(job\s+title|position|role)\s*[:\-]\s*(.+)", s)
        if m and not title:
            title = m.group(2).strip()[:200]
        m = re.match(r"(?i)(company|organi[sz]ation|employer)\s*[:\-]\s*(.+)", s)
        if m and not organization:
            organization = m.group(2).strip()[:200]
    if not title:
        first = next((l.strip() for l in lines if l.strip()), "")
        title = first[:200] if first and len(first) <= 100 and not first.endswith(":") else None

    section = None
    reqs = {}          # key -> dict, to merge duplicates
    min_years = None

    def add(kind, text_, strength, evidence, skill=None):
        key = (kind, skill or text_.lower())
        row = {"kind": kind, "requirement_text": text_[:500], "strength": strength,
               "evidence_span": evidence[:500], "skill_name": skill}
        cur = reqs.get(key)
        if cur is None or _STRENGTH_RANK[strength] > _STRENGTH_RANK[cur["strength"]]:
            reqs[key] = row

    for raw in lines:
        s = raw.strip()
        if not s:
            continue
        h = _heading(s)
        if h:
            section = h
            continue
        line = _clean_bullet(s)
        if len(line) < 3 or section == "ignore":
            continue
        if section == "responsibility":
            strength, how = _line_strength(line, None)
            if strength is None:
                strength = "optional"
            kind = "responsibility"
        else:
            strength, how = _line_strength(line, section)
            if strength is None:
                continue          # no heading and no cue: do not assume it is a requirement
            kind = None

        ym = _YEARS.search(line)
        has_edu = bool(_EDU_WORDS.search(line) or DEGREE_RE.search(line))
        has_cert = bool(CERT_RE.search(line) or re.search(r"\bcertif", line, re.I))
        skills = matcher.find_explicit(line)

        if ym and kind != "responsibility":
            add("experience", line, strength, line)
            if strength == "mandatory":
                n = int(ym.group(1))
                min_years = n if min_years is None else max(min_years, n)
        if has_edu and kind != "responsibility":
            add("qualification", line, strength, line)
        if has_cert and kind != "responsibility":
            for cm in CERT_RE.finditer(line):
                add("certification", re.sub(r"\s+", " ", cm.group(0)), strength, line)
            if not CERT_RE.search(line):
                add("certification", line, strength, line)
        for sk in skills:
            add("tool" if sk.category == "tools" else "skill", sk.name,
                "optional" if kind == "responsibility" else strength, line, skill=sk.name)
        if kind == "responsibility":
            add("responsibility", line, strength, line)
        elif not (ym or has_edu or has_cert or skills):
            add("domain", line, strength, line)

    requirements = list(reqs.values())
    return {"title": title, "organization": organization, "requirements": requirements,
            "min_experience_years": min_years,
            "summary": {"mandatory": sum(r["strength"] == "mandatory" and r["kind"] != "responsibility" for r in requirements),
                        "preferred": sum(r["strength"] == "preferred" for r in requirements),
                        "optional": sum(r["strength"] == "optional" and r["kind"] != "responsibility" for r in requirements),
                        "responsibilities": sum(r["kind"] == "responsibility" for r in requirements)}}
