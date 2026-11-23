# Chapter 1: Introduction

## 1.1 Background
A single job posting can attract hundreds of applications, and recruiters often spend seconds on each resume. Applicant
tracking systems reduce the load but frequently depend on exact keyword matches. A candidate who writes "intrusion detection"
may be missed by a filter that looks for "IDS", and an unusual layout can hide valid information. Meanwhile, resumes contain
personal data and are attacker-controlled input: a file can carry malware, exploit a parser, or embed text intended to
manipulate an AI system (indirect prompt injection).

## 1.2 Motivation
Three developments make a better approach practical: classical retrieval measures such as TF-IDF with cosine similarity give a
transparent baseline; transformer sentence encoders such as Sentence-BERT compare meaning rather than spelling; and mature
open-source libraries allow structured extraction. Doing this responsibly requires explainability, privacy and security from
the start, which is the intersection this project addresses.

## 1.3 Scope
In scope: candidate and administrator roles, English PDF and DOCX resumes, pasted or uploaded job descriptions, cyber security
roles, local deployment, a dashboard, PDF reports and testing on the author's own instance. Out of scope: automated hiring
decisions, OCR for scanned resumes, multilingual resumes, job-board or ATS integration, external AI APIs and production-scale
deployment.

## 1.4 Organisation of this report
Chapters 2 to 4 give the literature, problem and system comparison. Chapters 5 to 10 describe requirements, design, methods,
security, database and implementation. Chapters 11 to 14 present testing, results, limitations and conclusions.
