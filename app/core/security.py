"""Versioned password hashes with transparent legacy verification."""
import hashlib
import hmac
import secrets


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return f"scrypt:{salt}:{digest}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        if password_hash.startswith("scrypt:"):
            _, salt, expected = password_hash.split(":")
            actual = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
        else:
            salt, expected = password_hash.split(":")
            actual = hashlib.sha256((salt + password).encode()).hexdigest()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False
