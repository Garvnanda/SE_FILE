# Decisions — 2026-11-16

User confirmed the documented stack and delegated remaining implementation choices. User explicitly requires no Docker, no deployment, both themes, and supporting project documentation rather than completed lab experiments.

| ID | Resolution |
|---|---|
| OPEN-01 | TradeSphere |
| OPEN-02 | PostgreSQL + SQLAlchemy + Alembic; portable project-local Windows server |
| OPEN-03 | React + TypeScript + Vite + Tailwind |
| OPEN-04 / OPEN-14 | Three separate roles; enforced server-side on each endpoint |
| OPEN-05 | Closed market rejects market orders; retains/accepts limit orders; reopening evaluates eligible orders |
| OPEN-06 | Synthetic quotes only, manual operator publication and explicit 100/95/110 demo steps |
| OPEN-07 | Zero fees and slippage |
| OPEN-08 | Moving weighted-average cost, 8 decimal places, half-even rounding |
| OPEN-09 | INR 100,000 initial credit; no deposit or withdrawal |
| OPEN-10 | UTC persistence; Asia/Kolkata display |
| OPEN-11 | Source material for all 13 experiments; experiment submissions excluded by user |
| OPEN-12 | No deadline; actual development date recorded, no fictional schedule |
| OPEN-13 | Student names, ownership and independent sign-offs are student-authored, not generated |
| OPEN-15 | In-app only |
| OPEN-16 | Full fills only |
| OPEN-17 | Concurrent duplicate/cancel-fill/funds tests, no exchange matching |
| OPEN-18 | Local Windows; no Docker and no deployment |
| OPEN-19 | CSV reports deferred; API history and UI tables implemented |
| OPEN-20 | Fictional DEMO, NOVA, VERD, AXIS symbols; no association with listed companies |
| OPEN-21 | Opaque random HttpOnly SameSite=Strict session cookie; stored hashed, 8-hour expiry; CSRF header for authenticated writes |

## Additional implementation contracts

- Positive whole-share quantities, maximum 10,000 per order. Quotes valid for 86,400 seconds. Both configurable in environment.
- Concentration warning if a BUY order's reservation exceeds 50% of initial capital. This is an order-size warning, not a portfolio-level hard limit. Ordinary funds/share checks remain hard blocks.
- Prices: NUMERIC(18,4); wallet and ledger NUMERIC(24,4); average cost and realized P&L NUMERIC(24,8). UI displays two decimals. JSON money is decimal strings; all authoritative arithmetic uses Decimal.
- Limit orders already eligible execute immediately while open, at the current quote. Market reopen also triggers evaluation. Inactive instruments and disabled accounts do not fill.
- Validly shaped rejected order submissions are persisted and notified. Malformed payloads return 422 before an order is created; unknown instrument returns 404.
- Same user + idempotency key + identical payload returns existing order, including a rejected order. Changed payload returns 409. Repeated tick key returns the same tick; a changed price/symbol is 409.
- Cash ledger contains actual cash movements only; reservations/releases are in audit and order fields. Cancellation of CANCELLED is a stable no-op; cancellation of FILLED/REJECTED is 409.
- Session history is append-only. Highest committed ID is current session. Latest price uses the highest tick ID.
- Default PostgreSQL READ COMMITTED; all market/order/admin mutations take advisory lock 731002 first, then financial rows use FOR UPDATE. Transactions commit before sending successful HTTP responses. No worker, queue, scheduler or background polling; quote/reopen processing is synchronous.
- Because all financial writers share one global lock, internal lock-order deadlocks are avoided rather than retried. Unexpected database errors roll back; clients can safely retry with the original key. Multiple external database writers are unsupported.
- Admin can disable traders/operators; disabling a trader cancels pending orders and releases reservations. Admin accounts cannot be disabled through the UI. Instrument disable retains pending orders for cancellation or future reactivation; no hidden fills.
- No deletion API for users/instruments; FK defaults prevent orphaning. Audits, ticks, trades and ledger are append-only at the application boundary, not tamper-proof against a database administrator.
- Auth throttling: 30 attempts/minute per client IP, process-local. Demo only; no password reset or MFA.
- Offset pagination, default 100/max 500 records. Frontend history pages use 50; latest price chart 100 points. New pages refresh on navigation/manual refresh; no claim of streaming quotes.
- `.runtime` holds generated passwords, binaries and database, excluded from git. No privileged credentials are committed. Database's documented local-only demo password is not appropriate for hosting.
- Optional richer analytics, portfolio time series, CSV exports, leaderboards, partial fills and external notifications remain out of scope.

## Blueprint reconciliation

The four initial docs are retained as planning history. Their placeholders are not assertions about this release. Schema/API/runtime specifics are resolved by schema.md, schema.sql, openapi.json and evidence; UI choices by DESIGN.md and screenshots; state by as-built.md. Student names, calendar estimates, FP counts, final classroom diagrams and faculty review remain student-authored per the later user instruction. Therefore historical G07/G08 requirements to author all submissions and fabricate sign-offs are superseded; no such gate approval is claimed.


## Deployment amendment
User subsequently requested an all-Render deployment guide and vulnerability review. See render-deployment.md and security-review.md for current public configuration. Earlier local-only deployment/auth-limit descriptions remain historical. Production is prepared with secure cookies, origin checks, bounded limits and env-only bootstrap; cloud deployment is user-performed and not verified yet.
