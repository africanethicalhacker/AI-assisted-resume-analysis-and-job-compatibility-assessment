"""Hybrid compatibility score (Phase 11). Deterministic arithmetic over component scores.

Final = sum_i (w_i / W) * S_i   over the components that apply to this job,
        where W = sum of configured weights of the applicable components.
With all five applicable this is exactly the formula in the brief
(0.35 skills + 0.25 semantic + 0.15 education + 0.15 experience + 0.10 projects/certs).
A component is "not applicable" when the job description gives nothing to compare
(for example, no education requirement); its weight is redistributed and the report says so.

All component scores are 0-100. The weights and the rule values below are experimental
hypotheses to be tested in Experiment 2; they are not established constants.
No language model produces or adjusts any number here, so text inside a resume cannot change it.
"""
import re

from ..parsing.extractor import education_level

DEFAULT_WEIGHTS = {"skills": 0.35, "semantic": 0.25, "education": 0.15, "experience": 0.15, "projects_certs": 0.10}
ORDER = list(DEFAULT_WEIGHTS)
LABELS = {"skills": "Technical skills", "semantic": "Semantic similarity", "education": "Education",
          "experience": "Experience", "projects_certs": "Projects and certifications"}
SCORING_VERSION = "hybrid-1.0"

STRENGTH_WEIGHT = {"mandatory": 3.0, "preferred": 2.0, "optional": 1.0}
INFERRED_CREDIT = 0.5          # a skill only inferred from related tools earns half credit
INTERNSHIP_FACTOR = 0.5        # internship months count at half value
LEVEL_RANK = {"other": 0, "diploma": 1, "bachelor": 2, "master": 3, "doctorate": 4}
LEVEL_SCORE_BY_GAP = {0: 100.0, -1: 50.0, -2: 20.0}
EDU_LEVEL_SHARE, EDU_FIELD_SHARE = 0.7, 0.3

_YEARS = re.compile(r"(\d{1,2})\s*\+?\s*(?:(?:-|to)\s*\d{1,2}\s*)?(?:years?|yrs?)\b", re.I)
_FIELD_GROUPS = {"cyber": ("cyber", "security", "forensic", "information assurance", "infosec"),
                 "computing": ("computer", "information technology", "software", "informatics", "computing")}


def level_from_text(text: str) -> int:
    """Lowest education level that satisfies the text (0 if none stated)."""
    s = re.sub(r"post-?\s?graduate", " master ", (text or "").lower())
    found = []
    if re.search(r"ph\.?\s?d|doctorate|doctoral", s):
        found.append(4)
    if re.search(r"master|\bm\.?\s?sc\b|\bm\.?\s?tech\b|\bmca\b|\bmba\b", s):
        found.append(3)
    if re.search(r"bachelor|\bb\.?\s?sc\b|\bb\.?\s?tech\b|\bb\.?\s?e\b|\bbca\b|\bbba\b|undergraduate", s):
        found.append(2)
    if re.search(r"diploma", s):
        found.append(1)
    if found:
        return min(found)
    return 2 if re.search(r"\bdegree\b", s) else 0


def _groups(text: str) -> set:
    t = (text or "").lower()
    return {g for g, words in _FIELD_GROUPS.items() if any(w in t for w in words)}


def _norm_cert(name: str) -> str:
    return re.sub(r"[^a-z0-9+]", "", (name or "").lower())


def _result(name, score, explanation):
    return {"name": name, "label": LABELS[name], "score": None if score is None else round(score, 2),
            "explanation": explanation}


# ---------------- components ----------------
def skills_component(profile, reqs):
    cand = {s["name"]: s for s in profile.get("skills", [])}
    rows, num, den = [], 0.0, 0.0
    for r in reqs:
        if r["kind"] not in ("skill", "tool"):
            continue
        w = STRENGTH_WEIGHT[r["strength"]]
        c = cand.get(r["text"])
        if c and c["source_type"] == "explicit":
            credit, status = 1.0, "matched"
        elif c:
            credit, status = INFERRED_CREDIT, "partial"
        else:
            credit, status = 0.0, "missing"
        num, den = num + w * credit, den + w
        rows.append({"skill": r["text"], "strength": r["strength"], "status": status, "credit": credit,
                     "weight": w, "evidence": (c or {}).get("evidence", {}).get("text", "")})
    if not rows:
        return _result("skills", None, {"reason": "The job description lists no recognised technical skills."})
    return _result("skills", 100 * num / den, {
        "formula": "100 x sum(weight x credit) / sum(weight); weight: mandatory 3, preferred 2, optional 1; "
                   "credit: explicit 1.0, inferred 0.5, missing 0",
        "skills": rows})


def education_component(profile, reqs):
    quals = [r for r in reqs if r["kind"] == "qualification"]
    if not quals:
        return _result("education", None, {"reason": "The job description states no education requirement."})
    tier = [r for r in quals if r["strength"] == "mandatory"] or [r for r in quals if r["strength"] == "preferred"] or quals
    required = max((level_from_text(r["text"]) for r in tier), default=0)
    entries = profile.get("education", [])
    cand_rank = max((LEVEL_RANK.get(e.get("level", "other"), 0) for e in entries), default=0)
    parts, detail = [], {"required_level_rank": required, "candidate_level_rank": cand_rank,
                         "required_from": tier[0]["strength"], "ranks": "diploma 1, bachelor 2, master 3, doctorate 4"}
    if required:
        gap = cand_rank - required
        level_score = 100.0 if gap >= 0 else LEVEL_SCORE_BY_GAP.get(gap, 0.0)
        parts.append((level_score, EDU_LEVEL_SHARE))
        detail["level_score"] = level_score
    jd_groups = set().union(*(_groups(r["text"]) for r in quals))
    if jd_groups:
        cand_groups = set().union(*(_groups((e.get("degree") or "") + " " + (e.get("field") or "")) for e in entries)) if entries else set()
        if "cyber" in cand_groups:
            cand_groups = cand_groups | {"computing"}      # a cyber security degree is a computing degree
        field_score = 100.0 if jd_groups & cand_groups else (50.0 if cand_groups else 0.0)
        parts.append((field_score, EDU_FIELD_SHARE))
        detail.update(field_score=field_score, job_field_groups=sorted(jd_groups), candidate_field_groups=sorted(cand_groups))
    if not parts:
        return _result("education", None, {"reason": "The education requirement names no recognisable level or field."})
    total = sum(w for _, w in parts)
    return _result("education", sum(v * w for v, w in parts) / total, detail)


def experience_component(profile, reqs):
    exp = [r for r in reqs if r["kind"] == "experience"]
    mandatory_exp = [r for r in exp if r["strength"] == "mandatory"]
    tier = mandatory_exp or [r for r in exp if r["strength"] == "preferred"]
    years = [int(m.group(1)) for r in tier for m in [_YEARS.search(r["text"])] if m]
    if not years:
        return _result("experience", None, {"reason": "The job description states no experience requirement in years."})
    required = max(years) * 12
    es = profile.get("experience_summary", {})
    effective = es.get("professional_months", 0) + INTERNSHIP_FACTOR * es.get("internship_months", 0)
    return _result("experience", min(100.0, 100.0 * effective / required), {
        "required_months": required, "required_from": "mandatory" if mandatory_exp else "preferred",
        "professional_months": es.get("professional_months", 0),
        "internship_months": es.get("internship_months", 0), "effective_months": round(effective, 1),
        "formula": "min(100, 100 x (professional + 0.5 x internship months) / required months)"})


def projects_certs_component(profile, reqs, matcher):
    parts, detail = [], {}
    skill_reqs = {r["text"] for r in reqs if r["kind"] in ("skill", "tool")}
    if skill_reqs:
        text = "\n".join(p["title"] + "\n" + "\n".join(p.get("description", [])) for p in profile.get("projects", []))
        found = {m.name for m in matcher.find_explicit(text)} if text.strip() else set()
        hit = sorted(skill_reqs & found)
        score = 100.0 * len(hit) / len(skill_reqs)
        parts.append(score)
        detail["projects"] = {"score": round(score, 2), "job_skills_used_in_projects": hit, "job_skills_total": len(skill_reqs),
                              "n_projects": len(profile.get("projects", []))}
    cert_reqs = [r for r in reqs if r["kind"] == "certification"]
    if cert_reqs:
        have = [_norm_cert(c["name"]) for c in profile.get("certifications", [])]
        rows = []
        for r in cert_reqs:
            key = _norm_cert(r["text"])
            ok = bool(key) and any(key == h or (len(key) >= 4 and (key in h or h in key)) for h in have if h)
            rows.append({"certification": r["text"], "strength": r["strength"], "held": ok})
        score = 100.0 * sum(r["held"] for r in rows) / len(rows)
        parts.append(score)
        detail["certifications"] = {"score": round(score, 2), "rows": rows}
    if not parts:
        return _result("projects_certs", None, {"reason": "The job lists no skills or certifications to compare."})
    detail["formula"] = "average of the available sub-scores"
    return _result("projects_certs", sum(parts) / len(parts), detail)


def semantic_component(semantic: dict):
    return _result("semantic", semantic["score"], {
        "method_used": semantic["method_used"], "tfidf_cosine": semantic["tfidf_cosine"],
        "sbert_coverage": semantic["sbert_coverage"], "note": semantic.get("note", ""),
        "formula": "100 x cosine-based similarity, clipped to 0-1 (not rescaled)"})


# ---------------- integrity ----------------
def integrity_flags(profile, injection_lines_removed: int = 0) -> list:
    flags = []
    sec = profile.get("security", {})
    if sec.get("injection_findings") or injection_lines_removed:
        flags.append({"code": "instruction_like_text",
                      "message": "Instruction-like text was found and excluded from matching; it did not affect any score."})
    if sec.get("hidden_text_removed_chars"):
        flags.append({"code": "hidden_text_removed", "message": "Invisible text was removed before analysis."})
    if sec.get("white_text_chars"):
        flags.append({"code": "white_text", "message": "White-coloured text was present (may be a design choice or keyword stuffing)."})
    explicit = [s for s in profile.get("skills", []) if s["source_type"] == "explicit"]
    words = max(profile.get("word_count", 0), 1)
    mentions = sum(s.get("occurrences", 1) for s in explicit)
    if any(s.get("occurrences", 1) >= 12 for s in explicit) or (words >= 50 and mentions / words > 0.25):
        flags.append({"code": "possible_keyword_stuffing",
                      "message": "Skill keywords are repeated unusually often. Each skill counts once regardless."})
    return flags


# ---------------- orchestrator ----------------
def score_assessment(profile: dict, requirements: list, weights: dict, semantic: dict, matcher, removed_lines: int = 0) -> dict:
    comps = [skills_component(profile, requirements), semantic_component(semantic),
             education_component(profile, requirements), experience_component(profile, requirements),
             projects_certs_component(profile, requirements, matcher)]
    by_name = {c["name"]: c for c in comps}
    comps = [by_name[n] for n in ORDER]
    applicable_weight = sum(weights[c["name"]] for c in comps if c["score"] is not None)
    final = 0.0
    for c in comps:
        configured = weights[c["name"]]
        if c["score"] is None or applicable_weight <= 0:
            c.update(applicable=False, configured_weight=configured, effective_weight=0.0, contribution=0.0)
        else:
            eff = configured / applicable_weight
            c.update(applicable=True, configured_weight=configured, effective_weight=round(eff, 6),
                     contribution=round(eff * c["score"], 4))
            final += eff * c["score"]
    return {"final_score": round(final, 2), "components": comps, "weights_configured": dict(weights),
            "flags": integrity_flags(profile, removed_lines), "scoring_version": SCORING_VERSION}
