> **Implementation amendment (2026-11-16):** This file is the original planning baseline, preserved for context. The implemented contract is documented in [decision_log.md](decision_log.md), [as-built.md](as-built.md), [schema.md](schema.md), [openapi.json](openapi.json) and [traceability.csv](traceability.csv). Historical placeholders are reconciled in [placeholder_register.csv](placeholder_register.csv). The user explicitly excluded authoring experiment submissions: [lab-source-guide.md](lab-source-guide.md) supplies material for all 13. No Docker, deployment, student identities or invented sign-offs.

# TradeSphere — Idea, Product Scope, and Master Decisions

> **Status:** Planning baseline v1.1, 16 November 2026. **Product:** educational paper-trading ecosystem, not a broker, stock exchange, investment advisory service, or real-money transaction processor. **Team:** 3 students. **Course:** Software Engineering Lab; all 13 listed experiments are supported. **Canonical baseline:** the four documents in this folder must be updated together when a decision changes.

## 1. Executive concept
TradeSphere is a multi-user **virtual share-trading and portfolio management ecosystem**. A trader registers, receives a virtual INR balance, explores simulated stock quotations, places market/limit orders, manages a watchlist, tracks holdings, and reviews executed transactions, portfolio value, and profit/loss. A distinct MARKET_OPERATOR manages synthetic market quotations and trading sessions, while an ADMIN manages accounts, instruments, access policies and audit reports. A controlled execution engine validates orders and updates reserved funds, trades, wallet ledger, holdings, audit events and notifications consistently.

**Teacher-facing problem statement:** A simple record of bought/sold shares cannot represent the lifecycle of an online trading order, account balances, pending obligations, price movement, risk checks, and historical reporting. TradeSphere implements an integrated educational system for those workflows with transparent execution assumptions and auditable records.

**Value:** realistic software-engineering workflows (not predictions of real market returns); users can see exactly **what stock, how many shares, buy/sell price, execution time, order status, and P&L**. Real market prices are not necessary to demonstrate the workflows.

## 2. Explicit scope boundary
**Level 2 / MVP commitment (must work):**
- Trader registration/login, session/logout; role-protected Admin and Market Operator accounts (F01).
- Admin manages stock listings; Market Operator controls deterministic synthetic price updates and market-open/closed sessions; retain price/time history (F02).
- Virtual INR wallet with initial simulated credit and append-only ledger; available vs reserved funds (F03).
- Market and limit buy/sell orders, validation, reservation, pending order, cancellation, price-triggered execution; **full fills only in MVP**, no user-to-user matching (F04).
- Holdings, trade execution journal, realized/unrealized P&L, transaction history with timestamps and filters (F05).
- Watchlist + favorites (F06), basic charts and account analytics (F07).
- Risk checks: insufficient wallet balance, insufficient unreserved holdings, malformed orders, max quantity, concentration warning/limit as configured (F08).
- Admin portal for managing users, instruments and audit reports; separate Market Operator console for synthetic quotes and trading sessions, each with role-specific authorization (F09).
- Order and risk alerts in-app; auditable critical transitions (F10).
- Automated unit and integration tests with seeded repeatable scenarios (F11).

**Proposed Level 2 optional additions:** daily P&L charts, import/export CSV, richer notifications, leaderboards/social trading, advanced admin reports. These stay **OUT** of the committed MVP unless accepted in the decision register. No social copy-trading requirement silently enters the SRS.

**Excluded:** real brokerage connectivity, exchange execution, NSE/BSE authorization, live real-money wallet, payment gateway, tax filing, loan/margin trading, short selling, derivatives, user-to-user order book/matching, partial fill handling in MVP, prediction/recommendation algorithms, market manipulation detection, high-frequency/ultra-low-latency guarantees.

**Important language:** Synthetic quotes + local execution, *not actual NSE/BSE prices* unless a separately licensed/provider-backed extension is implemented. Avoid using 'real-time live market' to describe mock data.

## 3. Stakeholders and actors
| Actor | Goal | Primary interactions |
|---|---|---|
| Guest | Join platform | Register, login, view public landing |
| Trader | Simulated trading | Browse stocks, watchlists, wallet, orders, holdings, history, P&L |
| Admin | Govern ecosystem | Manage users, symbols, access, reports and audit trail |
| Market Operator | Operate simulated market | Publish synthetic ticks, open/close simulated market, inspect market-status summaries |
| Price Tick Scheduler (system actor) | Produce quotes | Advance synthetic prices if enabled |
| Execution Worker (system actor) | Fill eligible pending orders | Check market state / quote, record fills atomically |
| Notification Service (internal subsystem) | Deliver in-app alerts | Persist executed/cancelled/rejected order notices |

**Not an actor in MVP:** external exchange/broker. Three distinct authenticated roles are mandatory: `TRADER`, `ADMIN`, `MARKET_OPERATOR` (decision [OPEN-04], [OPEN-14]).

## 4. Key user stories and acceptance conditions
| Story ID | User story | Observable acceptance |
|---|---|---|
| US-01 | As guest I can register/login | Unique identity, protected endpoints, logout |
| US-02 | As trader I can browse stocks | Symbol, name, quote timestamp, last simulated price |
| US-03 | As trader I can place market buy | Checks funds, executes if market open, updates balances and holdings |
| US-04 | As trader I can place limit buy | Pending above/below quote as appropriate; fills at rule-defined quote when eligible |
| US-05 | As trader I can place market/limit sell | Cannot sell more than available (unreserved) shares |
| US-06 | As trader I can cancel pending | Order terminal; reserved resources released exactly once |
| US-07 | As trader I can inspect past activity | Exact executed price, quantity and UTC timestamp; local display timezone |
| US-08 | As trader I can inspect P&L | Realized and unrealized separated and traceable to trades/quotes |
| US-09 | As trader I can watch symbols | Add/delete watchlist entries without duplicate membership |
| US-10 | As market operator I can change a quote | Price event saved, eligible limit orders evaluated |
| US-11 | As market operator I can close market | No new execution while closed; pending orders retained |
| US-12 | As admin I can audit events | Critical events visible with actor, timestamp and correlated order ID |
| US-13 | As trader I receive alerts | Notification on executed, cancelled or rejected order |
| US-14 | As trader I see safe error responses | Invalid and duplicate requests cannot duplicate wallet deductions |

## 5. System rules (canonical references)
- BR-01: All balances, execution prices, money, average-cost calculations use decimal fixed precision; no binary float for currency.
- BR-02: Only positive whole-share quantities; symbol must be active; quotes must be positive and not stale according to configured policy.
- BR-03: Authentication and ownership checks precede reads or mutations; only ADMIN may modify listings, and only MARKET_OPERATOR may publish synthetic quotes or change sessions.
- BR-04: Buy order **reserves** max needed virtual cash. For a market order compute against current quote + configured simulated fees/slippage; MVP default fees=0 and slippage=0 pending [OPEN-07]. Limit buy reserves `qty × limit_price` (plus any configured fees).
- BR-05: Sell order reserves **units** from available holdings; cannot short sell.
- BR-06: Market orders execute immediately *only if the simulated market is open* and usable quote exists; when closed, reject market orders by default (pending [OPEN-05]).
- BR-07: Limit buy eligible when quote ≤ limit; limit sell eligible when quote ≥ limit; fill at **current synthetic quote** (not worse than limit) with full quantity in MVP.
- BR-08: Orders move through PENDING -> FILLED or CANCELLED; invalid submissions are REJECTED. CREATED/VALIDATED may be recorded as transient states. No partial fills in MVP.
- BR-09: Fill, wallet postings/reserve release, holdings change, order status, trade and audit record commit **in one DB transaction**. On failure, none of these commit.
- BR-10: Cancel must release only outstanding reserved money/shares once; repeated cancellation must not change balances.
- BR-11: Every trade includes order ID, stock, user, side, execution price, shares and timezone-aware `executed_at` persisted in UTC.
- BR-12: Realized P&L uses moving-average cost basis (default; pending [OPEN-08]). Unrealized P&L = held qty × (latest quote − average cost). Define treatment of fees when selected.
- BR-13: Price history append-only at application layer; never overwrite executed-price history to reflect later quotes.
- BR-14: Audit log append-only at API layer; not a claim of tamper-proof storage. Admin cannot edit/delete audit records through application.
- BR-15: Idempotency key recommended for order creation and execution event processing; database unique constraints prevent double fills.
- BR-16: No dividends/corporate actions, market holidays, circuit limits or tax computation in baseline; disclose their exclusion.
- BR-17: Use seeded/demo quotes to guarantee a reproducible end-to-end presentation.

## 6. Demo story (must pass during assessment)
1. Admin lists the fictional symbol `DEMO`; Market Operator opens virtual market and sets its simulated quote to ₹100.
2. Trader A logs in with ₹100,000 starting simulated funds.
3. Trader A buys 10 DEMO shares at simulated ₹100 -> ₹1,000 debit, holding 10; exact time recorded.
4. Trader places limit buy for 5 at ₹95 -> pending; wallet reservation is visible.
5. Market Operator updates quote to ₹95 -> limit buy executes atomically -> holdings 15, reserved cash released, ledger entry created.
6. Trader submits sell limit 3 at ₹110 -> reserved units visible; Market Operator changes quote to ₹110 -> 3 shares sold, P&L computed.
7. Trader opens orders, history, watchlist, holdings and P&L charts; admin shows audit trail.
8. Negative cases: insufficient funds, oversell, market closed, cancel pending, duplicate order retry.

**Note:** Test/demo values are illustrative, *not live stocks or recommendations*.

## 7. Success criteria
- End-to-end user story US-01 through US-14 demonstrated or tracked in explicitly documented deferrals.
- All MVP API workflows implemented and tested; no negative wallet/available shares or duplicate fills.
- DB schema and ERD agree; every sample diagram maps to implemented components or explicitly labeled planned scope.
- 13 lab experiments documented with evidence IDs and references, including testing outcomes and FP assumptions.
- One-command local setup, seeded demo, screenshots, and clean README.

## 8. Open decisions — answer when convenient (defaults allow coding to start)
Write chosen value, date, and owner in each line. A placeholder is not permission to silently omit the feature. Search these IDs across all four files.

| ID | Question | Working default | Decision / date / owner |
|---|---|---|---|
| OPEN-01 | Final name for project? | TradeSphere | **[TBD]** |
| OPEN-02 | Database preference and installation constraints? | PostgreSQL + SQLAlchemy + Alembic, from first migration | **RESOLVED — user, 2026-11-16** |
| OPEN-03 | Frontend preference? | React + Vite + Tailwind | **[TBD]** |
| OPEN-04 | Separate Market Operator from Admin role? | Three distinct authenticated roles: TRADER, ADMIN, MARKET_OPERATOR | **RESOLVED — user, 2026-11-16** |
| OPEN-05 | Market orders outside trading session? | Reject new market orders, retain pending limit orders | **[TBD]** |
| OPEN-06 | Market quotes source? | Fully synthetic, operator-controlled and scripted deterministic ticks; no live exchange data | **RESOLVED — user, 2026-11-16** |
| OPEN-07 | Fees/slippage for simulated trades? | 0 fees, 0 slippage | **[TBD]** |
| OPEN-08 | Cost-basis rule? | Moving weighted-average | **[TBD]** |
| OPEN-09 | Initial wallet funds / currency? | ₹100,000 INR per new trader; no real deposits | **[TBD]** |
| OPEN-10 | Real timestamp/timezone shown? | UTC in DB, Asia/Kolkata in UI | **[TBD]** |
| OPEN-11 | Which experiments teacher expects submitted (minimum 10 / all 13)? | Prepare all 13 | **[TBD]** |
| OPEN-12 | Submission and demo deadline; weekly availability? | No fixed deadline; nine milestone phases P00–P08, effort estimates optional; calendar dates remain unset | **RESOLVED (no deadline) — user, 2026-11-16** |
| OPEN-13 | Team member names / ownership? | Member A backend; B engine; C frontend/tests | **[TBD]** |
| OPEN-14 | Depth of admin and trader permissions? | TRADER: own trading data; ADMIN: users/stocks/audit; MARKET_OPERATOR: quotes/sessions | **RESOLVED — user, 2026-11-16** |
| OPEN-15 | Add notifications beyond in-app? | In-app only | **[TBD]** |
| OPEN-16 | Partial fill feature? | OUT of MVP (schema extensible) | **[TBD]** |
| OPEN-17 | Do we demonstrate multi-user simultaneous ordering? | Basic concurrency test, no exchange matching | **[TBD]** |
| OPEN-18 | Project hosting requirements? | Local Docker optional; presentation uses localhost | **[TBD]** |
| OPEN-19 | Transaction reports export? | Optional, defer unless requested | **[TBD]** |
| OPEN-20 | Real stock symbols vs fully fictional symbols? | Fictional/demo symbols; label synthetic | **[TBD]** |

## 9. Locked decisions and RBAC contract
- **PostgreSQL is mandatory** in local demo and automated integration tests; do not quietly substitute SQLite.
- **Synthetic prices only**; ticks are operator-posted or seeded reproducibly. Never claim market-feed integration.
- **Three roles** are separate login identities. ADMIN controls listing/user governance and audit; MARKET_OPERATOR controls ticks/session; TRADER handles own wallet, orders and portfolio. Implement role-negative tests in G03/G04/G07.
- **No deadline has been set.** Phase numbering is based on dependency gates, not weeks. Gantt calendar start/end remain placeholders until the team chooses actual dates.
- `US-10`, `US-11` now belong to MARKET_OPERATOR; `US-12` belongs to ADMIN.

## 10. Traceability contract
- `Fxx` = feature; `US-xx` = user story; `BR-xx` = invariant; `OPEN-xx` = unresolved decision.
- `FR-xx` and `NFR-xx` = testable requirements in technical.md.
- `Pxx` = implementation phase in implementation.md; `Gxx` = gate.
- `Dxx` = diagram in flowcharts.md; `E01–E13` = lab experiment.
- Change management: if a scope decision changes, update all four documents, schema, diagrams, tests, and acceptance checklist; record why.
