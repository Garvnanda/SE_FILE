# Demonstration walkthrough

Start the app using README. Use three browser profiles or isolated windows: ADMIN, MARKET_OPERATOR and TRADER (a fresh registered trader gives a clean INR 100,000 balance). Private windows in the same browser may share cookies; use separate profiles or different browsers.

1. Admin: inspect Instruments, Users and Audit trail. The seeded DEMO instrument is active; create another fictional instrument if demonstrating catalog creation.
2. Operator: select DEMO; open the market if closed; publish price 100.
3. Trader: Market > DEMO > Buy, Market, quantity 10. Submit. Orders shows FILLED, cash 99,000, holding 10.
4. Trader: Buy, Limit, quantity 5, limit 95. Submit. Order is PENDING; cash reserved 475, available 98,525.
5. Operator: publish 95. Trader refreshes: second order FILLED; cash 98,525, holding 15, average cost 98.33333333.
6. Trader: Sell, Limit, quantity 3, limit 110. Submit. Three shares reserved, twelve available.
7. Operator: publish 110. Trader opens Overview: holding 12, cash 98,855, equity 100,175, realized P&L approximately 35 and unrealized approximately 140. Eight-decimal cost rounding may leave sub-paise residuals; UI rounds to paise.
8. Trader: inspect Transactions, wallet ledger, Notifications and Watchlists. Admin: search ORDER_FILLED in Audit trail.
9. Negative paths: attempt oversell and unaffordable buy; close market and attempt market order; create a pending limit then cancel twice (second stable no-op is covered in API tests).

Every mutation is server-side. Screenshots in evidence show actual local browser renders, not mocks. `frontend/browser-demo.mjs` automates the central scenario with real browser contexts and a new trader. Re-running changes DEMO quotes and creates a trader; it does not wipe data.
