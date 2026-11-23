# Chapter 2: Literature Review

> Draft built only from the sources listed in the reference section. Extend it with additional peer-reviewed papers found through
> your own systematic search (IEEE Xplore, ACM DL, Scopus, Google Scholar) on resume parsing, person-job fit and ATS bias. Do not add a
> citation you have not opened and verified.

## 2.1 Term weighting and lexical similarity
Spärck Jones (1972) introduced inverse document frequency, the idea that rare terms carry more discriminating information.
Salton and Buckley (1988) compared term-weighting schemes for automatic retrieval and established TF-IDF weighting with cosine
similarity as a standard baseline (see also Manning, Raghavan and Schütze, 2008). Its strengths are transparency and speed; its
weakness is that it cannot recognise synonyms or paraphrase, which motivates semantic methods.

## 2.2 Transformers and sentence embeddings
Vaswani et al. (2017) introduced the Transformer architecture, and Devlin et al. (2019) showed that pre-trained bidirectional
encoders (BERT) transfer well to language tasks. BERT is inefficient for comparing many sentence pairs, so Reimers and Gurevych
(2019) proposed Sentence-BERT, which produces fixed-size embeddings that can be compared with cosine similarity. Wang et al.
(2020) distilled large Transformers into small models (MiniLM), which is the family of the all-MiniLM-L6-v2 model used here.

## 2.3 Evaluation of ranked results
Järvelin and Kekäläinen (2002) proposed cumulated-gain measures including nDCG, which reward placing highly relevant items early.
Together with Precision@K, Recall@K and MRR, these are the ranking metrics used in this project.

## 2.4 Fairness in hiring algorithms
Bogen and Rieke (2018) and Raghavan et al. (2020) examine how algorithmic hiring tools can produce biased outcomes and how vendors
describe their mitigation efforts. Mehrabi et al. (2021) survey sources of bias and fairness definitions in machine learning.
Reporting by Dastin (2018) described a recruiting tool withdrawn after it penalised women's resumes. These works motivate the
counterfactual and selection-rate screening in Experiment 6 and the decision-support (not decision-making) positioning.

## 2.4.1 Regulation context
India's Digital Personal Data Protection Act, 2023 and the EU Artificial Intelligence Act (Regulation (EU) 2024/1689) frame
personal-data processing and treat employment-related AI as high-risk. The project uses their principles (minimisation, consent,
erasure, transparency, human oversight) as design guidance, not as a claim of legal compliance.

## 2.5 Security of AI-enabled applications
Greshake et al. (2023) describe indirect prompt injection, where instructions hidden in content that an application processes
manipulate an AI-integrated system. The OWASP Application Security Verification Standard and the OWASP Top 10 lists (including the
list for large-language-model applications) provide control catalogues. Password and cryptography guidance comes from Biryukov
et al. (2016) for Argon2, NIST SP 800-38D for GCM, and NIST SP 800-63B for authentication.

## 2.6 Research gap
Much resume-matching work focuses on accuracy. This project's intended contribution is the combination of (i) a threat model for
the ingestion and AI layers, (ii) evidence-preserving extraction with explicit/inferred skill labels, (iii) a transparent,
configurable score validated on held-out data, and (iv) joint evaluation of accuracy, security, performance and fairness.
These are hypotheses about a gap; confirm them with your own literature search before claiming novelty.
