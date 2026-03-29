"""
generate_key.py
Run this ONCE to create your encryption key, then store it in your environment.

Usage:
    python generate_key.py

Copy the printed key and set it as an environment variable:
    export BIOMETRIC_ENCRYPTION_KEY="<printed key>"

Never commit this key to git. Treat it like a password.
"""

from cryptography.fernet import Fernet

key = Fernet.generate_key().decode()
print("Your encryption key (store this securely — do NOT commit to git):")
print()
print(f"  export BIOMETRIC_ENCRYPTION_KEY=\"{key}\"")
print()
print("Also set a strong Flask secret key:")
import secrets
print(f"  export FLASK_SECRET_KEY=\"{secrets.token_hex(32)}\"")
