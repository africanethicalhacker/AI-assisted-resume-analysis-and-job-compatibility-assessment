# Chapter 9: Database Design
Eleven normalised tables: users, resumes, candidate_profiles, skills, candidate_skills, job_descriptions, job_requirements,
assessments, assessment_details, recommendations, audit_logs. The full MySQL DDL with keys, indexes and constraints is in
`docs/schema.sql`, and the SQLAlchemy models are in `app/models/`. Migrations are generated with Flask-Migrate (`flask db migrate`).

Design notes: foreign keys cascade on user deletion, except `audit_logs.user_id`, which is deliberately not a foreign key so audit
rows never change when an account is erased. Sensitive columns (original file name, profile JSON, evidence, job text) hold AES-GCM
ciphertext. Check constraints enforce roles, score ranges, strengths and kinds. `assessments.meta` stores the semantic details, integrity
flags, configuration snapshot and gap report; `recommendations` stores fit score and evidence level.
Add the updated ER diagram from `docs/diagrams.md`.
