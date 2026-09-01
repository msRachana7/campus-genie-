"""Simple password login for the local Campus Genie demo; no email verification."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from psycopg.rows import dict_row
from database import get_connection

load_dotenv(Path(__file__).resolve().parent / ".env")
bearer = HTTPBearer(auto_error=False)


def jwt_settings():
    secret = os.getenv("JWT_SECRET_KEY", "")
    if len(secret) < 32:
        raise HTTPException(503, "Set JWT_SECRET_KEY to a random secret of at least 32 characters in backend/.env.")
    return secret, "HS256"


def password_version(encoded_password, secret):
    # An opaque tag invalidates existing tokens if the stored password changes.
    return hmac.new(secret.encode(), encoded_password.encode(), hashlib.sha256).hexdigest()


def access_token(user):
    secret, algorithm = jwt_settings()
    return jwt.encode({
        "sub": str(user["user_id"]),
        "email": user["email"],
        "usn": user["usn"],
        "pwdv": password_version(user["password_hash"], secret),
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
    }, secret, algorithm=algorithm)


def require_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    invalid = HTTPException(401, "Please sign in again.", headers={"WWW-Authenticate": "Bearer"})
    if credentials is None:
        raise invalid
    secret, algorithm = jwt_settings()
    try:
        claims = jwt.decode(credentials.credentials, secret, algorithms=[algorithm],
                            options={"require_exp": True, "require_sub": True})
        if not isinstance(claims.get("sub"), str) or not isinstance(claims.get("pwdv"), str):
            raise invalid
    except JWTError:
        raise invalid from None
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""SELECT user_id, usn, email, password_hash FROM student_private
                       WHERE user_id::text=%s""", (claims["sub"],))
        user = cur.fetchone()
    if not user or not user["password_hash"] or user["password_hash"] == "NOT_REGISTERED":
        raise invalid
    if not hmac.compare_digest(claims["pwdv"], password_version(user["password_hash"], secret)):
        raise invalid
    return {key: value for key, value in user.items() if key != "password_hash"}


def require_student(user: Annotated[dict, Depends(require_user)]) -> str:
    return str(user["user_id"])
