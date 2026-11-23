"""Skill-gap analysis (Phase 12): what the candidate has, what is missing, and what to fix first.

potential_points estimates how many points of the final score a missing skill is worth:
    effective_skills_weight x 100 x (skill_weight / sum of skill weights)   [partial skills: x 0.5]
It is a transparent estimate for prioritising, not a forecast of an employer's decision.
"""
from ..matching.scoring import INFERRED_CREDIT, LEVEL_RANK

RELEVANT = {"cybersecurity", "tools", "programming"}
_RANK_NAME = {v: k for k, v in LEVEL_RANK.items()}


def analyse_gap(profile: dict, requirements: list, components: list) -> dict:
    comp = {c["name"]: c for c in components}
    sk = comp["skills"]
    rows = sk["explanation"].get("skills", []) if sk.get("applicable") else []
    den = sum(r["weight"] for r in rows)
    eff = sk.get("effective_weight", 0.0)

    def points(r, gain):
        return round(eff * 100 * gain * r["weight"] / den, 2) if den else 0.0

    matched = [{"skill": r["skill"], "strength": r["strength"], "evidence": r["evidence"]} for r in rows if r["status"] == "matched"]
    partial = [{"skill": r["skill"], "strength": r["strength"], "potential_points": points(r, 1 - INFERRED_CREDIT),
                "note": "Only inferred from related tools. Add it explicitly if you have real experience."}
               for r in rows if r["status"] == "partial"]
    missing = {"mandatory": [], "preferred": [], "optional": []}
    for r in rows:
        if r["status"] == "missing":
            missing[r["strength"]].append({"skill": r["skill"], "potential_points": points(r, 1.0)})

    required_names = {r["skill"] for r in rows}
    additional = sorted(s["name"] for s in profile.get("skills", [])
                        if s["source_type"] == "explicit" and s["name"] not in required_names and s.get("category") in RELEVANT)

    gap = {"skills": {"matched": matched, "partial": partial, "missing": missing, "additional": additional,
                      "applicable": bool(rows)}}

    edu = comp["education"]
    if edu.get("applicable"):
        d = edu["explanation"]
        req, have = d.get("required_level_rank", 0), d.get("candidate_level_rank", 0)
        gap["education"] = {"required": _RANK_NAME.get(req, "not stated"), "candidate": _RANK_NAME.get(have, "none found"),
                            "level_met": have >= req if req else None, "field_score": d.get("field_score")}
    exp = comp["experience"]
    if exp.get("applicable"):
        d = exp["explanation"]
        gap["experience"] = {"required_months": d["required_months"], "effective_months": d["effective_months"],
                             "shortfall_months": max(0, round(d["required_months"] - d["effective_months"], 1))}
    pc = comp["projects_certs"]
    certs = pc["explanation"].get("certifications") if pc.get("applicable") else None
    if certs:
        gap["certifications"] = {"held": [r["certification"] for r in certs["rows"] if r["held"]],
                                 "missing": [{"certification": r["certification"], "strength": r["strength"]} for r in certs["rows"] if not r["held"]]}

    priorities = [{"item": m["skill"], "type": "missing " + s, "potential_points": m["potential_points"]}
                  for s in ("mandatory", "preferred", "optional") for m in missing[s]]
    priorities += [{"item": p["skill"], "type": "make explicit", "potential_points": p["potential_points"]} for p in partial]
    gap["priorities"] = sorted(priorities, key=lambda x: -x["potential_points"])[:10]
    gap["summary"] = {"matched": len(matched), "partial": len(partial), "missing_mandatory": len(missing["mandatory"]),
                      "missing_preferred": len(missing["preferred"]), "missing_optional": len(missing["optional"]),
                      "additional": len(additional)}
    return gap
