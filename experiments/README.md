# Experiments (Phase 17)

All experiments read one dataset folder (default `experiments/data/`) and write `experiments/results/*.json|md`.
Nothing here fabricates results: if you do not run an experiment, the report says NOT RUN.

## Data you must provide
Use consented, anonymised, synthetic-with-disclosure, or properly licensed resumes. Check each public dataset's licence
(for example Kaggle resume sets vary) and remove personal data before use. Aim for at least 30 resumes and 8 jobs, ideally more.

| File | Format |
|---|---|
| `resumes.jsonl` | `{"id": "R001", "text": "full plain-text resume"}` per line |
| `jobs.jsonl` | `{"id": "J001", "text": "full job description"}` per line |
| `labels.csv` | `job_id,resume_id,relevance` with grade 0 (not suitable) to 3 (excellent), made by people (ideally 2 annotators; report agreement) |
| `gold_extraction.jsonl` | per resume: `{"id","name","email","skills":[taxonomy names],"certifications":[],"highest_education_level","professional_months"}` (any subset of fields) |
| `groups.csv` | optional `resume_id,group` for selection-rate analysis (only with consent and ethics approval) |

`python -m experiments.synthetic_data experiments/data_synthetic` makes SYNTHETIC data to test that the scripts run.
Scores on it mean nothing, because the labels come from the same templates that wrote the text.

## Run (from the project root, venv active)
```
python -m experiments.exp1_matching     --data experiments/data --k 5
python -m experiments.exp2_hybrid       --data experiments/data --k 5 --grid-step 0.1
python -m experiments.exp3_extraction   --data experiments/data
python -m experiments.exp4_performance  --data experiments/data --n 30 --files path/to/real_resume_files
python -m experiments.run_security_suite
python -m experiments.exp6_fairness     --data experiments/data --k 5
python -m experiments.make_report_tables
```
Add `--no-sbert` to skip Sentence-BERT. Seeds are fixed (`--seed`), and each result file records the environment and a dataset fingerprint.

## Reporting rules
1. Report the dataset size, source, labelling method and limits next to every table.
2. Report confidence intervals; claim an improvement only when the interval excludes 0.
3. Tune weights on development jobs and report held-out results only.
4. Report negative or mixed results honestly.
