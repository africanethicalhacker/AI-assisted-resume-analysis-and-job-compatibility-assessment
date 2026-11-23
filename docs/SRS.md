# Software Requirements Specification (summary and traceability)

Approved in Phase 1. Full text of the requirements is in the Phase 1 document; this file adds traceability to the implementation.

## Functional requirements and where they are implemented
| ID | Requirement | Implementation | Tests |
|---|---|---|---|
| FR-01 | Register, log in, log out, reset password | `routes/auth.py`, `services/auth_service.py` | `test_auth.py`, `test_passwords.py` |
| FR-02 | Candidate and administrator roles, server-side authorisation | `security/rbac.py` | `test_access_control.py` |
| FR-03 | Secure PDF/DOCX upload with validation and malware scanning | `security/validators.py`, `scanner.py`, `services/resume_service.py` | `test_validators.py`, `test_upload.py` |
| FR-04 | Extract name, contacts, education, skills, certifications, experience, projects, achievements with evidence | `ai/parsing/*` | `test_extraction.py` |
| FR-05 | Never invent missing information | `extractor.py` (absent fields stay empty) | `test_no_invention_on_sparse_text` |
| FR-06 | Skill taxonomy; explicit versus inferred | `ai/skills/taxonomy.py` | `test_explicit_vs_inferred_never_duplicate` |
| FR-07 | Administrator manages the taxonomy | `routes/admin.py` (`/admin/skills`) | `test_admin_can_add_skill_and_candidate_cannot` |
| FR-08 | Job description analysis (paste or upload) | `ai/jobs/analyzer.py`, `services/job_service.py` | `test_job_analysis_strengths_and_no_assumptions` |
| FR-09 | Mandatory, preferred, optional only when supported | `analyzer.py` | `test_unlabelled_text_is_not_assumed_mandatory` |
| FR-10 | TF-IDF cosine and Sentence-BERT similarity | `ai/matching/tfidf.py`, `sbert.py`, `similarity.py` | `test_tfidf_matches_scikit_learn`, `test_semantic_modes_and_fallbacks` |
| FR-11 | Component scores normalised to 0-100 | `ai/matching/scoring.py` | `test_matching.py` |
| FR-12 | Configurable weights; contribution per component | `scoring.py`, `services/scoring_config.py` | `test_final_score_weights_and_renormalisation`, `test_admin_can_change_weights_and_invalid_sum_rejected` |
| FR-13 | Matching, missing, partial, additional skills | `ai/recommend/gap.py` | `test_gap_structure_and_priorities` |
| FR-14 | Role recommendations with certifications and roadmap | `ai/recommend/roles.py` | `test_recommendations_evidence_based` |
| FR-15 | Dashboard with Chart.js | `routes/main.py`, `routes/api.py`, `static/js/dashboard.js` | `test_dashboard.py` |
| FR-16 | Downloadable PDF report with twelve sections | `reporting/pdf_report.py` | `test_pdf_contains_all_twelve_sections` |
| FR-17 | View, download, delete own data | `routes/account.py`, `services/account_service.py` | `test_delete_account_requires_password_and_erases_everything`, `test_export_contains_only_own_data` |
| FR-18 | Audit logging | `security/audit.py` | `test_audit_chain_verifies_and_detects_tampering` |
| FR-19 | Administrators manage users/config without reading resume content | `routes/admin.py`, `rbac.py` | `test_admin_cannot_read_resume_content_pages` |
| FR-20 | Scoring configuration stored with each assessment | `assessment_service.py` | `test_assessment_end_to_end` |
| FR-21 | Administrators post jobs and can correct the detected requirements, open or close a job and set the match needed | `routes/admin.py` (`/admin/jobs`), `services/job_service.py` | `test_admin_posts_job_and_candidate_sees_it`, `test_admin_can_correct_requirement_strength_and_it_changes_the_verdict` |
| FR-22 | Candidates browse open jobs on a job board | `routes/board.py` | `test_admin_posts_job_and_candidate_sees_it`, `test_closed_job_is_hidden_and_cannot_be_checked` |
| FR-23 | A candidate uploads a CV for a posted job and receives a match percentage and an eligibility verdict with reasons | `services/board_service.py`, `ai/matching/eligibility.py` | `test_candidate_uploads_cv_and_gets_percentage_and_verdict`, `test_eligibility.py` |
| FR-24 | Administrators see only totals for a posted job, never candidate CVs or individual results | `services/job_service.py` (`posting_stats`), role checks | `test_admin_sees_only_aggregates_never_candidate_data` |

## Non-functional requirements
| Area | Requirement | Where |
|---|---|---|
| Security | Argon2id, AES-256-GCM, TLS, CSRF/XSS/SQLi defences, rate limits, headers, audit | Chapter 8 |
| Explainability | Every score traceable to components and evidence | assessment page and PDF report |
| Reproducibility | Weights and model version stored; experiments seeded | `assessments.weights_used`, `experiments/` |
| Maintainability | Layered modules, tests, configuration via environment | project layout |
| Privacy | Data minimisation, retention purge, export, erasure, no external AI | `account_service`, `purge_expired.py` |
| Performance | Targets set from Experiment 4 measurements, not assumed | `experiments/exp4_performance.py` |
