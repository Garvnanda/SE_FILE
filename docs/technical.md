# TradeSphere — Technical Specification and SRS Baseline

> **Version:** 1.0 (proposed, not implemented). Read `idea.md` for boundaries / unresolved choices. This is a **software design specification**, not a claim that the application already exists.

## 1. Architectural principles
**Modular monolith**: React/Vite/Tailwind browser client -> FastAPI REST backend -> SQLAlchemy + relational database (PostgreSQL required) -> background quote/order worker in the same app process for local demo. Production-like scalability is **not** a requirement. Main separation: Auth, Market, Wallet, Orders, Execution, Portfolio, Risk, Notifications, Audit, Analytics.

**Source of truth:** relational transaction records. Never put wallet or order correctness in the frontend. Prices are synthetic, server-validated. A scheduler is an implementation option; a deterministic Market Operator `POST /operator/ticks` endpoint is required for repeatable demo tests.

### Proposed directory tree
```text
tradesphere/
  backend/
    app/main.py
    app/api/{auth,stocks,orders,wallet,portfolio,watchlists,admin,analytics}.py
    app/core/{config,security,db,errors}.py
    app/models/{user,stock,price,portfolio,wallet,order,trade,holding,audit,notification}.py
    app/schemas/...
    app/services/{auth,market,order,risk,execution,ledger,portfolio,reporting,audit}.py
    app/workers/{market_ticks,limit_orders}.py
    alembic/  # if migrations adopted
    tests/{unit,integration,fixtures}/
    pyproject.toml / requirements.txt
  frontend/
    src/{pages,components,api,contexts,hooks,types}/
  scripts/{seed_demo,reset_demo}.py
  docs/{srs,diagrams,tests,estimations}/
  docker-compose.yml  # optional
  README.md
```

## 2. Functional requirements — individually testable
| ID | Requirement | Features | Test evidence |
|---|---|---|---|
| FR-01 | Register trader with unique email and securely hashed password | F01 | IT-AUTH-01 |
| FR-02 | Authenticate, issue session/token, authorize TRADER vs ADMIN APIs | F01 | IT-AUTH-02 |
| FR-03 | Admin create/disable listed instruments with symbol uniqueness | F02/F09 | IT-MKT-01 |
| FR-04 | Show latest quote, synthetic source and timestamp and chartable price history | F02/F07 | IT-MKT-02 |
| FR-05 | Market Operator open/close simulated market and create deterministic quote ticks | F02/F09 | IT-MKT-03 |
| FR-06 | On account setup credit configurable virtual INR in a ledger exactly once | F03 | IT-WAL-01 |
| FR-07 | Show total, reserved and available virtual cash with transaction history | F03 | IT-WAL-02 |
| FR-08 | Submit authenticated market buy/sell order, validate and execute at synthetic quote when open | F04/F08 | IT-ORD-01 |
| FR-09 | Submit limit buy/sell order, reserve funds/shares, persist pending status | F04/F08 | IT-ORD-02 |
| FR-10 | Check eligible pending limit orders when quote changes and execute full fill | F04 | IT-ORD-03 |
| FR-11 | Cancel unfilled order; release reserved cash/shares exactly once | F04 | IT-ORD-04 |
| FR-12 | Reject insufficient funds, oversell, unauthorized, invalid quantities, stale/missing quote or closed-market violations | F08 | IT-RISK-01 |
| FR-13 | Record immutable execution details (order, side, price, qty, timestamp, symbol) | F04/F05 | IT-TRADE-01 |
| FR-14 | Update wallet ledger, trade, holding and order atomically on fill | F03/F04/F05 | IT-TRADE-02 |
| FR-15 | Show positions, quantity, average cost, marked value, realized and unrealized P&L | F05/F07 | IT-PORT-01 |
| FR-16 | Filter own order/trade history by date, symbol, side, status | F05 | IT-ORD-05 |
| FR-17 | Create/list/delete user's watchlist entries, no duplicate symbol per watchlist | F06 | IT-WATCH-01 |
| FR-18 | Produce basic dashboard stats: portfolio total, cash, last price, P&L | F07 | IT-ANA-01 |
| FR-19 | Persist in-app order status and risk notifications with read/unread state | F10 | IT-NOTIF-01 |
| FR-20 | Log critical actions with actor, type, entity ID, UTC timestamp, previous/new state metadata | F10 | IT-AUD-01 |
| FR-21 | Allow ADMIN to inspect user/market/order summaries and audit without disclosing password data | F09 | IT-ADM-01 |
| FR-22 | Ensure idempotent order retries and duplicate execution protection | F04/F11 | IT-CONC-01 |

**Explicitly outside current FR baseline:** user-to-user matching, partial fills, broker integrations, real-money deposit/withdrawal, financial recommendations, price forecasting, taxes, production alert paging. If added later, get new FR IDs.

## 3. Non-functional requirements (thresholds for prototype; verify in tests)
| ID | Requirement | Planned verification |
|---|---|---|
| NFR-01 | No wallet or position goes below available zero after accepted operation | property/unit/integration test |
| NFR-02 | Complete order execution and settlement is ACID or entirely rolled back | forced-exception integration test |
| NFR-03 | Only owner accesses private orders/holdings; only MARKET_OPERATOR changes quotes; only ADMIN manages stocks/users/audit | auth tests, 403/404 cases |
| NFR-04 | Passwords stored with modern adaptive hash; no plaintext secrets in source | auth/security inspection |
| NFR-05 | Valid orders and trades record server-side UTC timestamp; UI formats Asia/Kolkata by default | time-zone test |
| NFR-06 | UI and API label synthetic quotes and virtual funds clearly | visual inspection |
| NFR-07 | Demo runs from clean checkout/seed and requires no paid market API | reproducibility check |
| NFR-08 | p95 of normal local list/API requests < 1 s for seeded demo load; **target**, not currently measured | timed benchmark |
| NFR-09 | Single deterministic market tick re-evaluates all applicable pending orders (within demo dataset) | fixture test |
| NFR-10 | Duplicate idempotency key cannot debit twice or create duplicate executions | concurrent/retry test |
| NFR-11 | Audit events append-only via application APIs and persist across restart | inspection/restart test |
| NFR-12 | Data model supports foreign keys, uniqueness, transaction isolation and reproducible migrations | migration and integrity checks |

## 4. Conceptual data model — entity inventory
**Use explicit PK/FK constraints; consider uniqueness and indices on symbol, user_id, order status, timestamps.**

| Entity | Representative fields (not final SQL DDL) | Relationships / constraints |
|---|---|---|
| users | id PK, email unique, password_hash, role, created_at, active | 1:N portfolios, orders, watchlists, notifications, audit events |
| stocks | id PK, symbol unique, name, sector, active, created_at | 1:N price_ticks, orders, trades, holdings |
| price_ticks | id PK, stock_id FK, price DECIMAL(18,4), source, recorded_at | append-only, price > 0 |
| market_sessions | id PK, is_open, updated_by FK, effective_at, note | MVP singleton current session plus history |
| portfolios | id PK, user_id FK unique, base_currency, created_at | 1:1 per trader by default |
| wallets | id PK, portfolio_id FK unique, currency, cash_total, cash_reserved, version | available = total - reserved; both >= 0 |
| wallet_ledger | id PK, wallet_id FK, order_id FK nullable, amount_signed, event_type, created_at | append-only; ledger posted at settlement; reservation separately evented |
| orders | id PK, user_id FK, stock_id FK, side, order_type, limit_price nullable, qty, status, reserved_cash, reserved_qty, idempotency_key, created_at, updated_at | user unique idempotency key; MVP at most one execution |
| trades | id PK, order_id FK unique (MVP), user_id FK, stock_id FK, side, qty, execution_price, executed_at | immutability of execution details |
| holdings | id PK, portfolio_id FK, stock_id FK, qty, reserved_qty, avg_cost, realized_pnl | unique (portfolio_id,stock_id) |
| watchlists | id PK, user_id FK, name, created_at | 1:N watchlist_items |
| watchlist_items | id PK, watchlist_id FK, stock_id FK | unique(watchlist_id,stock_id) |
| notifications | id PK, user_id FK, type, title, body, read_at nullable, created_at | no cross-user access |
| audit_logs | id PK, actor_id FK nullable, action, entity_type, entity_id, before_json, after_json, correlation_id, created_at | append-only via app; JSON metadata redact secrets |

**Normalization decisions:** `stocks` metadata distinct from `price_ticks` time series; `orders` distinct from `trades`; reservations not represented as money removed from posted balance; `wallet_ledger` distinct from wallet balance snapshot; `holdings` aggregate is a transactional materialization of trade history. `portfolios` 1:1 with traders for MVP. Avoid storing a single portfolio's `total_value` as authoritative field (derive from quotes).

### Outstanding database design placeholders
- [SCHEMA-TBD-01] **RESOLVED:** PostgreSQL dialect, SQLAlchemy ORM, Alembic migrations. Record actual PostgreSQL/server/client versions and migration revision at G01/G02.
- [SCHEMA-TBD-02] Define precision and rounding for prices, cost basis, ledger [OPEN-07], [OPEN-08].
- [SCHEMA-TBD-03] Full FK behavior, delete policy, index choices and transaction isolation strategy.
- [SCHEMA-TBD-04] Whether risk warnings persist in dedicated `risk_events` table (optional).
- [SCHEMA-TBD-05] `market_sessions` singleton vs session history representation.
- [SCHEMA-TBD-06] Decide if `wallet_ledger` includes explicit RESERVE/RELEASE rows; baseline: ledger posts cash adjustments; audit captures reservation transitions.

## 5. Transaction algorithms — authoritative pseudo-spec
### A. Place market buy
1. Authorize user; check idempotency key (return previous result for exact retry).
2. Validate active instrument, open market, valid quote, quantity/limits.
3. Compute cost with Decimal. Begin DB transaction, lock wallet/holding rows as DB supports.
4. Verify available cash. Create order; debit wallet cash; append ledger debit; create trade with server timestamp; update weighted-average holding; set FILLED; append audit and notification.
5. Commit all or roll back all. Return order + execution IDs.

### B. Place limit buy
1. Validate order/quote and compute maximum reservation `qty * limit` (+ fees if applicable).
2. Begin DB transaction; confirm sufficient *available* cash; increment wallet reserved amount; create PENDING order, append audit; commit.
3. On quote tick: if `price <= limit` and session open, within one transaction verify pending status and reservation; execute at tick price, charge actual cash, release full reserved amount, update holding, ledger, trade, status, event, notification.
4. Repeated tick must not fill a FILLED/CANCELLED order.

### C. Place limit sell
1. Validate owned unreserved shares, reserve units on holdings, PENDING.
2. Eligible when `price >= limit` and market open; execute at tick price; decrement held and reserved shares, credit wallet, compute realized P&L using moving-average cost, log execution and fill.
3. Pending cancellation releases remaining reserved shares once.

### D. Market sell
Like sell fill above, but fills immediately at current quote when session open; cannot sell reserved shares.

### E. Cancel pending order
Lock order; owner-only; if PENDING, change CANCELLED, release cash or shares reservation, audit, notify, commit; if already CANCELLED return stable no-op; if FILLED return conflict.

### Concurrency and isolation notes
**PostgreSQL is the required transaction store.** Use short SQLAlchemy transactions and `SELECT ... FOR UPDATE` row-level locks on affected wallet, holdings and order records; deterministic lock acquisition order; `UNIQUE` constraints on idempotency keys and per-order trade. Re-check status and reservations under lock before settlement. Choose and document isolation level (working default READ COMMITTED), implement deadlock retry for genuinely retryable exceptions, and test simultaneous requests. Row locks do not replace end-to-end correctness tests.

## 6. Order state machine
```
CREATED --validation failure--> REJECTED
CREATED --validation success + reservable limit order--> PENDING
CREATED --valid market order and execution--> FILLED
PENDING --eligible quote + successful settlement--> FILLED
PENDING --owner cancel--> CANCELLED
```
No PARTIALLY_FILLED state in implemented MVP. `FILLED`, `CANCELLED`, `REJECTED` terminal. Rejected orders may be persisted or returned without storage; choose [STATE-TBD-01] and align DFD/SRS/test data.

## 7. REST API contracts (proposed version `/api/v1`)
| Method and path | Role | Body / semantics |
|---|---|---|
| POST `/auth/register` | Guest | email, password; creates trader+portfolio+wallet+initial ledger credit |
| POST `/auth/login` | Guest | credentials -> token/session |
| GET `/auth/me` | Auth | role, safe profile |
| GET `/stocks` | Auth | list active symbols and latest quotes |
| GET `/stocks/{symbol}/history` | Auth | paginated synthetic price events |
| GET `/wallet` | Trader | balance, reserved, available |
| GET `/wallet/ledger` | Trader | paginated cash events |
| POST `/orders` | Trader | `stock_id`, `side`, `type`, `quantity`, `limit_price?`, `idempotency_key` |
| GET `/orders` | Trader | filter status, symbol, side and dates |
| GET `/orders/{id}` | Trader | owner scoped |
| POST `/orders/{id}/cancel` | Trader | only PENDING; release reserves |
| GET `/trades` | Trader | execution history |
| GET `/portfolio` | Trader | positions and valuation |
| GET `/portfolio/performance` | Trader | holdings / P&L summary with quote timestamp |
| GET/POST `/watchlists` | Trader | list/create user watchlists |
| POST/DELETE `/watchlists/{id}/items/{stock_id}` | Trader | add/remove symbol |
| GET/PATCH `/notifications` | Trader | list + mark read; split specific endpoints during implementation |
| GET `/admin/stocks` | Admin | list instruments incl inactive |
| POST/PATCH `/admin/stocks` | Admin | manage symbol metadata |
| POST `/operator/ticks` | Market Operator | symbol, new simulated price -> append tick, trigger worker |
| POST `/operator/market-session` | Market Operator | set market open/closed |
| GET `/admin/audit` | Admin | searchable paginated events |
| GET `/admin/users` | Admin | list users and roles with sensitive fields redacted |
| GET `/operator/market-status` | Market Operator | current synthetic session status, latest ticks |

**Contract placeholders:** [API-TBD-01] exact response/error JSON shape; [API-TBD-02] auth token storage strategy; [API-TBD-03] cursor vs offset pagination; [API-TBD-04] event/scheduler mechanism; [API-TBD-05] rate limiting and signup abuse safeguards. Use OpenAPI generated docs to freeze exact contracts at Phase P02.

## 8. Computations
- `available_cash = wallet.cash_total - wallet.cash_reserved`.
- `available_shares = holding.qty - holding.reserved_qty`.
- `buy_average_cost = (old_qty * old_avg_cost + fill_qty * execution_price) / (old_qty + fill_qty)`; fee inclusion TBD.
- `sell_realized_pnl = fill_qty * (execution_price - old_avg_cost)` minus fees if adopted.
- `position_market_value = held_qty * latest_simulated_price`.
- `position_unrealized_pnl = held_qty * (latest_simulated_price - avg_cost)`.
- `portfolio_equity = cash_total + sum(position_market_value)`; reservations are not extra assets. Include mark time to prevent false sense of freshness.
- `net_pnl` needs explicit treatment of wallet credits/deposits; compare portfolio equity to initial virtual capital for simple single-credit MVP.

## 9. Security and privacy
- Hash passwords with Argon2id or bcrypt; environment variables for secrets; no real payment credentials or brokerage tokens.
- Prefer HTTP-only session cookies with CSRF protection, or a secure token flow. Never store admin secrets in commits. Define exact chosen mechanism in [OPEN-21] / [API-TBD-02].
- Role access is enforced on every API call for `TRADER`, `ADMIN` and `MARKET_OPERATOR`; data filtered by authenticated user, not arbitrary client-sent user_id. No shared admin/operator credentials.
- Input validation, decimal parsing, SQLAlchemy parameterization, pagination, rate limiting for login; secure error logging.
- Simulated financial platform: prominently show **Virtual Funds • Simulated Prices • No Real Orders** in UI.
- Audit log is *application-level append-only*, not cryptographic immutability.

## 10. UX screens / navigation
1. Landing + login/signup.
2. Trader overview: cash/portfolio/P&L, alerts, watchlist.
3. Market: stock table, quotes, price history, order form.
4. Orders: all statuses, details, cancel pending.
5. Portfolio: holdings, average cost, realized/unrealized P&L.
6. Transactions: trade journal with execution time/price, wallet ledger.
7. Notifications: recent order/risk actions.
8. Admin: user directory, stock catalog, aggregate order report and audit viewer.
9. Market Operator: synthetic tick editor, scripted tick runner, market-open/closed control and market overview.

**UI placeholders:** [UI-TBD-01] wireframes and page layout; [UI-TBD-02] accessibility and responsive behavior; [UI-TBD-03] brand palette; [UI-TBD-04] screenshots to insert after implementation.

## 11. Test plan and sample IDs
| Test ID | Scenario | Expected |
|---|---|---|
| IT-AUTH-01/02 | Register, duplicate email, login, protected endpoint | Valid accounts, proper access control |
| IT-MKT-01/02/03 | Admin stock creation; Market Operator tick history and session toggle | Unique symbols, persisted timestamps, blocked trading when closed |
| IT-WAL-01/02 | Initialize wallet, view ledger | Exactly one initial credit; consistent available cash |
| IT-ORD-01 | Market buy and sell | Order FILLED with corresponding trade |
| IT-ORD-02 | Limit order creation | PENDING, reservation present |
| IT-ORD-03 | Quote crosses threshold | Exactly one fill, reservations released |
| IT-ORD-04 | Cancel pending twice | First releases; second no additional change |
| IT-ORD-05 | Filter order history | Only own matching results |
| IT-RISK-01 | Oversell, insufficient funds, invalid qty | Rejected without side effects |
| IT-TRADE-01/02 | Execution journal and forced DB fault | Correct immutable record / full rollback |
| IT-PORT-01 | Buy twice at different prices then sell | Correct average cost and realized P&L |
| IT-WATCH-01 | Add same stock twice | One membership; user isolation |
| IT-ANA-01 | Portfolio totals | Numerically consistent with transactions |
| IT-NOTIF-01 | Execute/cancel order | Notification created once, correct recipient |
| IT-AUD-01 | Run trade and Market Operator tick | Append-only audit entries with actor and entity |
| IT-ADM-01 | Trader tries admin routes | Forbidden |
| IT-CONC-01 | Same idempotency key/repeated tick | One debit, one trade only |

**[TEST-TBD-01]** Replace these planned expectations with executed test cases, pass/fail evidence, commit hash, environment and screenshots after coding. Experiment 11 must report *results*, not only intentions.

## 12. Design traceability + unresolved technical choices
- Architecture uses modules -> Component Diagram `D09` and Deployment Diagram `D10`.
- `orders/trades/wallet/holdings` -> ERD `D04`; class/object `D06`, state `D07`, sequence `D08`, tests E11.
- Requirement classification -> FP worksheet E12; scheduled tasks -> Gantt/PERT E13.
- [OPEN-21] Session mechanism: HttpOnly cookie vs JWT bearer (choose during P01).
- [TECH-TBD-01] Exact library versions and lockfiles (record during environment setup).
- [TECH-TBD-02] Decide whether a dedicated background worker is needed or operator tick performs synchronous deterministic processing.
- [TECH-TBD-03] Define seed data (symbol metadata and fixed quote timestamps).
- [TECH-TBD-04] Exact minimum/maximum order quantities and risk threshold defaults.
- [TECH-TBD-05] P&L rounding, price tick precision and fee treatment in unit-tested formula contract.


## 13. Explicit three-role authorization matrix (locked)
| Operation | TRADER | ADMIN | MARKET_OPERATOR |
|---|---|---|---|
| View own orders, wallet, holdings, watchlists | Own only | No implicit access | No implicit access |
| Submit/cancel orders | Own only | No | No |
| Browse simulated stock quotes | Yes | Yes | Yes |
| Create/edit stock catalog or user status | No | Yes | No |
| View redacted audit and aggregate admin reports | No | Yes | No |
| Publish synthetic ticks / change market session | No | No | Yes |
| View market operations status | Read-only public session | Read-only | Yes |

For tests, assert explicit `403` for disallowed role per route, and a distinct ownership check for trader-to-trader requests. [RBAC-TBD-01] Decide whether ADMIN can disable operator accounts (default yes) and how seeding obtains the two privileged accounts (default CLI seed only).

## 14. Locked infrastructure choices
- PostgreSQL is the single authoritative datastore, including CI integration test database; configure by `DATABASE_URL` and keep credentials in `.env` (never committed).
- Use SQLAlchemy with PostgreSQL `NUMERIC`, `TIMESTAMPTZ`, migration-backed `CHECK`/`UNIQUE`/FK constraints, consistent transaction boundaries and atomic settlement.
- Quote source remains `SIMULATED`; market operator inputs and seeded scripted ticks are the only baseline price producers.
- Phase IDs `P00`–`P08` and gates `G00`–`G08` in `implementation.md`; last phase `P08` explicitly closes every as-built documentation placeholder.
