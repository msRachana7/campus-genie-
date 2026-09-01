"""Password and link-token primitives; no database or web dependencies."""
import base64
import hashlib
import hmac
import secrets


def new_token():
    raw = secrets.token_urlsafe(32)
    return raw, token_hash(raw)


def token_hash(raw):
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32)
    return "scrypt$" + base64.b64encode(salt).decode() + "$" + base64.b64encode(digest).decode()


def check_password(password, encoded):
    if not encoded or encoded == "NOT_REGISTERED":
        return False
    try:
        if encoded.startswith("scrypt$"):
            _, salt, expected = encoded.split("$")
            salt = base64.b64decode(salt, validate=True)
            expected = base64.b64decode(expected, validate=True)
            if len(salt) != 16 or len(expected) != 32:
                return False
            actual = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32)
            return hmac.compare_digest(actual, expected)
        if encoded.startswith(("$2a$", "$2b$", "$2y$")):
            import bcrypt
            return bcrypt.checkpw(password.encode("utf-8"), encoded.encode("utf-8"))
    except (ValueError, TypeError, UnicodeError):
        return False
    return False
