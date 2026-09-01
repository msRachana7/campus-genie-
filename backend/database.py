import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


def get_connection():
    password = os.getenv("LAKEBASE_PASSWORD")

    if not password:
        raise RuntimeError(
            "LAKEBASE_PASSWORD is missing in backend/.env"
        )

    return psycopg.connect(
        host=os.environ["LAKEBASE_HOST"],
        port=int(os.getenv("LAKEBASE_PORT", "5432")),
        dbname=os.environ["LAKEBASE_DATABASE"],
        user=os.environ["LAKEBASE_USER"],
        password=password,
        sslmode="require",
        connect_timeout=10,
    )