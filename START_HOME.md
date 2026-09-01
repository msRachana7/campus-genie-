# Campus Genie — connected Home dashboard

This is the complete Home dashboard backend for the supplied screenshots, plus the matching frontend files. It plugs into your existing FastAPI application, Lakebase connection, email-verified login, and Genie chat. It is not a replacement backend for every other page in the website.

The frontend is based on the saved `Home.tsx` from September 1. If you have made newer local edits, compare that file before replacing it.

## What becomes dynamic

| Home feature | Source / behavior |
| --- | --- |
| Hi {name} and avatar | Signed-in student's Lakebase public profile |
| Day, date and morning/afternoon/evening/night | Asia/Kolkata; updates while the page is open |
| Weather | Open-Meteo, fixed to Basavanagudi |
| Worth knowing today | Active records from your shared Databricks content table |
| Matches | Student's own skills/interests compared with the active posts |
| Interested button | Saved privately in Lakebase for the authenticated user |
| Share | Shares a URL identifying that post; readers still sign in |
| Campus Pulse and weekly bars | Actual scheduled event counts, Monday–Sunday |
| Up next | Closest future event start; a deadline is labelled “Next deadline” |
| Resource count | Optional shared-resource table; no invented count if absent |
| Archive teaser | A dated past record, passed to the existing Genie chat |

The Community feed and Pulse destinations also use this data instead of their sample posts and fabricated activity statistics. Community here is a read-only feed with Interested/Share. This package does not add a post-publishing endpoint. Existing Notes/PYQs upload and Time Capsule implementations are retained; their sample content and other unfinished functionality are not converted into a full backend by this Home package. Authentication, profile editing, and Genie continue using your existing implementations.

The broken mascot image has an icon fallback.

## 1. Copy the files

Extract `campus-home-backend.zip`. Copy individual files into the project, not entire replacement directories.

Project: `/home/nightfury/campusgenie`

| Package file | Copy to |
| --- | --- |
| `backend/home_dashboard.py` | `backend/home_dashboard.py` |
| `backend/home_logic.py` | `backend/home_logic.py` |
| `backend/home_schema.sql` | `backend/home_schema.sql` |
| `backend/setup_home.py` | `backend/setup_home.py` |
| `backend/requirements-home.txt` | `backend/requirements-home.txt` |
| `backend/tests/test_home_logic.py` | `backend/tests/test_home_logic.py` |
| `frontend/client/src/hooks/useHomeDashboard.ts` | `frontend/client/src/hooks/useHomeDashboard.ts` |
| `frontend/client/src/components/LiveHomeView.tsx` | `frontend/client/src/components/LiveHomeView.tsx` |
| `frontend/client/src/pages/Home.tsx` | `frontend/client/src/pages/Home.tsx` — back up your current file first |

The `.env.home.example` is a reference for merging settings in step 3.

Required existing files: `backend/database.py` exposing `get_connection`, `backend/auth_security.py` exposing `require_user`, and the existing frontend `campusAuth`, `CampusLogin`, and Genie components/hooks. These were present in your earlier email-auth package. Do not substitute an unverified browser-provided student ID for the authentication dependency.

## 2. Register the router

In your EXISTING `backend/main.py`, add this import:

```python
from home_dashboard import router as home_router
```

Below `app = FastAPI(...)`, add this once:

```python
app.include_router(home_router)
```

Keep your existing auth, profile, Genie, resource routers, and CORS configuration. The new route is `/api/home`; the earlier `/api/home-dashboard` route is not used by these new frontend files.

## 3. Merge the configuration

Add/update these entries in `backend/.env`:

```dotenv
DATABRICKS_WAREHOUSE_ID=your_actual_sql_warehouse_id
CAMPUS_CONTENT_TABLE=campus_genie.silver.campus_content
CAMPUS_RESOURCES_TABLE=
```

Use the SQL warehouse in the workspace that can query your `campus_genie` catalog. This ID is different from your Genie space/serving endpoint and from your Lakebase PostgreSQL host.

Reuse your existing `DATABRICKS_HOST` and `DATABRICKS_TOKEN`, or your SDK OAuth configuration. The credential needs access to that warehouse and read access to the shared content. Keep your Lakebase and JWT settings.

Keep `CAMPUS_RESOURCES_TABLE` empty until your PDFs/resources have a shared metadata table or view. If configured, it must contain only student-visible resources: its row count is displayed to every signed-in user. The dashboard does not read individual students' private files.

In your existing `frontend/.env`, keep:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## 4. Install and start

In the VS Code terminal:

```bash
cd /home/nightfury/campusgenie
source venv/bin/activate
cd backend
python -m pip install -r requirements-home.txt
python setup_home.py
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

`setup_home.py` creates only the new `campus_home_interests` table in your existing Lakebase database. It does not reload students or alter authentication tables. It is safe to run again. This table contains private selections and must stay outside your public Genie ingestion.

In a second terminal:

```bash
cd /home/nightfury/campusgenie/frontend
npm run dev
```

Open the frontend URL and sign in. No new frontend dependencies are needed beyond the packages already imported by your original Home page.

## Event dates and honest trends

The content reader checks which columns exist; it does not assume that optional columns have already been added.

Required: `title`, and either `content_id` or `post_id`.

Recommended: `content_source` or `type`, `body`, `deadline`, `author_id`, `tags`, and `skills_required`. Authors are resolved against Lakebase public profiles; unresolved authors display “Campus community,” without exposing their identifiers.

Event records must have `content_source` or `type` equal to `event`, `events`, `club_event`, `technical_event`, or `technical event`. A recruitment post mentioning a hackathon is not counted as an event.

An actual start can be supplied in `starts_at`, `start_at`, `event_datetime`, `event_date`, or `start_date`, either as a column or inside a JSON `meta` object. Optional `event_time`/`start_time` fields accept `HH:MM` or `HH:MM:SS`. Optional `location`/`venue` values are displayed when available.

For example, this is the SHAPE of an event's `meta` field, not a real event to insert:

```json
{"event_date":"2026-09-06","event_time":"16:30","location":"Your actual venue"}
```

Timezone-aware timestamps retain their timezone; naive timestamps and date-plus-time metadata are interpreted as Asia/Kolkata. Databricks TIMESTAMP columns are read as epoch seconds to preserve the instant; TIMESTAMP_NTZ remains a local time.

If your table currently contains only `deadline`, the card displays the closest deadline. It cannot infer an event start, venue, or time from a registration deadline. Weekly event counts remain unavailable until actual event dates are present.

“AI events are up this week” is used only when the listed AI event count is higher than the previous week's nonzero count. This compares scheduled events in the retained table, not student browsing or bookmarking behavior. If the table drops historical records, last week's count is not a complete historical baseline.

The API reads up to 5,000 records and explicitly qualifies counts if that limit is reached. The feed returns up to 100 active posts, with skill/interest matches first. Shared links can only open posts still in that active feed.

## Refresh behavior

The frontend fetches every five minutes while visible and on focus/reconnection. The backend caches shared content for two minutes and weather for ten minutes. The week changes automatically using India time. A Refresh button retries the API; it does not bypass the short backend cache.

Your existing Bronze → Silver ingestion/cleaning jobs must still refresh the Databricks tables. This package does not schedule or rerun those jobs or scrape the BMSCE site. Genie chat still uses your existing Supervisor integration; dashboard cards query shared structured data directly.

## Check it locally

1. Confirm `GET /api/home`, `PUT /api/home/interests/{key}`, and `DELETE /api/home/interests/{key}` appear in `http://127.0.0.1:8000/docs`.
2. Sign in, confirm your name, and check the date against India time.
3. Click Interested, refresh, and confirm the selection persists. A different account should have its own selections.
4. Check an event with a known actual start. Confirm a deadline-only record says “Next deadline.”
5. Check the browser Network panel for `/api/home` if a section is unavailable. The response includes `content_status` and `interest_status` without exposing credentials.

If campus data is unavailable, confirm the warehouse is running and the host, credentials, warehouse ID, and table all belong to the intended setup. An empty result is shown as “No active campus posts”; a connection failure is shown as unavailable.

If Interested is unavailable, run `python setup_home.py` against the same Lakebase database used by FastAPI. An expired login requires signing in again.

To run the supplied offline checks:

```bash
cd /home/nightfury/campusgenie/backend
python -m unittest discover -s tests -p 'test_home_logic.py' -v
```

Validation performed here: Python compilation and 18 offline unit tests passed. Tests cover India-time boundaries, same-day events, deadline fallback, Monday–Sunday grouping, matching, stable post IDs, and private identity exclusion. Live FastAPI/database/weather/Databricks calls and a full TypeScript build were not run here; the dependency installation environment could not complete. Run your project's frontend build locally as well.

API references: [Databricks Statement Execution](https://docs.databricks.com/api/statement-execution/v1), [Open-Meteo Forecast API](https://open-meteo.com/en/docs).
