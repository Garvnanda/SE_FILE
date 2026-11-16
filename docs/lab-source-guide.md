# Source guide for the thirteen lab experiments

These are references and preparation instructions, not experiment submissions. Use actual code/evidence to draw and write your own lab material. Do not present historical blueprint placeholders as implemented design.

| Experiment | Project sources | What the student should author |
|---|---|---|
| 1 Problem statement | idea.md historical scope; as-built.md problem/actors; README | Your course-format statement, objectives and boundaries |
| 2 SRS | technical.md FR/NFR baseline; decision_log.md; traceability.csv; openapi.json | SRS in faculty format, accepted scope/assumptions and acceptance criteria |
| 3 DFD and structure chart | as-built.md actor I/O, process/store table, Level-2 flow and function call structure | Balanced context/Level1/Level2 DFDs and structure chart; use data labels |
| 4 ERD/data dictionary | schema.md, schema.sql, models.py, migration 0001 | ERD showing PK/FK, field types and optional participation; explain normalization |
| 5 Use cases | decision_log.md roles; as-built.md actor table; openapi.json routes | Three actors plus guest; application boundary and appropriate include/extend |
| 6 Class/object | models.py, trading.py; evidence/object-snapshot.json | Real ORM classes plus service functions; instance diagram with observed IDs/values |
| 7 State/activity | as-built.md state graph, validation/settlement/cancel flows | State and swimlane activity diagrams, with rollback and rejection distinctions |
| 8 Sequence/collaboration | as-built.md sequence and numbered messages; trading.py | Sequence plus separately numbered communication diagram, including failure path |
| 9 Components | as-built.md module graph; source tree | Logical component diagram of modules actually present (no fictional workers) |
| 10 Deployment | as-built.md physical runtime graph; evidence/environment.json | Windows/browser/Uvicorn/Postgres nodes, ports, protocols; no Docker/cloud |
| 11 Testing | backend/tests; browser-demo.mjs; evidence/pytest.xml and browser JSON/screenshots | Test tables using actual observed outcomes, date/environment; no invented passes |
| 12 Function points | openapi.json; schema.md; FR traceability; below | Identify user-recognizable transactions/logical groups and justify DET/FTR/RET and weights |
| 13 Gantt/PERT | intention.md phase plan; implementation.md historical dependency phases; below | Actual team dates and three-point estimates, dependency network, critical path |

## Function point counting inputs (not a completed count)

User transactions: register/login/logout, submit/cancel order, edit watchlist membership, create named watchlist, mark notice read, admin stock create/edit and user-status change, operator tick/session change. Queries: stocks/history/status, wallet/ledger, orders/trades, watchlists/notices, account directory/audit. Derived outputs: portfolio/P&L and aggregate admin counts. Logical business groups: accounts, market data, portfolio/holdings, wallet/ledger, order/trade lifecycle, watchlists, notifications/audit (justify grouping from user maintenance responsibility). Auth sessions are technical storage, not automatically a separate ILF. No externally maintained data => no assumed market-feed EIF. Count business functions, not raw endpoint/table totals. Faculty's counting method and complexity assessment remain yours.

## Scheduling inputs (not fabricated project history)

Actual agent implementation took place 2026-11-16. No student effort hours, teacher due date or member names were provided. Phase order: scope -> infrastructure/schema -> auth/wallet and market -> trading -> portfolio/reporting -> integrated UI -> QA/docs -> handoff. Auth/wallet and market both feed trading. Draft diagrams may overlap development. Use your actual team calendar for Gantt and your own optimistic/likely/pessimistic estimates for PERT; expected duration=(a+4m+b)/6, variance=((b-a)/6)^2. Do not claim generated software work proves student hours or signed review.

## Evidence conventions

Screenshots show the real local app with synthetic data. Tests use a separate PostgreSQL database. `evidence/manifest.json` identifies source file hashes for reproducibility without inventing a git commit or release tag. Record your final submission commit and reviewer when you actually create/review them.
