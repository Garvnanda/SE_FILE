# Implementation record

Completed 2026-11-16 for the local software engineering project. User owns the thirteen experiment submissions; this repository supplies the application, source documentation and observed evidence. See intention.md for continuation instructions.

## Requirements and decisions

- Read and analyzed every original file in docs/: idea.md, technical.md, implementation.md and flowcharts.md, plus the original README.
- Confirmed the documented stack, PostgreSQL persistence, synthetic quotations and three distinct application roles.
- Collected user answers; recorded delegated policies and exclusions in docs/decision_log.md.
- Followed explicit requirements: native local execution, no Docker, no deployment, light/dark professional themes, source material for all 13 experiments.
- Created PRODUCT.md and DESIGN.md. Preserved the original planning docs and added an implementation amendment pointing to the actual contract.

## Infrastructure and database

- Created backend/frontend/scripts structure, .gitignore, .env.example and locked dependency files.
- Installed project-local Python environment and frontend packages.
- Downloaded portable PostgreSQL 17.6 from EDB, extracted only runtime components under ignored .runtime, initialized an empty cluster and started it on loopback port 54329. No Windows service was installed.
- Added native PowerShell setup/start/stop/test scripts; setup installs dependencies, creates database, applies migrations, seeds and builds.
- Implemented 15 tables: users, auth_sessions, portfolios, wallets, wallet_ledger, stocks, price_ticks, market_sessions, orders, trades, holdings, watchlists, watchlist_items, notifications, audit_logs.
- Added frozen Alembic revision 0001 with PostgreSQL numeric/timezone types, foreign keys, checks, indexes and unique constraints.
- Used READ COMMITTED transactions, a shared transaction advisory lock for financial/admin/market writes, plus row locks for settlement resources.
- Created a separate disposable tradesphere_test database. Demo data is not cleared by backend tests.

## Backend features

- Registration always creates a TRADER; atomically creates portfolio, wallet, one initial INR 100,000 ledger credit and Favorites watchlist.
- Argon2id password hashes, opaque random 8-hour sessions stored hashed, HttpOnly SameSite cookies, CSRF write protection, logout and active-account checks.
- Role-specific API guards and trader resource ownership; sanitized profile/account responses.
- Authentication attempt throttling and safe HTTP/integrity errors; basic browser security headers.
- Active instrument browsing, timestamped synthetic history and market status.
- ADMIN instrument creation/edit/disable, account directory/status management, aggregate counts and searchable audit.
- MARKET_OPERATOR quote publication, idempotent tick events, session history/open/close and synchronous pending-order evaluation.
- Market and limit buy/sell, full fills, current-quote execution, cash/share reservation, owner cancellation and exactly-once reserve release.
- Per-user idempotency keys with payload-conflict detection; unique trade per order.
- Risk checks for malformed/invalid quantity, 10,000-share cap, missing/stale quotes, inactive instruments, closed-market market orders, insufficient funds and unreserved shares.
- Persisted business rejection reasons and notices; concentration warning for buy reservation over half initial capital.
- Atomic order/trade/ledger/holding/wallet/audit/notification settlement with rollback on failure.
- Portfolio positions, available/reserved units, weighted-average cost, realized/unrealized/net P&L, equity and quote freshness.
- Filtered, paginated order/trade history, wallet ledger, named watchlists with unique membership, notifications and read markers.
- Disabling a trader cancels pending orders and releases reserves; administrative self-lockout is prevented.
- Local static build serving, health check and generated API documentation.

## Frontend features

- React/TypeScript app, Vite/Tailwind build, bundled Inter fonts and Lucide icons.
- Login and public signup; role-aware persistent navigation and session restoration.
- Trader overview, market/price-history chart/order ticket, orders/cancel/filtering, holdings/P&L, execution journal/ledger, watchlists and notifications.
- Separate operator quote editor, explicit demo price-step controls and session management.
- Admin summary, instrument metadata editor/status controls, user-status directory and audit search.
- Persistent light/dark theme, responsive desktop/mobile layout, scrollable tables/navigation, labeled forms and keyboard focus.
- Loading/empty/error/success/disabled states, retry-safe order keys, IST timestamp formatting and persistent synthetic/virtual labeling.
- Explicit refresh/navigation data refresh; no streaming or external-feed claim.

## Bugs found and fixed during verification

- Changed the transaction dependency to function scope so database commit completes before HTTP success. A real browser signup/login sequence exposed a race that TestClient alone did not reveal.
- Replaced invalid .test seed emails with example.com for EmailStr validation.
- Corrected Windows source encoding and restored Unicode currency symbols.
- Corrected admin/operator landing page after session restoration.
- Added mobile sign-out and cleared account-specific watchlist/edit/pagination state on logout.
- Split watchlist API operation IDs to make the OpenAPI contract unambiguous.
- Added full instrument metadata editing to the admin UI and verified saving/restoring the seeded company name.

## Documentation and handoff delivered

- README.md: prerequisites, native setup/start/test/development commands and navigation.
- intention.md: complete intent, decisions, implementation plan, runtime state, commands and continuation rules.
- docs/decision_log.md: all historical OPEN decisions and detailed contracts.
- docs/as-built.md: real architecture, actor/data flows, state/sequence, module responsibilities, arithmetic, security and physical deployment.
- docs/schema.md and docs/schema.sql: generated data dictionary, FK graph and PostgreSQL DDL.
- docs/openapi.json: actual API schema.
- docs/traceability.csv and docs/verification.md: 22 FR mappings and 12 NFR checks/limits.
- docs/lab-source-guide.md: source references for all thirteen student-authored experiments, including counting/scheduling inputs without invented FP totals/dates.
- docs/placeholder_register.csv: original placeholder inventory and resolution/source authority.
- docs/demo.md: canonical multi-role demonstration with expected values.
- docs/evidence/: pytest output/XML, browser result JSON/screenshots, runtime version, actual object snapshot, source hashes and local benchmark.
- scripts/export_evidence.py and scripts/reconcile_docs.py: reusable exports and documentation reconciliation.
- Removed one-off migration-freezing, encoding, seed-repair and UI-patching development scripts.

## Verification performed

| Check | Observed result |
|---|---|
| PostgreSQL initial schema | Applied to freshly initialized local database |
| Migration downgrade/base + upgrade/head | Passed on isolated test database |
| Backend suite | 20 passed, 0 failed, 0 skipped in 10.91 seconds |
| Financial concurrency | Same-key duplicate, distinct competing purchases, cancel/fill race and reserved oversell scenarios passed |
| Fault injection | Settlement exception rolled back all financial writes |
| TypeScript/Vite production build | Passed |
| Native setup rerun | Passed, preserving existing data |
| Browser smoke | All 3 roles; dark/light and 390px mobile; no page errors or document overflow |
| Browser trading scenario | Buy 10 @100, buy 5 @95, sell 3 @110; all 3 orders filled, equity INR 100,175 |
| Browser administrator editing | Metadata save verified and original seed name restored |
| Local authenticated stock-list benchmark | 60 sequential requests; p95 about 8 ms, below 1s target; not a load test |
| npm installation audit | 0 vulnerabilities reported for installed dependency graph |
| Render inspection | Desktop dark/light, mobile and canonical-result screenshots inspected |

Backend tests emit one upstream Starlette/httpx deprecation warning; assertions pass. No independent teammate/faculty sign-offs or release commit/tag were fabricated. Exact results/source hashes are in docs/evidence; no production-scale or separate-machine clean-install claim is made.

## Running state and limits

Application: http://127.0.0.1:8000. API docs: /docs. Database: 127.0.0.1:54329. Generated demo passwords: .runtime/demo-accounts.json (ignored, never committed). Runtime processes were left running for review.

Completed the requested local MVP and supporting docs. No deployment, Docker, live feeds, real money, partial fills, CSV export, social features, external notifications, historical portfolio-value series, password recovery or MFA. Those are documented exclusions. The user authors the final experiment reports, actual team schedule/FP assessment and any independent review signatures.


## Follow-up completion audit — 2026-11-16

Checked remaining checklist/code markers. Hardened start-db.ps1 and test.ps1 to stop on PostgreSQL startup/query/creation and migration errors, and restore previous PGPASSWORD/DATABASE_URL values in finally blocks. Ran the complete native test script: 20 tests passed (9.69s), production build passed (2.21s). The only warning remains the upstream TestClient deprecation. No further known required MVP tasks remain; documented exclusions and student-authored experiments remain unchanged.
