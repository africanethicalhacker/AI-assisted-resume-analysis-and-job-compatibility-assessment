"""Shared helpers: dataset loading, reproducibility metadata, output writing."""
import csv
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone

DATA_FILES = ("resumes.jsonl", "jobs.jsonl", "labels.csv", "gold_extraction.jsonl", "groups.csv")


def load_jsonl(path):
    with open(path, encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def load_dataset(data_dir):
    resumes = {r["id"]: r for r in load_jsonl(os.path.join(data_dir, "resumes.jsonl"))}
    jobs = {j["id"]: j for j in load_jsonl(os.path.join(data_dir, "jobs.jsonl"))}
    labels = {}
    with open(os.path.join(data_dir, "labels.csv"), encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["resume_id"] in resumes and row["job_id"] in jobs:
                labels[(row["job_id"], row["resume_id"])] = int(row["relevance"])
    return resumes, jobs, labels


def candidates_by_job(labels):
    out = {}
    for (jid, rid), rel in sorted(labels.items()):
        out.setdefault(jid, []).append((rid, rel))
    return out


def load_groups(data_dir):
    path = os.path.join(data_dir, "groups.csv")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["resume_id"]: r["group"] for r in csv.DictReader(fh)}


def fingerprint(data_dir):
    h = hashlib.sha256()
    for name in DATA_FILES:
        p = os.path.join(data_dir, name)
        if os.path.exists(p):
            h.update(name.encode())
            with open(p, "rb") as fh:
                h.update(fh.read())
    return h.hexdigest()[:16]


def environment_info(seed=None, data_dir=None):
    info = {"python": sys.version.split()[0], "platform": platform.platform(), "seed": seed,
            "timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
    for mod in ("sklearn", "sentence_transformers", "numpy"):
        try:
            info[mod] = __import__(mod).__version__
        except Exception:  # noqa: BLE001
            info[mod] = None
    if data_dir:
        info["dataset_fingerprint"] = fingerprint(data_dir)
    return info


def try_sbert():
    """Return a working SbertMatcher, or None (with a reason) if the model cannot be loaded."""
    try:
        from app.ai.matching.sbert import SbertMatcher

        s = SbertMatcher()
        s.coverage(["test sentence"], ["test sentence"])
        return s, ""
    except Exception as exc:  # noqa: BLE001
        return None, f"SBERT unavailable: {type(exc).__name__}: {exc}"


def fmt(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def md_table(headers, rows):
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def write_results(out_dir, name, payload, markdown):
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, name + ".json"), "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True, default=str)
    with open(os.path.join(out_dir, name + ".md"), "w", encoding="utf-8") as fh:
        fh.write(markdown)


def common_args(description):
    import argparse

    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("--data", default="experiments/data", help="folder with resumes.jsonl, jobs.jsonl, labels.csv ...")
    ap.add_argument("--out", default="experiments/results")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-sbert", action="store_true", help="skip Sentence-BERT (TF-IDF only)")
    return ap
