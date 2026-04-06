"""
security.py
-----------
Provides password hashing and biometric data encryption for the SPE research site.

Password Hashing:
  - Uses bcrypt with a work factor of 12 (adjustable via BCRYPT_ROUNDS env var).
  - bcrypt is purpose-built for passwords: slow by design, includes salt automatically.

Biometric Encryption:
  - Uses AES-256-GCM for sensitive numeric data (e.g. heart rate).
  - A 256-bit key is derived from the BIOMETRIC_SECRET env var via PBKDF2-HMAC-SHA256.
  - GCM mode provides both confidentiality AND integrity (tamper detection).

Test Score Encryption:
    - Uses a separate AES-256-GCM key derived from TEST_SCORE_SECRET for encrypting test scores.

Setup — set these env vars before running the app:
    BIOMETRIC_SECRET   - Strong random secret (>=32 chars). NEVER commit to source control.
    BCRYPT_ROUNDS      - (Optional) bcrypt cost factor, default 12.

Generate a suitable secret:
    python -c "import secrets; print(secrets.token_hex(32))"
"""

import os
import base64
import hashlib

import bcrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Configuration
BCRYPT_ROUNDS: int = int(os.environ.get("BCRYPT_ROUNDS", 12))

_BIOMETRIC_SECRET: str = os.environ.get("BIOMETRIC_SECRET", "")
if not _BIOMETRIC_SECRET:
    raise EnvironmentError(
        "BIOMETRIC_SECRET environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

# Derive a 256-bit AES key from the secret using PBKDF2.
_AES_KEY: bytes = hashlib.pbkdf2_hmac(
    "sha256",
    _BIOMETRIC_SECRET.encode(),
    b"spe-biometric-salt-v1",
    iterations=200_000,
    dklen=32,
)

# Password helpers
def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password with bcrypt.
    Returns a UTF-8 string for database storage.
    The value embeds the random salt and cost factor — no extra columns needed.
    """
    hashed: bytes = bcrypt.hashpw(
        plain_password.encode("utf-8"),
        bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    )
    return hashed.decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a plaintext password against a stored bcrypt hash.
    Uses constant-time comparison to resist timing attacks.
    Returns True if the password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            stored_hash.encode("utf-8")
        )
    except Exception:
        return False

# Biometric encryption helpers
def encrypt_biometric(value: float) -> str:
    """
    Encrypt a sensitive biometric measurement (e.g. heart rate) for at-rest storage.

    Uses AES-256-GCM:
      - A fresh 12-byte random nonce is generated per call (never reused).
      - Nonce is prepended to ciphertext and base64url-encoded for string storage.
      - GCM authentication tag (16 bytes) is appended automatically and
        verified on decryption, catching any tampering.

    Returns a base64url string: base64(nonce || ciphertext+tag)
    """
    aesgcm = AESGCM(_AES_KEY)
    nonce: bytes = os.urandom(12)
    plaintext: bytes = str(value).encode("utf-8")
    ciphertext: bytes = aesgcm.encrypt(nonce, plaintext, None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_biometric(token: str) -> float:
    """
    Decrypt a biometric value produced by encrypt_biometric().
    Raises ValueError if the token is malformed or has been tampered with.
    """
    try:
        raw: bytes = base64.urlsafe_b64decode(token.encode("utf-8"))
        nonce, ciphertext = raw[:12], raw[12:]
        aesgcm = AESGCM(_AES_KEY)
        plaintext: bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return float(plaintext.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to decrypt biometric value: {exc}") from exc
    
# Test score encryption helpers (separate key from biometric)
_TEST_SCORE_SECRET: str = os.environ.get("TEST_SCORE_SECRET", "")
if not _TEST_SCORE_SECRET:
    raise EnvironmentError(
        "TEST_SCORE_SECRET environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

_TEST_SCORE_KEY: bytes = hashlib.pbkdf2_hmac(
    "sha256",
    _TEST_SCORE_SECRET.encode(),
    b"spe-testscore-salt-v1",
    iterations=200_000,
    dklen=32,
)


def encrypt_test_score(value: float) -> str:
    """Encrypt a test score using a separate AES-256-GCM key."""
    aesgcm = AESGCM(_TEST_SCORE_KEY)
    nonce: bytes = os.urandom(12)
    plaintext: bytes = str(value).encode("utf-8")
    ciphertext: bytes = aesgcm.encrypt(nonce, plaintext, None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_test_score(token: str) -> float:
    """Decrypt a test score encrypted with encrypt_test_score()."""
    try:
        raw: bytes = base64.urlsafe_b64decode(token.encode("utf-8"))
        nonce, ciphertext = raw[:12], raw[12:]
        aesgcm = AESGCM(_TEST_SCORE_KEY)
        plaintext: bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return float(plaintext.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"Failed to decrypt test score: {exc}") from exc