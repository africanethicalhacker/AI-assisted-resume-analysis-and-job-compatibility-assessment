# Test case catalogue

126 automated test functions (generated from the source; run `python -m pytest -v` for results).

| ID | File | Test | What it checks |
|---|---|---|---|
| TC-001 | `tests/integration/test_assessment_flow.py` | `test_assessment_end_to_end` | assessment end to end |
| TC-002 | `tests/integration/test_assessment_flow.py` | `test_other_users_cannot_use_or_view_assessment` | other users cannot use or view assessment |
| TC-003 | `tests/integration/test_assessment_flow.py` | `test_admin_can_change_weights_and_invalid_sum_rejected` | admin can change weights and invalid sum rejected |
| TC-004 | `tests/integration/test_assessment_flow.py` | `test_candidate_cannot_open_scoring_admin` | candidate cannot open scoring admin |
| TC-005 | `tests/integration/test_auth.py` | `test_register_creates_candidate_with_argon2id` | register creates candidate with argon2id |
| TC-006 | `tests/integration/test_auth.py` | `test_register_ignores_role_injection` | register ignores role injection |
| TC-007 | `tests/integration/test_auth.py` | `test_login_success_and_generic_failure` | login success and generic failure |
| TC-008 | `tests/integration/test_auth.py` | `test_lockout_after_repeated_failures` | lockout after repeated failures |
| TC-009 | `tests/integration/test_auth.py` | `test_open_redirect_blocked` | open redirect blocked |
| TC-010 | `tests/integration/test_auth.py` | `test_protected_page_requires_login` | protected page requires login |
| TC-011 | `tests/integration/test_auth.py` | `test_audit_chain_verifies_and_detects_tampering` | audit chain verifies and detects tampering |
| TC-012 | `tests/integration/test_dashboard.py` | `test_assessment_stores_gap_and_recommendations` | assessment stores gap and recommendations |
| TC-013 | `tests/integration/test_dashboard.py` | `test_dashboard_and_api_for_owner` | dashboard and api for owner |
| TC-014 | `tests/integration/test_dashboard.py` | `test_api_blocks_other_users_and_anonymous` | api blocks other users and anonymous |
| TC-015 | `tests/integration/test_dashboard.py` | `test_admin_dashboard_has_no_candidate_data` | admin dashboard has no candidate data |
| TC-016 | `tests/integration/test_dashboard.py` | `test_dashboard_js_served_under_csp` | dashboard js served under csp |
| TC-017 | `tests/integration/test_job_board.py` | `test_admin_posts_job_and_candidate_sees_it` | admin posts job and candidate sees it |
| TC-018 | `tests/integration/test_job_board.py` | `test_candidate_uploads_cv_and_gets_percentage_and_verdict` | candidate uploads cv and gets percentage and verdict |
| TC-019 | `tests/integration/test_job_board.py` | `test_admin_sees_only_aggregates_never_candidate_data` | admin sees only aggregates never candidate data |
| TC-020 | `tests/integration/test_job_board.py` | `test_other_candidate_cannot_open_result` | other candidate cannot open result |
| TC-021 | `tests/integration/test_job_board.py` | `test_closed_job_is_hidden_and_cannot_be_checked` | closed job is hidden and cannot be checked |
| TC-022 | `tests/integration/test_job_board.py` | `test_candidate_cannot_post_or_manage_jobs` | candidate cannot post or manage jobs |
| TC-023 | `tests/integration/test_job_board.py` | `test_private_jobs_are_not_on_the_board_or_reachable` | private jobs are not on the board or reachable |
| TC-024 | `tests/integration/test_job_board.py` | `test_admin_can_correct_requirement_strength_and_it_changes_the_verdict` | admin can correct requirement strength and it changes the verdict |
| TC-025 | `tests/integration/test_job_board.py` | `test_invalid_threshold_is_rejected` | invalid threshold is rejected |
| TC-026 | `tests/integration/test_job_board.py` | `test_delete_is_blocked_after_checks_but_allowed_otherwise` | delete is blocked after checks but allowed otherwise |
| TC-027 | `tests/integration/test_job_board.py` | `test_pdf_report_works_for_posted_job_and_states_eligibility` | pdf report works for posted job and states eligibility |
| TC-028 | `tests/integration/test_job_board.py` | `test_candidate_export_does_not_contain_the_admins_job` | candidate export does not contain the admins job |
| TC-029 | `tests/integration/test_job_board.py` | `test_admin_dashboard_shows_job_board_totals` | admin dashboard shows job board totals |
| TC-030 | `tests/integration/test_job_board.py` | `test_posting_is_audited` | posting is audited |
| TC-031 | `tests/integration/test_parsing_flow.py` | `test_upload_parses_and_stores_encrypted_profile` | upload parses and stores encrypted profile |
| TC-032 | `tests/integration/test_parsing_flow.py` | `test_profile_and_job_isolated_between_users` | profile and job isolated between users |
| TC-033 | `tests/integration/test_parsing_flow.py` | `test_job_requirements_stored_with_strengths` | job requirements stored with strengths |
| TC-034 | `tests/integration/test_parsing_flow.py` | `test_admin_can_add_skill_and_candidate_cannot` | admin can add skill and candidate cannot |
| TC-035 | `tests/integration/test_upload.py` | `test_upload_encrypts_at_rest_and_roundtrips` | upload encrypts at rest and roundtrips |
| TC-036 | `tests/integration/test_upload.py` | `test_docx_accepted` | docx accepted |
| TC-037 | `tests/integration/test_upload.py` | `test_malware_rejected` | malware rejected |
| TC-038 | `tests/integration/test_upload.py` | `test_scanner_down_fails_closed` | scanner down fails closed |
| TC-039 | `tests/integration/test_upload.py` | `test_disguised_executable_rejected` | disguised executable rejected |
| TC-040 | `tests/integration/test_upload.py` | `test_delete_removes_file_and_row` | delete removes file and row |
| TC-041 | `tests/integration/test_upload.py` | `test_purge_expired` | purge expired |
| TC-042 | `tests/security/test_access_control.py` | `test_idor_other_users_resume_is_404` | idor other users resume is 404 |
| TC-043 | `tests/security/test_access_control.py` | `test_candidate_cannot_reach_admin` | candidate cannot reach admin |
| TC-044 | `tests/security/test_access_control.py` | `test_admin_cannot_read_resume_content_pages` | admin cannot read resume content pages |
| TC-045 | `tests/security/test_access_control.py` | `test_anonymous_blocked_everywhere` | anonymous blocked everywhere |
| TC-046 | `tests/security/test_access_control.py` | `test_csrf_enforced_when_enabled` | csrf enforced when enabled |
| TC-047 | `tests/security/test_access_control.py` | `test_sql_injection_in_login_is_inert` | sql injection in login is inert |
| TC-048 | `tests/security/test_access_control.py` | `test_xss_in_filename_is_escaped` | xss in filename is escaped |
| TC-049 | `tests/security/test_access_control.py` | `test_security_headers_on_every_response` | security headers on every response |
| TC-050 | `tests/security/test_hardening.py` | `test_session_bound_to_user_agent` | session bound to user agent |
| TC-051 | `tests/security/test_hardening.py` | `test_absolute_session_timeout` | absolute session timeout |
| TC-052 | `tests/security/test_hardening.py` | `test_cross_origin_and_cache_headers` | cross origin and cache headers |
| TC-053 | `tests/security/test_hardening.py` | `test_production_cookie_hardening` | production cookie hardening |
| TC-054 | `tests/security/test_hardening.py` | `test_redacting_filter_masks_emails` | redacting filter masks emails |
| TC-055 | `tests/security/test_hardening.py` | `test_audit_log_never_contains_email` | audit log never contains email |
| TC-056 | `tests/security/test_hardening.py` | `test_path_traversal_rejected` | path traversal rejected |
| TC-057 | `tests/security/test_hardening.py` | `test_no_external_ai_or_network_clients_in_application_code` | no external ai or network clients in application code |
| TC-058 | `tests/security/test_hardening.py` | `test_external_ai_disabled_by_default` | external ai disabled by default |
| TC-059 | `tests/security/test_hardening.py` | `test_export_contains_only_own_data` | export contains only own data |
| TC-060 | `tests/security/test_hardening.py` | `test_delete_account_requires_password_and_erases_everything` | delete account requires password and erases everything |
| TC-061 | `tests/security/test_hardening.py` | `test_admin_cannot_use_candidate_account_routes` | admin cannot use candidate account routes |
| TC-062 | `tests/security/test_hardening.py` | `test_sensitive_values_not_in_pages` | sensitive values not in pages |
| TC-063 | `tests/security/test_hardening.py` | `test_clamav_detects_eicar_when_available` | clamav detects eicar when available |
| TC-064 | `tests/unit/test_crypto.py` | `test_file_roundtrip` | file roundtrip |
| TC-065 | `tests/unit/test_crypto.py` | `test_wrong_context_rejected` | wrong context rejected |
| TC-066 | `tests/unit/test_crypto.py` | `test_tampered_ciphertext_rejected` | tampered ciphertext rejected |
| TC-067 | `tests/unit/test_crypto.py` | `test_wrong_master_key_rejected` | wrong master key rejected |
| TC-068 | `tests/unit/test_crypto.py` | `test_field_roundtrip_and_unique_nonce` | field roundtrip and unique nonce |
| TC-069 | `tests/unit/test_crypto.py` | `test_bad_key_length_and_b64` | bad key length and b64 |
| TC-070 | `tests/unit/test_eligibility.py` | `test_all_mandatory_met_and_high_match_is_eligible` | all mandatory met and high match is eligible |
| TC-071 | `tests/unit/test_eligibility.py` | `test_threshold_decides_between_eligible_and_partial` | threshold decides between eligible and partial |
| TC-072 | `tests/unit/test_eligibility.py` | `test_missing_mandatory_skill_blocks_eligibility_even_with_high_score` | missing mandatory skill blocks eligibility even with high score |
| TC-073 | `tests/unit/test_eligibility.py` | `test_two_unmet_mandatory_requirements_is_not_eligible` | two unmet mandatory requirements is not eligible |
| TC-074 | `tests/unit/test_eligibility.py` | `test_inferred_only_skill_is_unconfirmed_not_failed` | inferred only skill is unconfirmed not failed |
| TC-075 | `tests/unit/test_eligibility.py` | `test_preferred_requirements_do_not_block` | preferred requirements do not block |
| TC-076 | `tests/unit/test_eligibility.py` | `test_job_without_mandatory_items_depends_on_score_only` | job without mandatory items depends on score only |
| TC-077 | `tests/unit/test_eligibility.py` | `test_percentage_matches_final_score_and_rule_text_present` | percentage matches final score and rule text present |
| TC-078 | `tests/unit/test_experiments.py` | `test_ranking_metrics_hand_computed` | ranking metrics hand computed |
| TC-079 | `tests/unit/test_experiments.py` | `test_bootstrap_is_reproducible_and_sensible` | bootstrap is reproducible and sensible |
| TC-080 | `tests/unit/test_experiments.py` | `test_smoke_all_experiments_run_and_are_reproducible` | smoke all experiments run and are reproducible |
| TC-081 | `tests/unit/test_extraction.py` | `test_skill_matching_precision` | skill matching precision |
| TC-082 | `tests/unit/test_extraction.py` | `test_explicit_vs_inferred_never_duplicate` | explicit vs inferred never duplicate |
| TC-083 | `tests/unit/test_extraction.py` | `test_profile_fields_and_evidence` | profile fields and evidence |
| TC-084 | `tests/unit/test_extraction.py` | `test_no_invention_on_sparse_text` | no invention on sparse text |
| TC-085 | `tests/unit/test_extraction.py` | `test_experience_months_merge_overlaps` | experience months merge overlaps |
| TC-086 | `tests/unit/test_extraction.py` | `test_education_level` | education level |
| TC-087 | `tests/unit/test_extraction.py` | `test_sanitiser_and_injection_detection` | sanitiser and injection detection |
| TC-088 | `tests/unit/test_extraction.py` | `test_job_analysis_strengths_and_no_assumptions` | job analysis strengths and no assumptions |
| TC-089 | `tests/unit/test_extraction.py` | `test_unlabelled_text_is_not_assumed_mandatory` | unlabelled text is not assumed mandatory |
| TC-090 | `tests/unit/test_extraction.py` | `test_docx_reader_order_tables_and_hidden_text` | docx reader order tables and hidden text |
| TC-091 | `tests/unit/test_gap_roles.py` | `test_gap_structure_and_priorities` | gap structure and priorities |
| TC-092 | `tests/unit/test_gap_roles.py` | `test_gap_handles_job_without_skills` | gap handles job without skills |
| TC-093 | `tests/unit/test_gap_roles.py` | `test_roles_only_reference_taxonomy_skills` | roles only reference taxonomy skills |
| TC-094 | `tests/unit/test_gap_roles.py` | `test_recommendations_evidence_based` | recommendations evidence based |
| TC-095 | `tests/unit/test_gap_roles.py` | `test_no_evidence_means_no_recommendations` | no evidence means no recommendations |
| TC-096 | `tests/unit/test_matching.py` | `test_tfidf_basic_properties` | tfidf basic properties |
| TC-097 | `tests/unit/test_matching.py` | `test_tfidf_matches_scikit_learn` | tfidf matches scikit learn |
| TC-098 | `tests/unit/test_matching.py` | `test_chunking_and_sbert_coverage` | chunking and sbert coverage |
| TC-099 | `tests/unit/test_matching.py` | `test_semantic_modes_and_fallbacks` | semantic modes and fallbacks |
| TC-100 | `tests/unit/test_matching.py` | `test_strip_flagged_lines` | strip flagged lines |
| TC-101 | `tests/unit/test_matching.py` | `test_level_from_text` | level from text |
| TC-102 | `tests/unit/test_matching.py` | `test_skills_component_weighted_credit` | skills component weighted credit |
| TC-103 | `tests/unit/test_matching.py` | `test_education_experience_projects_certs` | education experience projects certs |
| TC-104 | `tests/unit/test_matching.py` | `test_final_score_weights_and_renormalisation` | final score weights and renormalisation |
| TC-105 | `tests/unit/test_matching.py` | `test_weights_change_result_and_injection_cannot` | weights change result and injection cannot |
| TC-106 | `tests/unit/test_matching.py` | `test_keyword_stuffing_flag` | keyword stuffing flag |
| TC-107 | `tests/unit/test_matching.py` | `test_field_relevance_asymmetry` | field relevance asymmetry |
| TC-108 | `tests/unit/test_passwords.py` | `test_policy` | policy |
| TC-109 | `tests/unit/test_passwords.py` | `test_argon2id_hash_and_verify` | argon2id hash and verify |
| TC-110 | `tests/unit/test_passwords.py` | `test_reset_token_binds_to_password_hash` | reset token binds to password hash |
| TC-111 | `tests/unit/test_report.py` | `test_pdf_contains_all_twelve_sections` | pdf contains all twelve sections |
| TC-112 | `tests/unit/test_report.py` | `test_pdf_survives_hostile_markup_and_unicode` | pdf survives hostile markup and unicode |
| TC-113 | `tests/unit/test_report.py` | `test_pdf_has_chart_image_and_reasonable_size` | pdf has chart image and reasonable size |
| TC-114 | `tests/unit/test_report.py` | `test_combine_scores_matches_scoring_engine` | combine scores matches scoring engine |
| TC-115 | `tests/unit/test_smoke.py` | `test_healthz_returns_ok` | healthz returns ok |
| TC-116 | `tests/unit/test_smoke.py` | `test_security_headers_present` | security headers present |
| TC-117 | `tests/unit/test_smoke.py` | `test_session_cookie_flags` | session cookie flags |
| TC-118 | `tests/unit/test_validators.py` | `test_valid_pdf_and_docx` | valid pdf and docx |
| TC-119 | `tests/unit/test_validators.py` | `test_empty_oversize_and_bad_extension` | empty oversize and bad extension |
| TC-120 | `tests/unit/test_validators.py` | `test_magic_mismatch_both_directions` | magic mismatch both directions |
| TC-121 | `tests/unit/test_validators.py` | `test_double_extension_uses_last` | double extension uses last |
| TC-122 | `tests/unit/test_validators.py` | `test_pdf_active_content_and_encryption_and_truncation` | pdf active content and encryption and truncation |
| TC-123 | `tests/unit/test_validators.py` | `test_docx_macro_and_embedded_rejected` | docx macro and embedded rejected |
| TC-124 | `tests/unit/test_validators.py` | `test_docx_remote_template_rejected_but_hyperlink_allowed` | docx remote template rejected but hyperlink allowed |
| TC-125 | `tests/unit/test_validators.py` | `test_docx_path_traversal_and_bomb_and_structure` | docx path traversal and bomb and structure |
| TC-126 | `tests/unit/test_validators.py` | `test_safe_display_name` | safe display name |

Expected result for every test: PASS. Record actual results from your own run in Chapter 11, and attach the pytest summary line.