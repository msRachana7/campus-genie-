# Simple Campus Genie login

This replaces email verification with ordinary email/password registration and login.

## Replace exactly THREE files

Back up these files, then copy the matching files from this ZIP:

1. `backend/routes/auth.py`
2. `backend/auth_security.py`
3. `frontend/client/src/components/CampusLogin.tsx`

Do not replace `Home.tsx`, `main.py`, `database.py`, `.env`, your folders, or any other file.

This uses `auth_crypto.py`, `auth_schema.py`, and `campusAuth.ts` already supplied in the previous package. Keep those files, plus the previous profile and Genie routes. No new packages are needed if the previous backend starts successfully.

## Run

Stop both servers with Ctrl+C, then restart them.

Backend terminal:

```bash
cd /home/nightfury/campusgenie
source venv/bin/activate
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Frontend terminal:

```bash
cd /home/nightfury/campusgenie/frontend
npm run dev
```

Open the Local URL printed by Vite. It should now say **Welcome back**, not **Verify your college email**. If it still shows the email-verification screen, check that you replaced the component in the running project.

## Use it

First time: click **New here? Create an account**, enter your details and a password of at least 12 characters, then click **Create account and enter**. It saves your account in Lakebase and signs you in immediately.

Later: enter the same college email and app password, then click **Sign in**.

No Gmail/SMTP settings, email links, OTP, or email-auth migration are required by these new routes. Do not delete any previously created tables; they can remain unused. Old verification links no longer apply. Old login tokens are invalid, so log in again.

Your Lakebase connection settings, existing student tables, and a random `JWT_SECRET_KEY` of at least 32 characters are still required. This is real backend authentication, not a frontend-only bypass. Accounts created with passwords using the earlier code can sign in without email verification. Pending signups that never created an account must register again.

Registration still asks for your profile fields because the existing database/UI uses them. They are entered only once; login asks only for email and password.

## Important boundaries

- This is for your local prototype. A typed college email is NOT proof of mailbox ownership or college membership.
- Existing records are never overwritten on registration. If your USN/email already belongs to a preloaded sample record, stop at the conflict and ask the project administrator to reconcile it. Guessing an email or USN must not unlock another student's data.
- Passwords are hashed. Requests use signed, expiring backend tokens. Changing a stored password invalidates previously issued tokens.
- The small in-memory request limit is suitable for a single localhost process only. It is not a production distributed rate limiter.
- Password reset and email verification are intentionally absent from this simple version. No account can reset a password merely by naming its email.
- The existing profile/Genie routes must use `require_user` / `require_student` from `auth_security.py`, as in the previous package.
- New Lakebase profiles do not automatically sync into your Databricks Genie Silver/Gold data.

Python syntax, frontend TSX syntax, and offline branch checks were validated during preparation. Live Lakebase inserts, full server startup, and a complete frontend build must still be checked in your environment. No live account or database was modified here.
