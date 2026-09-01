"""Home dashboard add-on for the existing FastAPI + Lakebase Campus Genie app.

Reuse database.get_connection and auth_security.require_user from email auth.
Register home_dashboard.router once in main.py. See README.md for setup.
"""
from __future__ import annotations

import logging
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlsplit

import requests
from databricks.sdk import WorkspaceClient
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Response
from psycopg.rows import dict_row

from auth_security import require_user
from database import get_connection
from home_logic import (IST, MAX_ROWS, SourceUnavailable, table_name, parse_moment, content_key,
                        matches, active, weekly_pulse, next_item, archive_item, post_payload, period)

load_dotenv(Path(__file__).resolve().parent / ".env")
router = APIRouter(prefix="/api/home", tags=["Home dashboard"])
User = Annotated[dict, Depends(require_user)]
LOG = logging.getLogger(__name__)
_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="home-dashboard")
_cache: dict[str, tuple[float, Any]] = {}
_locks = {key: threading.Lock() for key in ("content", "resources", "weather")}
PUBLIC_COLUMNS = (
    "content_id", "post_id", "content_source", "type", "title", "body", "deadline",
    "author_id", "author_name", "club_name", "initials", "tags", "skills_required",
    "team_slots", "meta", "created_at", "published_at", "starts_at", "start_at",
    "start_time", "event_time", "event_datetime", "event_date", "start_date",
    "location", "venue", "source_url", "url",
)


def cached(key, loader, ttl):
    """Cache only shared/public source data. Never cache a user's profile/saves."""
    with _locks[key]:
        item = _cache.get(key)
        if item and time.monotonic() - item[0] < ttl:
            return item[1]
        try:
            value = {"status": "ok", "data": loader(), "fetched_at": datetime.now(IST).isoformat()}
        except Exception as exc:
            # Do not log response bodies, SQL, tokens, or connection strings.
            LOG.warning("Home %s source unavailable (%s)", key, type(exc).__name__)
            value = {"status": "unavailable", "data": None, "fetched_at": None}
        _cache[key] = (time.monotonic(), value)
        return value


@lru_cache(maxsize=1)
def workspace():
    return WorkspaceClient()


def sql_rows(statement):
    """Read every INLINE result chunk; never silently treat PENDING as empty."""
    warehouse = os.getenv("DATABRICKS_WAREHOUSE_ID", "").strip()
    if not warehouse:
        raise SourceUnavailable("DATABRICKS_WAREHOUSE_ID is required")
    ws = workspace()
    host = ws.config.host.rstrip("/")
    if urlsplit(host).scheme != "https":
        raise SourceUnavailable("Databricks host must use HTTPS")
    response = requests.post(
        host + "/api/2.0/sql/statements", headers=ws.config.authenticate(),
        json={"warehouse_id": warehouse, "statement": statement, "format": "JSON_ARRAY",
              "disposition": "INLINE", "wait_timeout": "10s", "on_wait_timeout": "CANCEL"},
        timeout=(5, 15), allow_redirects=False,
    )
    response.raise_for_status()
    result = response.json()
    if result.get("status", {}).get("state") != "SUCCEEDED":
        raise SourceUnavailable("SQL warehouse did not complete the read")
    manifest = result.get("manifest") or {}
    if manifest.get("truncated"):
        raise SourceUnavailable("Incomplete SQL result")
    names = [column["name"] for column in manifest.get("schema", {}).get("columns", [])]
    chunk = result.get("result") or {}
    rows, seen = [], set()
    while True:
        rows.extend(dict(zip(names, row)) for row in chunk.get("data_array") or [])
        link = chunk.get("next_chunk_internal_link")
        if not link:
            break
        # Credentials go only to the configured host and SQL chunk endpoint.
        if not re.fullmatch(r"/api/2\.0/sql/statements/[A-Za-z0-9-]+/result/chunks/\d+(?:\?[^\s]*)?", link) or link in seen:
            raise SourceUnavailable("Invalid SQL continuation")
        seen.add(link)
        response = requests.get(host + link, headers=ws.config.authenticate(), timeout=(5, 15), allow_redirects=False)
        response.raise_for_status()
        chunk = response.json()
    return rows


def read_content():
    table = table_name("CAMPUS_CONTENT_TABLE", "campus_genie.silver.campus_content")
    schema = {str(row.get("col_name", "")).lower(): str(row.get("data_type", "")).lower()
              for row in sql_rows(f"DESCRIBE TABLE {table}")}
    available = set(schema)
    if "title" not in available or not ({"content_id", "post_id"} & available):
        raise SourceUnavailable("Content needs title and content_id or post_id")
    selected = [column for column in PUBLIC_COLUMNS if column in available]
    order_column = next((column for column in ("created_at", "published_at", "deadline", "content_id", "post_id") if column in available))
    expressions = [f"CAST(unix_micros(`{c}`) / 1000000.0 AS DOUBLE) AS `{c}`"
                   if schema[c] in {"timestamp", "timestamp_ltz"} else f"`{c}`" for c in selected]
    rows = sql_rows(f"SELECT {', '.join(expressions)} FROM {table} ORDER BY `{order_column}` DESC NULLS LAST LIMIT {MAX_ROWS + 1}")
    # Explicitly expose bounded datasets; do not claim a sample is a campus total.
    return {"rows": rows[:MAX_ROWS], "partial": len(rows) > MAX_ROWS}


def read_resource_count():
    table = table_name("CAMPUS_RESOURCES_TABLE")
    if table is None:
        return None
    rows = sql_rows(f"SELECT COUNT(*) AS total FROM {table}")
    return int(rows[0]["total"])


def own_profile(user):
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT name, skills, interests FROM student_public WHERE user_id=%s", (user["user_id"],))
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Complete your student profile first.")
    return row


def authors_for(rows):
    ids = list({str(row["author_id"]) for row in rows if row.get("author_id")})
    if not ids:
        return {}
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""SELECT user_id::text, student_id, name, department, year_of_study
                       FROM student_public WHERE user_id::text=ANY(%s) OR student_id=ANY(%s)""", (ids, ids))
        authors = cur.fetchall()
    return {str(author[key]): author for author in authors for key in ("user_id", "student_id")}


def saved_ids(user):
    with get_connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT content_key FROM campus_home_interests WHERE user_id=%s", (user["user_id"],))
        return {row["content_key"] for row in cur.fetchall()}


def weather_data():
    response = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": 12.9417, "longitude": 77.5750, "current": "temperature_2m,weather_code,is_day",
        "temperature_unit": "celsius", "timezone": "Asia/Kolkata",
    }, timeout=(3, 7))
    response.raise_for_status()
    current = response.json()["current"]
    code = int(current["weather_code"])
    names = {0: "Clear", 1: "Mainly clear", 2: "Partly cloudy", 3: "Cloudy", 45: "Foggy", 48: "Foggy",
             51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle", 56: "Freezing drizzle", 57: "Freezing drizzle",
             61: "Light rain", 63: "Rain", 65: "Heavy rain", 66: "Freezing rain", 67: "Freezing rain",
             71: "Light snow", 73: "Snow", 75: "Heavy snow", 77: "Snow grains", 80: "Rain showers",
             81: "Rain showers", 82: "Heavy showers", 85: "Snow showers", 86: "Snow showers",
             95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with hail"}
    return {"temperature_c": round(float(current["temperature_2m"])), "condition": names.get(code, "Current weather"),
            "is_day": bool(current.get("is_day", 1)), "observed_at": current.get("time"), "location": "Basavanagudi"}


@router.get("")
def home(user: User, response: Response):
    response.headers["Cache-Control"] = "no-store"
    now = datetime.now(IST)
    profile = own_profile(user)
    first = (str(profile.get("name") or "").split() or ["there"])[0]
    futures = {
        "content": _pool.submit(cached, "content", read_content, 120),
        "resources": _pool.submit(cached, "resources", read_resource_count, 300),
        "weather": _pool.submit(cached, "weather", weather_data, 600),
    }
    source = {key: future.result() for key, future in futures.items()}
    content = source["content"]["data"] or {"rows": [], "partial": False}
    # Stable identity deduplication also handles accidental duplicate ingestions.
    rows = list({content_key(row): row for row in content["rows"]}.values())
    available = source["content"]["status"] == "ok"
    live_rows = [row for row in rows if active(row, now)]
    live_rows.sort(key=lambda row: (not matches(row, profile), -(parse_moment(row.get("created_at") or row.get("published_at"))[0] or datetime(1970, 1, 1, tzinfo=IST)).timestamp(), str(row.get("title") or "")))
    feed_rows = live_rows[:100]
    try:
        authors = authors_for(feed_rows)
    except Exception as exc:
        LOG.warning("Home author lookup unavailable (%s)", type(exc).__name__)
        authors = {}
    interest_status = "ok"
    try:
        saved = saved_ids(user)
    except Exception as exc:
        LOG.warning("Home interest storage unavailable (%s)", type(exc).__name__)
        saved, interest_status = set(), "unavailable"
    resource_count = source["resources"]["data"]
    weather = source["weather"]["data"] or {"location": "Basavanagudi", "temperature_c": None, "condition": "Weather unavailable", "is_day": True, "observed_at": None}
    return {
        "generated_at": now.isoformat(), "timezone": "Asia/Kolkata", "first_name": first,
        "greeting": f"{now.strftime('%A')} {period(now.hour)}, {first}",
        "date_label": f"{now.strftime('%A')}, {now.day} {now.strftime('%B')}",
        "weather": {**weather, "status": source["weather"]["status"]},
        "pulse": weekly_pulse(rows, now, content["partial"]) if available else None,
        "shortcuts": {"resource_count": resource_count, "matching_posts": sum(matches(row, profile) for row in live_rows) if available else None},
        "posts": [post_payload(row, authors, saved, profile) for row in feed_rows],
        "up_next": next_item(rows, now) if available else None,
        "archive": archive_item(rows, now) if available else None,
        "content_status": source["content"]["status"], "content_fetched_at": source["content"]["fetched_at"],
        "partial": content["partial"], "feed_limited": len(live_rows) > len(feed_rows), "interest_status": interest_status,
    }


def check_key(key):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,1024}", key):
        raise HTTPException(422, "Invalid post ID.")


@router.put("/interests/{key}")
def add_interest(key: str, user: User):
    check_key(key)
    source = cached("content", read_content, 120)
    if source["status"] != "ok":
        raise HTTPException(503, "Campus posts are temporarily unavailable. Try again shortly.")
    if not any(content_key(row) == key for row in source["data"]["rows"]):
        raise HTTPException(404, "This post is no longer available.")
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("""INSERT INTO campus_home_interests (user_id, content_key) VALUES (%s, %s)
                           ON CONFLICT (user_id, content_key) DO NOTHING""", (user["user_id"], key))
    except Exception as exc:
        LOG.warning("Home interest save unavailable (%s)", type(exc).__name__)
        raise HTTPException(503, "Interested could not be saved. Try again shortly.") from None
    return {"id": key, "interested": True}


@router.delete("/interests/{key}")
def remove_interest(key: str, user: User):
    check_key(key)
    try:
        with get_connection() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM campus_home_interests WHERE user_id=%s AND content_key=%s", (user["user_id"], key))
    except Exception as exc:
        LOG.warning("Home interest removal unavailable (%s)", type(exc).__name__)
        raise HTTPException(503, "Interested could not be removed. Try again shortly.") from None
    return {"id": key, "interested": False}
