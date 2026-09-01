"""Authenticated bridge to the existing Campus Genie Supervisor.

This is a shared-data prototype: Databricks sees the backend credential, not
the student's JWT. Do not give that credential access to private student data.
"""

import logging
import os
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

router = APIRouter(prefix="/api/genie", tags=["Campus Genie"])
bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger(__name__)


def require_student(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer)
    ],
) -> str:
    """Validate the same signed, expiring JWT returned by /api/auth/login."""
    if credentials is None:
        raise HTTPException(
            401, "Please sign in first.", headers={"WWW-Authenticate": "Bearer"}
        )
    secret = os.getenv("JWT_SECRET_KEY")
    if not secret:
        raise HTTPException(503, "Chat authentication is not configured.")
    try:
        claims = jwt.decode(
            credentials.credentials,
            secret,
            algorithms=[os.getenv("JWT_ALGORITHM", "HS256")],
            options={"require_exp": True, "require_sub": True},
        )
        subject = claims["sub"]
        if not isinstance(subject, str) or not subject.strip():
            raise JWTError("Missing subject")
        return subject
    except (JWTError, KeyError, ValueError, TypeError):
        raise HTTPException(
            401,
            "Your session has expired or is invalid. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=16000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Six previous exchanges, followed by the current question.
    messages: list[ChatMessage] = Field(min_length=1, max_length=13)

    @model_validator(mode="after")
    def validate_history(self):
        if self.messages[-1].role != "user":
            raise ValueError("The last message must be a user question.")
        for index, message in enumerate(self.messages):
            expected = "user" if index % 2 == 0 else "assistant"
            if message.role != expected:
                raise ValueError("Messages must alternate user and assistant.")
            if message.role == "user" and len(message.content) > 4000:
                raise ValueError("Each question must be at most 4000 characters.")
        if sum(len(message.content) for message in self.messages) > 48000:
            raise ValueError("Conversation is too long. Start a new chat.")
        return self


class Citation(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)


def public_link(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def extract_answer(response) -> ChatResponse:
    """Return the final assistant message, never reasoning/tool outputs."""
    payload = response if isinstance(response, dict) else response.model_dump()
    if payload.get("error") or payload.get("status") in {"failed", "incomplete"}:
        raise HTTPException(502, "The Supervisor could not complete its answer.")
    messages = [
        item
        for item in payload.get("output", []) or []
        if item.get("type") == "message"
        and item.get("role") == "assistant"
        and item.get("channel") not in {"analysis", "commentary"}
    ]
    finals = [item for item in messages if item.get("channel") == "final"]
    if not (finals or messages):
        raise HTTPException(502, "The Supervisor returned no final answer.")
    final = (finals or messages)[-1]
    text_parts = []
    citations = []
    seen_urls = set()
    for part in final.get("content", []) or []:
        if part.get("type") == "refusal" and isinstance(part.get("refusal"), str):
            text_parts.append(part["refusal"])
        if part.get("type") not in {"output_text", "text"}:
            continue
        if isinstance(part.get("text"), str):
            text_parts.append(part["text"])
        for annotation in part.get("annotations", []) or []:
            if annotation.get("type") != "url_citation":
                continue
            # Standard Responses annotation; also accept a nested citation.
            source = annotation.get("url_citation") or annotation
            url = source.get("url")
            if public_link(url) and url not in seen_urls:
                seen_urls.add(url)
                citations.append(Citation(title=str(source.get("title") or url), url=url))
    answer = "\n\n".join(text_parts).strip()
    if not answer:
        raise HTTPException(502, "The Supervisor returned an empty answer.")
    return ChatResponse(answer=answer, citations=citations)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _student_id: Annotated[str, Depends(require_student)],
):
    token = os.getenv("DATABRICKS_TOKEN", "").strip()
    if not token:
        raise HTTPException(503, "The Databricks connection is not configured.")
    # Never accept the host, endpoint or Databricks token from the browser.
    host = os.getenv(
        "DATABRICKS_HOST", "https://dbc-c577b6cd-19b2.cloud.databricks.com"
    ).rstrip("/")
    endpoint = os.getenv("DATABRICKS_SUPERVISOR_ENDPOINT", "mas-29c70270-endpoint")
    try:
        async with AsyncOpenAI(
            api_key=token,
            base_url=f"{host}/serving-endpoints",
            timeout=180.0,
            max_retries=0,
        ) as client:
            response = await client.responses.create(
                model=endpoint,
                input=[message.model_dump() for message in request.messages],
            )
        return extract_answer(response)
    except APITimeoutError:
        raise HTTPException(504, "Genie took too long to respond. Please try again.") from None
    except APIConnectionError:
        raise HTTPException(502, "The backend could not reach Databricks.") from None
    except APIStatusError as exc:
        # Do not log tokens, student prompts, or the complete upstream body.
        logger.warning("Databricks Supervisor returned HTTP %s", exc.status_code)
        if exc.status_code == 429:
            raise HTTPException(429, "Genie is busy or has reached its usage limit.") from None
        if exc.status_code in {401, 403}:
            detail = "The backend Databricks credential is invalid or lacks access."
        elif exc.status_code == 404:
            detail = "The configured Databricks Supervisor endpoint was not found."
        else:
            detail = "Databricks could not complete the request. Please try again."
        raise HTTPException(502, detail) from None

"""Authenticated bridge to the existing Campus Genie Supervisor.

This is a shared-data prototype: Databricks sees the backend credential, not
the student's JWT. Do not give that credential access to private student data.
"""

import logging
import os
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlsplit

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from auth_security import require_student
from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

router = APIRouter(prefix="/api/genie", tags=["Campus Genie"])
logger = logging.getLogger(__name__)


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=16000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    # Six previous exchanges, followed by the current question.
    messages: list[ChatMessage] = Field(min_length=1, max_length=13)

    @model_validator(mode="after")
    def validate_history(self):
        if self.messages[-1].role != "user":
            raise ValueError("The last message must be a user question.")
        for index, message in enumerate(self.messages):
            expected = "user" if index % 2 == 0 else "assistant"
            if message.role != expected:
                raise ValueError("Messages must alternate user and assistant.")
            if message.role == "user" and len(message.content) > 4000:
                raise ValueError("Each question must be at most 4000 characters.")
        if sum(len(message.content) for message in self.messages) > 48000:
            raise ValueError("Conversation is too long. Start a new chat.")
        return self


class Citation(BaseModel):
    title: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)


def public_link(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and parsed.username is None
            and parsed.password is None
        )
    except ValueError:
        return False


def extract_answer(response) -> ChatResponse:
    """Return the final assistant message, never reasoning/tool outputs."""
    payload = response if isinstance(response, dict) else response.model_dump()
    if payload.get("error") or payload.get("status") in {"failed", "incomplete"}:
        raise HTTPException(502, "The Supervisor could not complete its answer.")
    messages = [
        item
        for item in payload.get("output", []) or []
        if item.get("type") == "message"
        and item.get("role") == "assistant"
        and item.get("channel") not in {"analysis", "commentary"}
    ]
    finals = [item for item in messages if item.get("channel") == "final"]
    if not (finals or messages):
        raise HTTPException(502, "The Supervisor returned no final answer.")
    final = (finals or messages)[-1]
    text_parts = []
    citations = []
    seen_urls = set()
    for part in final.get("content", []) or []:
        if part.get("type") == "refusal" and isinstance(part.get("refusal"), str):
            text_parts.append(part["refusal"])
        if part.get("type") not in {"output_text", "text"}:
            continue
        if isinstance(part.get("text"), str):
            text_parts.append(part["text"])
        for annotation in part.get("annotations", []) or []:
            if annotation.get("type") != "url_citation":
                continue
            # Standard Responses annotation; also accept a nested citation.
            source = annotation.get("url_citation") or annotation
            url = source.get("url")
            if public_link(url) and url not in seen_urls:
                seen_urls.add(url)
                citations.append(Citation(title=str(source.get("title") or url), url=url))
    answer = "\n\n".join(text_parts).strip()
    if not answer:
        raise HTTPException(502, "The Supervisor returned an empty answer.")
    return ChatResponse(answer=answer, citations=citations)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    _student_id: Annotated[str, Depends(require_student)],
):
    token = os.getenv("DATABRICKS_TOKEN", "").strip()
    if not token:
        raise HTTPException(503, "The Databricks connection is not configured.")
    # Never accept the host, endpoint or Databricks token from the browser.
    host = os.getenv(
        "DATABRICKS_HOST", "https://dbc-c577b6cd-19b2.cloud.databricks.com"
    ).rstrip("/")
    endpoint = os.getenv("DATABRICKS_SUPERVISOR_ENDPOINT", "mas-29c70270-endpoint")
    try:
        async with AsyncOpenAI(
            api_key=token,
            base_url=f"{host}/serving-endpoints",
            timeout=180.0,
            max_retries=0,
        ) as client:
            response = await client.responses.create(
                model=endpoint,
                input=[message.model_dump() for message in request.messages],
            )
        return extract_answer(response)
    except APITimeoutError:
        raise HTTPException(504, "Genie took too long to respond. Please try again.") from None
    except APIConnectionError:
        raise HTTPException(502, "The backend could not reach Databricks.") from None
    except APIStatusError as exc:
        # Do not log tokens, student prompts, or the complete upstream body.
        logger.warning("Databricks Supervisor returned HTTP %s", exc.status_code)
        if exc.status_code == 429:
            raise HTTPException(429, "Genie is busy or has reached its usage limit.") from None
        if exc.status_code in {401, 403}:
            detail = "The backend Databricks credential is invalid or lacks access."
        elif exc.status_code == 404:
            detail = "The configured Databricks Supervisor endpoint was not found."
        else:
            detail = "Databricks could not complete the request. Please try again."
        raise HTTPException(502, detail) from None