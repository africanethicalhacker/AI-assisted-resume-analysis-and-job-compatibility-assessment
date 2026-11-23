"""Rule-based structured extraction. Every field carries evidence; absent fields stay absent.

Nothing is guessed: if a field is not found it is None or an empty list.
"""
import re
from datetime import date

from .sections import Line, section_at, segment_sections

PARSER_VERSION = "1.0.0"

_BULLET = "•·▪●◦*-–—►>"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RES = [re.compile(r"(?<![\w/])(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)"),
             re.compile(r"(?<![\w/])\+\d{1,3}[\s-]?\d[\d\s-]{7,12}\d(?!\d)")]
LINK_RE = re.compile(r"(?:https?://)?(?:www\.)?(?:linkedin\.com/in|github\.com)/[A-Za-z0-9_./-]+", re.I)

MON = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
DATE = rf"(?:{MON}\s+)?(?:19|20)\d{{2}}|\d{{1,2}}/(?:19|20)\d{{2}}"
RANGE_RE = re.compile(rf"(?P<s>{DATE})\s*(?:-|–|—|to)\s*(?P<e>{DATE}|Present|Current|Now|Ongoing|Till\s+date)", re.I)
_MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}

_SHORT_DEG = r"B\.?\s?Tech|B\.\s?E\.?|BE|B\.?\s?Sc\.?|BCA|BBA|M\.?\s?Tech|M\.?\s?Sc\.?|MCA|MBA|PGDM|Ph\.?\s?D\.?"
_LONG_DEG = (r"Bachelor(?:'s|s)?(?:\s+of\s+[A-Za-z]+(?:\s+[A-Za-z]+){0,3})?"
             r"|Master(?:'s|s)?(?:\s+of\s+[A-Za-z]+(?:\s+[A-Za-z]+){0,3})?"
             r"|Diploma(?:\s+in\s+[A-Za-z]+(?:\s+[A-Za-z]+){0,3})?|Doctorate")
DEGREE_RE = re.compile(rf"(?<![A-Za-z])(?:{_SHORT_DEG})(?![A-Za-z])|(?i:{_LONG_DEG})")
INSTITUTION_RE = re.compile(
    r"((?:[A-Z][\w.&'-]*\s+){0,6}(?:University|Institute|College|School|Academy)"
    r"(?:\s+of\s+[A-Z][\w&-]*(?:\s+[A-Z][\w&-]*){0,3})?(?:\s*\([A-Z]{2,10}\))?)")
YEAR_RE = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")

CERT_RE = re.compile(
    r"(?<![A-Za-z])(CEH|CHFI|CISSP|CISM|CISA|CCSP|OSCP|OSCE|OSWE|GCIH|GPEN|GCFA|GSEC|GREM|eJPT|eCPPT|PNPT|CRTP|CRTO|CCNA|CCNP|"
    r"CompTIA\s+(?:Security\+|Network\+|CySA\+|PenTest\+|A\+)|Security\+|CySA\+|PenTest\+|Certified\s+Ethical\s+Hacker|"
    r"AWS\s+Certified\s+[A-Za-z][A-Za-z -]{2,40}|AZ-500|SC-200|SC-900)(?![A-Za-z])", re.I)
_NOT_NAMES = {"resume", "curriculum vitae", "cv", "curriculum", "vitae", "biodata"}


# ---------- helpers ----------
def _clean_bullet(s: str) -> str:
    return s.strip().lstrip(_BULLET + " \t").strip()


def _ev(text, start, end=None):
    snippet = re.sub(r"\s+", " ", text).strip()[:300]
    return {"text": snippet, "start": start, "end": end if end is not None else start + len(text)}


def _parse_date(token: str, today: date):
    t = token.strip().lower()
    if t in ("present", "current", "now", "ongoing") or t.startswith("till"):
        return today.year, today.month
    year = int(re.search(r"(?:19|20)\d{2}", t).group(0))
    if "/" in t:
        month = int(t.split("/")[0])
    else:
        mm = re.match(r"[a-z]{3}", re.sub(r"[^a-z]", "", t)) if re.search(r"[a-z]", t) else None
        month = _MONTHS.get(mm.group(0)) if mm else 1
    return year, month if month and 1 <= month <= 12 else 1


def _range_months(m, today):
    s, e = _parse_date(m.group("s"), today), _parse_date(m.group("e"), today)
    a, b = s[0] * 12 + s[1] - 1, e[0] * 12 + e[1] - 1
    return (a, b) if b >= a else None


def _merged_months(intervals) -> int:
    total, cur = 0, None
    for a, b in sorted(i for i in intervals if i):
        if cur and a <= cur[1]:
            cur = (cur[0], max(cur[1], b))
        else:
            if cur:
                total += cur[1] - cur[0]
            cur = (a, b)
    if cur:
        total += cur[1] - cur[0]
    return total


def education_level(degree: str) -> str:
    norm = re.sub(r"[^a-z]", "", degree.lower())
    if norm.startswith(("phd", "doctor")):
        return "doctorate"
    if norm.startswith(("msc", "mtech", "mca", "mba", "master", "pgdm", "postgraduate")):
        return "master"
    if norm.startswith(("bsc", "btech", "be", "bca", "bba", "bachelor")):
        return "bachelor"
    if norm.startswith("diploma"):
        return "diploma"
    return "other"


# ---------- field extractors ----------
def extract_name(header_lines):
    for ln in header_lines[:6]:
        s = ln.text.strip()
        words = s.split()
        if not 2 <= len(words) <= 4 or s.lower() in _NOT_NAMES:
            continue
        if re.search(r"[\d@:/]|http", s) or not all(re.fullmatch(r"[A-Za-z][A-Za-z.'-]*", w) for w in words):
            continue
        if all(w[0].isupper() for w in words):
            return {"value": s, "evidence": _ev(s, ln.start)}
    return None


def extract_contacts(text):
    email = EMAIL_RE.search(text)
    phone = next((m for rx in PHONE_RES if (m := rx.search(text))), None)
    links = []
    for m in LINK_RE.finditer(text):
        links.append({"value": m.group(0), "evidence": _ev(m.group(0), m.start(), m.end())})
    return (
        {"value": email.group(0).lower(), "evidence": _ev(email.group(0), email.start(), email.end())} if email else None,
        {"value": re.sub(r"\s+", " ", phone.group(0)).strip(), "evidence": _ev(phone.group(0), phone.start(), phone.end())} if phone else None,
        links[:5],
    )


def parse_education(lines):
    entries = []
    for k, ln in enumerate(lines):
        m = DEGREE_RE.search(ln.text)
        if not m:
            continue
        window = [ln]
        for nxt in lines[k + 1:k + 3]:
            if DEGREE_RE.search(nxt.text):
                break
            window.append(nxt)
        joined = " ".join(w.text.strip() for w in window)
        inst = INSTITUTION_RE.search(joined)
        years = [int(y) for y in YEAR_RE.findall(joined)]
        degree = m.group(0).strip()
        field = None
        fm = re.match(r"\s*(?:(?:in|of)\s+|[,(\-–:]\s*)?([A-Za-z][A-Za-z&/ ]{2,50}?)(?=\s*(?:[,;()|\n]|\d|$|\s-\s|\sat\s|\sfrom\s))",
                      ln.text[m.end():])
        if fm and not INSTITUTION_RE.fullmatch(fm.group(1).strip()):
            field = fm.group(1).strip()
        elif " in " in degree.lower():
            degree, field = re.split(r"\s+in\s+", degree, maxsplit=1, flags=re.I)
        entries.append({"degree": degree, "level": education_level(degree), "field": field,
                        "institution": inst.group(1).strip() if inst else None,
                        "start_year": min(years) if len(years) > 1 else None,
                        "end_year": max(years) if years else None,
                        "evidence": _ev(joined, ln.start)})
    return entries[:10]


def parse_dated_entries(lines, today):
    idxs = [k for k, ln in enumerate(lines) if RANGE_RE.search(ln.text)]
    uses_prev = []
    for k in idxs:
        m = RANGE_RE.search(lines[k].text)
        rest = (lines[k].text[:m.start()] + " " + lines[k].text[m.end():]).strip(" -–—|,:()")
        uses_prev.append(not rest and k > 0)
    entries = []
    for pos, k in enumerate(idxs):
        m = RANGE_RE.search(lines[k].text)
        header = (lines[k].text[:m.start()] + " " + lines[k].text[m.end():]).strip(" -–—|,:()")
        first = k
        if not header and k > 0:
            header, first = lines[k - 1].text.strip(), k - 1
        end_k = len(lines)
        if pos + 1 < len(idxs):
            end_k = idxs[pos + 1] - (1 if uses_prev[pos + 1] else 0)
        desc = [_clean_bullet(l.text) for l in lines[k + 1:end_k] if l.text.strip()][:8]
        iv = _range_months(m, today)
        entries.append({"title": _clean_bullet(header)[:200], "start": m.group("s"), "end": m.group("e"),
                        "months": (iv[1] - iv[0]) if iv else None, "_iv": iv, "description": desc,
                        "evidence": _ev(" ".join(l.text for l in lines[first:k + 1]), lines[first].start)})
    return entries[:20]


def parse_projects(lines):
    projects, cur = [], None
    for ln in lines:
        s = ln.text.strip()
        is_bullet = s[:1] in _BULLET
        if not is_bullet and len(s) <= 100 and (cur is None or cur["description"] or len(cur["title"]) == 0):
            cur = {"title": s, "description": [], "evidence": _ev(s, ln.start)}
            projects.append(cur)
        elif cur is not None:
            cur["description"].append(_clean_bullet(s)[:300])
        else:
            cur = {"title": _clean_bullet(s)[:100], "description": [], "evidence": _ev(s, ln.start)}
            projects.append(cur)
    return projects[:20]


def parse_certifications(text, cert_lines):
    found, seen = [], set()

    def add(name, ev):
        key = re.sub(r"[^a-z0-9+]", "", name.lower())
        if key and key not in seen:
            seen.add(key)
            found.append({"name": name.strip()[:120], "evidence": ev})

    for ln in cert_lines:
        s = _clean_bullet(ln.text)
        if s and len(s) <= 150:
            add(s, _ev(ln.text, ln.start))
    for m in CERT_RE.finditer(text):
        add(re.sub(r"\s+", " ", m.group(0)), _ev(m.group(0), m.start(), m.end()))
    return found[:20]


# ---------- quality heuristic ----------
def quality_score(p):
    b = {
        "contact": (10 if p["email"] else 0) + (5 if p["phone"] else 0),
        "name": 5 if p["name"] else 0,
        "education": 15 if p["education"] else 0,
        "skills": round(20 * min(len([s for s in p["skills"] if s["source_type"] == "explicit"]), 5) / 5),
        "experience": 10 if (p["experience"] or p["internships"]) else 0,
        "projects": 10 if p["projects"] else 0,
        "certifications": 5 if p["certifications"] else 0,
        "achievements": 5 if p["achievements"] else 0,
        "length": 10 if 150 <= p["word_count"] <= 1200 else (5 if 60 <= p["word_count"] < 150 or 1200 < p["word_count"] <= 2000 else 0),
        "structure": 5 if len(p["sections_found"]) >= 4 else 0,
    }
    return {"score": sum(b.values()), "breakdown": b,
            "note": "Heuristic completeness score, not a measure of candidate ability."}


# ---------- orchestrator ----------
def extract_profile(text: str, matcher, today: date = None) -> dict:
    today = today or date.today()
    sections = segment_sections(text)
    by_name = {}
    for s in sections:
        by_name.setdefault(s.name, []).extend(s.lines)

    email, phone, links = extract_contacts(text)
    skills = []
    for m in matcher.find_all(text):
        where = section_at(sections, m.start) if m.start >= 0 else None
        skills.append({"name": m.name, "category": m.category, "source_type": m.source_type,
                       "confidence": m.confidence, "section": where, "occurrences": m.occurrences,
                       "evidence": {"text": m.snippet, "start": m.start, "end": m.end}})

    jobs = parse_dated_entries(by_name.get("experience", []), today)
    interns = parse_dated_entries(by_name.get("internships", []), today)
    still_jobs = []
    for e in jobs:
        (interns if re.search(r"\bintern(ship)?\b", e["title"], re.I) else still_jobs).append(e)
    prof_m = _merged_months(e["_iv"] for e in still_jobs)
    intern_m = _merged_months(e["_iv"] for e in interns)
    total_m = _merged_months(e["_iv"] for e in still_jobs + interns)
    for e in still_jobs + interns:
        e.pop("_iv", None)

    summary_lines = by_name.get("summary", [])
    profile = {
        "parser_version": PARSER_VERSION,
        "name": extract_name(by_name.get("header", [])),
        "email": email, "phone": phone, "links": links,
        "summary": " ".join(l.text.strip() for l in summary_lines)[:600] or None,
        "education": parse_education(by_name.get("education", [])),
        "skills": skills,
        "certifications": parse_certifications(text, by_name.get("certifications", [])),
        "experience": still_jobs, "internships": interns,
        "experience_summary": {"professional_months": prof_m, "internship_months": intern_m, "total_months": total_m,
                               "note": "Computed only from explicit date ranges; year-only dates count from January."},
        "projects": parse_projects(by_name.get("projects", [])),
        "achievements": [{"text": _clean_bullet(l.text)[:300], "evidence": _ev(l.text, l.start)}
                         for l in by_name.get("achievements", []) if l.text.strip()][:20],
        "sections_found": [s.name for s in sections if s.name != "header" and s.lines],
        "word_count": len(text.split()),
    }
    profile["quality"] = quality_score(profile)
    return profile
