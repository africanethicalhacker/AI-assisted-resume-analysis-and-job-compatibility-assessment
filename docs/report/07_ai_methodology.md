# Chapter 7: AI and Machine Learning Methodology

## 7.1 Text extraction and sectioning
PyMuPDF and python-docx extract text (tables in reading order; hidden DOCX runs removed). Text is normalised (Unicode NFKC,
invisible and control characters removed). Headings (education, experience, skills, projects, certifications, achievements)
segment the document; each field is extracted with regular expressions and rules, with evidence stored.

## 7.2 Skill extraction
A taxonomy of skills, categories and aliases is matched with word-boundary regular expressions. Ambiguous single-letter skills
(C, R) match only in list context. Inferred skills come from an implication map (for example Splunk suggests SIEM) and carry
confidence 0.6; an explicit mention always overrides an inference. Administrators extend the taxonomy through the interface.

## 7.3 Job analysis
Headings and cue phrases classify requirements. Priority: optional cues, then preferred cues, then mandatory cues, then the section
default. Lines without a heading or cue are left out rather than assumed. Years of experience, education level, certifications and
skills are extracted per line.

## 7.4 Similarity
**TF-IDF.** tf = 1 + ln(count); idf = ln((1+N)/(1+df)) + 1; vectors are L2-normalised; similarity is the dot product (cosine).
Unigrams and bigrams after stop-word removal. The implementation matches scikit-learn to nine decimal places (unit test).
**Sentence-BERT.** all-MiniLM-L6-v2 produces 384-dimensional embeddings. Documents are split into passages of about 120 words; the
coverage score is the mean over job passages of the maximum cosine similarity to any resume passage.

## 7.4.1 Hybrid score
Final = Σ (wᵢ / W) Sᵢ over applicable components, with W the sum of their weights; with all five applicable and default weights
this equals 0.35 Skills + 0.25 Semantic + 0.15 Education + 0.15 Experience + 0.10 Projects and Certifications.
- Skills: 100 Σ(w·credit)/Σw; weights mandatory 3, preferred 2, optional 1; credit explicit 1.0, inferred 0.5, missing 0.
- Education: 0.7 × level score + 0.3 × field score (levels diploma < bachelor < master < doctorate).
- Experience: min(100, 100 × (professional + 0.5 × internship months) / required months).
- Projects and certifications: mean of job-skill coverage in projects and held required certifications.
All rule values are experimental hypotheses; Experiment 2 tests them on held-out data.

## 7.5 Gap analysis and recommendations
Gap analysis lists matched, partial, missing and additional skills and estimates the points each missing skill is worth.
Role fit = 100 Σ(w·credit)/Σw over core (w=2) and supporting (w=1) skills for ten cyber security roles; a role is shown only when at
least one core skill is explicit and fit ≥ 30. Certification lists are commonly associated credentials, not eligibility advice.

## 7.6 Evaluation methods
Precision@K, Recall@K, nDCG@K (linear gain), MRR; micro precision, recall and F1 for extraction; bootstrap 95% confidence intervals
over jobs; paired bootstrap for method comparisons; development/held-out split for weight tuning.
