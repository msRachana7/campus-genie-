-- Run once against the same Lakebase PostgreSQL database as student_public.
-- New table only: existing auth/profile/content tables are not altered.
CREATE TABLE IF NOT EXISTS campus_home_interests (
    user_id UUID NOT NULL,
    content_key TEXT NOT NULL CHECK (length(content_key) BETWEEN 1 AND 1024),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, content_key)
);

-- Private per-user selections. Do not include this table in Genie data ingestion.
