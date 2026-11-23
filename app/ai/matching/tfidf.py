"""TF-IDF and cosine similarity, implemented from first principles (explainable for the viva).

tf(t, d)    = 1 + ln(count(t, d))                     (sublinear term frequency)
idf(t)      = ln((1 + N) / (1 + df(t))) + 1           (smoothed inverse document frequency)
w(t, d)     = tf(t, d) * idf(t), then L2-normalised
cos(a, b)   = sum_t w(t, a) * w(t, b)                 (dot product of unit vectors)

Terms are lower-cased unigrams plus bigrams after stop-word removal. By default the IDF
statistics come from the two documents being compared; pass `corpus` to use a larger
background collection (used in Experiment 1).
"""
import math
import re
from collections import Counter

STOP_WORDS = frozenset(
    "a an and are as at be been being but by for from has have had he her his i in into is it its of on or our "
    "she that the their them they this to was we were will with you your not no can may should would could "
    "also such than then there these those who which while within across including etc using use used".split())
TOKEN_PATTERN = r"[a-z0-9][a-z0-9+#]*"  # nosec B105 - a regular expression, not a credential
_TOKEN = re.compile(TOKEN_PATTERN)


def tokenize(text: str) -> list:
    return [t for t in _TOKEN.findall((text or "").lower()) if t not in STOP_WORDS]


def terms(text: str) -> list:
    toks = tokenize(text)
    return toks + [a + " " + b for a, b in zip(toks, toks[1:])]


def _vector(term_list, idf):
    v = {t: (1 + math.log(n)) * idf[t] for t, n in Counter(term_list).items()}
    norm = math.sqrt(sum(x * x for x in v.values()))
    return {t: x / norm for t, x in v.items()} if norm else {}


def tfidf_cosine(a: str, b: str, corpus=None) -> float:
    docs = [terms(a), terms(b)] + [terms(c) for c in (corpus or [])]
    df = Counter()
    for tl in docs:
        df.update(set(tl))
    n = len(docs)
    idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
    va, vb = _vector(docs[0], idf), _vector(docs[1], idf)
    if not va or not vb:
        return 0.0
    small, large = (va, vb) if len(va) <= len(vb) else (vb, va)
    return max(0.0, min(1.0, sum(x * large.get(t, 0.0) for t, x in small.items())))
