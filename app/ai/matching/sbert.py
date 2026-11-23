"""Sentence-BERT semantic similarity (all-MiniLM-L6-v2 by default).

MiniLM reads at most ~256 word-pieces, so long documents are split into passages.
Coverage score: for each job passage j, take its best-matching resume passage, then average:

    coverage = (1/m) * sum_j max_i cos(J_j, R_i)

This answers "how much of what the job describes is addressed somewhere in the resume".
The encoder can be injected (used by tests); otherwise the model is loaded lazily, once.
"""
import math
import threading

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def chunk_text(text: str, max_words: int = 120, max_chunks: int = 60) -> list:
    chunks, cur, n = [], [], 0
    for line in (text or "").split("\n"):
        words = line.split()
        if not words:
            continue
        if cur and n + len(words) > max_words:
            chunks.append(" ".join(cur))
            cur, n = [], 0
        while len(words) > max_words:
            chunks.append(" ".join(words[:max_words]))
            words = words[max_words:]
        cur.extend(words)
        n += len(words)
    if cur:
        chunks.append(" ".join(cur))
    return chunks[:max_chunks]


def _unit(vec):
    v = [float(x) for x in vec]
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v] if norm else v


class SbertMatcher:
    def __init__(self, model_name: str = DEFAULT_MODEL, encoder=None):
        self.model_name = model_name
        self._encoder = encoder
        self._lock = threading.Lock()

    def _load(self):
        if self._encoder is None:
            with self._lock:
                if self._encoder is None:
                    from sentence_transformers import SentenceTransformer

                    model = SentenceTransformer(self.model_name)
                    self._encoder = lambda texts: model.encode(
                        texts, normalize_embeddings=True, show_progress_bar=False).tolist()
        return self._encoder

    def coverage(self, job_chunks: list, resume_chunks: list) -> float:
        if not job_chunks or not resume_chunks:
            return 0.0
        vecs = [_unit(v) for v in self._load()(list(job_chunks) + list(resume_chunks))]
        jv, rv = vecs[:len(job_chunks)], vecs[len(job_chunks):]
        best = [max(sum(a * b for a, b in zip(j, r)) for r in rv) for j in jv]
        return max(0.0, min(1.0, sum(best) / len(best)))
