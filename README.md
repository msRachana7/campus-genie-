# Campus Genie

Campus Genie is an AI-powered campus intelligence platform built to help students discover opportunities, events, clubs, research, peers, skills, and important campus information from one place.

Instead of searching through scattered websites, notices, groups, and posts, students can interact with Campus Genie using natural language.

## Features

- AI-powered campus assistant
- Discover technical and non-technical events
- Find club recruitment opportunities
- Explore research and collaboration posts
- Student skill and teammate matching
- Skill-gap and missing-skill analysis
- Personalized opportunity recommendations
- Upcoming event tracking
- Campus information discovery
- Natural-language querying using Databricks Genie

## How Databricks is Used

Campus Genie uses Databricks as the core data and intelligence layer.

The project follows a Medallion Architecture:

### Bronze Layer
Stores raw campus data collected from sources such as:

- College websites
- Club posts
- Events
- Opportunities
- Research posts
- Student-provided data

### Silver Layer
Cleans, standardizes, and structures the raw data so it can be reliably queried and analyzed.

### Gold Layer
Creates analytics and intelligent datasets such as:

- Skill demand across campus
- Opportunity summaries
- Student-to-opportunity matching
- Matching skills
- Missing skills
- Personalized recommendations

## Databricks Genie Integration

Databricks Genie allows students to query structured campus data using natural language.

Example questions:

- "What technical events are happening this week?"
- "Which clubs are currently recruiting?"
- "What opportunities match my Python skills?"
- "What skills am I missing for this opportunity?"
- "What research opportunities are available?"
- "Which skills are currently in demand on campus?"

The Genie Agent is integrated with Campus Genie so users can receive data-driven answers without writing SQL.

## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- Tailwind CSS

### Backend
- Python
- FastAPI

### Data & AI
- Databricks
- Databricks Genie
- Delta Tables
- SQL
- Medallion Architecture
- AI Agents

## Project Architecture

```text

## Vercel deployment

The application is intentionally deployed as two Vercel projects:

1. **Frontend** — create a Vercel project with `frontend/` as its root directory.
   Vercel uses [`frontend/vercel.json`](frontend/vercel.json) to build the Vite
   app and preserve client-side routes. Set `VITE_API_BASE_URL` to the deployed
   API URL.
2. **API** — create a second Vercel project from the repository root. The
   [`api/index.py`](api/index.py) entrypoint exposes the FastAPI app and
   [`vercel.json`](vercel.json) routes `/api/*` requests to it.

Set these variables on the API project:

- `JWT_SECRET_KEY` — a random secret of at least 32 characters
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`
- `DATABRICKS_SUPERVISOR_ENDPOINT`
- `CORS_ORIGINS` — the full frontend URL, comma-separated with any local URLs
- The database and email variables required by the selected backend routes

Set `VITE_API_BASE_URL` on the frontend project to the API project's public URL.
Only public configuration may use the `VITE_` prefix; Databricks tokens must
never be added to frontend variables. A starter file is available at
[`frontend/.env.example`](frontend/.env.example).

Databricks remains the data and intelligence layer: Bronze/Silver/Gold cleaning
and modeling happen in Databricks, while the FastAPI `/api/genie/chat` route
acts as the authenticated server-side bridge to Genie. This keeps the
Databricks credential out of the browser and works with Vercel's serverless
Python runtime.

### Local validation

```bash
cd frontend
npm install
npm run check
npm run build

cd ../
python3 -m unittest backend.tests.test_home_logic -v
```text
Campus Data Sources
        |
        v
+-------------------+
|   Bronze Layer    |
|     Raw Data      |
+-------------------+
        |
        v
+-------------------+
|   Silver Layer    |
| Cleaned Data      |
+-------------------+
        |
        v
+-------------------+
|    Gold Layer     |
| Analytics &       |
| Recommendations   |
+-------------------+
        |
        v
+-------------------+
| Databricks Genie  |
| Natural Language  |
| Queries           |
+-------------------+
        |
        v
+-------------------+
|   Campus Genie    |
| React + FastAPI   |
+-------------------+
