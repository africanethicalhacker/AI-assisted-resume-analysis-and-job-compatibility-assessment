# Abstract

Recruitment teams and candidates increasingly depend on software to compare resumes with job descriptions, yet common
tools rely on keyword filters, give scores without explanation, and concentrate sensitive personal data without strong
protection. This project designs, implements and evaluates a secure, web-based decision-support platform for resume
analysis and job-compatibility assessment, built for a cyber security audience.

The platform accepts PDF and DOCX resumes through a layered upload pipeline (extension, magic-byte, structure and
malware checks), extracts structured information with source evidence, identifies skills against an administrator-extensible
taxonomy (labelling each as explicit or inferred), analyses job descriptions, and computes an explainable compatibility score.
The score is hybrid: skill coverage, Sentence-BERT semantic similarity (all-MiniLM-L6-v2) with a TF-IDF baseline, education,
experience, and projects and certifications, combined by configurable weights whose initial values (35/25/15/15/10) are treated
as hypotheses to be validated. The system also reports skill gaps, evidence-based role recommendations with learning roadmaps,
an interactive dashboard, and downloadable PDF reports.

Security is integral: Argon2id password hashing, AES-256-GCM envelope encryption of stored data, role-based access control with
ownership checks, CSRF and XSS defences, rate limiting, a tamper-evident audit log, data export and erasure, and AI-specific
protections against prompt injection, score manipulation and data leakage. All scoring is deterministic arithmetic, so text
inside a document cannot alter a score, and resume content never leaves the server.

Evaluation is designed as six reproducible experiments (TF-IDF versus SBERT, skill matching versus hybrid with held-out weight
validation, extraction accuracy, performance, security testing, and bias screening) using precision, recall, F1, Precision@K,
Recall@K, nDCG, time and memory, with bootstrap confidence intervals. The thesis reports only measured results and states
the limits of its dataset.

**Keywords:** resume screening, semantic similarity, Sentence-BERT, explainable AI, secure software development, prompt injection, decision support.
