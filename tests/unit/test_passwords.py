from app.security import passwords, tokens


def test_policy():
    assert passwords.validate_password("short") != []
    assert passwords.validate_password("aaaaaaaaaaaaaaaa") != []
    assert passwords.validate_password("johnsmith-2024-secure", "johnsmith@example.com") != []
    assert passwords.validate_password("Correct-Horse-Battery-9", "x@example.com") == []


def test_argon2id_hash_and_verify():
    h = passwords.hash_password("Correct-Horse-Battery-9")
    assert h.startswith("$argon2id$")
    assert passwords.verify_password(h, "Correct-Horse-Battery-9")
    assert not passwords.verify_password(h, "wrong-password-123")
    assert not passwords.verify_password("not-a-hash", "x")


def test_reset_token_binds_to_password_hash():
    tok = tokens.make_reset_token("k" * 32, 7, "hash-A")
    uid, fp = tokens.read_reset_token("k" * 32, tok, 60)
    assert uid == 7 and tokens.fingerprint_matches("hash-A", fp)
    assert not tokens.fingerprint_matches("hash-B", fp)   # token dies once the password changes
    assert tokens.read_reset_token("other" * 8, tok, 60) is None
    assert tokens.read_reset_token("k" * 32, tok + "x", 60) is None
