"""Eligibility screening for a posted job: a percentage, a verdict and the reasons behind it.

Percentage = the hybrid compatibility score, rounded. It is a measure of how well the CV matches
the job text, not a probability of being hired.

Mandatory checks (only requirements the job text marks as mandatory):
  skills (must be written in the CV; a skill only inferred from related tools is 'unconfirmed'),
  education level, years of experience, certifications.
Verdict:
  eligible      percentage >= threshold, every mandatory check met, none unconfirmed
  partial       percentage >= threshold - 15, at most one mandatory check not met
  not eligible  otherwise
The threshold is chosen by the employer for each job. The rules are a transparent screening aid; the
employer makes every decision.
"""
RANK_NAME = {1: "diploma", 2: "bachelor", 3: "master", 4: "doctorate"}
PARTIAL_MARGIN = 15
LABELS = {"eligible": "Likely eligible", "partial": "Partially eligible", "not_eligible": "Not eligible yet"}
RULE_TEXT = ("Likely eligible: the match reaches the job's threshold and every mandatory requirement is evidenced in the CV. "
             "Partially eligible: within 15 points of the threshold with at most one mandatory requirement not met. "
             "Otherwise: not eligible yet. This is an automated screening aid; the employer makes the decision.")


def _checks(components: list) -> list:
    comp = {c["name"]: c for c in components}
    out = []
    sk = comp["skills"]
    if sk.get("applicable"):
        for r in sk["explanation"].get("skills", []):
            if r["strength"] != "mandatory":
                continue
            status = {"matched": "met", "partial": "unconfirmed", "missing": "not met"}[r["status"]]
            detail = {"met": "found in the CV", "unconfirmed": "only inferred from related tools; write it explicitly if you have it",
                      "not met": "not found in the CV"}[status]
            out.append({"type": "Skill", "requirement": r["skill"], "status": status, "detail": detail})
    ed = comp["education"]
    if ed.get("applicable"):
        d = ed["explanation"]
        req, have = d.get("required_level_rank", 0), d.get("candidate_level_rank", 0)
        if d.get("required_from") == "mandatory" and req:
            ok = have >= req
            out.append({"type": "Education", "requirement": f"{RANK_NAME.get(req, 'degree')} level or higher",
                        "status": "met" if ok else "not met",
                        "detail": f"your highest level found: {RANK_NAME.get(have, 'none found')}"})
    ex = comp["experience"]
    if ex.get("applicable") and ex["explanation"].get("required_from") == "mandatory":
        d = ex["explanation"]
        ok = d["effective_months"] >= d["required_months"]
        out.append({"type": "Experience", "requirement": f"{d['required_months'] / 12:g} years",
                    "status": "met" if ok else "not met",
                    "detail": f"{d['effective_months'] / 12:.1f} years evidenced (internships count half)"})
    pc = comp["projects_certs"]
    certs = pc["explanation"].get("certifications") if pc.get("applicable") else None
    if certs:
        for row in certs["rows"]:
            if row["strength"] == "mandatory":
                out.append({"type": "Certification", "requirement": row["certification"],
                            "status": "met" if row["held"] else "not met",
                            "detail": "listed in the CV" if row["held"] else "not found in the CV"})
    return out


def decide(components: list, final_score: float, threshold: int) -> dict:
    pct = int(round(final_score))
    checks = _checks(components)
    hard = [c for c in checks if c["status"] == "not met"]
    unconfirmed = [c for c in checks if c["status"] == "unconfirmed"]
    if pct >= threshold and not hard and not unconfirmed:
        verdict = "eligible"
    elif pct >= threshold - PARTIAL_MARGIN and len(hard) <= 1:
        verdict = "partial"
    else:
        verdict = "not_eligible"
    reasons = []
    if pct < threshold:
        reasons.append(f"The match of {pct}% is below the {threshold}% this job asks for.")
    for c in hard:
        reasons.append(f"Mandatory requirement not met: {c['requirement']} ({c['detail']}).")
    for c in unconfirmed:
        reasons.append(f"Mandatory requirement not confirmed: {c['requirement']} ({c['detail']}).")
    if verdict == "eligible":
        reasons.append(f"The match of {pct}% reaches the {threshold}% threshold and every mandatory requirement is evidenced in your CV.")
    return {"verdict": verdict, "label": LABELS[verdict], "percentage": pct, "threshold": threshold,
            "checks": checks, "reasons": reasons, "rule": RULE_TEXT}
