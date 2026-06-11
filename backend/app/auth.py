from __future__ import annotations
from datetime import datetime, timedelta, timezone
import base64
import hashlib
import hmac
import json
import os
from .config import get_settings


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return f"pbkdf2_sha256${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        scheme, salt_b64, digest_b64 = stored.split("$", 2)
    except ValueError:
        return False
    if scheme != "pbkdf2_sha256":
        return False
    salt = _unb64(salt_b64)
    expected = _unb64(digest_b64)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 260_000)
    return hmac.compare_digest(actual, expected)


def create_access_token(subject: str) -> str:
    settings = get_settings()
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": int(exp.timestamp())}
    body = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    sig = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64(sig)}"


def verify_access_token(token: str) -> str | None:
    settings = get_settings()
    try:
        body, sig = token.split(".", 1)
        expected = hmac.new(settings.secret_key.encode(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_unb64(sig), expected):
            return None
        payload = json.loads(_unb64(body))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return str(payload["sub"])
    except Exception:
        return None

