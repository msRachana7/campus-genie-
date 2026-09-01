# BMSCE Email/Password Auth

Backend auth module: signup restricted to `@bmsce.ac.in` addresses, email
verification required before login, and a forgot-password flow.

## How it works

**Signup**
1. `POST /api/auth/signup` with `{ email, password }`.
2. Rejected if the email doesn't end in `@bmsce.ac.in`.
3. Password is hashed with bcrypt; user is saved with `isVerified: false`.
4. A random token is generated — only its SHA-256 hash is stored in the DB,
   the raw token is emailed as a link. This way a DB leak can't be used to
   forge verification links.
5. Verification email is sent with a link valid for 24 hours.

**Verify email**
1. User clicks the link → `GET /api/auth/verify-email?token=...&email=...`.
2. Server hashes the incoming token and compares it to the stored hash, and
   checks it hasn't expired.
3. On success, `isVerified` is set to `true` and the token fields are cleared.

**Login**
1. `POST /api/auth/login` with `{ email, password }`.
2. Blocked with a 403 if `isVerified` is `false`.
3. Otherwise password is checked with bcrypt and a JWT is returned.

**Forgot password**
1. `POST /api/auth/forgot-password` with `{ email }`.
2. Always returns the same generic message, whether or not the account
   exists — this prevents attackers from using it to check which emails
   are registered.
3. If the account exists and is verified, a reset token (hashed in DB,
   raw token emailed) is generated with a 15-minute expiry.

**Reset password**
1. `POST /api/auth/reset-password` with `{ token, email, newPassword }`.
2. Token is validated the same way as verification tokens.
3. Password is updated and the reset token is cleared.

## Setup

```bash
npm install
cp .env.example .env   # fill in MONGO_URI, JWT_SECRET, EMAIL_USER, EMAIL_PASS
npm run dev
```

For `EMAIL_USER`/`EMAIL_PASS` with Gmail, you need a Google Account
**App Password** (Gmail no longer allows plain password SMTP login) —
enable 2-Step Verification, then generate one under
Google Account → Security → App Passwords.

## Notes / things to adapt

- Swap Gmail SMTP for a transactional provider (SendGrid, SES, Postmark)
  if you expect real volume — Gmail SMTP has low sending limits.
- Add rate limiting on `/signup`, `/login`, and `/forgot-password` to
  prevent brute-force and spam abuse (e.g. `express-rate-limit`).
- The frontend needs two pages: `/verify-email` and `/reset-password`,
  which read `token` and `email` from the query string / form, and call
  the corresponding API endpoints.
