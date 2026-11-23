# Chapter 11: Testing and Evaluation

## 11.1 Strategy
Unit tests for pure modules (cryptography, validators, extraction, matching, scoring, gap analysis, reports, metrics), integration
tests through the Flask test client (authentication, upload, parsing, assessments, dashboard, account), and security tests
(`tests/security`). Run with `python -m pytest -v`. The list of test cases with identifiers is in `docs/test_cases.md`.

## 11.2 Security testing (Experiment 5)
`python -m experiments.run_security_suite` runs the security-relevant tests and generates `docs/security_test_results.md` with
expected and actual results taken from the run. Complement it with OWASP ZAP (baseline and active scan of the local instance), Bandit
(`bandit -r app`) and `pip-audit`, and paste the real findings. Test only the instance you own.

## 11.3 Experiments
Experiments 1, 2, 3, 4 and 6 are described in `experiments/README.md`, with dataset format, commands, metrics and reporting rules.
Describe your dataset (source, licence or consent, size, labelling process, annotator agreement) and its limits here.
