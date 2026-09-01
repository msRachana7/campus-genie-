"""Pure formatting, matching, and date logic for the Campus Genie Home API."""
from __future__ import annotations
import base64
import json
import os
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
MAX_ROWS = 5000
AI_WORDS = re.compile(r"\b(ai|artificial intelligence|machine learning|data science|generative ai|genai|llm|rag|deep learning)\b", re.I)
EVENT_TYPES = {"event", "events", "club_event", "technical event", "technical_event"}

class SourceUnavailable(RuntimeError):
    pass

def table_name(env, default=""):
    name = os.getenv(env, default).strip()
    if not name:
        return None
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z_][A-Za-z0-9_]*", name):
        raise SourceUnavailable(f"Invalid {env}")
    return ".".join(f"`{part}`" for part in name.split("."))


def text_list(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except (ValueError, TypeError):
            value = value.split(",")
    if not isinstance(value, (list, tuple)):
        return []
    return list(dict.fromkeys(str(item).strip() for item in value if str(item).strip()))[:100]


def json_object(value):
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except ValueError:
            return {}
    return value if isinstance(value, dict) else {}


def parse_moment(value):
    """Return (IST datetime, has_time). DATE values retain date-only precision."""
    if not value:
        return None, False
    # SQL TIMESTAMP columns are exported as epoch seconds to retain timezone.
    if isinstance(value, (int, float)) or (isinstance(value, str) and re.fullmatch(r"-?\d{10,}(?:\.\d+)?", value)):
        try:
            return datetime.fromtimestamp(float(value), IST), True
        except (ValueError, OverflowError, OSError):
            return None, False
    if isinstance(value, datetime):
        parsed, timed = value, True
    elif isinstance(value, date):
        parsed, timed = datetime.combine(value, datetime.min.time()), False
    else:
        value = str(value).strip()
        timed = len(value) > 10
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None, False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=IST)
    return parsed.astimezone(IST), timed


def event_moment(row):
    meta = json_object(row.get("meta"))
    for field in ("starts_at", "start_at", "event_datetime", "event_date", "start_date"):
        value = row.get(field) or meta.get(field)
        parsed, timed = parse_moment(value)
        if parsed:
            clock = row.get("event_time") or row.get("start_time") or meta.get("event_time") or meta.get("start_time")
            if not timed and clock and re.fullmatch(r"\d{2}:\d{2}(?::\d{2})?", str(clock)):
                combined, precise = parse_moment(f"{parsed.date().isoformat()}T{clock}")
                if combined:
                    return combined, precise
            return parsed, timed
    return None, False


def is_event(row):
    # A teammate call mentioning a hackathon is not itself an event.
    return str(row.get("content_source", "")).lower() in EVENT_TYPES or str(row.get("type", "")).lower() in EVENT_TYPES


def content_key(row):
    source = str(row.get("content_source") or row.get("type") or "post")
    identifier = str(row.get("content_id") or row.get("post_id") or "")
    if not identifier:
        raise ValueError("Missing content ID")
    raw = json.dumps([source, identifier], separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


def plain_text(row):
    return " ".join([str(row.get("title") or ""), str(row.get("body") or ""), *text_list(row.get("tags")), *text_list(row.get("skills_required"))])


def matches(row, profile):
    haystack = plain_text(row).casefold()
    preferences = text_list(profile.get("skills")) + text_list(profile.get("interests"))
    for preference in preferences:
        if preference.casefold() == "ai & data" and AI_WORDS.search(haystack):
            return True
        if re.search(r"(?<!\w)" + re.escape(preference.casefold()) + r"(?!\w)", haystack):
            return True
    return False


def active(row, now):
    starts, precise = event_moment(row) if is_event(row) else (None, False)
    if starts:
        return starts >= now if precise else starts.date() >= now.date()
    deadline, _ = parse_moment(row.get("deadline"))
    return deadline is None or deadline.date() >= now.date()


def weekly_pulse(rows, now, partial):
    monday = now.date() - timedelta(days=now.weekday())
    week_end = monday + timedelta(days=7)
    ai_days, all_days = [0] * 7, [0] * 7
    previous = 0
    known_dates = False
    for row in rows:
        starts, _ = event_moment(row)
        if not is_event(row) or starts is None:
            continue
        known_dates = True
        ai = bool(AI_WORDS.search(plain_text(row)))
        if monday <= starts.date() < week_end:
            all_days[starts.weekday()] += 1
            if ai:
                ai_days[starts.weekday()] += 1
        elif monday - timedelta(days=7) <= starts.date() < monday and ai:
            previous += 1
    count = sum(ai_days)
    if not known_dates:
        headline = "Campus opportunities, in one place."
        detail = "Event dates are not available yet. Browse the active campus posts below."
    elif count == 0:
        headline = "No dated AI events listed this week."
        detail = "The chart shows scheduled campus events for Monday through Sunday."
    else:
        headline = f"{count} AI event{'s' if count != 1 else ''} scheduled this week."
        detail = f"{count} listed this week; {previous} listed last week. Counts use scheduled event dates."
        if count > previous and previous > 0 and not partial:
            headline = "AI events are up this week."
    if partial:
        detail += f" Counts cover the {MAX_ROWS:,} loaded records only."
    return {"headline": headline, "detail": detail, "week_start": monday.isoformat(),
            "week_end": (week_end - timedelta(days=1)).isoformat(), "ai_event_count": count,
            "previous_ai_event_count": previous, "event_days": all_days, "ai_days": ai_days,
            "has_event_dates": known_dates, "active_count": sum(active(row, now) for row in rows)}


def next_item(rows, now):
    events, deadlines = [], []
    for row in rows:
        starts, precise = event_moment(row) if is_event(row) else (None, False)
        if starts and (starts >= now if precise else starts.date() >= now.date()):
            events.append((starts, str(row.get("title") or ""), row, precise))
        deadline, timed = parse_moment(row.get("deadline"))
        if deadline and deadline.date() >= now.date() and active(row, now):
            deadlines.append((deadline, str(row.get("title") or ""), row, timed))
    candidates = events or deadlines
    if not candidates:
        return None
    starts, _, row, precise = min(candidates, key=lambda item: (item[0], item[1]))
    meta = json_object(row.get("meta"))
    return {"id": content_key(row), "title": row.get("title") or "Campus listing",
            "kind": "event" if events else "deadline", "date": starts.date().isoformat(),
            "day": f"{starts.day:02d}", "month": starts.strftime("%b").upper(),
            "time": starts.strftime("%I:%M %p").lstrip("0") if precise else "Time not listed",
            "location": str(row.get("location") or row.get("venue") or meta.get("location") or meta.get("venue") or "Location not listed")}


def archive_item(rows, now):
    dated = []
    for row in rows:
        moment, _ = event_moment(row) if is_event(row) else (None, False)
        moment = moment or parse_moment(row.get("deadline"))[0]
        if moment and moment.date() < now.date():
            dated.append((moment, row))
    if not dated:
        return None
    moment, row = max(dated, key=lambda item: item[0])
    return {"title": str(row.get("title") or "Past campus post"), "year": moment.year}


def post_payload(row, authors, saved, profile):
    author = authors.get(str(row.get("author_id")), {})
    name = str(author.get("name") or row.get("author_name") or row.get("club_name") or "Campus community")
    # No student_id/email/phone/author_id is sent in the shared feed.
    if "@" in name:
        name = "Campus community"
    meta = [str(author.get("department") or row.get("content_source") or row.get("type") or "Campus post")]
    year = author.get("year_of_study")
    if year:
        meta.append(f"Year {year}")
    deadline, _ = parse_moment(row.get("deadline"))
    key = content_key(row)
    return {"id": key, "initials": "".join(word[0] for word in name.split()[:2]).upper(),
            "name": name, "meta": " · ".join(meta), "color": "sage", "title": str(row.get("title") or "Campus post"),
            "body": str(row.get("body") or ""), "tags": text_list(row.get("tags")),
            "skills_required": text_list(row.get("skills_required")),
            "deadline": deadline.date().isoformat() if deadline else None,
            "interested": key in saved, "matches_you": matches(row, profile)}


def period(hour):
    return "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 21 else "night"
