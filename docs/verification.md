# Non-functional verification

Observed 2026-11-16. These claims apply to the local prototype and recorded dataset.

| ID | Verification/evidence | Result and limits |
|---|---|---|
| NFR-01 | pytest canonical, overspend, oversell, reservation/cancel and race cases; DB CHECK constraints | Passed; nonnegative available funds/shares enforced |
| NFR-02 | test_forced_rollback | Passed; injected settlement failure leaves no order, trade or wallet debit |
| NFR-03 | role-boundary and owner/CSRF tests; browser separate role sessions | Passed; role 403 and private foreign ID 404 |
| NFR-04 | main.py Argon2 PasswordHasher; generated passwords ignored; session hashes in DB | Implemented; no production credential review claimed |
| NFR-05 | models TIMESTAMPTZ; now() UTC; frontend date() Asia/Kolkata | Implemented and observed in screenshots; object snapshot retains offsets |
| NFR-06 | Persistent UI disclosure, operator/source labels | Visually checked desktop/mobile and both themes |
| NFR-07 | setup.ps1 native installation, migrations, idempotent seed, build | Initial local DB created from empty cluster; setup rerun succeeded. No paid service required. Fresh separate-machine rehearsal not performed |
| NFR-08 | evidence/benchmark.json | 60 sequential authenticated stock-list requests; p95 below 1s. Local sample only; see measured ms in JSON |
| NFR-09 | canonical tick-fill, immediate limit/reopen, repeated tick tests | Passed for test dataset; synchronous execution, no latency/scale guarantee |
| NFR-10 | concurrent same-key orders and duplicate tick tests, UNIQUE constraints | Passed; one resulting fill/debit |
| NFR-11 | No mutation route for audits; browser demo audits readable after API restart | Observed persistence; append-only at API boundary only |
| NFR-12 | revision 0001 downgrade to base, upgrade to head on separate test DB; schema constraints | Passed, followed by 20 passing tests. schema.sql and schema.md record actual model |

TestClient currently emits one upstream Starlette/httpx deprecation warning. It does not change passing assertions. Runtime uses a single process and process-local auth throttling; there is no claim of production security or throughput.

## Source references

Portable PostgreSQL distribution follows [PostgreSQL Windows guidance](https://www.postgresql.org/download/windows/), which links EDB archives. Transaction and lock choices use [SQLAlchemy transaction documentation](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html). These links explain infrastructure choices; executed local evidence is stored alongside this file.
