"""Experiment 4: processing time and memory.

Measures per-stage wall time (perf_counter), Python heap peak (tracemalloc) per resume, process peak
RSS, and optionally PDF/DOCX reading time for real files. Numbers depend on YOUR hardware; always report
the machine (printed in the results). Run: python -m experiments.exp4_performance --n 30 [--files DIR]
"""
import os
import resource
import statistics
import time
import tracemalloc

from app.ai.matching.sbert import chunk_text
from app.ai.matching.tfidf import tfidf_cosine
from app.ai.pipeline import analyse_job_text, analyse_resume, score_pair
from app.ai.skills.taxonomy import SkillMatcher

from .common import common_args, environment_info, fmt, load_dataset, md_table, try_sbert, write_results


def stats(xs):
    if not xs:
        return {"n": 0}
    s = sorted(xs)
    return {"n": len(xs), "mean": statistics.fmean(xs), "median": statistics.median(xs),
            "p95": s[min(len(s) - 1, int(0.95 * len(s)))], "max": s[-1]}


def run(data_dir, out_dir, n=30, use_sbert=True, files_dir=None, seed=42):
    resumes, jobs, _ = load_dataset(data_dir)
    matcher = SkillMatcher.from_seed()
    job = analyse_job_text(next(iter(jobs.values()))["text"], matcher)
    sbert, note = (try_sbert() if use_sbert else (None, "SBERT disabled by option"))
    t = {"extract_profile": [], "tfidf": [], "sbert": [], "full_score_pair": []}
    heap = []
    rss0 = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    load_s = None
    if sbert:
        t0 = time.perf_counter()
        sbert._load()
        load_s = time.perf_counter() - t0
    for r in list(resumes.values())[:n]:
        tracemalloc.start()
        t0 = time.perf_counter()
        prof = analyse_resume(r["text"], matcher)
        t["extract_profile"].append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        tfidf_cosine(prof["text"], job["text"])
        t["tfidf"].append(time.perf_counter() - t0)
        if sbert:
            t0 = time.perf_counter()
            sbert.coverage(chunk_text(job["text"]), chunk_text(prof["text"]))
            t["sbert"].append(time.perf_counter() - t0)
        t0 = time.perf_counter()
        score_pair(prof, job, matcher, mode="sbert" if sbert else "tfidf", sbert=sbert)
        t["full_score_pair"].append(time.perf_counter() - t0)
        heap.append(tracemalloc.get_traced_memory()[1] / 1e6)
        tracemalloc.stop()
    file_times = []
    if files_dir:
        from app.ai.parsing.readers import DOCX_MIME, PDF_MIME, read_document
        for f in sorted(os.listdir(files_dir)):
            mime = PDF_MIME if f.lower().endswith(".pdf") else DOCX_MIME if f.lower().endswith(".docx") else None
            if mime:
                data = open(os.path.join(files_dir, f), "rb").read()
                t0 = time.perf_counter()
                read_document(data, mime)
                file_times.append(time.perf_counter() - t0)
    payload = {"experiment": "exp4_performance", "n_resumes": min(n, len(resumes)), "stage_seconds": {k: stats(v) for k, v in t.items()},
               "file_read_seconds": stats(file_times), "python_heap_peak_mb": stats(heap), "sbert_load_seconds": load_s, "sbert_note": note,
               "process_peak_rss_mb_start": rss0, "process_peak_rss_mb_end": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
               "environment": environment_info(seed, data_dir)}
    rows = [[k, v.get("n", 0), fmt(v.get("mean"), 4), fmt(v.get("median"), 4), fmt(v.get("p95"), 4), fmt(v.get("max"), 4)] for k, v in payload["stage_seconds"].items()]
    if file_times:
        v = payload["file_read_seconds"]
        rows.append(["read_pdf_docx", v["n"], fmt(v["mean"], 4), fmt(v["median"], 4), fmt(v["p95"], 4), fmt(v["max"], 4)])
    md = ["# Experiment 4: performance", "", md_table(["Stage", "n", "mean s", "median s", "p95 s", "max s"], rows), "",
          f"- SBERT model load: {fmt(load_s, 2)} s (one-off per process). {note}",
          f"- Python heap peak per resume (MB): mean {fmt(payload['python_heap_peak_mb'].get('mean'), 2)}, max {fmt(payload['python_heap_peak_mb'].get('max'), 2)}",
          f"- Process peak RSS (MB): {payload['process_peak_rss_mb_start']:.0f} before, {payload['process_peak_rss_mb_end']:.0f} after",
          f"- Machine: {payload['environment']['platform']}, Python {payload['environment']['python']}", "",
          "RSS includes the loaded model and libraries; heap numbers cover Python allocations only (native model memory is not counted by tracemalloc)."]
    write_results(out_dir, "exp4_performance", payload, "\n".join(md))
    return payload


if __name__ == "__main__":
    ap = common_args(__doc__)
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--files", default=None, help="folder of real PDF/DOCX resumes to time the file readers")
    a = ap.parse_args()
    run(a.data, a.out, a.n, not a.no_sbert, a.files, a.seed)
    print("Results written to", a.out)
