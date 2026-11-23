"""Experiment 5: run the security tests and document EXPECTED versus ACTUAL results.

The 'actual' column comes only from a real pytest run (JUnit XML); nothing is written by hand.
Run: python -m experiments.run_security_suite   ->  docs/security_test_results.md
Only run this against your own local copy of the application.
"""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# test name -> (threat category, expected result)
CATALOGUE = {
    "test_sql_injection_in_login_is_inert": ("SQL injection", "Injection string is treated as data; login fails normally with no error"),
    "test_xss_in_filename_is_escaped": ("Cross-site scripting", "Script tag in a file name is HTML-escaped in the page"),
    "test_csrf_enforced_when_enabled": ("CSRF", "POST without a valid token is rejected (HTTP 400)"),
    "test_idor_other_users_resume_is_404": ("Broken access control / unauthorised resume access", "Another user's resume cannot be read or deleted (HTTP 404)"),
    "test_candidate_cannot_reach_admin": ("Broken access control", "Candidate gets HTTP 403 on admin pages"),
    "test_admin_cannot_read_resume_content_pages": ("Broken access control", "Administrator cannot open resume content pages"),
    "test_anonymous_blocked_everywhere": ("Broken access control", "Anonymous visitors are redirected to log in"),
    "test_other_users_cannot_use_or_view_assessment": ("Broken access control", "Other users get 404 for assessments they do not own"),
    "test_api_blocks_other_users_and_anonymous": ("Broken access control", "API returns 404 or a redirect for foreign data"),
    "test_security_headers_on_every_response": ("Security headers", "CSP, X-Frame-Options and related headers present"),
    "test_cross_origin_and_cache_headers": ("Security headers", "COOP, CORP, no-store and strict CSP present"),
    "test_production_cookie_hardening": ("Session hijacking", "Production cookies are Secure, HttpOnly, SameSite and __Host- prefixed"),
    "test_session_bound_to_user_agent": ("Session hijacking", "A stolen session used with a different browser identity is rejected"),
    "test_absolute_session_timeout": ("Session hijacking", "Sessions expire after the absolute lifetime"),
    "test_lockout_after_repeated_failures": ("Brute-force login", "Account locks after the configured number of failures"),
    "test_open_redirect_blocked": ("Open redirect", "External 'next' targets are ignored"),
    "test_register_ignores_role_injection": ("Privilege escalation", "Role cannot be set through the registration form"),
    "test_malware_rejected": ("Malicious document upload", "File flagged by the scanner is rejected and not stored"),
    "test_scanner_down_fails_closed": ("Malicious document upload", "Uploads are refused when the scanner is unavailable"),
    "test_disguised_executable_rejected": ("Malicious document upload", "Executable renamed .pdf is rejected by magic-byte check"),
    "test_magic_mismatch_both_directions": ("Malicious document upload", "Extension and content must agree"),
    "test_pdf_active_content_and_encryption_and_truncation": ("Malicious document upload", "PDFs with scripts, encryption or truncation are rejected"),
    "test_docx_macro_and_embedded_rejected": ("Malicious document upload", "DOCX with macros or embedded objects is rejected"),
    "test_docx_remote_template_rejected_but_hyperlink_allowed": ("Malicious document upload", "Remote template rejected; ordinary hyperlinks allowed"),
    "test_docx_path_traversal_and_bomb_and_structure": ("Malicious document upload / path traversal", "Zip-slip names, zip bombs and bad structure rejected"),
    "test_path_traversal_rejected": ("Path traversal", "Storage paths cannot escape the upload directory"),
    "test_clamav_detects_eicar_when_available": ("Malware scanning (live ClamAV)", "EICAR test string is detected (skipped if clamd is unreachable)"),
    "test_sanitiser_and_injection_detection": ("Prompt injection", "Instruction-like text is flagged"),
    "test_strip_flagged_lines": ("Prompt injection", "Flagged lines are removed before matching"),
    "test_weights_change_result_and_injection_cannot": ("Prompt injection / score manipulation", "Injected text does not change the score"),
    "test_keyword_stuffing_flag": ("Score manipulation", "Keyword stuffing is flagged and counted once"),
    "test_no_external_ai_or_network_clients_in_application_code": ("Sensitive data exposure (AI)", "No external AI or HTTP client libraries are imported"),
    "test_external_ai_disabled_by_default": ("Sensitive data exposure (AI)", "External AI use is disabled by default"),
    "test_audit_log_never_contains_email": ("Sensitive data exposure", "Audit log holds no e-mail addresses"),
    "test_redacting_filter_masks_emails": ("Sensitive data exposure", "E-mail addresses are masked in log messages"),
    "test_sensitive_values_not_in_pages": ("Sensitive data exposure", "Password hashes and wrapped keys never appear in pages"),
    "test_upload_encrypts_at_rest_and_roundtrips": ("Data protection", "Stored file is ciphertext and decrypts correctly"),
    "test_export_contains_only_own_data": ("Data protection / access control", "Export contains only the requesting user's data"),
    "test_delete_account_requires_password_and_erases_everything": ("Data protection (erasure)", "Wrong password or missing confirmation deletes nothing; correct request erases data and files"),
    "test_audit_chain_verifies_and_detects_tampering": ("Audit integrity", "Edited audit rows are detected by the hash chain"),
    "test_tampered_ciphertext_rejected": ("Data protection", "Modified ciphertext fails authentication"),
    "test_wrong_context_rejected": ("Data protection", "Ciphertext moved to another record fails authentication"),
}
TARGETS = ["tests/security", "tests/integration/test_auth.py", "tests/integration/test_upload.py", "tests/integration/test_assessment_flow.py",
           "tests/integration/test_dashboard.py", "tests/unit/test_validators.py", "tests/unit/test_crypto.py", "tests/unit/test_extraction.py",
           "tests/unit/test_matching.py"]


def main(out_md="docs/security_test_results.md", junit="experiments/results/security_junit.xml"):
    os.makedirs(os.path.dirname(junit), exist_ok=True)
    proc = subprocess.run([sys.executable, "-m", "pytest", *TARGETS, "-q", f"--junitxml={junit}"], capture_output=True, text=True)
    root = ET.parse(junit).getroot()
    rows, counts = [], {"passed": 0, "failed": 0, "skipped": 0}
    for case in root.iter("testcase"):
        name = case.get("name")
        if name not in CATALOGUE:
            continue
        cat, expected = CATALOGUE[name]
        if case.find("failure") is not None or case.find("error") is not None:
            actual, key = "FAILED", "failed"
        elif case.find("skipped") is not None:
            actual, key = "SKIPPED", "skipped"
        else:
            actual, key = "PASSED", "passed"
        counts[key] += 1
        rows.append((cat, name, expected, actual))
    rows.sort()
    lines = ["# Security test results (Experiment 5)", "",
             f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} from a real pytest run. "
             f"Passed {counts['passed']}, failed {counts['failed']}, skipped {counts['skipped']}.", "",
             "| Threat | Test | Expected result | Actual |", "|---|---|---|---|"]
    lines += [f"| {c} | `{n}` | {e} | {a} |" for c, n, e, a in rows]
    lines += ["", "Penetration-style testing with OWASP ZAP should be added by the student against the local instance, with the findings pasted here.",
              "A test suite shows these controls work for the cases tested; it is not proof of the absence of vulnerabilities."]
    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    open(out_md, "w", encoding="utf-8").write("\n".join(lines))
    print(open(out_md).read())
    return 0 if counts["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
