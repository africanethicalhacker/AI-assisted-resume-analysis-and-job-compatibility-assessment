# Chapter 8: Cyber Security Architecture

## 8.1 Threat model
Trust boundaries: browser to server, server to database and file store, server to ClamAV, and document content to the AI layer
(treated as untrusted data, never instructions). STRIDE analysis from Phase 2 is the basis; add the table here.

## 8.2 Controls implemented
| Area | Controls |
|---|---|
| Authentication | Argon2id; 12-character minimum policy; lockout after 5 failures for 15 minutes; generic failure messages; dummy-hash timing equalisation; one-time expiring reset tokens bound to the password hash |
| Sessions | HttpOnly, SameSite=Lax, Secure and `__Host-` prefix in production; sliding 30-minute lifetime; 8-hour absolute lifetime; session binding to the browser identity; session cleared on login (fixation) |
| Authorisation | Role checks on every protected route; ownership checks returning 404; administrators cannot read resume content |
| Input and output | CSRF tokens, Jinja auto-escaping, parameterised ORM queries, form validation, escaped PDF text, safe-redirect check |
| Uploads | Size, extension, magic bytes, structure, macros, embedded objects, remote templates, zip bombs, path traversal, ClamAV scan, fail closed, random names |
| Data protection | AES-256-GCM envelope encryption (AAD binds each blob to its record); keys outside the database; encrypted filenames, profiles and job text; retention purge; export and erasure; PII-free audit log; e-mail masking in logs |
| Availability | Rate limits on login, upload, job, assessment, report and export routes; PDF page and size limits |
| Audit | Hash-chained, append-style audit log with an integrity check |
| AI security | Deterministic scoring; instruction-like text flagged and excluded; hidden text removed; stuffing flagged; no external AI APIs (test-enforced); model runs locally |
| Headers | CSP without inline script, X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy, COOP, CORP, HSTS when secure |

## 8.3 Known limitations
PDF scanning of compressed streams is shallow; pattern-based injection detection is not exhaustive; session binding uses the User-Agent
only; signature-based malware scanning misses unknown malware; in-memory rate-limit storage suits development only; password-reset
e-mail delivery is not implemented; CDN assets are used unless vendored with `scripts/vendor_assets.py`.
