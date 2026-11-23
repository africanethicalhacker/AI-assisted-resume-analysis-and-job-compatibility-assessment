# Security test results (Experiment 5)

Generated 2026-11-10 03:01 UTC from a real pytest run. Passed 42, failed 0, skipped 0.

| Threat | Test | Expected result | Actual |
|---|---|---|---|
| Audit integrity | `test_audit_chain_verifies_and_detects_tampering` | Edited audit rows are detected by the hash chain | PASSED |
| Broken access control | `test_admin_cannot_read_resume_content_pages` | Administrator cannot open resume content pages | PASSED |
| Broken access control | `test_anonymous_blocked_everywhere` | Anonymous visitors are redirected to log in | PASSED |
| Broken access control | `test_api_blocks_other_users_and_anonymous` | API returns 404 or a redirect for foreign data | PASSED |
| Broken access control | `test_candidate_cannot_reach_admin` | Candidate gets HTTP 403 on admin pages | PASSED |
| Broken access control | `test_other_users_cannot_use_or_view_assessment` | Other users get 404 for assessments they do not own | PASSED |
| Broken access control / unauthorised resume access | `test_idor_other_users_resume_is_404` | Another user's resume cannot be read or deleted (HTTP 404) | PASSED |
| Brute-force login | `test_lockout_after_repeated_failures` | Account locks after the configured number of failures | PASSED |
| CSRF | `test_csrf_enforced_when_enabled` | POST without a valid token is rejected (HTTP 400) | PASSED |
| Cross-site scripting | `test_xss_in_filename_is_escaped` | Script tag in a file name is HTML-escaped in the page | PASSED |
| Data protection | `test_tampered_ciphertext_rejected` | Modified ciphertext fails authentication | PASSED |
| Data protection | `test_upload_encrypts_at_rest_and_roundtrips` | Stored file is ciphertext and decrypts correctly | PASSED |
| Data protection | `test_wrong_context_rejected` | Ciphertext moved to another record fails authentication | PASSED |
| Data protection (erasure) | `test_delete_account_requires_password_and_erases_everything` | Wrong password or missing confirmation deletes nothing; correct request erases data and files | PASSED |
| Data protection / access control | `test_export_contains_only_own_data` | Export contains only the requesting user's data | PASSED |
| Malicious document upload | `test_disguised_executable_rejected` | Executable renamed .pdf is rejected by magic-byte check | PASSED |
| Malicious document upload | `test_docx_macro_and_embedded_rejected` | DOCX with macros or embedded objects is rejected | PASSED |
| Malicious document upload | `test_docx_remote_template_rejected_but_hyperlink_allowed` | Remote template rejected; ordinary hyperlinks allowed | PASSED |
| Malicious document upload | `test_magic_mismatch_both_directions` | Extension and content must agree | PASSED |
| Malicious document upload | `test_malware_rejected` | File flagged by the scanner is rejected and not stored | PASSED |
| Malicious document upload | `test_pdf_active_content_and_encryption_and_truncation` | PDFs with scripts, encryption or truncation are rejected | PASSED |
| Malicious document upload | `test_scanner_down_fails_closed` | Uploads are refused when the scanner is unavailable | PASSED |
| Malicious document upload / path traversal | `test_docx_path_traversal_and_bomb_and_structure` | Zip-slip names, zip bombs and bad structure rejected | PASSED |
| Malware scanning (live ClamAV) | `test_clamav_detects_eicar_when_available` | EICAR test string is detected (skipped if clamd is unreachable) | PASSED |
| Open redirect | `test_open_redirect_blocked` | External 'next' targets are ignored | PASSED |
| Path traversal | `test_path_traversal_rejected` | Storage paths cannot escape the upload directory | PASSED |
| Privilege escalation | `test_register_ignores_role_injection` | Role cannot be set through the registration form | PASSED |
| Prompt injection | `test_sanitiser_and_injection_detection` | Instruction-like text is flagged | PASSED |
| Prompt injection | `test_strip_flagged_lines` | Flagged lines are removed before matching | PASSED |
| Prompt injection / score manipulation | `test_weights_change_result_and_injection_cannot` | Injected text does not change the score | PASSED |
| SQL injection | `test_sql_injection_in_login_is_inert` | Injection string is treated as data; login fails normally with no error | PASSED |
| Score manipulation | `test_keyword_stuffing_flag` | Keyword stuffing is flagged and counted once | PASSED |
| Security headers | `test_cross_origin_and_cache_headers` | COOP, CORP, no-store and strict CSP present | PASSED |
| Security headers | `test_security_headers_on_every_response` | CSP, X-Frame-Options and related headers present | PASSED |
| Sensitive data exposure | `test_audit_log_never_contains_email` | Audit log holds no e-mail addresses | PASSED |
| Sensitive data exposure | `test_redacting_filter_masks_emails` | E-mail addresses are masked in log messages | PASSED |
| Sensitive data exposure | `test_sensitive_values_not_in_pages` | Password hashes and wrapped keys never appear in pages | PASSED |
| Sensitive data exposure (AI) | `test_external_ai_disabled_by_default` | External AI use is disabled by default | PASSED |
| Sensitive data exposure (AI) | `test_no_external_ai_or_network_clients_in_application_code` | No external AI or HTTP client libraries are imported | PASSED |
| Session hijacking | `test_absolute_session_timeout` | Sessions expire after the absolute lifetime | PASSED |
| Session hijacking | `test_production_cookie_hardening` | Production cookies are Secure, HttpOnly, SameSite and __Host- prefixed | PASSED |
| Session hijacking | `test_session_bound_to_user_agent` | A stolen session used with a different browser identity is rejected | PASSED |

Penetration-style testing with OWASP ZAP should be added by the student against the local instance, with the findings pasted here.
A test suite shows these controls work for the cases tested; it is not proof of the absence of vulnerabilities.