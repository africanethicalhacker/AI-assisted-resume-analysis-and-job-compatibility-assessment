"""Resume-to-job text similarity: TF-IDF, SBERT, or a blend, with an honest fallback."""
from ...security.sanitise import detect_injection
from .sbert import chunk_text
from .tfidf import tfidf_cosine

MODES = ("sbert", "tfidf", "blend")


def strip_flagged_lines(text: str):
    """Drop lines that look like instructions to an AI before any matching. Returns (clean_text, removed_count)."""
    kept, removed = [], 0
    for line in (text or "").split("\n"):
        if line.strip() and detect_injection(line):
            removed += 1
        else:
            kept.append(line)
    return "\n".join(kept), removed


def semantic_similarity(resume_text: str, job_text: str, mode: str = "sbert", sbert=None, alpha: float = 0.5) -> dict:
    tf = tfidf_cosine(resume_text, job_text)
    out = {"tfidf_cosine": round(tf, 4), "sbert_coverage": None, "mode_requested": mode,
           "method_used": "tfidf", "note": "", "model": None}
    sb = None
    if mode in ("sbert", "blend"):
        if sbert is None:
            out["note"] = "SBERT not available; TF-IDF used instead."
        else:
            try:
                sb = sbert.coverage(chunk_text(job_text), chunk_text(resume_text))
                out["sbert_coverage"] = round(sb, 4)
                out["model"] = sbert.model_name
            except Exception as exc:  # noqa: BLE001 - never fail an assessment because the model is missing
                out["note"] = f"SBERT failed ({type(exc).__name__}); TF-IDF used instead."
    if sb is not None and mode == "sbert":
        value, out["method_used"] = sb, "sbert"
    elif sb is not None and mode == "blend":
        value, out["method_used"] = alpha * sb + (1 - alpha) * tf, "blend"
    else:
        value = tf
    out["score"] = round(100 * max(0.0, min(1.0, value)), 2)
    return out
