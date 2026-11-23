import base64
import os

import pytest

from app.security.crypto import CryptoError, CryptoService


def svc():
    return CryptoService(os.urandom(32))


def test_file_roundtrip():
    s = svc()
    ct, nonce, wrapped = s.encrypt_file(b"secret resume", b"ctx")
    assert b"secret" not in ct
    assert s.decrypt_file(ct, nonce, wrapped, b"ctx") == b"secret resume"


def test_wrong_context_rejected():
    s = svc()
    ct, nonce, wrapped = s.encrypt_file(b"data", b"resume-file:A")
    with pytest.raises(CryptoError):
        s.decrypt_file(ct, nonce, wrapped, b"resume-file:B")


def test_tampered_ciphertext_rejected():
    s = svc()
    ct, nonce, wrapped = s.encrypt_file(b"data", b"ctx")
    bad = bytes([ct[0] ^ 1]) + ct[1:]
    with pytest.raises(CryptoError):
        s.decrypt_file(bad, nonce, wrapped, b"ctx")


def test_wrong_master_key_rejected():
    ct, nonce, wrapped = svc().encrypt_file(b"data", b"ctx")
    with pytest.raises(CryptoError):
        svc().decrypt_file(ct, nonce, wrapped, b"ctx")


def test_field_roundtrip_and_unique_nonce():
    s = svc()
    a, b = s.encrypt_field(b"name", b"ctx"), s.encrypt_field(b"name", b"ctx")
    assert a != b
    assert s.decrypt_field(a, b"ctx") == b"name"


def test_bad_key_length_and_b64():
    with pytest.raises(CryptoError):
        CryptoService(b"short")
    with pytest.raises(CryptoError):
        CryptoService.from_b64("")
    assert CryptoService.from_b64(base64.b64encode(os.urandom(32)).decode())
