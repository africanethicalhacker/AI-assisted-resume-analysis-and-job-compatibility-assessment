# Chapter 6: System Architecture and Design

## 6.1 Architectural style
A modular monolith with five layers and one-way dependencies: presentation (Jinja2, Bootstrap, Chart.js), application (Flask
blueprints and thin controllers), AI processing (pure, stateless functions), security (validation, cryptography, RBAC, audit) and
data/reporting (SQLAlchemy, encrypted file store, ReportLab). A monolith suits a single-developer project: one process plus MySQL
and ClamAV, with the separation of concerns an examiner can inspect, and without the network attack surface of microservices.

## 6.2 Key design decisions
1. Application factory and blueprints for testable configuration.
2. A service layer enforces ownership in one place (prevents inconsistent broken access control).
3. AI modules are pure functions, so experiments reuse them without a database (`app/ai/pipeline.py`).
4. Deterministic scoring: no language model produces or adjusts a score.
5. Local NLP only; no external AI API is used and a test enforces this.
6. Envelope encryption: a data key per file wrapped by a master key held outside the database.
7. Evidence preservation: every extracted field carries source text and offsets.
8. Reproducibility: each assessment stores the weights and model version it used.
9. A hash-chained audit log for tamper evidence.

## 6.3 Diagrams
Place here the diagrams from the Phase 2 document (layered architecture, DFD levels 0 to 2, use case, class, sequence, activity,
deployment) and the updated ER diagram in `docs/diagrams.md`. Mermaid source can be exported from mermaid.live as PNG or SVG.

## 6.4 Project structure
`app/` (models, routes, services, ai, security, reporting, templates, static), `experiments/`, `tests/`, `scripts/`, `docs/`.
