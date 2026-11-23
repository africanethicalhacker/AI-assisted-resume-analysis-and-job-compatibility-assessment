# Chapter 4: Existing and Proposed System

## 4.1 Existing practice
Keyword-based applicant tracking filters and manual review. Typical limits: exact-match dependence, opaque scoring, little
treatment of upload or AI threats, and no feedback to candidates.

## 4.2 Proposed system
| Aspect | Typical existing tool | This system |
|---|---|---|
| Matching | Keywords | TF-IDF baseline + Sentence-BERT + structured skills, education, experience |
| Explanation | Single score | Per-component scores, weights, points added, evidence snippets |
| Requirement strength | Assumed | Mandatory only when the text supports it |
| Skills | Present or absent | Explicit versus inferred, with confidence |
| Uploads | Basic type check | Extension, magic-byte, structure, macro, zip-bomb and malware checks, fail-closed |
| Stored data | Plaintext | AES-256-GCM envelope encryption, ownership checks, erasure and export |
| AI manipulation | Not addressed | Deterministic scoring, injection flagging and exclusion, stuffing detection |
| Validation | Assumed | Held-out evaluation, confidence intervals, fairness screening |
