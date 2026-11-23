import json
import os

import pytest

from experiments import exp1_matching, exp2_hybrid, exp3_extraction, exp4_performance, exp6_fairness, metrics as M, synthetic_data


def test_ranking_metrics_hand_computed():
    assert M.precision_at_k([3, 0, 2, 0], 2) == 0.5
    assert M.recall_at_k([3, 0, 2, 0], 2) == 0.5
    assert M.recall_at_k([0, 0], 2) is None
    assert M.mrr([0, 1, 3]) == pytest.approx(1 / 3)
    assert M.ndcg_at_k([0, 1], 2) == pytest.approx((1 / 1.5849625007211562) / 1.0, abs=1e-9)   # 1/log2(3) over ideal 1/log2(2)
    assert M.ndcg_at_k([3, 2, 1, 0], 4) == pytest.approx(1.0)
    assert M.ndcg_at_k([0, 0, 0], 3) is None
    p, r, f = M.prf(8, 2, 8)
    assert (p, r) == (0.8, 0.5) and f == pytest.approx(2 * 0.8 * 0.5 / 1.3)


def test_bootstrap_is_reproducible_and_sensible():
    vals = [0.2, 0.4, 0.6, 0.8, 1.0]
    assert M.bootstrap_ci(vals, 500, seed=1) == M.bootstrap_ci(vals, 500, seed=1)
    lo, hi = M.bootstrap_ci(vals, 500, seed=1)
    assert lo <= 0.6 <= hi
    same = M.paired_bootstrap([0.5, 0.6, 0.7, 0.4], [0.5, 0.6, 0.7, 0.4], 500)
    assert same["mean_diff"] == 0 and same["p_value"] == 1.0
    clear = M.paired_bootstrap([0.9, 0.8, 0.85, 0.95, 0.9], [0.1, 0.2, 0.15, 0.1, 0.2], 1000)
    assert clear["ci"][0] > 0 and clear["p_value"] < 0.05


@pytest.fixture(scope="module")
def data_dir(tmp_path_factory):
    d = str(tmp_path_factory.mktemp("synthetic"))
    synthetic_data.generate(d, n_resumes=16, seed=3)
    return d


def test_smoke_all_experiments_run_and_are_reproducible(data_dir, tmp_path):
    out1, out2 = str(tmp_path / "a"), str(tmp_path / "b")
    r1 = exp1_matching.run(data_dir, out1, k=3, use_sbert=False, n_boot=200)
    assert r1["n_jobs_evaluated"] == 4 and set(r1["aggregate"]) == {"tfidf"}
    for v in r1["aggregate"]["tfidf"].values():
        assert 0.0 <= v["mean"] <= 1.0
    again = exp1_matching.run(data_dir, out2, k=3, use_sbert=False, n_boot=200)
    assert json.dumps(r1["aggregate"], sort_keys=True) == json.dumps(again["aggregate"], sort_keys=True)

    r2 = exp2_hybrid.run(data_dir, out1, k=3, use_sbert=False, grid_step=0.25, n_boot=200)
    assert abs(sum(r2["tuned_weights_on_dev"].values()) - 1.0) < 1e-9 and r2["split"]["held_out"] is True
    assert "hybrid_default" in r2["results"]["all_jobs"] and "ablation_without_skills" in r2["results"]["all_jobs"]

    r3 = exp3_extraction.run(data_dir, out1)
    assert r3["n_resumes"] == 16 and 0 <= r3["skills_micro"]["f1"] <= 1 and r3["email_exact_match"] == 1.0

    r4 = exp4_performance.run(data_dir, out1, n=5, use_sbert=False)
    assert r4["stage_seconds"]["extract_profile"]["n"] == 5 and r4["stage_seconds"]["full_score_pair"]["mean"] > 0

    r6 = exp6_fairness.run(data_dir, out1, k=3, use_sbert=False, max_resumes=4, max_jobs=2)
    assert r6["counterfactual"]["name"]["n"] > 0 and r6["selection"]["n_jobs"] >= 1
    for name in ("exp1_tfidf_vs_sbert", "exp2_skill_vs_hybrid", "exp3_extraction", "exp4_performance", "exp6_fairness"):
        assert os.path.exists(os.path.join(out1, name + ".md")) and os.path.exists(os.path.join(out1, name + ".json"))
