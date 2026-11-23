# User manual

## Candidate
1. **Register** with an e-mail address and a password of at least 12 characters, then log in.
2. **Resumes**: upload a PDF or DOCX (up to 5 MB). The file is scanned, encrypted and analysed. Open the resume to see what was extracted, with the
   evidence for each item, the skills found (explicit or inferred) and a completeness score. Click Re-analyse after the taxonomy changes. Delete a resume at any time.
3. **Jobs**: paste a job description or upload a PDF or DOCX. Review the Mandatory, Preferred and Optional requirements the system found.
4. **Assessments**: choose a resume and a job and run the assessment. The page shows the compatibility score, the points each component adds, the integrity notes,
   matched, partial and missing skills, the gap analysis, recommended roles with a learning roadmap, and a PDF report button.
5. **Dashboard**: cards, charts and the history of your assessments.
6. **Account**: download all your data as JSON, or permanently delete your account and everything stored.

How to read the score: it supports a human decision and is not a hiring decision. Each component is 0-100; weights are experimental and configurable; a component marked
n/a had nothing to compare in that job description.

## Job board: check whether you are eligible for a posted job
1. Open **Job board** and choose a job. You see what it asks for (mandatory, preferred, optional) and the match percentage it requires.
2. Upload your CV (PDF or DOCX), or pick one you uploaded before, and press **Check my eligibility**.
3. You get a **match percentage**, a verdict (**Likely eligible**, **Partially eligible** or **Not eligible yet**), the reasons, a checklist of the mandatory requirements, a breakdown of how the percentage was made, and what would improve it.
4. The verdict rules: *Likely eligible* means the match reaches the job's threshold and every mandatory requirement is evidenced in your CV. *Partially eligible* means you are within 15 points of the threshold with at most one mandatory requirement not met, or a mandatory skill is only implied by related tools (write it explicitly if you have it). Otherwise the result is *Not eligible yet*.
5. The percentage shows how well your CV matches the job text. It is not a probability of being hired, and the employer makes the final decision. Nobody but you can see your CV or your result.

## Administrator
- **Audit log**: recent events and an integrity check of the log chain.
- **Jobs**: post a job by pasting the description (or uploading a PDF or DOCX), set the match percentage needed to be eligible, then **review the detected requirements** and correct any classified wrongly (a mandatory requirement that is not met blocks "likely eligible"). Close or reopen a job at any time. A job that candidates have checked cannot be deleted, only closed. You see totals only: number of checks, average match and outcome counts, never a candidate's CV or result.
- **Skills**: add skills with aliases, disable or enable skills.
- **Scoring**: set the five weights (they must total 100) and the semantic method (Sentence-BERT, TF-IDF or a blend).
- Administrators manage the system but cannot read candidates' resume content.

## Troubleshooting
| Problem | Likely cause and fix |
|---|---|
| "The file could not be scanned" | ClamAV is not running: `sudo systemctl start clamav-daemon`, check `CLAMD_SOCKET` in `.env` |
| Login fails repeatedly | The account locks for 15 minutes after 5 failures |
| Charts are empty | No assessment yet, or no internet for the CDN; run `python scripts/vendor_assets.py` |
| First assessment is slow | The Sentence-BERT model is loading (one-off) |
| Resume says it could not be analysed | Scanned image PDFs are not supported; use a text PDF or DOCX |
