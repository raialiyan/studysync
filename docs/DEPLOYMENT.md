# Deployment, permanent domain and security checklist

## Make the Vercel link permanent

1. Open Vercel → **studysync** → **Domains**.
2. Find the domain assigned to the **Production** environment. Do not copy a versioned deployment URL from **Deployments → Visit**.
3. Open that domain in a private browser window. Confirm `/login` loads and it does not require Vercel authentication.
4. In Render → **studysync-api** → **Environment**, set `ALLOWED_ORIGINS` to the exact production domain with `https://` and **without a trailing slash**. If the backend accepts a comma-separated set of origins, use only documented/configured allowed values; don't open CORS to every site.
5. Save and deploy the Render change, then test registration/login at the permanent domain.
6. Update the link in the root README to this domain. If the final permanent domain differs from the deploy URL, use the permanent domain on your CV and GitHub profile.

## Rotate exposed Supabase password

An earlier screenshot showed the database connection string. Treat that credential as compromised, even if the app currently works.

1. In Supabase, generate and set a **new strong database password**.
2. Copy the project's **Session pooler** connection string from Supabase Connect. Enter the new password privately, percent-encoding reserved characters (for example `!` → `%21`); remove any literal placeholder brackets.
3. In Render → Environment, update **only `DATABASE_URL`**. Preserve the pooler's complete `postgres.<project-ref>` username, the supplied host and port, `postgresql+psycopg://` scheme and `?sslmode=require`.
4. Deploy and verify that Render reports **Live** and the login page works. Never paste secrets, URLs containing passwords or screenshots of revealed values into a chat or GitHub issue.
5. Consider rotating any other secrets that were disclosed. Rotating `JWT_SECRET_KEY` invalidates existing login sessions, so do it deliberately.

## Production config reference

Frontend Vercel build settings (root `frontend`):

```ini
VITE_API_URL=https://YOUR-BACKEND.onrender.com
VITE_WS_URL=wss://YOUR-BACKEND.onrender.com
```

Backend Render variables (root `backend`):

```ini
DATABASE_URL=postgresql+psycopg://<private-credentials>@<supabase-pooler-host>:5432/postgres?sslmode=require
JWT_SECRET_KEY=<private-random-secret>
ALLOWED_ORIGINS=https://YOUR-PRODUCTION-DOMAIN.vercel.app
RUN_MIGRATIONS=true
```

`RUN_MIGRATIONS` should only be enabled where the existing schema is already tracked by Alembic or the database is genuinely new. Avoid running a baseline over a pre-existing schema.

## Final acceptance checklist

- [ ] Permanent Vercel Production domain opens `/login` and `/register` directly
- [ ] Login succeeds in a fresh browser session
- [ ] Create workspace/module/task and add a comment
- [ ] Two-browser task updates arrive in real time
- [ ] Supabase password rotated and Render redeployed successfully
- [ ] README live link updated to the permanent domain
- [ ] GitHub contains no `.env` files, DB passwords or JWT keys
- [ ] Public screenshots (if added later) exclude real personal emails and tokens

The 18/18 production suite passed on 14 November 2026 before the final UI/auth CORS correction; it should be rerun if production configuration changes significantly.
