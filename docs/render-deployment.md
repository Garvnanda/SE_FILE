# Deploy TradeSphere entirely on Render

Prepared 2026-11-16. Deploy one Python Web Service serving both FastAPI and built React, plus one Render PostgreSQL database. No cloud resources have been created by the agent.

## Free-plan limitation

**Render Free PostgreSQL expires after 30 days. UptimeRobot does not extend this.** After expiry it becomes inaccessible unless upgraded; Render currently provides a 14-day upgrade grace period before deletion. Back up before day 30. This is a temporary free classroom deployment, not indefinite free database hosting.

Web services sleep after 15 minutes without inbound traffic. Periodic GET requests may prevent ordinary idle sleep, but do not prevent restarts, maintenance, quotas or suspension. Render provides 750 free service hours per workspace/month. Monitor bandwidth and build limits too. Source: https://render.com/docs/free

## 1. Push the source to GitHub

Your existing remote is https://github.com/Garvnanda/SE_FILE.git and branch is main. Use VS Code Source Control or GitHub Desktop: review changes, commit them, then Push. Do not force-add ignored files.

Include the project root and these files/folders:

- backend/, including app, migrations and requirements.lock.txt
- frontend/, including src, package.json, package-lock.json, index.html, tsconfig.json and vite.config.ts
- scripts/, especially render_start.py and seed_production.py
- alembic.ini, .python-version, .node-version, render.yaml and .gitignore
- README/docs can be included; they are not served by the application.

Do NOT upload .env, real .env.production or other secrets, .runtime/, .venv/, frontend/node_modules/, frontend/dist/, database dumps, or local demo-accounts.json. The ignore file excludes these. .env.example contains intentionally public local defaults only. Never paste real database URLs or passwords into committed files.

Render builds from GitHub source; no ZIP, PostgreSQL binaries or local database upload is needed. This creates a fresh cloud database, not a copy of local traders/trades. A private GitHub repo is supported through Render's GitHub integration.

## 2. Create PostgreSQL

1. Sign in at https://dashboard.render.com/.
2. Choose **New + > Postgres**.
3. Name: `tradesphere-db`. Database: `tradesphere` (or keep generated). Let Render generate credentials.
4. Choose a region available for both the Free database and Free Web Service. Both must use the same region.
5. Select PostgreSQL **17**, matching the locally tested major version.
6. Choose **Free**, then Create Database.
7. Wait for Available. Copy its **Internal Database URL** from Connections. Treat it as a password.
8. Restrict/disable external database access in its access settings where available; this app uses the internal URL. Temporarily allow only your public IP if later making a local backup.
9. Record the expiry date in your calendar.

Source: https://render.com/docs/postgresql-creating-connecting

## 3. Create the Web Service

Choose **New + > Web Service**, connect GitHub, and select `Garvnanda/SE_FILE`.

| Setting | Value |
|---|---|
| Name | tradesphere, or another available name |
| Branch | main |
| Region | Same as the PostgreSQL database |
| Runtime / Language | Python 3 |
| Root Directory | Leave EMPTY (repository root) |
| Build Command | `pip install -r backend/requirements.lock.txt && npm ci --prefix frontend && npm run build --prefix frontend` |
| Start Command | `python scripts/render_start.py` |
| Instance type | Free |
| Health Check Path | `/health` |

The committed `.python-version` selects the latest available Python 3.11 patch; `.node-version` selects Node 22. Render's Python runtime includes Node/npm. Do not use the local Windows .ps1 scripts on Render. No Docker or separate frontend service is needed.

Leave Pre-Deploy Command empty. The start script migrates the database, safely creates missing privileged accounts/instruments, then starts one Uvicorn worker on Render's PORT. Existing trading data and passwords are preserved on redeploys.

Sources: https://render.com/docs/deploy-fastapi ; https://render.com/docs/native-runtimes ; https://render.com/docs/python-version

## 4. Enter environment variables

Enter these in Render's Environment section before deploying. These are dashboard secrets, not GitHub files.

| Key | Value |
|---|---|
| DATABASE_URL | Internal Database URL copied from PostgreSQL |
| ENVIRONMENT | `production` |
| COOKIE_SECURE | `true` |
| PUBLIC_ORIGIN | Exact `https://YOUR-SERVICE.onrender.com`, with NO trailing slash |
| ADMIN_EMAIL | Valid email for your administrator login |
| ADMIN_PASSWORD | Unique random password, 16–128 characters |
| OPERATOR_EMAIL | A DIFFERENT valid email for the market operator |
| OPERATOR_PASSWORD | A DIFFERENT unique random password, 16–128 characters |
| ALLOW_REGISTRATION | `true` (set `false` later to close public signup) |

Use the actual assigned Render URL, not a guessed hostname. If the final URL appears only after creation, correct PUBLIC_ORIGIN to match it and redeploy before testing login. Update it when changing domains. A mismatch causes cross-origin write rejection.

Render's `postgres://` or `postgresql://` database URL is automatically converted to the installed psycopg driver. Do not use localhost or the local example database password. Do not set PORT yourself.

Optional defaults: INITIAL_CASH=100000, MAX_ORDER_QUANTITY=10000, QUOTE_MAX_AGE_SECONDS=86400. Avoid changing INITIAL_CASH after accounts exist because it also sets the P&L baseline.

Keep privileged passwords in a password manager. Bootstrap creates only missing accounts: changing an env password does NOT rotate an existing account password. It refuses to promote an existing trader when an email collides with a privileged role. Password rotation needs a separate controlled maintenance action; this demo has no recovery endpoint.

## 5. Deploy and test

Click Deploy Web Service. Expect dependency installation, successful Vite build, database migration, `Production bootstrap complete`, and Uvicorn listening on Render's assigned port. No passwords should appear in logs.

After Live:

1. Open `https://YOUR-SERVICE.onrender.com/health`; expect JSON with `status: ok`.
2. Open the root URL and log in with your ADMIN_EMAIL/ADMIN_PASSWORD; check Instruments/Users.
3. In another browser profile, log in as operator, select DEMO, open the market and publish 100.
4. Register a fresh trader; verify INR 100,000 starting funds.
5. Follow docs/demo.md: buy 10 at 100, limit buy 5 at 95, limit sell 3 at 110. Expected equity: 100175. Check the audit trail.
6. Sign out/in and verify histories, notifications, themes and mobile layout.

The public deployment intentionally disables `/docs`, `/redoc` and `/openapi.json`; use the repository's docs/openapi.json for your lab. HTTPS is required for secure cookies. Keep UI and API on the same origin; permissive CORS is unnecessary.

## 6. Optional UptimeRobot monitor

Create an HTTP(s) monitor for `https://YOUR-SERVICE.onrender.com/health`, method **GET**, at the interval available on your plan (5 minutes if offered). Do not use HEAD or provide login credentials. Expected response: HTTP 200 and status=ok.

Monitoring can report downtime and may prevent idle sleep; it cannot guarantee always-on free hosting. It will report failure if PostgreSQL expires. Pinging more frequently will not fix that. Monitor the health endpoint, not signup, trading or quote endpoints.

## 7. Backup before expiry

Free Render PostgreSQL lacks paid backup features. Use `pg_dump` while the database is accessible. The included local PostgreSQL 17 client works with the recommended server major version 17.

Temporarily allow your public IP for external database access. Use the **External Host**, database and user displayed on Render (not the internal hostname):

```powershell
New-Item -ItemType Directory -Force .runtime/backups
$env:PGSSLMODE='require'
& .runtime/pgsql/bin/pg_dump.exe --host=YOUR_EXTERNAL_HOST --port=5432 --username=YOUR_DB_USER --dbname=YOUR_DB_NAME --password --format=custom --file=.runtime/backups/tradesphere.dump
```

Enter the database password at the prompt, not in the command or GitHub. Check `$LASTEXITCODE` is 0. Restore your previous PGSSLMODE afterward and remove the temporary external access rule. Keep the dump privately in a second safe location; it contains account/session data. Dumps are ignored by Git.

A backup does not extend free hosting. Beyond day 30 you need a paid Render database or a supported migration/recreation approach subject to Render's current rules. Do not delete a database until a usable backup has been verified.

## Troubleshooting

- Build paths missing: Root Directory must be empty; use the exact build/start commands above.
- Database connection failure: check INTERNAL URL, same region and expiry.
- Bootstrap invalid: use distinct valid emails and distinct 16–128-character passwords; avoid existing trader emails.
- Cross-origin write rejected: PUBLIC_ORIGIN must exactly match the HTTPS browser origin without a trailing slash.
- Login failure: use production env credentials, not local demo-accounts.json. Confirm HTTPS/secure cookies.
- HTTP 429: wait one minute. This single-instance configuration deliberately does not trust forwarded client-IP headers; proxy traffic may share a limiter bucket. Suitable for a small classroom demo.
- Stale quote: publish a new quote as operator. Keeping the app awake does not refresh prices.
- Cold start: allow about a minute, then inspect service logs/status if it persists.
- /docs is 404: intentional in production.
- Dependency install failure: inspect logs; retain the pinned lock and Python 3.11 rather than upgrading everything blindly.

See security-review.md for the audit scope and residual limits. Actual cloud startup and deployed-host checks must still be performed after you create the services.
