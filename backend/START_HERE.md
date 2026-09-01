# Connect Campus Genie to your website

This package connects the existing FastAPI backend and React chat to:

- Workspace: `https://dbc-c577b6cd-19b2.cloud.databricks.com`
- Supervisor serving endpoint: `mas-29c70270-endpoint`

It uses the Responses API example you supplied. Do not substitute the Genie
space ID, AI Search endpoint, or broken Knowledge Assistant endpoint.

The supplied React attachment starts in the middle of another component and
does not contain the parent state or login handler. Therefore this package is
an integration overlay, not a replacement for your complete project.

## 1. Copy the new files into your existing project

Use the folder paths in this package as destinations in your existing
`campusgenie` project. Add:

| File | Destination |
| --- | --- |
| `backend/routes/genie.py` | `backend/routes/genie.py` |
| `backend/requirements-genie.txt` | `backend/requirements-genie.txt` |
| `frontend/client/src/lib/genieApi.ts` | Same path in your project |
| `frontend/client/src/hooks/useGenieChat.ts` | Same path in your project |
| `frontend/client/src/components/GenieView.tsx` | Same path in your project |
| `frontend/client/src/components/genie-chat.css` | Same path in your project |

Do not replace your entire backend or frontend folder. Keep your existing
files, database settings, login routes and styles.

## 2. Connect the backend router

In your existing `backend/main.py`, add this import beside the other routes:

```python
from routes.genie import router as genie_router
```

Below the other `app.include_router(...)` calls, add:

```python
app.include_router(genie_router)
```

The package also includes a complete `backend/main.py` based on your supplied
version, with just these integration additions. Prefer the two-line edit if
you have since changed your own file.

Do not paste the standalone OpenAI test call at the top of `main.py`: requests
should run when a student sends a message, not when the server starts.

## 3. Install backend dependencies

In VS Code's terminal, from the existing project's backend folder, activate the
same Python virtual environment you use to run the backend, then run:

```bash
python -m pip install -r requirements-genie.txt
```

Keep your original `requirements.txt`. The supplemental file includes OpenAI
and also the bcrypt, python-jose and email-validator packages already imported
by your supplied auth code but missing from its pasted requirements.

If this is a fresh local checkout, first create a virtual environment and
install your original requirements as well. Do not install into system Python.

## 4. Set the backend credentials

Open `backend/.env`. Keep its existing database settings and JWT_SECRET_KEY.
Add the following locally:

```dotenv
DATABRICKS_HOST=https://dbc-c577b6cd-19b2.cloud.databricks.com
DATABRICKS_SUPERVISOR_ENDPOINT=mas-29c70270-endpoint
DATABRICKS_TOKEN=your_actual_databricks_token_here
```

Use the credential for an identity allowed to query the Supervisor and its
underlying Genie/AI Search tools. This is the Databricks token, not the JWT
returned by your site's login route. Do not send it in chat.

Make sure the repository's `.gitignore` excludes `.env`, `.env.local` and
`.venv/`. Never commit credentials. The included `.env.genie.example` files
contain placeholders only; do not overwrite your actual environment file.

## 5. Install the Markdown renderer and set the frontend URL

Open a second terminal in `frontend` (the directory containing `package.json`):

```bash
npm install react-markdown remark-gfm
```

The component uses the existing project's `lucide-react` icons. If that
dependency is not in your package.json, also install `lucide-react`.

In `frontend/.env.local`, add:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

This URL is public configuration. NEVER put a Databricks token or JWT signing
secret in a VITE_ variable. Restart the frontend after changing environment
variables. If your project uses pnpm consistently, use `pnpm add` instead of
switching package managers.

## 6. Save the app's JWT after successful login

Use VS Code's Ctrl+Shift+F to find the frontend call to `/api/auth/login`.
In that source file, import:

```tsx
import { saveGenieAccessToken } from "@/lib/genieApi";
```

Immediately after a SUCCESSFUL login response has been parsed, add:

```tsx
saveGenieAccessToken(data.access_token);
```

Here `data` means your parsed login response. If your handler calls it `result`
or `loginData`, use that actual variable name. For example:

```tsx
const data = await response.json();
if (!response.ok) {
  // Keep your existing failed-login handling here.
  return;
}
saveGenieAccessToken(data.access_token);
// Keep the rest of your existing successful-login handling.
```

This stores only your site's short-lived JWT in sessionStorage. Do not remove
your existing profile/user/session logic. In your logout handler, also call:

```tsx
saveGenieAccessToken(null);
```

This clears this integration's token and current chat, and aborts any pending
response. It does not replace your existing logout code. Log out and log back
in after installing the integration so the new token storage is populated.

The `@/` import examples assume the usual Vite alias points to `client/src`.
If your project does not define it, use a relative import from that file to
`lib/genieApi.ts` instead; the new files use relative imports internally.

## 7. Replace the mock chat state in the parent component

In the file that currently contains or renders `GenieView`, add:

```tsx
import GenieView from "@/components/GenieView";
import { useGenieChat } from "@/hooks/useGenieChat";
```

Delete ONLY the old local `function GenieView(...) { ... }` definition supplied
in your attachment. Keep HomeView, ProfileView, and all the other components.

Find the PARENT component where the current `chat`, `query`, `setQuery`, and
`ask` are declared. Replace those old mock-chat declarations and mock `ask`
function with the following. Keep the existing `setActiveTab` state unchanged:

```tsx
const {
  chat,
  query,
  setQuery,
  sendQuestion,
  isLoading,
  error,
  resetChat,
} = useGenieChat();

const ask = (text: string) => {
  setActiveTab("genie");
  void sendQuestion(text);
};
```

Call the hook at the top level of that component, alongside its other hooks,
not inside an if statement or event handler. Use it once in the parent so the
Home page's existing `ask` buttons and the chat page share the same conversation.

Keep your existing conditional rendering for the genie tab, but replace its
`<GenieView ... />` invocation with:

```tsx
<GenieView
  chat={chat}
  query={query}
  setQuery={setQuery}
  ask={ask}
  isLoading={isLoading}
  error={error}
  resetChat={resetChat}
/>
```

If you see "Identifier has already been declared", an old mock state, old
`ask` function or local GenieView definition still remains. Do not replace
your entire App file with the uploaded fragment: it is incomplete and some
of its template-literal characters were damaged during copying.

## 8. Run locally and test

Backend terminal, inside `backend`, with its virtual environment active:

```bash
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal, inside `frontend`:

```bash
npm run dev
```

Open the localhost URL printed by the frontend. Your supplied CORS settings
allow localhost/127.0.0.1 on ports 3000 and 5173. If Vite chooses another port,
add that exact origin to the existing backend CORS list and restart it.

Sign out and sign back in, then try:

1. `Show me events related to Vak.`
2. `What facilities does BMSCE provide? Cite official website pages.`
3. A follow-up such as `Which of those have upcoming deadlines?` after asking
   about upcoming opportunities.

Use browser Developer Tools > Network to confirm `POST /api/genie/chat`
returns 200. Do not share Authorization header values in screenshots.

The backend API documentation is at `http://localhost:8000/docs`. For a direct
test, log in using `/api/auth/login`, then use Authorize with the returned app
access_token. POST this to `/api/genie/chat`:

```json
{"messages":[{"role":"user","content":"Show me events related to Vak."}]}
```

The response is `{"answer":"...","citations":[...]}`. Sources appear when
the Supervisor returns URL annotations; Markdown links in its final answer
also render. The integration does not invent missing citations.

## 9. Publishing is a separate step

The Manus-hosted preview in your screenshot is not the same origin as local
Vite. Start by testing locally as above. For a publicly hosted frontend:

- Host the Python backend at a reachable HTTPS URL.
- Set VITE_API_BASE_URL to that backend URL and rebuild the frontend.
- Add the exact frontend HTTPS origin to backend CORS. Do not use `*` with
  credentialed requests.
- Set Databricks credentials and JWT settings as backend hosting secrets.
- Ensure the reverse proxy permits the request duration (up to 180 seconds
  here), or implement streaming/async jobs for long tasks.

`localhost:8000` on a visitor's machine does not point to your laptop. The
Databricks browser UI need not stay open, but the backend must stay running.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Chat asks you to sign in | Add the successful-login helper call; sign out/in again |
| Backend returns 401 | Missing, invalid or expired app JWT; check the existing JWT_SECRET_KEY |
| Backend returns 503 | DATABRICKS_TOKEN or JWT_SECRET_KEY is missing |
| Backend returns 502 mentioning credential | Databricks token/permissions, not the student's login |
| Backend returns 502 mentioning endpoint | Serving endpoint must be `mas-29c70270-endpoint` |
| Backend returns 429 | Databricks usage/capacity limit |
| Backend returns 504 | Supervisor exceeded the request timeout |
| Browser says Failed to fetch | Backend URL, port, HTTPS or exact CORS origin |
| Imports conflict | Remove only the previous mock GenieView/chat state/ask declarations |

## Scope and security

- Your existing auth.py is unchanged. The new route verifies its JWT signature,
  expiry and subject. It does not query the database on every chat request.
- JWT identity is NOT passed through as a Databricks user. Every student uses
  the same server-side Databricks identity's permissions. App login alone is
  not per-student data authorization.
- Before sharing this app beyond your own local test, use a least-privilege
  Databricks identity with access ONLY to shared campus data and public pages,
  or implement per-user Databricks OAuth/authorization. Do not expose private
  student tables, financial details or other users' restricted records. Merely
  listing public tables in Genie instructions is not an access-control boundary.
- Conversations live only in React memory; New chat, logout or refreshing
  clears them. The client sends up to six successful prior exchanges, within
  a 48,000-character budget. This is not durable chat history or resumable
  long-running Supervisor task storage.
- The server accepts only user/assistant transcript messages, with length
  limits. It does not trust client-supplied endpoint names, system prompts or
  Databricks credentials. Client history is context, never authorization.
- Only the final assistant message is shown; structured reasoning/tool items
  and intermediate commentary are discarded. Markdown renders without raw
  HTML or external images; links are limited to HTTP(S).
- Add server-side rate limiting and deploy-time access controls before a
  public rollout. The in-browser duplicate-submit guard is not a rate limiter.
- This does not implement file uploads, PDF ingestion, live scraping, new
  Genie configuration, or changes to your other pages.

## Tests and verification

The package includes `backend/tests/test_genie.py`. After installing backend
dependencies, run from your backend directory:

```bash
python -m unittest discover -s tests -p 'test_genie.py' -v
```

These tests mock Databricks and make no external requests. They check JWTs,
payload limits, endpoint forwarding, final-answer extraction and error mapping.
They do not prove that your live endpoint/token/permissions work.

During preparation, Python parsing and isolated Pydantic/response-extraction
checks were run. Full FastAPI/React tests and a live Databricks call could not
be run in the preparation environment. Follow step 8 to verify the actual app.

# Campus Genie: email-verified registration

This package adapts your Gmail-auth example to your existing **FastAPI + Lakebase** application. It does not add MongoDB or a separate Node authentication server.

New users can register with a verified `@bmsce.ac.in` address without being preloaded in Lakebase. This is **email/password login with email verification**, not Google OAuth / a “Continue with Google” button.

## What changes

- Registration saves a pending signup and emails a single-use verification link.
- Confirming the link creates `student_public` and `student_private` together in one transaction. `student_id` is the verified college email; the shared `user_id` is a generated UUID.
- Exact matching preloaded email + USN records with `NOT_REGISTERED` can be activated without replacing the public profile.
- Existing registered accounts keep their passwords but must verify their email before using the new login. Use **Resend verification email** on the login page.
- Password-reset links expire in 15 minutes. A successful reset revokes old sessions through `auth_version`.
- Your existing Supervisor endpoint is retained. The replacement Genie route checks that the student is verified and their session has not been revoked.
- Both profile reads and updates use `/api/profile/me`, identified by the signed login token. Legacy profile URLs are restricted to the same signed-in user.
- Home uses your existing visual styles, the connected Genie chat component, a functional login/registration/reset screen, and a sign-out button. Resource uploads no longer use the hardcoded sample student's email. The server-side resources route was not supplied and still needs its own ownership checks.

No real database, email account, or Databricks endpoint was accessed while creating this package.

## 1. Back up and copy the files

Stop your backend and frontend terminals with Ctrl+C before replacing files.

Extract `campus-email-auth.zip`. Copy the **individual files** into the matching folders in `/home/nightfury/campusgenie`. Do not replace the whole backend or frontend folder.

Back up these existing files first, outside the running project if possible:

- `backend/routes/auth.py`
- `backend/routes/profiles.py`
- `backend/routes/genie.py`
- `frontend/client/src/pages/Home.tsx`
- Any existing Genie component/helper files listed below that you have edited since the earlier package.

| Package file | Destination / action |
| --- | --- |
| `backend/routes/auth.py` | Replace the existing file |
| `backend/routes/profiles.py` | Replace the existing file |
| `backend/routes/genie.py` | Replace the earlier integration route; retains `mas-29c70270-endpoint` as default |
| `backend/auth_crypto.py` | Add |
| `backend/auth_mail.py` | Add |
| `backend/auth_schema.py` | Add |
| `backend/auth_security.py` | Add |
| `backend/setup_email_auth.py` | Add |
| `backend/requirements-email-auth.txt` | Add alongside existing requirements |
| `backend/requirements-genie.txt` | Add if missing; compare first if you changed it |
| `backend/tests/test_email_auth_offline.py` | Add; does not use real accounts |
| `frontend/client/src/pages/Home.tsx` | Replace your uploaded Home.tsx version; compare if you made newer changes |
| `frontend/client/src/components/CampusLogin.tsx` | Add |
| `frontend/client/src/lib/campusAuth.ts` | Add |
| `frontend/client/src/components/GenieView.tsx` | Copy the connected chat component |
| `frontend/client/src/components/genie-chat.css` | Copy its styles |
| `frontend/client/src/lib/genieApi.ts` | Copy the compatible chat API helper |
| `frontend/client/src/hooks/useGenieChat.ts` | Copy the compatible chat hook |

**Keep your existing `database.py`, data-loader scripts, posts/resources routes, and all existing `.env` values. Do not rerun `load_private.py` or reload sample students.**

Your existing `main.py` should already include the auth and profile routers. Check that it also includes the Genie router, exactly once:

```python
from routes.genie import router as genie_router

# Below app = FastAPI(...):
app.include_router(genie_router)
```

No change to the database connection function you supplied is necessary.

## 2. Install Python dependencies

In the VS Code terminal:

```bash
cd /home/nightfury/campusgenie
source venv/bin/activate
cd backend
python -m pip install -r requirements.txt -r requirements-genie.txt -r requirements-email-auth.txt
```

Use your existing working virtual environment. If `venv/bin/activate` is missing or a command fails, stop and send the final error lines; don't install into system Python with `--break-system-packages`.

The added requirements include `databricks-sdk`, which your supplied `database.py` imports. Packages used by other routes must also be in your existing requirements. If backend startup reports an unrelated missing module, that route needs its own dependency installed too.

## 3. Configure the email sender and JWT

Open your existing `backend/.env`. **Merge** the entries below. Do not replace the file or remove your Databricks/Lakebase variables.

```dotenv
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
CLIENT_URL=http://localhost:3000
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
EMAIL_USER=your_sender_account@gmail.com
EMAIL_PASS=your_google_app_password
```

`CLIENT_URL` must match the frontend address shown by Vite. If it runs on port 5173, use `http://localhost:5173`. It is the website URL, not the Databricks URL.

`EMAIL_USER` is the mailbox **sending** verification messages. Students still sign up using their own `@bmsce.ac.in` addresses. You may use a separate Gmail sender; it doesn't have to be a student's college mailbox.

For Gmail SMTP:

1. Sign in to the sender's Google account.
2. Enable 2-Step Verification.
3. If the account permits it, create an app password at [Google App Passwords](https://myaccount.google.com/apppasswords).
4. Paste that app password into `EMAIL_PASS` locally. Never use your normal Google password and never share the app password here or commit it to Git.

If Google does not offer app passwords for that account, stop: use an administrator-approved SMTP sender/provider instead. Do not disable account security. See [Google's app-password help](https://support.google.com/accounts/answer/185833).

Keep your existing `JWT_SECRET_KEY` if it is random and at least 32 characters. If you need one, generate it locally:

```bash
python -c 'import secrets; print(secrets.token_urlsafe(48))'
```

Paste that output into the existing `JWT_SECRET_KEY=` entry in `backend/.env`. Changing it invalidates old sessions. Do not post the output in chat. Do not put any of these secrets in a `VITE_` variable.

Keep `.env` excluded from Git. Do not use `git add .` without reviewing what would be committed.

## 4. Check the database BEFORE applying changes

The supplied `load_private.py` inserts data but does not define the tables, so the exact DDL could not be verified here. This package supports UUID `user_id` columns, textual email/USN/student IDs, an integer study year, and text-array or JSON/JSONB skill fields.

From the activated backend terminal, run:

```bash
python setup_email_auth.py
```

This is read-only. It reports column names/types and checks for common identity conflicts without printing student records.

**If it reports incompatible columns, missing tables, duplicate identities, or an error, stop and share the error. Do not drop tables, delete students, change IDs, or bypass the check.** Additional application-specific constraints may still need review; this check cannot prove compatibility with every trigger or CHECK constraint.

If it prints `Preflight passed`, run:

```bash
python setup_email_auth.py --apply
```

This performs one transaction that adds:

- `student_private.email_verified_at`
- `student_private.auth_version`
- Unique identity indexes
- `campus_auth_pending` for expiring signup/verification/reset requests
- `campus_auth_limits` for shared rate-limit counters

It preserves existing rows and passwords. If the migration fails, its transaction is rolled back. Re-running a successful migration is intended to be safe. Existing users remain unverified until they click a new verification link.

**Important privacy rule:** `student_private` and both `campus_auth_*` tables are private authentication data. Do not grant Genie access to them, add them to a Genie space, or include them in public Bronze/Silver ingestion jobs.

## 5. Frontend configuration and packages

Merge this into `frontend/.env`:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

If your earlier Genie component packages are not installed:

```bash
cd /home/nightfury/campusgenie/frontend
npm install react-markdown remark-gfm --legacy-peer-deps
```

`--legacy-peer-deps` is a temporary workaround for the existing Vite 7 / Builder plugin peer conflict you encountered; it does not fix that conflict. Keep your existing package manager/lockfile workflow consistent. Do not use `--force` or downgrade Vite blindly.

## 6. Start both servers

Terminal 1:

```bash
cd /home/nightfury/campusgenie
source venv/bin/activate
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Wait for `Application startup complete`, not just the initial reloader message. Check [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

Terminal 2:

```bash
cd /home/nightfury/campusgenie/frontend
npm run dev
```

Keep both terminals running. Your supplied CORS list already permits localhost ports 3000 and 5173. If Vite picks another port, configure both `CLIENT_URL` and the backend's exact allowed frontend origin accordingly.

## 7. Test the complete flow

1. Open the frontend and select **New user? Create an account**.
2. Enter your real college email, your own USN, name, department and year. Choose a separate Campus Genie password of at least 12 characters.
3. Click **Send verification email**. Check inbox and spam.
4. Open the newest link while both servers are running, preferably on the same computer. `localhost` on a phone refers to the phone, not your laptop.
5. Click **Confirm email verification**. Merely previewing the email link does not activate the account.
6. Sign in with your college email and Campus Genie password.
7. Open your profile. Edit a field and save. Sign out and sign back in to check persistence.
8. Ask Genie a question to check the shared login token reaches the Supervisor bridge.
9. Test **Forgot password?**, open the newest reset link, and set a new password. Old tokens should fail on profile/Genie requests after the reset.

Verification links expire in 24 hours and can be used once. Resending invalidates the previous link. Reset links expire in 15 minutes. A pending signup that has already expired must be registered again.

The email request budget is four attempts per address per hour across registration/resend/reset, with additional IP and global limits. Don't repeatedly click Send during testing; a 429 response means wait for the window to expire.

### Existing sample records and fabricated emails

Your loader used `USN@bmsce.ac.in` for sample private records. That may not be the student's real mailbox.

If a student's real email differs from the existing email for that USN, registration deliberately returns a conflict. **Verifying an arbitrary college email does not prove ownership of someone else's USN.** Do not automatically reassign that old profile. The project administrator must verify the mapping against trusted student records and reconcile it explicitly.

New, non-conflicting students do not need a preload at all. For matching existing accounts, use registration only for `NOT_REGISTERED`; use resend verification / forgot password for established accounts.

## Validation and limits

Python compilation, TypeScript/TSX parsing/transformation and 19 offline unit tests were run while preparing this package. The tests exercise password hashing, link-token handling, identity-conflict protection, new-account verification branches and reset-version logic. They do not run a real FastAPI server, PostgreSQL transaction, SMTP delivery, full frontend build or live Databricks request.

Run the included checks locally:

```bash
cd /home/nightfury/campusgenie/backend
python -m unittest discover -s tests -p 'test_email_auth_offline.py' -v
```

Before public deployment, use HTTPS, secure secret storage, an approved email sender, verified proxy/rate-limit configuration, and a complete authorization review of posts/resources and any other routes. The client now sends the signed-in student's ID for uploads, but a client-supplied ID is not server authorization. Restrict the Databricks credential to shared/public data; a website JWT does not establish per-student Databricks row-level access.

Study-year choices currently remain 1–4, matching the supplied UI. A verified school mailbox proves control of that mailbox, not a verified USN or student status. The public profile's details are self-reported until checked against trusted records.

Home.tsx still contains the original sample dashboard/event content. This authentication change does not make those static dashboard sections live or synchronize new Lakebase profiles to your Genie Silver/Gold tables automatically.

For rollback: restore the backed-up route/Home files, keep any newly registered student data, and review the additive migration with the administrator. Do not drop authentication tables or reset all passwords to undo a UI problem.