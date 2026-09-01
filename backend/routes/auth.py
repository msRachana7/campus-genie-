"""Register -> signed in. Subsequent visits: email + password. No SMTP or migration."""
import hashlib
import threading
import time
import uuid
from collections import deque
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from psycopg import DataError, IntegrityError, sql
from psycopg.rows import dict_row

from database import get_connection
from auth_crypto import check_password, hash_password
from auth_schema import adapt_list, check_schema
from auth_security import access_token, jwt_settings, require_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
_attempts = {}
_lock = threading.Lock()


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)

    @field_validator("email", mode="before")
    @classmethod
    def normalize(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def college_email(cls, value):
        if value.rsplit("@", 1)[-1] != "bmsce.ac.in":
            raise ValueError("Use your @bmsce.ac.in college email.")
        return value


class RegisterRequest(LoginRequest):
    password: str = Field(min_length=12, max_length=256)
    name: str = Field(min_length=1, max_length=120)
    usn: str = Field(min_length=5, max_length=24)
    department: str = Field(min_length=1, max_length=120)
    year_of_study: int = Field(ge=1, le=4)
    contact_number: str | None = Field(default=None, max_length=32)

    @field_validator("name", "department", "usn", mode="before")
    @classmethod
    def trim_text(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("usn")
    @classmethod
    def normalize_usn(cls, value):
        if not value.isascii() or not value.isalnum():
            raise ValueError("USN must contain only letters and numbers.")
        return value.upper()


def limit_attempts(request, email):
    """Small in-memory limit for a single-process localhost demo."""
    now = time.monotonic()
    ip = request.client.host if request.client else "unknown"
    keys = [("ip:" + ip, 60), ("email:" + email, 15)]
    with _lock:
        for key in list(_attempts):
            while _attempts[key] and _attempts[key][0] <= now - 600:
                _attempts[key].popleft()
            if not _attempts[key]:
                del _attempts[key]
        for raw, limit in keys:
            key = hashlib.sha256(raw.encode()).hexdigest()
            if len(_attempts) >= 4096 and key not in _attempts:
                raise HTTPException(429, "Too many attempts. Try again later.")
            attempts = _attempts.setdefault(key, deque())
            if len(attempts) >= limit:
                raise HTTPException(429, "Too many attempts. Try again in 10 minutes.")
        for raw, _ in keys:
            _attempts[hashlib.sha256(raw.encode()).hexdigest()].append(now)


def account(cur, email):
    cur.execute("""SELECT pr.user_id, pr.usn, pr.email, pr.password_hash, p.email AS public_email
                   FROM student_private pr JOIN student_public p ON p.user_id=pr.user_id
                   WHERE lower(trim(pr.email))=%s""", (email,))
    return cur.fetchone()


def session_result(user):
    return {"access_token": access_token(user), "token_type": "bearer", "user": {
        "user_id": str(user["user_id"]), 
        "email": user["email"], "usn": user["usn"],
    }}


def check_available(cur, email, usn):
    # Serializes signups even when the optional previous migration was never run.
    for identity in sorted(["cg-signup-email:" + email, "cg-signup-usn:" + usn]):
        cur.execute("SELECT pg_advisory_xact_lock(hashtextextended(%s, 0))", (identity,))
    cur.execute("""SELECT password_hash FROM student_private
                   WHERE lower(trim(email))=%s OR upper(trim(usn))=%s""", (email, usn))
    if cur.fetchone():
        # Without mailbox verification, a signup cannot claim a preloaded identity.
        raise HTTPException(409, "This email or USN already exists. Sign in if you registered it. For an unregistered sample record, ask the administrator to resolve the conflict; registration will not overwrite it.")
    cur.execute("SELECT 1 FROM student_public WHERE lower(trim(email))=%s", (email,))
    if cur.fetchone():
        raise HTTPException(409, "An existing profile uses this email. Ask the administrator to check it.")


def create_account(conn, cur, data, encoded_password):
    schema = check_schema(conn)
    now = datetime.now(timezone.utc)
    user_id = uuid.uuid4()
    public = {"user_id": user_id, "email": str(data.email), "name": data.name,
              "department": data.department, "year_of_study": data.year_of_study}
    for field in ("skills", "interests", "looking_for"):
        public[field] = adapt_list([], schema["student_public"][field])
    private = {"user_id": user_id, "usn": data.usn, "email": str(data.email),
               "password_hash": encoded_password, "contact_number": data.contact_number}
    if private["contact_number"] is None and schema["student_private"]["contact_number"]["required"]:
        private["contact_number"] = ""
    # Never write a fake email_verified_at. This flow does not verify email ownership.
    private["auth_version"] = 0

    for table, values in (("student_private", private), ("student_public", public)):
        for field in ("created_at", "updated_at"):
            if field in schema[table]:
                values[field] = now
        for field, value in values.items():
            max_length = schema[table].get(field, {}).get("max_length")
            if isinstance(value, str) and max_length and len(value) > max_length:
                raise HTTPException(400, f"{field} must be at most {max_length} characters for your database.")
        cur.execute(sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table), sql.SQL(",").join(map(sql.Identifier, values)),
            sql.SQL(",").join(sql.Placeholder() for _ in values)), tuple(values.values()))
    return {**private, "email": str(data.email)}


@router.post("/register", status_code=201)
def register(data: RegisterRequest, request: Request):
    jwt_settings()
    limit_attempts(request, str(data.email))
    encoded = hash_password(data.password)
    try:
        with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            check_available(cur, str(data.email), data.usn)
            user = create_account(conn, cur, data, encoded)
    except (IntegrityError, DataError):
        raise HTTPException(409, "The account conflicts with your database rules. No partial account was saved. Send the table definition so the insert can be matched to it.") from None
    except ValueError:
        raise HTTPException(503, "The student-table schema differs from the supplied code. Run the read-only setup_email_auth.py check and share its error; do not change or delete existing records.") from None
    return {"message": "Account created. You are signed in.", **session_result(user)}


@router.post("/login")
def login(data: LoginRequest, request: Request):
    limit_attempts(request, str(data.email))
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        user = account(cur, str(data.email))
    if not user:
        hash_password(data.password)
        raise HTTPException(401, "Invalid email or password.")
    if not check_password(data.password, user["password_hash"]):
        raise HTTPException(401, "Invalid email or password.")
    return {"message": "Login successful.", **session_result(user)}


@router.get("/me")
def me(user: Annotated[dict, Depends(require_user)]):
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        current = account(cur, user["email"].strip().lower())
    if not current:
        raise HTTPException(401, "Your account has no profile. Please contact the administrator.")
    return {"user": {"user_id": str(current["user_id"]), 
                     "email": current["email"], "usn": current["usn"]}}
