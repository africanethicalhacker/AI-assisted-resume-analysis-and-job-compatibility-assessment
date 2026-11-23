"""Collect experiment outputs into one Markdown file for the thesis (docs/report/results_auto.md).
Only experiments that were actually run appear; missing ones are listed as NOT RUN. Nothing is invented."""
import os

NAMES = [("exp1_tfidf_vs_sbert", "Experiment 1"), ("exp2_skill_vs_hybrid", "Experiment 2"), ("exp3_extraction", "Experiment 3"),
         ("exp4_performance", "Experiment 4"), ("exp6_fairness", "Experiment 6")]


def main(results="experiments/results", out="docs/report/results_auto.md"):
    parts = ["# Experimental results (auto-collected)", ""]
    for stem, label in NAMES:
        p = os.path.join(results, stem + ".md")
        parts.append(open(p, encoding="utf-8").read() if os.path.exists(p) else f"## {label}\n\nNOT RUN yet. No results are reported.")
        parts.append("")
    sec = "docs/security_test_results.md"
    parts.append(open(sec, encoding="utf-8").read() if os.path.exists(sec) else "## Experiment 5\n\nNOT RUN yet. Run `python -m experiments.run_security_suite`.")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(parts))
    print("Wrote", out)


if __name__ == "__main__":
    main()
