import React, { useState, useEffect } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  ChartNoAxesCombined,
  Wallet,
  Layers,
  ListOrdered,
  Star,
  Bell,
  Shield,
  Radio,
  Sun,
  Moon,
  LogOut,
  ArrowUpRight,
  RefreshCw,
} from "lucide-react";
import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "./style.css";

type Row = Record<string, any>;
let csrf = "";
async function api(path: string, method = "GET", body?: unknown) {
  const r = await fetch("/api/v1" + path, {
    method,
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await r.json();
  if (!r.ok)
    throw Error(
      data.error?.message ||
        data.detail?.map?.((e: Row) => e.msg).join("; ") ||
        "Request failed. Please try again.",
    );
  return data;
}
const money = (v: unknown) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(v || 0));
const date = (v: unknown) =>
  v
    ? new Date(String(v)).toLocaleString("en-IN", {
        timeZone: "Asia/Kolkata",
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "—";
const key = () => crypto.randomUUID();
function Badge({ value }: { value: string }) {
  return (
    <span className={"badge " + value.toLowerCase()}>
      {value.replaceAll("_", " ")}
    </span>
  );
}
function Table({
  rows,
  columns,
  empty = "No records yet.",
}: {
  rows: Row[];
  columns: [string, string, ((r: Row) => React.ReactNode)?][];
  empty?: string;
}) {
  return rows.length ? (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map(([k, label]) => (
              <th key={k}>{label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.id || i}>
              {columns.map(([k, , render]) => (
                <td key={k}>{render ? render(r) : String(r[k] ?? "—")}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  ) : (
    <div className="empty">{empty}</div>
  );
}
function Chart({ ticks }: { ticks: Row[] }) {
  const values = [...ticks].reverse().map((t) => Number(t.price));
  if (!values.length)
    return (
      <div className="empty">
        Publish a synthetic quote to start price history.
      </div>
    );
  const low = Math.min(...values),
    high = Math.max(...values),
    range = high - low || 1;
  const points = values
    .map(
      (p, i) =>
        `${30 + (i * 700) / Math.max(values.length - 1, 1)},${170 - ((p - low) * 130) / range}`,
    )
    .join(" ");
  return (
    <div className="chart">
      <div className="chart-labels">
        <span>{money(high)}</span>
        <span>Recent synthetic quotes</span>
      </div>
      <svg
        viewBox="0 0 760 200"
        role="img"
        aria-label={`Synthetic price history, ${values.length} quotes, from ${money(values[0])} to ${money(values.at(-1))}`}
      >
        <path d="M30 40H730 M30 105H730 M30 170H730" className="grid-line" />
        <polyline points={points} fill="none" className="price-line" />
        {values.length === 1 && (
          <circle cx="30" cy="170" r="4" className="price-dot" />
        )}
      </svg>
      <div className="chart-labels">
        <span>{money(low)}</span>
        <span>{values.length} price events · IST</span>
      </div>
    </div>
  );
}
function App() {
  const [user, setUser] = useState<Row | null>(null),
    [boot, setBoot] = useState(true),
    [theme, setTheme] = useState(localStorage.getItem("theme") || "dark"),
    [page, setPage] = useState("Overview"),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [busy, setBusy] = useState(false),
    [data, setData] = useState<Row>({}),
    [stocks, setStocks] = useState<Row[]>([]),
    [market, setMarket] = useState(false),
    [selected, setSelected] = useState(0),
    [ticks, setTicks] = useState<Row[]>([]),
    [filter, setFilter] = useState(""),
    [sideFilter, setSideFilter] = useState(""),
    [statusFilter, setStatusFilter] = useState(""),
    [since, setSince] = useState(""),
    [until, setUntil] = useState(""),
    [offset, setOffset] = useState(0),
    [editingStock, setEditingStock] = useState<Row | null>(null);
  const [authMode, setAuthMode] = useState("login"),
    [orderType, setOrderType] = useState("MARKET"),
    [orderSide, setOrderSide] = useState("BUY"),
    [qty, setQty] = useState("10"),
    [limit, setLimit] = useState("95"),
    [orderKey, setOrderKey] = useState(key()),
    [watchId, setWatchId] = useState(0);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("theme", theme);
  }, [theme]);
  useEffect(() => {
    api("/auth/me")
      .then((d) => {
        csrf = d.csrf;
        setUser(d.user);
        setPage(
          d.user.role === "ADMIN"
            ? "Administration"
            : d.user.role === "MARKET_OPERATOR"
              ? "Market operations"
              : "Overview",
        );
      })
      .catch(() => {})
      .finally(() => setBoot(false));
  }, []);
  const isTrader = user?.role === "TRADER",
    isAdmin = user?.role === "ADMIN";
  const nav = isTrader
    ? [
        "Overview",
        "Market",
        "Orders",
        "Portfolio",
        "Transactions",
        "Watchlists",
        "Notifications",
      ]
    : isAdmin
      ? ["Administration", "Instruments", "Users", "Audit trail"]
      : ["Market operations", "Market"];
  async function refresh() {
    if (!user) return;
    const [s, m] = await Promise.all([api("/stocks"), api("/market-status")]);
    setStocks(s);
    setMarket(m.is_open);
    if (!selected && s.length) setSelected(s[0].id);
    let d: Row = {};
    const params = new URLSearchParams({ limit: "50", offset: String(offset) });
    if (filter) params.set("symbol", filter.toUpperCase());
    if (sideFilter) params.set("side", sideFilter);
    if (statusFilter) params.set("status", statusFilter);
    if (since)
      params.set("since", new Date(since + "T00:00:00+05:30").toISOString());
    if (until)
      params.set("until", new Date(until + "T23:59:59+05:30").toISOString());
    if (isTrader) {
      const [p, w, wl] = await Promise.all([
        api("/portfolio"),
        api("/wallet"),
        api("/watchlists"),
      ]);
      d = { portfolio: p, wallet: w, watchlists: wl };
      if (!watchId && wl.length) setWatchId(wl[0].id);
      if (page === "Orders" || page === "Overview")
        d.orders = await api("/orders?" + params);
      if (page === "Transactions") {
        d.trades = await api("/trades?" + params);
        d.ledger = await api("/wallet/ledger?limit=50&offset=" + offset);
      }
      if (page === "Notifications" || page === "Overview")
        d.notifications = await api("/notifications?limit=50&offset=" + offset);
    } else if (isAdmin) {
      d.summary = await api("/admin/summary");
      if (page === "Instruments") d.instruments = await api("/admin/stocks");
      if (page === "Users")
        d.users = await api("/admin/users?limit=50&offset=" + offset);
      if (page === "Audit trail")
        d.audit = await api(
          "/admin/audit?limit=50&offset=" +
            offset +
            "&action=" +
            encodeURIComponent(filter),
        );
    }
    setData(d);
  }
  useEffect(() => {
    refresh().catch((e) => setError(e.message));
  }, [user, page, offset, filter, sideFilter, statusFilter, since, until]);
  useEffect(() => {
    const s = stocks.find((s) => s.id === selected);
    if (s)
      api("/stocks/" + s.symbol + "/history")
        .then(setTicks)
        .catch((e) => setError(e.message));
  }, [selected, stocks]);
  async function act(
    fn: () => Promise<unknown>,
    message = "Saved successfully",
  ) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await fn();
      setNotice(message);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const current = stocks.find((s) => s.id === selected),
    p = data.portfolio || {},
    w = data.wallet || {};
  const icons: Record<string, React.ReactNode> = {
    Overview: <Activity />,
    Market: <ChartNoAxesCombined />,
    Orders: <ListOrdered />,
    Portfolio: <Layers />,
    Transactions: <Wallet />,
    Watchlists: <Star />,
    Notifications: <Bell />,
    Administration: <Shield />,
    Instruments: <Layers />,
    Users: <Shield />,
    "Audit trail": <ListOrdered />,
    "Market operations": <Radio />,
  };
  const themeButton = (
    <button
      className="icon-button"
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
    >
      {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
  if (boot) return <main className="loading">Loading your workspace…</main>;
  if (!user)
    return (
      <div className="auth-layout">
        <section className="auth-story">
          <a className="brand" href="#">
            <Activity />
            TradeSphere
          </a>
          <div>
            <h1>
              Understand the market.
              <br />
              <span>
                One virtual trade
                <br />
                at a time.
              </span>
            </h1>
            <p>
              A complete paper-trading workspace. Explore synthetic prices, test
              an order, and see exactly how your portfolio changes.
            </p>
            <div className="auth-facts">
              <span>₹1,00,000 virtual starting funds</span>
              <span>Market & limit orders</span>
              <span>Transparent execution history</span>
            </div>
          </div>
          <small>
            Built for learning. No real money, exchange feed, or brokerage
            connection.
          </small>
        </section>
        <section className="auth-panel">
          <div className="auth-theme">{themeButton}</div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              const f = new FormData(e.currentTarget);
              act(async () => {
                const body = {
                  email: f.get("email"),
                  password: f.get("password"),
                };
                if (authMode === "register")
                  await api("/auth/register", "POST", body);
                const d = await api("/auth/login", "POST", body);
                csrf = d.csrf;
                setUser(d.user);
                setPage(
                  d.user.role === "ADMIN"
                    ? "Administration"
                    : d.user.role === "MARKET_OPERATOR"
                      ? "Market operations"
                      : "Overview",
                );
              }, "Welcome to TradeSphere");
            }}
          >
            <h2>
              {authMode === "login" ? "Welcome back" : "Create your account"}
            </h2>
            <p className="muted">
              {authMode === "login"
                ? "Sign in to your trading workspace."
                : "Start with ₹1,00,000 in virtual funds."}
            </p>
            {error && (
              <div role="alert" className="message error">
                {error}
              </div>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                required
                autoComplete="email"
                placeholder="you@example.com"
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                required
                minLength={10}
                maxLength={128}
                autoComplete={
                  authMode === "login" ? "current-password" : "new-password"
                }
                placeholder="At least 10 characters"
              />
            </label>
            <button className="primary" disabled={busy}>
              {busy
                ? "Please wait…"
                : authMode === "login"
                  ? "Sign in"
                  : "Create account"}
              <ArrowUpRight size={18} />
            </button>
            <p className="auth-switch">
              {authMode === "login"
                ? "New to TradeSphere?"
                : "Already registered?"}{" "}
              <button
                type="button"
                className="text-button"
                onClick={() => {
                  setAuthMode(authMode === "login" ? "register" : "login");
                  setError("");
                }}
              >
                {authMode === "login" ? "Create account" : "Sign in"}
              </button>
            </p>
            <div className="disclosure">
              Virtual funds · Simulated prices · No real orders
            </div>
          </form>
        </section>
      </div>
    );
  const orderColumns: [string, string, ((r: Row) => React.ReactNode)?][] = [
    ["symbol", "Instrument"],
    ["side", "Side", (r) => <Badge value={r.side} />],
    ["order_type", "Type"],
    ["qty", "Shares"],
    [
      "limit_price",
      "Limit",
      (r) => (r.limit_price ? money(r.limit_price) : "Market"),
    ],
    [
      "status",
      "Status",
      (r) => (
        <>
          <Badge value={r.status} />
          {r.rejection_reason && (
            <small className="reason">{r.rejection_reason}</small>
          )}
        </>
      ),
    ],
    ["created_at", "Placed (IST)", (r) => date(r.created_at)],
    [
      "action",
      "",
      (r) =>
        r.status === "PENDING" ? (
          <button
            disabled={busy}
            onClick={() =>
              act(
                () => api(`/orders/${r.id}/cancel`, "POST"),
                "Order cancelled; reservations released",
              )
            }
          >
            Cancel
          </button>
        ) : null,
    ],
  ];
  const pager = (
    <div className="pager">
      <button
        disabled={!offset}
        onClick={() => setOffset(Math.max(0, offset - 50))}
      >
        Previous
      </button>
      <span>
        Records {offset + 1}–{offset + 50}
      </span>
      <button onClick={() => setOffset(offset + 50)}>Next</button>
    </div>
  );
  const filters = (
    <div className="filters">
      <label>
        Symbol
        <input
          value={filter}
          placeholder="All symbols"
          onChange={(e) => {
            setFilter(e.target.value);
            setOffset(0);
          }}
        />
      </label>
      <label>
        Side
        <select
          value={sideFilter}
          onChange={(e) => setSideFilter(e.target.value)}
        >
          <option value="">All sides</option>
          <option>BUY</option>
          <option>SELL</option>
        </select>
      </label>
      {page === "Orders" && (
        <label>
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All statuses</option>
            {["PENDING", "FILLED", "CANCELLED", "REJECTED"].map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        </label>
      )}
      <label>
        From (IST)
        <input
          type="date"
          value={since}
          onChange={(e) => setSince(e.target.value)}
        />
      </label>
      <label>
        To (IST)
        <input
          type="date"
          value={until}
          onChange={(e) => setUntil(e.target.value)}
        />
      </label>
    </div>
  );
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => setPage(nav[0])}>
          <Activity />
          TradeSphere
        </a>
        <div className="workspace-label">
          {isTrader
            ? "Trading workspace"
            : isAdmin
              ? "Governance workspace"
              : "Operator workspace"}
        </div>
        <nav aria-label="Main navigation">
          {nav.map((n) => (
            <button
              key={n}
              className={page === n ? "active" : ""}
              onClick={() => {
                setPage(n);
                setOffset(0);
                setFilter("");
                setError("");
                setNotice("");
              }}
            >
              {icons[n]}
              {n}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="simulation-note">
            <Radio size={18} />
            <div>
              Practice with purpose<small>Every trade here is simulated.</small>
            </div>
          </div>
          <div className="profile">
            <strong>{user.email}</strong>
            <small>{user.role.replaceAll("_", " ")}</small>
          </div>
          <button
            onClick={() =>
              act(async () => {
                await api("/auth/logout", "POST");
                setUser(null);
                setWatchId(0);
                setEditingStock(null);
                setOffset(0);
                setData({});
                setSelected(0);
              }, "Signed out")
            }
          >
            <LogOut size={16} />
            Sign out
          </button>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <span className={"market-status " + (market ? "open" : "closed")}>
            <i />
            {market ? "Market open" : "Market closed"}
          </span>
          <span className="top-disclaimer">
            Virtual funds · Simulated prices · No real orders
          </span>
          <div className="top-actions">
            <button
              className="icon-button"
              disabled={busy}
              aria-label="Refresh workspace"
              onClick={() => act(refresh, "Workspace refreshed")}
            >
              <RefreshCw size={17} />
            </button>
            {themeButton}
            <button
              className="icon-button mobile-logout"
              aria-label="Sign out"
              onClick={() =>
                act(async () => {
                  await api("/auth/logout", "POST");
                  setUser(null);
                  setWatchId(0);
                  setEditingStock(null);
                  setOffset(0);
                  setData({});
                  setSelected(0);
                }, "Signed out")
              }
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <h1>{page}</h1>
              <p>
                {page === "Overview"
                  ? "Your portfolio, in perspective."
                  : page === "Market"
                    ? "Explore fictional instruments and place a virtual order."
                    : page === "Market operations"
                      ? "Publish synthetic prices and control the trading session."
                      : "Clear records. Every change accounted for."}
              </p>
            </div>
            {isTrader && page !== "Market" && (
              <button className="primary" onClick={() => setPage("Market")}>
                Place an order
                <ArrowUpRight size={17} />
              </button>
            )}
          </div>
          {error && (
            <div role="alert" className="message error">
              {error}
              <button onClick={() => setError("")}>Dismiss</button>
            </div>
          )}
          {notice && (
            <div role="status" className="message success">
              {notice}
              <button onClick={() => setNotice("")}>Dismiss</button>
            </div>
          )}
          {isTrader && (page === "Overview" || page === "Portfolio") && (
            <>
              <section className="balance-strip">
                <div>
                  <span>Portfolio equity</span>
                  <strong>{money(p.equity)}</strong>
                  <small>Cash + current holdings</small>
                </div>
                <div>
                  <span>Available cash</span>
                  <strong>{money(w.available)}</strong>
                  <small>{money(w.cash_reserved)} reserved</small>
                </div>
                <div>
                  <span>Unrealized P&L</span>
                  <strong
                    className={
                      Number(p.unrealized_pnl) >= 0 ? "positive" : "negative"
                    }
                  >
                    {money(p.unrealized_pnl)}
                  </strong>
                  <small>At latest synthetic quotes</small>
                </div>
                <div>
                  <span>Realized P&L</span>
                  <strong>{money(p.realized_pnl)}</strong>
                  <small>Moving-average cost basis</small>
                </div>
              </section>
              <section className="panel">
                <div className="section-heading">
                  <h2>Your holdings</h2>
                  <span>
                    {p.positions?.filter((h: Row) => h.qty > 0).length || 0}{" "}
                    positions
                  </span>
                </div>
                <Table
                  rows={p.positions || []}
                  empty="Your portfolio starts here. Place a buy order to add your first holding."
                  columns={[
                    ["symbol", "Instrument"],
                    ["qty", "Shares"],
                    ["reserved_qty", "Reserved"],
                    ["avg_cost", "Avg. cost", (r) => money(r.avg_cost)],
                    [
                      "price",
                      "Last quote",
                      (r) => (
                        <>
                          {money(r.price)}
                          {r.stale && <Badge value="STALE" />}
                        </>
                      ),
                    ],
                    [
                      "market_value",
                      "Market value",
                      (r) => money(r.market_value),
                    ],
                    [
                      "unrealized_pnl",
                      "Unrealized P&L",
                      (r) => (
                        <span
                          className={
                            Number(r.unrealized_pnl) >= 0
                              ? "positive"
                              : "negative"
                          }
                        >
                          {money(r.unrealized_pnl)}
                        </span>
                      ),
                    ],
                    [
                      "realized_pnl",
                      "Realized P&L",
                      (r) => money(r.realized_pnl),
                    ],
                  ]}
                />
              </section>
              {page === "Overview" && (
                <section className="panel">
                  <div className="section-heading">
                    <h2>Recent orders</h2>
                    <button
                      className="text-button"
                      onClick={() => setPage("Orders")}
                    >
                      View all orders
                    </button>
                  </div>
                  <Table
                    rows={(data.orders || []).slice(0, 5)}
                    columns={orderColumns}
                  />
                </section>
              )}
            </>
          )}
          {(page === "Market" || page === "Market operations") && (
            <>
              <div className="market-layout">
                <section className="panel market-main">
                  <div className="section-heading">
                    <h2>Instruments</h2>
                    <span>Synthetic market</span>
                  </div>
                  <div className="instrument-tabs">
                    {stocks.map((s) => (
                      <button
                        className={selected === s.id ? "selected" : ""}
                        key={s.id}
                        onClick={() => setSelected(s.id)}
                      >
                        <strong>{s.symbol}</strong>
                        <span>{money(s.quote?.price)}</span>
                      </button>
                    ))}
                  </div>
                  <div className="quote-heading">
                    <div>
                      <h2>{current?.name || "No instruments available"}</h2>
                      <span className="muted">
                        {current?.symbol} · {current?.sector}
                      </span>
                    </div>
                    <div>
                      <strong>{money(current?.quote?.price)}</strong>
                      <small>Updated {date(current?.quote?.recorded_at)}</small>
                    </div>
                  </div>
                  <Chart ticks={ticks} />
                  <div className="quote-footer">
                    Prices are operator-controlled. Orders use the latest valid
                    quote.
                  </div>
                </section>
                {isTrader ? (
                  <section className="panel order-ticket">
                    <h2>Place an order</h2>
                    <p className="muted">{current?.symbol} · Virtual INR</p>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        act(async () => {
                          const o = await api("/orders", "POST", {
                            stock_id: selected,
                            side: orderSide,
                            type: orderType,
                            quantity: Number(qty),
                            limit_price: orderType === "LIMIT" ? limit : null,
                            idempotency_key: orderKey,
                          });
                          setOrderKey(key());
                          if (o.status === "REJECTED")
                            throw Error(o.rejection_reason);
                          setNotice(`Order #${o.id}: ${o.status}`);
                        }, "Order submitted. Check Orders for execution status.");
                      }}
                    >
                      <div className="segmented">
                        {["BUY", "SELL"].map((s) => (
                          <button
                            type="button"
                            key={s}
                            className={orderSide === s ? "selected" : ""}
                            onClick={() => {
                              setOrderSide(s);
                              setOrderKey(key());
                            }}
                          >
                            {s === "BUY" ? "Buy" : "Sell"}
                          </button>
                        ))}
                      </div>
                      <label>
                        Order type
                        <select
                          value={orderType}
                          onChange={(e) => {
                            setOrderType(e.target.value);
                            setOrderKey(key());
                          }}
                        >
                          <option value="MARKET">Market — current quote</option>
                          <option value="LIMIT">Limit — set your price</option>
                        </select>
                      </label>
                      <label>
                        Quantity
                        <input
                          type="number"
                          required
                          min="1"
                          max="10000"
                          step="1"
                          value={qty}
                          onChange={(e) => {
                            setQty(e.target.value);
                            setOrderKey(key());
                          }}
                        />
                      </label>
                      {orderType === "LIMIT" && (
                        <label>
                          Limit price (INR)
                          <input
                            type="number"
                            min="0.0001"
                            step="0.0001"
                            value={limit}
                            required
                            onChange={(e) => {
                              setLimit(e.target.value);
                              setOrderKey(key());
                            }}
                          />
                        </label>
                      )}
                      <dl className="order-summary">
                        <div>
                          <dt>Estimated value</dt>
                          <dd>
                            {money(
                              Number(qty) *
                                (orderType === "LIMIT"
                                  ? Number(limit)
                                  : Number(current?.quote?.price)),
                            )}
                          </dd>
                        </div>
                        <div>
                          <dt>Available cash</dt>
                          <dd>{money(w.available)}</dd>
                        </div>
                        <div>
                          <dt>Fees / slippage</dt>
                          <dd>₹0 / 0%</dd>
                        </div>
                      </dl>
                      <button className="primary" disabled={busy || !current}>
                        {busy
                          ? "Submitting…"
                          : `${orderSide === "BUY" ? "Buy" : "Sell"} ${current?.symbol || "shares"}`}
                      </button>
                      <p className="hint">
                        Full fills only. Limit orders reserve funds or shares
                        until filled or cancelled.
                      </p>
                    </form>
                  </section>
                ) : user.role === "MARKET_OPERATOR" ? (
                  <section className="panel order-ticket">
                    <h2>Market controls</h2>
                    <p className="muted">
                      Session is {market ? "open" : "closed"}.
                    </p>
                    <button
                      disabled={busy}
                      onClick={() =>
                        act(
                          () =>
                            api("/operator/market-session", "POST", {
                              is_open: !market,
                            }),
                          `Market ${market ? "closed" : "opened"}`,
                        )
                      }
                    >
                      {market ? "Close market" : "Open market"}
                    </button>
                    <form
                      onSubmit={(e) => {
                        e.preventDefault();
                        const f = new FormData(e.currentTarget);
                        act(
                          () =>
                            api("/operator/ticks", "POST", {
                              stock_id: selected,
                              price: f.get("price"),
                              event_key: key(),
                            }),
                          "Synthetic quote published; eligible orders evaluated",
                        );
                      }}
                    >
                      <label>
                        New quote for {current?.symbol} (INR)
                        <input
                          name="price"
                          type="number"
                          min="0.0001"
                          step="0.0001"
                          required
                          defaultValue="100"
                        />
                      </label>
                      <button className="primary" disabled={busy || !current}>
                        Publish quote
                      </button>
                    </form>
                    <h3>Demo price steps</h3>
                    <p className="hint">
                      Use each step after the trader places the corresponding
                      order.
                    </p>
                    <div className="demo-steps">
                      {[100, 95, 110].map((v) => (
                        <button
                          key={v}
                          disabled={busy || !current}
                          onClick={() =>
                            act(
                              () =>
                                api("/operator/ticks", "POST", {
                                  stock_id: selected,
                                  price: String(v),
                                  event_key: key(),
                                }),
                              `Published ₹${v}`,
                            )
                          }
                        >
                          ₹{v}
                        </button>
                      ))}
                    </div>
                  </section>
                ) : null}
              </div>
              <section className="panel">
                <div className="section-heading">
                  <h2>Quote history</h2>
                  <span>Latest 100 events</span>
                </div>
                <Table
                  rows={ticks}
                  columns={[
                    ["price", "Price", (r) => money(r.price)],
                    [
                      "recorded_at",
                      "Published (IST)",
                      (r) => date(r.recorded_at),
                    ],
                    ["source", "Source"],
                  ]}
                />
              </section>
            </>
          )}
          {page === "Orders" && (
            <section className="panel">
              {filters}
              <Table rows={data.orders || []} columns={orderColumns} />
              {pager}
            </section>
          )}
          {page === "Transactions" && (
            <>
              <section className="panel">
                <div className="section-heading">
                  <h2>Execution journal</h2>
                </div>
                {filters}
                <Table
                  rows={data.trades || []}
                  columns={[
                    ["symbol", "Instrument"],
                    ["side", "Side", (r) => <Badge value={r.side} />],
                    ["qty", "Shares"],
                    [
                      "execution_price",
                      "Execution price",
                      (r) => money(r.execution_price),
                    ],
                    [
                      "executed_at",
                      "Executed (IST)",
                      (r) => date(r.executed_at),
                    ],
                    ["order_id", "Order ID"],
                  ]}
                />
                {pager}
              </section>
              <section className="panel">
                <div className="section-heading">
                  <h2>Wallet ledger</h2>
                  <span>Posted cash movements</span>
                </div>
                <Table
                  rows={data.ledger || []}
                  columns={[
                    ["event_type", "Event"],
                    ["amount_signed", "Amount", (r) => money(r.amount_signed)],
                    ["order_id", "Order ID"],
                    [
                      "created_at",
                      "Timestamp (IST)",
                      (r) => date(r.created_at),
                    ],
                  ]}
                />
              </section>
            </>
          )}
          {page === "Watchlists" && (
            <section className="panel">
              <div className="section-heading">
                <h2>Your watchlists</h2>
              </div>
              <div className="filters">
                <label>
                  Watchlist
                  <select
                    value={watchId}
                    onChange={(e) => setWatchId(Number(e.target.value))}
                  >
                    {(data.watchlists || []).map((wl: Row) => (
                      <option key={wl.id} value={wl.id}>
                        {wl.name}
                      </option>
                    ))}
                  </select>
                </label>
                <form
                  className="inline-form"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const f = new FormData(e.currentTarget);
                    act(
                      () => api("/watchlists", "POST", { name: f.get("name") }),
                      "Watchlist created",
                    );
                  }}
                >
                  <label>
                    New watchlist
                    <input name="name" required maxLength={80} />
                  </label>
                  <button disabled={busy}>Create</button>
                </form>
              </div>
              <Table
                rows={stocks}
                columns={[
                  ["symbol", "Symbol"],
                  ["name", "Company"],
                  ["sector", "Sector"],
                  [
                    "edit",
                    "Metadata",
                    (r) => (
                      <button onClick={() => setEditingStock(r)}>Edit</button>
                    ),
                  ],
                  ["quote", "Last quote", (r) => money(r.quote?.price)],
                  [
                    "action",
                    "Watchlist",
                    (r) => {
                      const saved = data.watchlists
                        ?.find((a: Row) => a.id === watchId)
                        ?.items.some((i: Row) => i.stock_id === r.id);
                      return (
                        <button
                          disabled={busy || !watchId}
                          onClick={() =>
                            act(
                              () =>
                                api(
                                  `/watchlists/${watchId}/items/${r.id}`,
                                  saved ? "DELETE" : "POST",
                                ),
                              saved
                                ? "Removed from watchlist"
                                : "Added to watchlist",
                            )
                          }
                        >
                          {saved ? "Remove" : "Add to watchlist"}
                        </button>
                      );
                    },
                  ],
                ]}
              />
            </section>
          )}
          {page === "Notifications" && (
            <section className="panel">
              <div className="section-heading">
                <h2>Order & risk alerts</h2>
              </div>
              {!data.notifications?.length && (
                <div className="empty">
                  You’re all caught up. Order updates will appear here.
                </div>
              )}
              {data.notifications?.map((n: Row) => (
                <article className="notification" key={n.id}>
                  <Bell size={18} />
                  <div>
                    <h3>
                      {n.title} {!n.read_at && <Badge value="NEW" />}
                    </h3>
                    <p>{n.body}</p>
                    <small>{date(n.created_at)}</small>
                  </div>
                  {!n.read_at && (
                    <button
                      disabled={busy}
                      onClick={() =>
                        act(
                          () => api("/notifications/" + n.id, "PATCH"),
                          "Marked as read",
                        )
                      }
                    >
                      Mark read
                    </button>
                  )}
                </article>
              ))}
              {pager}
            </section>
          )}
          {page === "Administration" && (
            <>
              <section className="balance-strip">
                {Object.entries(data.summary || {}).map(([k, v]) => (
                  <div key={k}>
                    <span>{k.replaceAll("_", " ")}</span>
                    <strong>{String(v)}</strong>
                    <small>Across the simulation</small>
                  </div>
                ))}
              </section>
              <section className="panel admin-intro">
                <Shield size={32} />
                <h2>Keep the workspace accountable.</h2>
                <p>
                  Manage the instrument catalog, enable or disable accounts, and
                  inspect the audit trail. Market operators independently
                  control prices and trading sessions.
                </p>
                <button onClick={() => setPage("Audit trail")}>
                  Open audit trail
                </button>
              </section>
            </>
          )}
          {page === "Instruments" && (
            <section className="panel">
              <div className="section-heading">
                <h2>
                  {editingStock
                    ? `Edit ${editingStock.symbol}`
                    : "Instrument catalog"}
                </h2>
              </div>
              <form
                className="filters"
                key={editingStock?.id || "new"}
                onSubmit={(e) => {
                  e.preventDefault();
                  const f = new FormData(e.currentTarget);
                  act(async () => {
                    await api(
                      editingStock
                        ? `/admin/stocks/${editingStock.id}`
                        : "/admin/stocks",
                      editingStock ? "PATCH" : "POST",
                      {
                        ...Object.fromEntries(f),
                        active: editingStock?.active ?? true,
                      },
                    );
                    setEditingStock(null);
                  }, "Instrument saved");
                }}
              >
                <label>
                  Symbol
                  <input
                    name="symbol"
                    pattern="[A-Z][A-Z0-9]{0,15}"
                    required
                    placeholder="DEMO"
                    defaultValue={editingStock?.symbol || ""}
                  />
                </label>
                <label>
                  Company name
                  <input
                    name="name"
                    required
                    maxLength={100}
                    defaultValue={editingStock?.name || ""}
                  />
                </label>
                <label>
                  Sector
                  <input
                    name="sector"
                    required
                    maxLength={100}
                    defaultValue={editingStock?.sector || ""}
                  />
                </label>
                <button className="primary" disabled={busy}>
                  {editingStock ? "Save changes" : "Add instrument"}
                </button>
                {editingStock && (
                  <button type="button" onClick={() => setEditingStock(null)}>
                    Cancel edit
                  </button>
                )}
              </form>
              <Table
                rows={data.instruments || []}
                columns={[
                  ["symbol", "Symbol"],
                  ["name", "Company"],
                  ["sector", "Sector"],
                  [
                    "edit",
                    "Metadata",
                    (r) => (
                      <button onClick={() => setEditingStock(r)}>Edit</button>
                    ),
                  ],
                  [
                    "active",
                    "Status",
                    (r) => <Badge value={r.active ? "ACTIVE" : "DISABLED"} />,
                  ],
                  [
                    "action",
                    "Action",
                    (r) => (
                      <button
                        disabled={busy}
                        onClick={() =>
                          act(
                            () =>
                              api("/admin/stocks/" + r.id, "PATCH", {
                                symbol: r.symbol,
                                name: r.name,
                                sector: r.sector,
                                active: !r.active,
                              }),
                            "Instrument status updated",
                          )
                        }
                      >
                        {r.active ? "Disable" : "Enable"}
                      </button>
                    ),
                  ],
                ]}
              />
            </section>
          )}
          {page === "Users" && (
            <section className="panel">
              <div className="section-heading">
                <h2>Account directory</h2>
              </div>
              <Table
                rows={data.users || []}
                columns={[
                  ["email", "Email"],
                  ["role", "Role", (r) => <Badge value={r.role} />],
                  [
                    "active",
                    "Status",
                    (r) => (r.active ? "Active" : "Disabled"),
                  ],
                  ["created_at", "Joined (IST)", (r) => date(r.created_at)],
                  [
                    "action",
                    "Action",
                    (r) =>
                      r.role !== "ADMIN" && (
                        <button
                          disabled={busy}
                          onClick={() =>
                            act(
                              () =>
                                api("/admin/users/" + r.id, "PATCH", {
                                  active: !r.active,
                                }),
                              "Account updated",
                            )
                          }
                        >
                          {r.active ? "Disable account" : "Enable account"}
                        </button>
                      ),
                  ],
                ]}
              />
              {pager}
            </section>
          )}
          {page === "Audit trail" && (
            <section className="panel">
              <div className="filters">
                <label>
                  Search action
                  <input
                    placeholder="ORDER_FILLED"
                    value={filter}
                    onChange={(e) => {
                      setFilter(e.target.value);
                      setOffset(0);
                    }}
                  />
                </label>
              </div>
              <Table
                rows={data.audit || []}
                columns={[
                  ["action", "Action"],
                  ["actor_id", "Actor"],
                  ["entity_type", "Entity"],
                  ["entity_id", "Entity ID"],
                  [
                    "after_json",
                    "Recorded detail",
                    (r) => <code>{JSON.stringify(r.after_json)}</code>,
                  ],
                  ["created_at", "Timestamp (IST)", (r) => date(r.created_at)],
                ]}
              />
              {pager}
            </section>
          )}
          <footer>
            TradeSphere · Educational simulation{" "}
            <span>All displayed times: Asia/Kolkata (IST)</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
