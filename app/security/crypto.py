"""AES-256-GCM envelope encryption.

Files: random 256-bit data key (DEK) per file; DEK wrapped by the master key.
Fields: encrypted directly with the master key; output = nonce || ciphertext||tag.
Associated data (AAD) binds each ciphertext to its context, so a blob copied to
another record fails authentication.
"""
import base64
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_LEN = 12
WRAP_AAD = b"dek-wrap-v1"


class CryptoError(Exception):
    pass


class CryptoService:
    def __init__(self, master_key: bytes):
        if len(master_key) != 32:
            raise CryptoError("Master key must be exactly 32 bytes (AES-256).")
        self._master = AESGCM(master_key)

    @classmethod
    def from_b64(cls, b64: str) -> "CryptoService":
        if not b64:
            raise CryptoError("MASTER_KEY is not configured.")
        try:
            return cls(base64.b64decode(b64, validate=True))
        except Exception as exc:  # noqa: BLE001
            raise CryptoError("MASTER_KEY is not valid base64 for 32 bytes.") from exc

    # ---- files (envelope) ----
    def encrypt_file(self, plaintext: bytes, aad: bytes):
        """Return (ciphertext, nonce, wrapped_dek)."""
        dek = AESGCM.generate_key(bit_length=256)
        nonce = os.urandom(NONCE_LEN)
        ciphertext = AESGCM(dek).encrypt(nonce, plaintext, aad)
        wrap_nonce = os.urandom(NONCE_LEN)
        wrapped = wrap_nonce + self._master.encrypt(wrap_nonce, dek, WRAP_AAD)
        return ciphertext, nonce, wrapped

    def decrypt_file(self, ciphertext: bytes, nonce: bytes, wrapped_dek: bytes, aad: bytes) -> bytes:
        try:
            dek = self._master.decrypt(wrapped_dek[:NONCE_LEN], wrapped_dek[NONCE_LEN:], WRAP_AAD)
            return AESGCM(dek).decrypt(nonce, ciphertext, aad)
        except InvalidTag as exc:
            raise CryptoError("Authentication failed: data tampered or wrong key/context.") from exc

    # ---- small fields ----
    def encrypt_field(self, plaintext: bytes, aad: bytes) -> bytes:
        nonce = os.urandom(NONCE_LEN)
        return nonce + self._master.encrypt(nonce, plaintext, aad)

    def decrypt_field(self, blob: bytes, aad: bytes) -> bytes:
        try:
            return self._master.decrypt(blob[:NONCE_LEN], blob[NONCE_LEN:], aad)
        except InvalidTag as exc:
            raise CryptoError("Authentication failed: field tampered or wrong context.") from exc


def get_crypto() -> CryptoService:
    from flask import current_app

    svc = current_app.extensions.get("crypto_service")
    if svc is None:
        svc = CryptoService.from_b64(current_app.config["MASTER_KEY_B64"])
        current_app.extensions["crypto_service"] = svc
    return svc
