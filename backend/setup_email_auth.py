"""Run without arguments first. --apply performs one additive transaction."""
import argparse
from database import get_connection
from auth_schema import check_schema


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with get_connection() as conn:
        schema = check_schema(conn)
        for table, fields in schema.items():
            print(table + ": " + ", ".join(f"{k} ({v['type']})" for k, v in fields.items()))
        with conn.cursor() as cur:
            # Never print student records, only conflict counts.
            checks = {
                "duplicate private emails": "SELECT count(*) FROM (SELECT lower(trim(email)) FROM student_private GROUP BY 1 HAVING count(*) > 1) q",
                "duplicate private USNs": "SELECT count(*) FROM (SELECT upper(trim(usn)) FROM student_private GROUP BY 1 HAVING count(*) > 1) q",
                "duplicate public student IDs": "SELECT count(*) FROM (SELECT lower(trim(student_id)) FROM student_public GROUP BY 1 HAVING count(*) > 1) q",
                "private records without profiles": "SELECT count(*) FROM student_private pr LEFT JOIN student_public p ON p.user_id = pr.user_id WHERE p.user_id IS NULL",
            }
            for label, query in checks.items():
                cur.execute(query)
                if cur.fetchone()[0]:
                    raise ValueError(label + ": reconcile these before migration. No records were modified.")
            if not args.apply:
                print("Preflight passed. This did not change the database. Next: python setup_email_auth.py --apply")
                return
            cur.execute("ALTER TABLE student_private ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ")
            cur.execute("ALTER TABLE student_private ADD COLUMN IF NOT EXISTS auth_version INTEGER NOT NULL DEFAULT 0")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS cg_auth_private_user ON student_private (user_id)")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS cg_auth_public_user ON student_public (user_id)")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS cg_auth_private_email ON student_private (lower(trim(email)))")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS cg_auth_private_usn ON student_private (upper(trim(usn)))")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS cg_auth_public_student ON student_public (lower(trim(student_id)))")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS campus_auth_pending (
                    token_hash TEXT PRIMARY KEY,
                    kind TEXT NOT NULL CHECK (kind IN ('signup', 'verify', 'reset')),
                    email TEXT NOT NULL,
                    payload JSONB NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    UNIQUE(kind, email)
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS campus_auth_limits (
                    key TEXT NOT NULL,
                    bucket BIGINT NOT NULL,
                    count INTEGER NOT NULL,
                    expires_at TIMESTAMPTZ NOT NULL,
                    PRIMARY KEY (key, bucket)
                )
            """)
    print("Migration applied. Existing student data and passwords were preserved.")
    print("Existing accounts must verify their email before logging in with the new routes.")


if __name__ == "__main__":
    main()
