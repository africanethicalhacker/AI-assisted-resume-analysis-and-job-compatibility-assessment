"""Experiment 1: TF-IDF + cosine similarity versus Sentence-BERT for ranking resumes against a job.

For each job, the labelled candidate resumes are ranked by each method's text-similarity score and
compared with human relevance labels. Reports P@K, R@K, nDCG@K and MRR (mean over jobs, with a
bootstrap 95% CI) and paired-bootstrap comparisons against TF-IDF.
Run: python -m experiments.exp1_matching --data experiments/data --k 5
"""
from app.ai.matching.sbert import chunk_text
from app.ai.matching.tfidf import tfidf_cosine
from app.security.sanitise import normalise_text

from . import metrics as M
from .common import (candidates_by_job, common_args, environment_info, fmt, load_dataset, md_table, try_sbert, write_results)


def rank(cands, score_of):
    return sorted(cands, key=lambda c: (-score_of(c[0]), c[0]))


def job_metrics(ranked, k, thr):
    rels = [rel for _, rel in ranked]
    return {"p@k": M.precision_at_k(rels, k, thr), "r@k": M.recall_at_k(rels, k, thr), "ndcg@k": M.ndcg_at_k(rels, k), "mrr": M.mrr(rels, thr)}


def run(data_dir, out_dir, k=5, threshold=2, use_sbert=True, seed=42, n_boot=2000):
    resumes, jobs, labels = load_dataset(data_dir)
    text = {rid: normalise_text(r["text"]) for rid, r in resumes.items()}
    jtext = {jid: normalise_text(j["text"], 20000) for jid, j in jobs.items()}
    sbert, note = (try_sbert() if use_sbert else (None, "SBERT disabled by option"))
    methods = ["tfidf"] + (["sbert", "blend"] if sbert else [])
    per = {m: {} for m in methods}
    skipped = 0
    for jid, cands in candidates_by_job(labels).items():
        if len(cands) < 2 or not any(rel >= threshold for _, rel in cands):
            skipped += 1
            continue
        tf = {rid: tfidf_cosine(text[rid], jtext[jid]) for rid, _ in cands}
        sb = {rid: sbert.coverage(chunk_text(jtext[jid]), chunk_text(text[rid])) for rid, _ in cands} if sbert else {}
        scorers = {"tfidf": lambda r: tf[r], "sbert": lambda r: sb[r], "blend": lambda r: 0.5 * sb[r] + 0.5 * tf[r]}
        for m in methods:
            per[m][jid] = job_metrics(rank(cands, scorers[m]), k, threshold)
    job_ids = sorted(per["tfidf"])
    agg = {}
    for m in methods:
        agg[m] = {}
        for name in ("p@k", "r@k", "ndcg@k", "mrr"):
            vals = [per[m][j][name] for j in job_ids]
            lo, hi = M.bootstrap_ci(vals, n_boot, seed)
            agg[m][name] = {"mean": M.mean(vals), "ci_low": lo, "ci_high": hi}
    tests = {}
    for m in methods[1:]:
        for name in ("ndcg@k", "p@k"):
            tests[f"{m}_vs_tfidf_{name}"] = M.paired_bootstrap([per[m][j][name] for j in job_ids], [per["tfidf"][j][name] for j in job_ids], n_boot, seed)
    payload = {"experiment": "exp1_tfidf_vs_sbert", "k": k, "relevance_threshold": threshold, "n_jobs_evaluated": len(job_ids),
               "n_jobs_skipped": skipped, "n_pairs": len(labels), "sbert_note": note, "aggregate": agg, "paired_tests": tests,
               "per_job": per, "environment": environment_info(seed, data_dir)}
    rows = [[m] + [f"{fmt(agg[m][n]['mean'])} [{fmt(agg[m][n]['ci_low'])}, {fmt(agg[m][n]['ci_high'])}]" for n in ("p@k", "r@k", "ndcg@k", "mrr")] for m in methods]
    md = [f"# Experiment 1: TF-IDF vs Sentence-BERT (K={k}, relevant = grade >= {threshold})", "",
          f"Jobs evaluated: {len(job_ids)} (skipped {skipped}); labelled pairs: {len(labels)}. Values: mean [95% bootstrap CI over jobs].", "",
          md_table(["Method", f"P@{k}", f"R@{k}", f"nDCG@{k}", "MRR"], rows), ""]
    if note:
        md.append(f"Note: {note}\n")
    for name, t in tests.items():
        md.append(f"- {name}: mean difference {fmt(t['mean_diff'])}, 95% CI [{fmt(t['ci'][0])}, {fmt(t['ci'][1])}], p = {fmt(t['p_value'])} (n = {t['n']} jobs)")
    md.append("\nInterpret with care: a small number of jobs gives wide intervals, and a difference whose interval includes 0 is not evidence of improvement.")
    write_results(out_dir, "exp1_tfidf_vs_sbert", payload, "\n".join(md))
    return payload


if __name__ == "__main__":
    ap = common_args(__doc__)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--threshold", type=int, default=2)
    a = ap.parse_args()
    run(a.data, a.out, a.k, a.threshold, not a.no_sbert, a.seed)
    print("Results written to", a.out)
