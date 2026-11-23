"""Regenerate docs/test_cases.md from the actual test files: python scripts/generate_test_catalog.py"""
import ast
import os

root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for dp, _, files in sorted(os.walk(os.path.join(root, "tests"))):
    for f in sorted(files):
        if f.startswith("test_") and f.endswith(".py"):
            path = os.path.join(dp, f)
            for node in ast.parse(open(path, encoding="utf-8").read()).body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    rows.append((os.path.relpath(path, root), node.name, node.name[5:].replace("_", " ")))
lines = ["# Test case catalogue", "", f"{len(rows)} automated test functions (generated from the source; run `python -m pytest -v` for results).", "",
         "| ID | File | Test | What it checks |", "|---|---|---|---|"]
lines += [f"| TC-{i:03d} | `{f}` | `{n}` | {d} |" for i, (f, n, d) in enumerate(rows, 1)]
lines += ["", "Expected result for every test: PASS. Record actual results from your own run in Chapter 11, and attach the pytest summary line."]
open(os.path.join(root, "docs", "test_cases.md"), "w", encoding="utf-8").write("\n".join(lines))
print(f"Wrote docs/test_cases.md with {len(rows)} tests")
