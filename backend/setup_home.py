"""Run: python setup_home.py. Uses your existing Lakebase connection."""
from pathlib import Path
from database import get_connection

if __name__ == "__main__":
    with get_connection() as conn, conn.cursor() as cur:
        cur.execute(Path(__file__).with_name("home_schema.sql").read_text())
    print("Home interest storage is ready.")
