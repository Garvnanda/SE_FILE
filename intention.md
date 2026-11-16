# TradeSphere â€” intent, plan and AI handoff

Last updated: 2026-11-16. Read this FIRST when continuing the project. Then read implemented.md, docs/decision_log.md and README.md. Implementation is complete for the authorized local MVP. This record preserves the plan and continuation map; see the completion checkpoint immediately below.


## Completion checkpoint â€” authoritative current state

The requested local MVP and supporting documentation are complete. `implemented.md` is now the comprehensive change/verification record. All unchecked tasks in the original mid-build checkpoint below have been completed; that section has been marked accordingly.

Final verification: 20 PostgreSQL tests passed in 10.91s; migration down/up on the separate test DB passed; TypeScript/Vite build passed; native setup rerun passed; browser smoke passed (three roles, two themes, 390px mobile); actual browser canonical trading scenario passed with equity INR 100175 and three fills; admin metadata editing passed and seed name was restored. One upstream TestClient deprecation warning remains informational. No production-load or separate-machine-install claim.

Current app runs at http://127.0.0.1:8000, PostgreSQL at loopback port 54329. Credentials remain .runtime/demo-accounts.json. Discover current API PID through the listening port before restarting; the older PID references below are historical.

Docs now include as-built.md, schema.md/schema.sql, openapi.json, traceability.csv, verification.md, lab-source-guide.md, placeholder_register.csv, demo.md and evidence/. All four historical planning docs carry an implementation amendment. The one-off freeze_migration/ui_fix/encoding_fix/seed_fix/final_fixes helpers were removed; do not look for or recreate them. Permanent helpers include setup/start/start-db/stop-db/test, seed_demo, extract_postgres, export_evidence and reconcile_docs.

Future AI: do not restart the project or repeat completed work. Read user steering, inspect existing code and current evidence, then implement only requested changes. Re-run checks appropriate to those changes. Do not reset data, overwrite pending user edits, deploy or install Docker. Keep this file and implemented.md current.

> Current next step: follow the Render preparation/security update at the END of this file. User now authorizes deployment preparation and wants to perform Render deployment themselves. Earlier local-only instructions are historical.

## User intent and authority

Build the software engineering subject project described by all four original docs: idea.md, technical.md, implementation.md and flowcharts.md. Initial user requested no assumptions; after a question round the user explicitly delegated remaining product, technical, risk and visual decisions. Keep the documented stack and confirmed trading rules. Do not reopen settled questions.

Explicit constraints:
- PostgreSQL, SQLAlchemy and Alembic. No SQLite substitution.
- FastAPI backend; React/Vite/Tailwind frontend (TypeScript chosen).
- Three separate roles: TRADER, ADMIN, MARKET_OPERATOR. ADMIN must not gain operator powers or personal trader access.
- Synthetic quotations only; virtual INR only; no external market feed or brokerage.
- Initial INR 100,000; zero fees/slippage; moving weighted-average cost; full fills only.
- NO Docker. NO deployment. Native local Windows setup.
- Both light and dark themes; professional/formal technical interface.
- User will write all 13 lab experiments. Our deliverables are the working project and supporting technical docs/evidence, NOT completed experiment submissions.
- Keep implemented.md with all work and verification. User subsequently requested this intention.md on priority to enable another AI to resume midway.
- No deadline supplied. Never invent teammate identities, signatures, effort hours, test results, or faculty approvals.

## Product and completion target

A local, multi-user educational trading workspace: register/login/logout, fictional stock catalog, synthetic quote chart, wallet/ledger, market/limit buy/sell, reservation/cancellation, atomic execution, positions/P&L, filters, watchlists/favorites, notifications, admin governance/audit, operator quote/session controls. Include repeatable seed, real PostgreSQL tests, real browser demo, native setup commands, API/schema/architecture documentation and requirement traceability useful for all 13 experiments.

Completion means clean build, passing meaningful automated checks, actual canonical browser demo, usable UI in both themes/mobile, accurate README and as-built docs, and implemented.md/intention.md honestly reconciled with remaining limitations. Student-authored experiment sheets and independent teammate sign-offs are outside this agent's deliverable.

## Plan and dependency order

1. Review original docs and repository; identify contradictions/open choices. DONE.
2. Resolve user choices, choose/document remaining policies. DONE; docs/decision_log.md.
3. Create native local PostgreSQL infrastructure, environment, schema and migration. IMPLEMENTED; migration round-trip verified.
4. Implement auth, role ownership, initial wallet, seed. IMPLEMENTED and tested.
5. Implement catalog, synthetic quotes/session, synchronous pending-order processing. IMPLEMENTED and tested.
6. Implement trading, reservations, settlement, idempotency, rejection/cancel notifications and audits. IMPLEMENTED and tested.
7. Implement portfolio/P&L, history/filtering, watchlists, admin summaries. IMPLEMENTED; final expanded tests passed.
8. Build responsive three-role UI with both themes, price chart and order ticket. IMPLEMENTED; render smoke and actual browser trade scenario pass.
9. Final QA: extend focused coverage, migration downgrade/upgrade on test DB, full regression, build, benchmark, evidence exports, inspect light/dark/mobile and demo screenshots.
10. Finish supporting docs: as-built architecture/flow/state/security, generated schema/data dictionary/OpenAPI, traceability, source guide for 13 experiments, closure register. Preserve original blueprint as historical with clear amendment.
11. Clean temporary development scripts, update implemented.md and this file, final status with local URL, demo-account file location, test results and limitations. Do not deploy or commit without request.

## Current repository implementation

Backend:
- backend/app/db.py: env settings, PostgreSQL engine and session factory.
- backend/app/models.py: 15 tables including sessions, users, portfolios/wallet/ledger, stock/ticks/session history, orders/trades/holdings, watchlists/items, notifications/audit.
- backend/app/trading.py: lock_market, quote, market_open, wallet_for, holding_for, average_cost, eligible, place, settle, process_pending, cancel, record, notify.
- backend/app/main.py: FastAPI endpoints, validation, auth/CSRF, rate limiting, role guards, data queries, static frontend serving.
- backend/alembic/versions/0001_initial.py: frozen explicit PostgreSQL DDL (original metadata-based draft was replaced; do not regenerate after schema evolution).
- backend/tests/: PostgreSQL integration/unit tests (16 passing at initial run).

Frontend:
- frontend/src/main.tsx: React app, fetch client, table/chart components, role-aware screens and forms.
- frontend/src/style.css: responsive light/dark tokens and styles.
- frontend/vite.config.ts: React/Tailwind and API proxy.
- frontend/package-lock.json, backend/requirements.lock.txt: installed dependency locks.
- frontend/browser-smoke.mjs: three-role login, screenshots, themes/mobile overflow and JS errors.
- frontend/browser-demo.mjs: real isolated-browser canonical trading demo, new trader each run; validates equity 100175 and 3 fills, checks other pages/admin reload.
- frontend/browser-admin.mjs: administrator metadata editing and restoration.

Infrastructure:
- scripts/setup.ps1: native Python venv/npm dependencies, portable PG download/extraction, start DB/migrate/seed/build.
- scripts/start-db.ps1: starts ignored project-local PostgreSQL, loopback 127.0.0.1:54329.
- scripts/start.ps1: migrate and run API 127.0.0.1:8000.
- scripts/stop-db.ps1: stop local database.
- scripts/test.ps1: separate test DB migrations/tests/build.
- scripts/seed_demo.py: idempotent seed; generated passwords stored only under ignored .runtime.
- scripts/extract_postgres.py: extracts bin/lib/share from official EDB ZIP.
- Temporary development helpers were removed; see completion checkpoint.

Docs already written: README.md, PRODUCT.md, DESIGN.md, docs/decision_log.md, docs/demo.md. Original four docs unchanged at this checkpoint. implemented.md now contains the full implementation and verification record. Evidence contains pytest.xml, browser-smoke.json, browser-demo.json and screenshots.

## Runtime state and exact commands

Workspace: C:\projects\se_file. Shell: Windows PowerShell. Python 3.11.7, Node 24.8.0, npm 11.6.0. Portable PostgreSQL 17.6 extracted under .runtime/pgsql. No global service installed.

Database is running at 127.0.0.1:54329. Demo DB: tradesphere. Test DB: tradesphere_test. Local-only connection example is in .env.example. Do not display or commit generated account passwords; user can open .runtime/demo-accounts.json. Demo emails admin@example.com, operator@example.com, trader@example.com. Additional browser-created demo traders exist.

API has been started as a hidden background Python process on port 8000. Its PID changed after a fix; discover current process by port/process command line before restarting, never kill arbitrary Python processes. Logs: .runtime/api.log and .runtime/api-error.log. Frontend built bundle is served by FastAPI; restart backend only for backend edits or if frontend dist first appears. Frontend changes require npm build. Vite dev is optional on 5173, not currently required.

Commands from repository root:
```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup.ps1
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
powershell -ExecutionPolicy Bypass -File scripts/test.ps1
.venv/Scripts/python.exe -m alembic upgrade head
.venv/Scripts/python.exe -m pytest backend/tests -v --junitxml=docs/evidence/pytest.xml
npm.cmd run build --prefix frontend
```
Browser commands MUST run with working directory frontend because scripts use relative ../ paths:
```powershell
cd frontend
node browser-smoke.mjs
node browser-demo.mjs
```
Browser demo creates a NEW trader and changes DEMO synthetic quotes; safe for disposable demonstration data, no reset. Canonical final DEMO price 110.

## Important fixes and traps already found

- FastAPI transaction dependency MUST use Depends(db_session, scope="function"). This commits before the response is sent. Default request scope caused real browser signup/login to race: registration returned 201 before user commit, immediate login got 401. Fixed, actual browser demo subsequently PASSED. Keep this invariant; TestClient alone did not reveal it.
- EmailStr rejects .test demo addresses. Seed now uses example.com; local generated account file/database were migrated. Do not revert to .test.
- Windows PowerShell Set-Content defaults to legacy encoding. Always specify UTF8 for new Unicode files. main.tsx was corrected from cp1252 to UTF-8 and rupee signs repaired; do not rerun encoding_fix.py.
- Persisted admin/operator session reload initially landed on Overview; corrected boot logic picks correct role start page.
- Mobile sidebar hides footer; added topbar mobile sign-out.
- Browser screenshot result: no horizontal document overflow at 390px, scrollable navigation/tables intentional.
- Ruff formatted backend; Prettier formatted UI. No final lint cleanliness claimed yet.
- Initial pytest run: 16 passed, 1 Starlette httpx deprecation warning (not failure), 7.71 seconds. Superseded by the final 20-pass run.
- Frontend builds pass; npm audit installation reported zero vulnerabilities.
- Browser smoke passes three roles/two themes/mobile, no page errors. Actual browser canonical scenario also passes after transaction-scope fix; docs/evidence/browser-demo.json records it.

## Core policies/invariants to preserve

- All financial mutations acquire PostgreSQL transaction advisory lock 731002, then row locks. This serializes demo writes deliberately. READ COMMITTED; no exchange-scale throughput claim. External DB writers unsupported. No worker, queue, Docker or async scheduler.
- Financial state, trade, ledger, audit, notification and order status commit atomically; any exception rolls back all.
- Decimal prices 4dp, cash 4dp, cost/P&L 8dp; half-even average. UI 2dp. JSON decimals strings.
- Quote expiry 24h; maximum quantity 10,000. Configurable in db.py/settings.
- BUY reservation >50% initial capital yields warning only, not a portfolio concentration hard limit.
- LIMIT immediate full fill if already eligible; otherwise reserve. Eligible pending orders process on tick/reopen. Buy quote<=limit, sell quote>=limit; execute at quote.
- Closed market rejects market orders, retains/allows limits. Quotes must still be fresh.
- Cancel releases once; cancelled retry no-op, filled/rejected conflict.
- Idempotency scoped to user+key; payload mismatch 409. Tick event key similarly protected.
- Valid business rejections persist/notify; malformed requests rejected before persistence.
- Admin disables trader => cancels pending orders first. Admin cannot disable admin. Inactive stock pending orders stay cancellable and cannot fill while inactive.
- No secrets in committed output, no raw password hashes in API. Append-only APIs are not database tamper-proofing.

## Original mid-build checklist â€” completed

- [x] Write as-built.md with real architecture, state/sequence/data flows, deployment, numerical examples and known limits.
- [x] Generate schema.md/schema.sql/openapi.json from implemented code; include real constraints/fields and schema revision.
- [x] Write traceability.csv mapping FR01â€“FR22 and NFR evidence, and lab-source-guide.md mapping all 13 experiments to source docs (do not author student submissions/FP counts/calendar estimates).
- [x] Amend four blueprint docs with current authoritative scope and historical-placeholder status; produce explicit closure/deferred register rather than pretending placeholders are completed experiments.
- [x] Improve test coverage for concurrent distinct buys/oversell, sell reservation cancellation, duplicate tick, stock management and persistence where material.
- [x] Migration round-trip on tradesphere_test only, then full regression and build; save results.
- [x] Measure seeded API list p95 and capture environment/schema/object snapshot evidence without secrets.
- [x] Check final UI screenshots including actual demo result; run final browser checks after any relevant UI change.
- [x] Consider admin metadata editing UI: backend PATCH supports name/sector, current UI only toggles active plus creates instruments. Implement inline edit if needed to fulfill full catalog editing UX.
- [x] Fix any discovered issues; no invented passes.
- [x] Remove one-off helper scripts safely by explicit paths within workspace. Keep reusable seed/extraction/setup/start/test helpers.
- [x] Update implemented.md comprehensively and this checklist; final response with app URL/run commands, test outcomes and docs links.

## Known boundaries / not unfinished hidden features

No CSV export, email/SMS, social trading, leaderboard, portfolio value-over-time series, partial fills, payment gateway, live prices, recommendations, production hosting, password recovery or MFA. Price chart is synthetic quote history. Reporting is tables/portfolio summary. Security/rate limiting optimized for localhost single process. Student identities, independent reviews, experiment reports and calendar/PERT estimates are deliberately left to the student, not fabricated.

## Tools and permissions

Current permissions unrestricted, approval policy never; do not pass sandbox_permissions. Do not spawn subagents unless explicitly authorized by user or applicable instructions. No agents have been used. Impeccable skill used for UI; context and craft guidance read, manual detector run. Detector only flagged Inter as common; retained for a restrained operational interface. A setup-hook issue was reported by skill; do not alter project hooks as side effect. Browser checks use Playwright headless CLI and local screenshot inspection.

## Handoff rule

Continue from the completion checkpoint and any new user request. Do not regenerate the whole app, reset the user's git changes, clear demo data, install Docker, deploy, or reopen resolved choices. Keep giving concise progress updates; the user recently asked duration and was told about 20â€“30 minutes for remaining QA/docs, not a deadline guarantee. Update this file whenever major state changes so it remains the primary continuation map.


## Follow-up completion audit â€” 2026-11-16

Checked remaining checklist/code markers. Hardened start-db.ps1 and test.ps1 to stop on PostgreSQL startup/query/creation and migration errors, and restore previous PGPASSWORD/DATABASE_URL values in finally blocks. Ran the complete native test script: 20 tests passed (9.69s), production build passed (2.21s). The only warning remains the upstream TestClient deprecation. No further known required MVP tasks remain; documented exclusions and student-authored experiments remain unchanged.


## Render preparation and security review â€” 2026-11-16

User now wants to deploy all components on Render and requested instructions/security review. This supersedes the earlier local-only deployment constraint, while no Docker remains required. No cloud resources were created and nothing was pushed by the agent.

Added docs/render-deployment.md with exact GitHub/Render steps and docs/security-review.md with findings, fixes and remaining limits. Added .python-version (latest 3.11 patch), .node-version (22), render.yaml, scripts/render_start.py and scripts/seed_production.py. Production uses environment-only privileged secrets, creates only missing identities, rejects role collisions and preserves stored data. DATABASE_URL accepts Render URL schemes. One worker, startup migrations, platform PORT, same-origin React/API serving. Public docs disabled; no real credentials in source.

Fixed insecure production configuration, session reactivation after account disabling, unbounded request/limiter/session growth, parallel Argon2 memory pressure, missing public origin/security headers/cache policy. Added tests for secure cookies/origin checks, registration switch, body size, bounded limiter/hash concurrency, session cap, bootstrap idempotency/role-collision and fail-closed settings.

Verification: 27 tests passed in 13.25s, frontend production build passed. pip-audit and npm audit found no known dependency vulnerabilities. Results in docs/evidence/*security-audit.json and security-test-results.txt. These are local checks, not a cloud deployment or penetration-test claim.

Render FREE PostgreSQL expires after 30 days; monitoring does not extend it. Free web-service uptime/quota limitations remain. Deployment guide includes backup and manual smoke-check steps. Remaining user actions: push reviewed source, create same-region Render database and free Python service, set secrets and exact HTTPS PUBLIC_ORIGIN, deploy, verify live URL. Do not falsely mark live deployment complete or invent a public URL.
