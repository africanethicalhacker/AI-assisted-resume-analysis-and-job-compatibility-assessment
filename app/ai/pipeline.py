"""Flask-free analysis pipeline, shared by experiments and tests.

The web app wires the same functions together through its services; keeping a pure version
lets every experiment run without a database and with fixed inputs (reproducibility).
"""
from .jobs.analyzer import analyze_job
from .matching.scoring import DEFAULT_WEIGHTS, ORDER, score_assessment
from .matching.similarity import semantic_similarity, strip_flagged_lines
from .parsing.extractor import extract_profile
from ..security.sanitise import detect_injection, normalise_text


def analyse_resume(text: str, matcher, today=None) -> dict:
    clean = normalise_text(text)
    profile = extract_profile(clean, matcher, today)
    profile["text"] = clean
    profile["security"] = {"injection_findings": detect_injection(clean), "hidden_text_removed_chars": 0, "white_text_chars": 0}
    return profile


def analyse_job_text(text: str, matcher) -> dict:
    clean = normalise_text(text, 20000)
    analysis = analyze_job(clean, matcher)
    analysis["text"] = clean
    analysis["reqs"] = [{"kind": r["kind"], "text": r["requirement_text"], "strength": r["strength"]} for r in analysis["requirements"]]
    return analysis


def score_pair(profile: dict, job: dict, matcher, weights=None, mode="tfidf", sbert=None, alpha=0.5) -> dict:
    resume_clean, rm = strip_flagged_lines(profile["text"])
    job_clean, jm = strip_flagged_lines(job["text"])
    sem = semantic_similarity(resume_clean, job_clean, mode, sbert, alpha)
    return score_assessment(profile, job["reqs"], weights or DEFAULT_WEIGHTS, sem, matcher, rm + jm)


def combine_scores(component_scores: dict, weights: dict) -> float:
    """Final score from precomputed component scores (None = not applicable), renormalising weights."""
    w = sum(weights[k] for k in ORDER if component_scores.get(k) is not None)
    if w <= 0:
        return 0.0
    return sum(weights[k] * component_scores[k] for k in ORDER if component_scores.get(k) is not None) / w
