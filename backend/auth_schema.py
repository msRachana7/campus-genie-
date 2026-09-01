"""Inspect existing Lakebase tables before enabling new account creation."""
from psycopg.rows import dict_row
from psycopg.types.json import Json, Jsonb

PUBLIC_FIELDS = {"user_id", "student_id", "name", "department", "year_of_study", "skills", "interests", "looking_for"}
PRIVATE_FIELDS = {"user_id", "usn", "email", "password_hash", "contact_number"}
TIMESTAMPS = {"created_at", "updated_at"}


def columns(conn, table):
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute("""
            SELECT a.attname AS name, t.typname AS type,
                   a.attnotnull AS required, a.atthasdef AS has_default,
                   a.attidentity <> '' AS identity,
                   CASE WHEN t.typname IN ('varchar','bpchar') AND a.atttypmod > 4
                        THEN a.atttypmod - 4 ELSE NULL END AS max_length
            FROM pg_attribute a JOIN pg_type t ON t.oid = a.atttypid
            WHERE a.attrelid = to_regclass(%s) AND a.attnum > 0 AND NOT a.attisdropped
        """, (table,))
        return {row["name"]: row for row in cur.fetchall()}


def check_schema(conn):
    result = {}
    for table, needed, generated in (
        ("student_public", PUBLIC_FIELDS, TIMESTAMPS),
        ("student_private", PRIVATE_FIELDS, TIMESTAMPS | {"email_verified_at", "auth_version"}),
    ):
        found = columns(conn, table)
        missing = needed - found.keys()
        if missing:
            raise ValueError(f"{table}: missing columns {sorted(missing)}. No migration applied.")
        if found["user_id"]["type"] != "uuid":
            raise ValueError(f"{table}.user_id must be UUID for this package. Send the table definition; no migration applied.")
        extra = [name for name, col in found.items() if name not in needed | generated
                 and col["required"] and not col["has_default"] and not col["identity"]]
        if extra:
            raise ValueError(f"{table}: additional required columns {extra}. Send the table definition; no migration applied.")
        for name in TIMESTAMPS & found.keys():
            if found[name]["type"] not in {"timestamp", "timestamptz"}:
                raise ValueError(f"Unsupported type for {table}.{name}; no migration applied.")
        result[table] = found
    public = result["student_public"]
    private = result["student_private"]
    for field in ("skills", "interests", "looking_for"):
        if public[field]["type"] not in {"_text", "_varchar", "json", "jsonb"}:
            raise ValueError(f"student_public.{field} must be a text array or JSON/JSONB; no migration applied.")
    for field in ("student_id", "name", "department"):
        if public[field]["type"] not in {"text", "varchar", "bpchar", "citext"}:
            raise ValueError(f"Unsupported student_public.{field} type; no migration applied.")
    for field in ("usn", "email", "password_hash", "contact_number"):
        if private[field]["type"] not in {"text", "varchar", "bpchar", "citext"}:
            raise ValueError(f"Unsupported student_private.{field} type; no migration applied.")
    if private["password_hash"].get("max_length") and private["password_hash"]["max_length"] < 76:
        raise ValueError("password_hash is too short for the new hashes. Increase its capacity to TEXT after reviewing the table definition; no migration applied.")
    for name, expected in (("email_verified_at", "timestamptz"), ("auth_version", "int4")):
        if name in private and private[name]["type"] != expected:
            raise ValueError(f"Existing student_private.{name} has an incompatible type; no migration applied.")
    if public["year_of_study"]["type"] not in {"int2", "int4", "int8"}:
        raise ValueError("year_of_study must be an integer; no migration applied.")
    return result


def adapt_list(value, column):
    if column["type"] == "jsonb":
        return Jsonb(value)
    if column["type"] == "json":
        return Json(value)
    return value
