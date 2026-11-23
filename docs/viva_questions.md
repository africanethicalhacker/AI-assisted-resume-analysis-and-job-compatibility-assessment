# Viva preparation: likely questions and model answers

Answers describe what the system actually does. Where a number matters, quote your own measured results, not these notes.

## Project and design
**1. What problem does the project solve?** Keyword resume screening misses meaning, gives opaque scores and handles sensitive documents carelessly. The project gives an explainable, secure decision-support system for resume and job compatibility.

**2. Why "decision support" and not automated hiring?** Scores are imperfect and can be biased. A human must decide. The reports say so, and the system never rejects anyone.

**3. Why a modular monolith?** One developer, one deployment, strong separation of concerns without the network attack surface and operational cost of microservices.

**4. Walk me through one assessment.** Upload, validate, scan, encrypt, store; parse and extract with evidence; analyse the job; compute component scores; combine with weights; gap analysis; role recommendations; store with weights and model version; show the breakdown.

**5. How do the layers depend on each other?** Upper layers call lower ones only. The AI layer is pure (no database or HTTP), so experiments reuse it.

## NLP and ML
**6. Explain TF-IDF.** Term frequency 1 + ln(count) times smoothed inverse document frequency ln((1+N)/(1+df)) + 1, L2-normalised. Cosine similarity is the dot product of the unit vectors.

**7. Why does cosine similarity suit text?** It compares direction, not length, so a long resume and a short job description can be compared.

**8. What is Sentence-BERT and why use it?** A BERT model fine-tuned with a Siamese structure so that each text gets one fixed-size embedding. Cosine similarity then measures meaning, so "intrusion detection" and "IDS monitoring" can match. Plain BERT would need a full pass per pair.

**9. Why all-MiniLM-L6-v2?** Small (about 90 MB) and fast on CPU, with good sentence-similarity quality. It reads about 256 word-pieces, so documents are split into passages.

**10. How is the semantic score computed?** Split both texts into passages; for each job passage take the best cosine to any resume passage; average. It measures how much of the job is addressed by the resume.

**11. Why is the semantic score not rescaled to look larger?** Rescaling would be an arbitrary choice. The raw clipped cosine is reported, and calibration is a topic for the experiments.

**12. Why is skill matching not enough?** It misses context and related experience. It is also the most explainable part, which is why it carries the highest weight.

**13. Where do the weights 35/25/15/15/10 come from?** They are initial hypotheses from the project brief, not scientific constants. Experiment 2 tests them against ablations and tunes alternatives on development jobs, reporting held-out results.

**14. What happens when a job has no education requirement?** That component is "not applicable". Its weight is redistributed over the applicable components, and the report states this. With all components applicable the formula equals the brief's.

**15. How do you distinguish explicit from inferred skills?** Explicit skills are matched in the text. Inferred skills come from an implication map (for example Splunk suggests SIEM), carry confidence 0.6 and earn half credit. An explicit mention always overrides an inference.

**16. How do you avoid inventing information?** Extraction is rule-based. Absent fields stay empty, and every extracted item stores its source text and offsets. A unit test checks sparse text.

**17. How do you decide a requirement is mandatory?** Only from the job text: a Requirements heading or words such as "must" or "required". Lines with no signal are left out. "Preferred" or "optional" cues override the section default.

**18. What are the limitations of rule-based extraction?** Complex layouts, unusual headings and non-English text. A learned model trained on labelled data is future work. Experiment 3 measures the actual accuracy.

**19. Why not use a large language model?** Privacy (resumes would leave the server), cost, non-determinism and prompt-injection exposure. Local deterministic components are explainable and testable.

## Evaluation
**20. Which metrics did you use and why?** Precision@K and Recall@K for the quality of the top results, nDCG for graded ranking, MRR for the first relevant result, and precision, recall and F1 for extraction. Ranking metrics fit a screening task better than accuracy.

**21. Define nDCG.** DCG@K = Σ grade_i / log2(i+1); nDCG divides by the DCG of the ideal ordering.

**22. How do you know the hybrid model is better than skills alone?** Only if the held-out confidence interval for the difference excludes zero. If it does not, I report that no improvement was shown.

**23. Why use a held-out split for weight tuning?** Tuning and evaluating on the same jobs over-fits. Weights are chosen on development jobs and judged on held-out ones.

**24. What are the threats to validity?** Dataset size and representativeness, subjective labels, possible leakage between the taxonomy and the labels, a single machine for timing. These are stated with the results.

**25. Why did you not report results on synthetic data?** Its labels come from the same templates as the text, so scores are meaninglessly high. It exists only to test that the scripts run.

## Security
**26. Why Argon2id?** It is memory-hard, which resists GPU cracking, and combines side-channel resistance (Argon2i) with brute-force resistance (Argon2d). It is the current recommendation for password hashing.

**27. Why AES-256-GCM and what is envelope encryption?** GCM gives confidentiality and integrity. Each file gets its own random data key, wrapped by a master key kept outside the database, so a database leak alone does not reveal resumes. The associated data binds a ciphertext to its record.

**28. Why a random nonce per encryption?** Reusing a nonce with the same GCM key is catastrophic. Each encryption draws a fresh random 96-bit nonce.

**29. How do you validate uploads?** Size, extension, magic bytes, structure (encrypted files, macros, embedded objects, remote templates, zip bombs, path traversal), then a ClamAV scan. Failure to scan rejects the file (fail closed). Files are stored under random names.

**30. What is prompt injection and how do you defend against it?** Text in a document that tries to instruct an AI. The scoring uses fixed arithmetic, so no text can change it; instruction-like lines are flagged and excluded from matching, hidden text is removed, and no external AI service is used. Detection is pattern-based, so it is not exhaustive.

**31. How do you prevent broken access control?** Role checks on every route and ownership checks in the service layer. Non-owners get 404 so IDs cannot be probed. Administrators cannot read resume content.

**32. How do you handle CSRF and XSS?** CSRF tokens on every state-changing request, Jinja auto-escaping, a Content-Security-Policy without inline scripts, and escaped text in PDFs.

**33. Why is the audit log hash-chained?** Each row stores the hash of the previous row, so edits or deletions in the middle of the log are detectable. It does not detect truncation of the newest rows, which would need external anchoring.

**34. How does the system respect privacy?** Minimal data, encryption at rest, retention purge, export and erasure, no PII in logs or the audit trail, and no external AI.

**35. What security weaknesses remain?** Compressed-PDF content is only shallowly inspected, malware scanning is signature-based, session binding uses the User-Agent only, rate limits use in-memory storage in development, and password-reset e-mail is not implemented.

**36. How did you test security?** Automated tests for injection, XSS, CSRF, access control, uploads, path traversal, sessions, brute force and data exposure, with expected and actual results generated from a real run, plus Bandit, pip-audit and OWASP ZAP against the local instance.

## Ethics and future work
**37. What bias risks exist?** Embedding models reflect training data, and names, institutions or phrasing may sway similarity. Experiment 6 measures score changes from name and institution swaps and group selection rates, as a screening aid and not an audit.

**38. What would you do with more time?** OCR, a learned extractor, a larger human-labelled dataset with inter-annotator agreement, a learned ranker with calibrated scores, key-management integration, and a fuller fairness study with ethics approval.

**39. What did you learn?** Explainability and security must be designed in from the start, and claims need measurement. Rules around what the system will not guess matter as much as what it extracts.

## Job board and eligibility
**40. How is "eligible" decided?** The percentage is the hybrid compatibility score. A candidate is *likely eligible* when it reaches the employer's threshold for that job and every mandatory requirement is evidenced in the CV; *partially eligible* when within 15 points with at most one mandatory requirement unmet (or a mandatory skill only inferred); otherwise *not eligible yet*. The rules and reasons are shown to the candidate.

**41. Is the percentage a probability of getting the job?** No. It measures how well the CV text matches the job text. The employer makes the decision, and the report says so.

**42. Why can an administrator not see who checked a job?** Privacy by design: administrators see totals only (checks, average match, outcome counts). CVs, profiles and individual results are visible only to their owner, and tests enforce this.

**43. Why can administrators edit the detected requirements?** The automatic classification can be wrong, and a wrong "mandatory" label could unfairly exclude people, so a human reviews it before candidates are screened against it. Every edit is audited.

**44. Why can a job with checks not be deleted?** Deleting it would erase candidates' own history. It can be closed instead, which hides it from the board.

**45. Why is a skill that is only implied (for example SIEM from Splunk) not counted as met?** The system never assumes a qualification the CV does not state. It marks the skill "unconfirmed" and tells the candidate to write it explicitly if they have it.
