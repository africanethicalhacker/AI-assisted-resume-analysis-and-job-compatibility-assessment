"""Experiment 2: traditional skill matching versus the hybrid model, ablations, and weight validation.

Component scores are computed once per labelled (job, resume) pair; every method is then a different
way of combining them, so all methods see identical inputs. Weights are tuned on a development half of
the jobs and evaluated on the held-out half, to avoid reporting an over-fitted number.
Run: python -m experiments.exp2_hybrid --data experiments/data --k 5 --grid-step 0.1
"""
import random

from app.ai.matching.scoring import DEFAULT_WEIGHTS, ORDER
from app.ai.pipeline import analyse_job_text, analyse_resume, combine_scores, score_pair
from app.ai.skills.taxonomy import SkillMatcher

from . import metrics as M
from .common import (candidates_by_job, common_args, environment_info, fmt, load_dataset, md_table, try_sbert, write_results)


def compositions(total, parts):
    if parts == 1:
        yield (total,)
        return
    for i in range(total + 1):
        for rest in compositions(total - i, parts - 1):
            yield (i,) + rest


def evaluate(score_of, cands_by_job, job_ids, k, thr):
    out = {}
    for jid in job_ids:
        ranked = sorted(cands_by_job[jid], key=lambda c: (-score_of(jid, c[0]), c[0]))
        rels = [r for _, r in ranked]
        out[jid] = {"ndcg@k": M.ndcg_at_k(rels, k), "p@k": M.precision_at_k(rels, k, thr), "mrr": M.mrr(rels, thr)}
    return out


def summarise(per_job, name, n_boot, seed):
    vals = [v[name] for v in per_job.values()]
    lo, hi = M.bootstrap_ci(vals, n_boot, seed)
    return {"mean": M.mean(vals), "ci_low": lo, "ci_high": hi}


def run(data_dir, out_dir, k=5, threshold=2, use_sbert=True, seed=42, grid_step=0.1, n_boot=2000):
    resumes, jobs, labels = load_dataset(data_dir)
    matcher = SkillMatcher.from_seed()
    sbert, note = (try_sbert() if use_sbert else (None, "SBERT disabled by option"))
    mode = "sbert" if sbert else "tfidf"
    profiles = {rid: analyse_resume(r["text"], matcher) for rid, r in resumes.items()}
    janalyses = {jid: analyse_job_text(j["text"], matcher) for jid, j in jobs.items()}
    comps = {}
    for (jid, rid) in labels:
        res = score_pair(profiles[rid], janalyses[jid], matcher, mode=mode, sbert=sbert)
        comps[(jid, rid)] = {c["name"]: c["score"] for c in res["components"]}
    by_job = {j: c for j, c in candidates_by_job(labels).items() if len(c) >= 2 and any(r >= threshold for _, r in c)}
    all_jobs = sorted(by_job)
    rng = random.Random(seed)
    shuffled = all_jobs[:]
    rng.shuffle(shuffled)
    split = len(shuffled) >= 4
    dev, test = (shuffled[: len(shuffled) // 2], shuffled[len(shuffled) // 2:]) if split else (all_jobs, all_jobs)

    def with_weights(w):
        return lambda j, r: combine_scores(comps[(j, r)], w)

    only = lambda key: (lambda j, r: comps[(j, r)].get(key) or 0.0)
    methods = {"skills_only": only("skills"), "semantic_only": only("semantic"), "hybrid_default": with_weights(DEFAULT_WEIGHTS)}
    for c in ORDER:
        w = dict(DEFAULT_WEIGHTS)
        w[c] = 0.0
        methods[f"ablation_without_{c}"] = with_weights(w)

    n = round(1 / grid_step)
    best, best_key = None, None
    for comp in compositions(n, len(ORDER)):
        w = {key: v / n for key, v in zip(ORDER, comp)}
        score = M.mean([v["ndcg@k"] for v in evaluate(with_weights(w), by_job, dev, k, threshold).values()]) or 0.0
        dist = sum(abs(w[key] - DEFAULT_WEIGHTS[key]) for key in ORDER)
        key = (round(score, 6), -dist)
        if best_key is None or key > best_key:
            best_key, best = key, w
    methods["hybrid_tuned_on_dev"] = with_weights(best)

    on_all = {m: evaluate(f, by_job, all_jobs, k, threshold) for m, f in methods.items()}
    on_test = {m: evaluate(f, by_job, test, k, threshold) for m, f in methods.items()}
    table = {"all_jobs": {m: {n_: summarise(v, n_, n_boot, seed) for n_ in ("ndcg@k", "p@k", "mrr")} for m, v in on_all.items()},
             "held_out_jobs": {m: {n_: summarise(v, n_, n_boot, seed) for n_ in ("ndcg@k", "p@k", "mrr")} for m, v in on_test.items()}}
    cmp_ = M.paired_bootstrap([on_all["hybrid_default"][j]["ndcg@k"] for j in all_jobs], [on_all["skills_only"][j]["ndcg@k"] for j in all_jobs], n_boot, seed)
    payload = {"experiment": "exp2_skill_vs_hybrid", "k": k, "semantic_mode": mode, "sbert_note": note, "n_jobs": len(all_jobs),
               "split": {"dev_jobs": len(dev), "test_jobs": len(test), "held_out": split}, "default_weights": DEFAULT_WEIGHTS,
               "tuned_weights_on_dev": best, "grid_step": grid_step, "results": table,
               "hybrid_vs_skills_only_ndcg_all_jobs": cmp_, "environment": environment_info(seed, data_dir)}
    rows = [[m] + [f"{fmt(table['all_jobs'][m]['ndcg@k']['mean'])}", f"{fmt(table['held_out_jobs'][m]['ndcg@k']['mean'])}",
                   f"{fmt(table['all_jobs'][m]['p@k']['mean'])}"] for m in methods]
    md = [f"# Experiment 2: skill matching vs hybrid model (K={k})", "",
          f"Semantic component method: **{mode}**. Jobs: {len(all_jobs)} (development {len(dev)}, held-out {len(test)})."
          + ("" if split else " Fewer than 4 jobs: no held-out split was possible, so tuned weights are NOT validated."), "",
          md_table(["Method", f"nDCG@{k} (all jobs)", f"nDCG@{k} (held-out)", f"P@{k} (all jobs)"], rows), "",
          f"Tuned weights (best on development jobs, step {grid_step}): " + ", ".join(f"{key}={best[key]:.2f}" for key in ORDER),
          f"Default weights: " + ", ".join(f"{key}={DEFAULT_WEIGHTS[key]:.2f}" for key in ORDER), "",
          f"Hybrid minus skills-only nDCG@{k}: {fmt(cmp_['mean_diff'])}, 95% CI [{fmt(cmp_['ci'][0])}, {fmt(cmp_['ci'][1])}], p = {fmt(cmp_['p_value'])}.", "",
          "Only claim an improvement if the held-out interval excludes 0. Ablation rows show how much each component matters; tuned weights from a small dataset may not generalise."]
    if note:
        md.append(f"\nNote: {note}")
    write_results(out_dir, "exp2_skill_vs_hybrid", payload, "\n".join(md))
    return payload


if __name__ == "__main__":
    ap = common_args(__doc__)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--threshold", type=int, default=2)
    ap.add_argument("--grid-step", type=float, default=0.1)
    a = ap.parse_args()
    run(a.data, a.out, a.k, a.threshold, not a.no_sbert, a.seed, a.grid_step)
    print("Results written to", a.out)
