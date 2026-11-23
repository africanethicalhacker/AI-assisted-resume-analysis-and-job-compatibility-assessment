"""Experiment 3: resume information-extraction accuracy against hand-made gold annotations.

gold_extraction.jsonl, one object per resume (include only the fields you annotated):
  {"id": "R001", "name": "...", "email": "...", "skills": ["Python", ...], "certifications": ["CEH"],
   "highest_education_level": "master", "professional_months": 18}
Skills are compared with the explicitly extracted skills (taxonomy names). Run: python -m experiments.exp3_extraction
"""
import re
from collections import Counter

from app.ai.pipeline import analyse_resume
from app.ai.skills.taxonomy import SkillMatcher

from . import metrics as M
from .common import common_args, environment_info, fmt, load_dataset, load_jsonl, md_table, write_results
import os

RANK = {"diploma": 1, "bachelor": 2, "master": 3, "doctorate": 4}


def _norm(s):
    return re.sub(r"[^a-z0-9+]", "", (s or "").lower())


def run(data_dir, out_dir, seed=42):
    resumes, _, _ = load_dataset(data_dir)
    gold = {g["id"]: g for g in load_jsonl(os.path.join(data_dir, "gold_extraction.jsonl")) if g["id"] in resumes}
    matcher = SkillMatcher.from_seed()
    tp = fp = fn = ctp = cfp = cfn = 0
    per_resume_f1, missed, spurious = [], Counter(), Counter()
    edu = [0, 0]
    name = [0, 0]
    email = [0, 0]
    months_err = []
    for rid, g in gold.items():
        p = analyse_resume(resumes[rid]["text"], matcher)
        if "skills" in g:
            pred = {s["name"] for s in p["skills"] if s["source_type"] == "explicit"}
            truth = set(g["skills"])
            tp, fp, fn = tp + len(pred & truth), fp + len(pred - truth), fn + len(truth - pred)
            per_resume_f1.append(M.prf(len(pred & truth), len(pred - truth), len(truth - pred))[2])
            missed.update(truth - pred)
            spurious.update(pred - truth)
        if "certifications" in g:
            pred = {_norm(c["name"]) for c in p["certifications"]}
            truth = {_norm(c) for c in g["certifications"]}
            hit = {t for t in truth if any(t == x or (len(t) >= 4 and (t in x or x in t)) for x in pred)}
            ctp, cfn = ctp + len(hit), cfn + len(truth - hit)
            cfp += len([x for x in pred if not any(x == t or (len(t) >= 4 and (t in x or x in t)) for t in truth)])
        if "highest_education_level" in g:
            top = max((RANK.get(e["level"], 0) for e in p["education"]), default=0)
            edu[0] += top == RANK.get(g["highest_education_level"], -1)
            edu[1] += 1
        if "name" in g:
            name[0] += bool(p["name"]) and p["name"]["value"].lower() == g["name"].lower()
            name[1] += 1
        if "email" in g:
            email[0] += bool(p["email"]) and p["email"]["value"] == g["email"].lower()
            email[1] += 1
        if g.get("professional_months") is not None:
            months_err.append(abs(p["experience_summary"]["professional_months"] - g["professional_months"]))
    sp, sr, sf = M.prf(tp, fp, fn)
    cp, cr, cf = M.prf(ctp, cfp, cfn)
    acc = lambda a: None if a[1] == 0 else a[0] / a[1]
    payload = {"experiment": "exp3_extraction", "n_resumes": len(gold),
               "skills_micro": {"precision": sp, "recall": sr, "f1": sf, "mean_per_resume_f1": M.mean(per_resume_f1)},
               "certifications_micro": {"precision": cp, "recall": cr, "f1": cf},
               "education_level_accuracy": acc(edu), "name_exact_match": acc(name), "email_exact_match": acc(email),
               "professional_months_mae": M.mean(months_err), "professional_months_within_3": (sum(e <= 3 for e in months_err) / len(months_err)) if months_err else None,
               "most_missed_skills": missed.most_common(10), "most_spurious_skills": spurious.most_common(10),
               "environment": environment_info(seed, data_dir)}
    rows = [["Skills (micro)", fmt(sp), fmt(sr), fmt(sf)], ["Certifications (micro)", fmt(cp), fmt(cr), fmt(cf)]]
    md = [f"# Experiment 3: extraction accuracy ({len(gold)} annotated resumes)", "", md_table(["Field", "Precision", "Recall", "F1"], rows), "",
          f"- Highest education level accuracy: {fmt(payload['education_level_accuracy'])}",
          f"- Name exact match: {fmt(payload['name_exact_match'])}; email exact match: {fmt(payload['email_exact_match'])}",
          f"- Professional months MAE: {fmt(payload['professional_months_mae'], 1)} (share within 3 months: {fmt(payload['professional_months_within_3'])})",
          f"- Most missed skills: {payload['most_missed_skills']}", f"- Most spurious skills: {payload['most_spurious_skills']}", "",
          "Error analysis should read these lists: misses usually mean missing aliases in the taxonomy; spurious hits mean ambiguous terms."]
    write_results(out_dir, "exp3_extraction", payload, "\n".join(md))
    return payload


if __name__ == "__main__":
    a = common_args(__doc__).parse_args()
    run(a.data, a.out, a.seed)
    print("Results written to", a.out)
