"""Experiment 6: bias and fairness screening.

(a) Counterfactual tests: change ONLY the candidate's name, or ONLY the institution, and measure how much
    the final score moves. A fair scorer should not move (names and institutions are not job criteria).
(b) Group selection rates (needs groups.csv): top-K selection rate per group, impact ratio (min/max) and
    the "four-fifths" screening heuristic, shown beside the groups' share of truly relevant candidates.
This is a screening aid on a small sample, NOT a legal compliance or discrimination audit.
Run: python -m experiments.exp6_fairness --data experiments/data --k 5
"""
from app.ai.pipeline import analyse_job_text, analyse_resume, score_pair
from app.ai.skills.taxonomy import SkillMatcher

from . import metrics as M
from .common import (candidates_by_job, common_args, environment_info, fmt, load_dataset, load_groups, md_table, try_sbert, write_results)

SWAP_NAMES = ["Aarav Sharma", "Emily Johnson", "Chinedu Okafor", "Fatima Al-Hassan", "Wei Zhang", "Maria Garcia", "Priya Nair", "John Smith"]
SWAP_INSTITUTIONS = ["Indian Institute of Technology Bombay", "Government Polytechnic College", "University of Oxford", "Regional Community College"]


def _swap(text, old, new):
    return text.replace(old, new) if old and old in text else None


def run(data_dir, out_dir, k=5, threshold=2, use_sbert=True, seed=42, max_resumes=20, max_jobs=6):
    resumes, jobs, labels = load_dataset(data_dir)
    groups = load_groups(data_dir)
    matcher = SkillMatcher.from_seed()
    sbert, note = (try_sbert() if use_sbert else (None, "SBERT disabled by option"))
    mode = "sbert" if sbert else "tfidf"
    janalyses = {jid: analyse_job_text(j["text"], matcher) for jid, j in list(jobs.items())[:max_jobs]}

    def score(text, jid):
        return score_pair(analyse_resume(text, matcher), janalyses[jid], matcher, mode=mode, sbert=sbert)["final_score"]

    deltas = {"name": [], "institution": []}
    for rid in list(resumes)[:max_resumes]:
        text = resumes[rid]["text"]
        base_p = analyse_resume(text, matcher)
        name = base_p["name"]["value"] if base_p["name"] else None
        insts = [e["institution"] for e in base_p["education"] if e.get("institution")]
        for jid in janalyses:
            base = score(text, jid)
            for new in SWAP_NAMES:
                t = _swap(text, name, new)
                if t is not None and new != name:
                    deltas["name"].append(score(t, jid) - base)
            for new in SWAP_INSTITUTIONS:
                t = _swap(text, insts[0], new) if insts else None
                if t is not None:
                    deltas["institution"].append(score(t, jid) - base)

    def summ(ds):
        a = sorted(abs(d) for d in ds)
        return {"n": len(a), "mean_abs_delta": M.mean(a), "p95_abs_delta": a[int(0.95 * (len(a) - 1))] if a else None,
                "max_abs_delta": a[-1] if a else None, "share_moving_1pt_or_more": (sum(x >= 1 for x in a) / len(a)) if a else None}

    counterfactual = {kind: summ(ds) for kind, ds in deltas.items()}

    selection = []
    if groups:
        text = {rid: r["text"] for rid, r in resumes.items()}
        profiles = {rid: analyse_resume(text[rid], matcher) for rid in resumes}
        for jid, cands in candidates_by_job(labels).items():
            if jid not in jobs or len(cands) < 2 * k:
                continue
            ja = janalyses.get(jid) or analyse_job_text(jobs[jid]["text"], matcher)
            sc = {rid: score_pair(profiles[rid], ja, matcher, mode=mode, sbert=sbert)["final_score"] for rid, _ in cands}
            top = {rid for rid, _ in sorted(cands, key=lambda c: (-sc[c[0]], c[0]))[:k]}
            rates, relevant = {}, {}
            for g in sorted({groups[r] for r, _ in cands if r in groups}):
                members = [(r, rel) for r, rel in cands if groups.get(r) == g]
                rates[g] = sum(r in top for r, _ in members) / len(members)
                relevant[g] = sum(rel >= threshold for _, rel in members) / len(members)
            if len(rates) >= 2 and max(rates.values()) > 0:
                selection.append({"job": jid, "rates": rates, "relevant_share": relevant, "impact_ratio": min(rates.values()) / max(rates.values())})
    ratios = [s["impact_ratio"] for s in selection]
    payload = {"experiment": "exp6_fairness", "semantic_mode": mode, "sbert_note": note, "counterfactual": counterfactual,
               "selection": {"n_jobs": len(selection), "mean_impact_ratio": M.mean(ratios),
                             "jobs_below_0.8": sum(r < 0.8 for r in ratios), "per_job": selection},
               "environment": environment_info(seed, data_dir)}
    rows = [[kind, v["n"], fmt(v["mean_abs_delta"], 2), fmt(v["p95_abs_delta"], 2), fmt(v["max_abs_delta"], 2), fmt(v["share_moving_1pt_or_more"], 2)] for kind, v in counterfactual.items()]
    md = ["# Experiment 6: bias and fairness screening", "", f"Scoring mode: {mode}.", "",
          "## Counterfactual score changes (points on the 0-100 scale)", "",
          md_table(["Change", "pairs", "mean |delta|", "p95 |delta|", "max |delta|", "share >= 1 point"], rows), ""]
    if selection:
        md += [f"## Group selection rates (top {k})", "", f"Jobs analysed: {len(selection)}; mean impact ratio {fmt(M.mean(ratios), 2)}; "
               f"jobs below the 0.8 screening threshold: {payload['selection']['jobs_below_0.8']}.", ""]
    else:
        md.append("No groups.csv (or too few candidates per job), so selection rates were not computed.\n")
    md.append("Limits: small samples, one synthetic or limited dataset, and a screening heuristic only. Differences in qualification between groups can lower the ratio without any bias in the scorer, so compare with the relevant-share values in the JSON.")
    if note:
        md.append(f"\nNote: {note}")
    write_results(out_dir, "exp6_fairness", payload, "\n".join(md))
    return payload


if __name__ == "__main__":
    ap = common_args(__doc__)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--threshold", type=int, default=2)
    a = ap.parse_args()
    run(a.data, a.out, a.k, a.threshold, not a.no_sbert, a.seed)
    print("Results written to", a.out)
