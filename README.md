# TradeSphere

A local educational paper-trading application: FastAPI, PostgreSQL, SQLAlchemy/Alembic, React, TypeScript, Vite and Tailwind. Virtual funds, synthetic quotations, no real orders.

## Deploy on Render

Follow [the Render guide](docs/render-deployment.md) for exact upload, database, service and secret settings. Read [the security review](docs/security-review.md). Free Render PostgreSQL expires after 30 days; uptime monitoring does not extend it. Deployment is prepared but has not been performed.

## Start on Windows (no Docker)

Prerequisites: Python 3.11+, Node 22.12+ and internet access for the first installation. Run from this repository in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

Open **http://127.0.0.1:8000**. Setup downloads a portable PostgreSQL 17.6 distribution into ignored `.runtime/`, initializes a loopback-only instance on port 54329, installs locked dependencies, applies migration `0001`, seeds accounts and builds the frontend. Nothing is deployed; no Windows service or Docker is installed. Local database credentials are demo-only and documented in `.env.example`.

The three separately generated demo account passwords are in **`.runtime/demo-accounts.json`**. Do not commit that file. You can also register a trader through the UI. Initial virtual balance: INR 100,000. Seed reruns preserve existing accounts and trading data. Fresh quotes can be published through the operator console if seeded quotes expire after 24 hours.

Stop the API with Ctrl+C. Stop PostgreSQL with `powershell -ExecutionPolicy Bypass -File scripts/stop-db.ps1`.

## Development and tests

```powershell
# Backend + database: scripts/start.ps1
npm.cmd run dev --prefix frontend
# Open http://127.0.0.1:5173; Vite proxies the API to port 8000.
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
# Browser checks, while the built app is running on port 8000:
cd frontend
npx playwright install chromium
node browser-smoke.mjs
node browser-demo.mjs
node browser-admin.mjs
```

Backend tests clear ONLY the separate `tradesphere_test` database. Browser-demo creates a new demo trader and operates the DEMO instrument; use the local demonstration database. Test artifacts are in `docs/evidence/`. API documentation: **http://127.0.0.1:8000/docs**. Rebuild after frontend edits with `npm.cmd run build --prefix frontend`.

## Features

- Trader registration, secure sessions, logout, role and owner authorization.
- Market/limit buy and sell; cash/share reservations, cancellation and full fills.
- Idempotent order requests and tick events; transaction-safe settlement.
- Wallet ledger, holdings, weighted-average cost and realized/unrealized P&L.
- Filterable order/trade history, named watchlists/favorites, in-app notifications.
- Separate administrator catalog/users/audit/aggregate report and operator quotes/sessions.
- Synthetic price chart, dark/light themes, responsive layout and keyboard-friendly forms.

## Documentation

- `implemented.md`: work performed and verification results.
- `intention.md`: complete plan, decisions and continuation map for a future AI.
- `docs/decision_log.md`: resolved product and implementation policies.
- `docs/as-built.md`: architecture, flows, security, formulas, state and deployment.
- `docs/schema.md`, `docs/schema.sql`: generated data dictionary and PostgreSQL schema.
- `docs/openapi.json`: actual API contract.
- `docs/traceability.csv`: FR-to-code/test map.
- `docs/lab-source-guide.md`: source material for all thirteen experiments; student authors submissions.
- `docs/demo.md`: reproducible three-role walkthrough.
- Original four blueprint documents remain historical baselines with an amendment pointing to the implementation.

No live exchange data, real money, partial fills, CSV exports, email delivery, social features or public deployment. The application is intentionally a single-process local prototype. Mutations serialize under a PostgreSQL transaction advisory lock; this favors correctness and clear demonstrations over production throughput.
