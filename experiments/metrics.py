"""Evaluation metrics. `rels` is the list of relevance grades (0-3) in RANKED order, best first.

P@K        = (# relevant in top K) / K                       relevant means grade >= threshold
R@K        = (# relevant in top K) / (# relevant overall)
DCG@K      = sum_{i=1..K} grade_i / log2(i + 1)              (linear gain, Jarvelin and Kekalainen 2002)
nDCG@K     = DCG@K / DCG@K of the ideal ordering
MRR        = 1 / rank of the first relevant item
"""
import math
import random


def precision_at_k(rels, k, thr=2):
    return sum(r >= thr for r in rels[:k]) / k if k else 0.0


def recall_at_k(rels, k, thr=2):
    total = sum(r >= thr for r in rels)
    return None if total == 0 else sum(r >= thr for r in rels[:k]) / total


def dcg_at_k(rels, k):
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels[:k]))


def ndcg_at_k(rels, k):
    ideal = dcg_at_k(sorted(rels, reverse=True), k)
    return None if ideal == 0 else dcg_at_k(rels, k) / ideal


def mrr(rels, thr=2):
    for i, r in enumerate(rels):
        if r >= thr:
            return 1.0 / (i + 1)
    return 0.0


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def bootstrap_ci(values, n=2000, seed=0, alpha=0.05):
    vals = [v for v in values if v is not None]
    if len(vals) < 2:
        return None, None
    rng = random.Random(seed)
    means = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(n))
    return means[int(n * alpha / 2)], means[int(n * (1 - alpha / 2)) - 1]


def paired_bootstrap(a, b, n=5000, seed=0):
    """Compare two methods measured on the same items. Returns mean difference (a - b), 95% CI, two-sided p."""
    pairs = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pairs) < 2:
        return {"n": len(pairs), "mean_diff": None, "ci": (None, None), "p_value": None}
    diffs = [x - y for x, y in pairs]
    rng = random.Random(seed)
    boots = sorted(sum(rng.choice(diffs) for _ in diffs) / len(diffs) for _ in range(n))
    le0 = sum(m <= 0 for m in boots) / n
    ge0 = sum(m >= 0 for m in boots) / n
    return {"n": len(pairs), "mean_diff": sum(diffs) / len(diffs), "ci": (boots[int(n * 0.025)], boots[int(n * 0.975) - 1]),
            "p_value": min(1.0, 2 * min(le0, ge0))}
