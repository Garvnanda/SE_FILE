from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import uuid
import pytest
from sqlalchemy import select, func
from app.db import Session
from app.models import *
from app import trading
from app.main import OrderInput


def order(c, sid, **kw):
    body = {
        "stock_id": sid,
        "side": "BUY",
        "type": "MARKET",
        "quantity": 10,
        "idempotency_key": str(uuid.uuid4()),
    }
    body.update(kw)
    r = c.post("/api/v1/orders", json=body)
    assert r.status_code == 200, r.text
    return r.json()


def tick(c, sid, price):
    r = c.post(
        "/api/v1/operator/ticks",
        json={"stock_id": sid, "price": str(price), "event_key": str(uuid.uuid4())},
    )
    assert r.status_code == 200, r.text
    return r.json()


def wallet(c):
    return c.get("/api/v1/wallet").json()


def test_canonical_demo(world):
    clients, sid, _ = world
    t = clients["TRADER"]
    op = clients["MARKET_OPERATOR"]
    assert order(t, sid)["status"] == "FILLED"
    pending = order(t, sid, type="LIMIT", quantity=5, limit_price="95")
    assert pending["status"] == "PENDING"
    assert Decimal(wallet(t)["cash_reserved"]) == 475
    tick(op, sid, 95)
    sell = order(t, sid, side="SELL", type="LIMIT", quantity=3, limit_price="110")
    assert sell["status"] == "PENDING"
    tick(op, sid, 110)
    p = t.get("/api/v1/portfolio").json()
    h = p["positions"][0]
    assert h["qty"] == 12
    assert Decimal(p["cash"]) == 98855
    assert abs(Decimal(p["realized_pnl"]) - Decimal(35)) < Decimal(".000001")
    assert abs(Decimal(p["unrealized_pnl"]) - Decimal(140)) < Decimal(".000001")
    assert Decimal(p["equity"]) == 100175
    assert len(t.get("/api/v1/trades").json()) == 3
    assert Decimal(wallet(t)["cash_reserved"]) == 0
    assert (
        sum(Decimal(x["amount_signed"]) for x in t.get("/api/v1/wallet/ledger").json())
        == 98855
    )


@pytest.mark.parametrize(
    "role,path,method,body",
    [
        ("TRADER", "/admin/users", "get", None),
        ("MARKET_OPERATOR", "/admin/stocks", "post", {"symbol": "X", "name": "X"}),
        (
            "ADMIN",
            "/operator/ticks",
            "post",
            {"stock_id": 1, "price": "1", "event_key": "12345678"},
        ),
        ("ADMIN", "/wallet", "get", None),
        ("MARKET_OPERATOR", "/orders", "get", None),
    ],
)
def test_role_boundaries(world, role, path, method, body):
    c = world[0][role]
    r = (
        c.get("/api/v1" + path)
        if method == "get"
        else c.post("/api/v1" + path, json=body)
    )
    assert r.status_code == 403


def test_owner_and_csrf_and_logout(world):
    clients, sid, _ = world
    t = clients["TRADER"]
    o = order(t, sid)
    assert clients["OTHER"].get("/api/v1/orders/" + str(o["id"])).status_code == 404
    assert (
        clients["OTHER"].post("/api/v1/orders/" + str(o["id"]) + "/cancel").status_code
        == 404
    )
    saved = t.headers.pop("X-CSRF-Token")
    assert t.post("/api/v1/auth/logout").status_code == 403
    t.headers["X-CSRF-Token"] = saved
    assert t.post("/api/v1/auth/logout").status_code == 200
    assert t.get("/api/v1/wallet").status_code == 401


def test_rejections_and_cancel(world):
    clients, sid, _ = world
    t = clients["TRADER"]
    op = clients["MARKET_OPERATOR"]
    for kw in [
        {"quantity": 1001},
        {"side": "SELL", "quantity": 1},
        {"quantity": 10001},
    ]:
        assert order(t, sid, **kw)["status"] == "REJECTED"
    op.post("/api/v1/operator/market-session", json={"is_open": False})
    assert order(t, sid)["status"] == "REJECTED"
    o = order(t, sid, type="LIMIT", limit_price="95", quantity=5)
    assert Decimal(wallet(t)["cash_reserved"]) == 475
    for _ in range(2):
        assert (
            t.post(f"/api/v1/orders/{o['id']}/cancel").json()["status"] == "CANCELLED"
        )
    assert Decimal(wallet(t)["available"]) == 100000
    op.post("/api/v1/operator/market-session", json={"is_open": True})
    tick(op, sid, 95)
    assert not t.get("/api/v1/trades").json()
    assert len(t.get("/api/v1/notifications").json()) >= 5


def test_immediate_limit_and_reopen(world):
    clients, sid, _ = world
    t = clients["TRADER"]
    op = clients["MARKET_OPERATOR"]
    assert order(t, sid, type="LIMIT", limit_price="105")["status"] == "FILLED"
    op.post("/api/v1/operator/market-session", json={"is_open": False})
    o = order(t, sid, type="LIMIT", limit_price="100")
    assert o["status"] == "PENDING"
    op.post("/api/v1/operator/market-session", json={"is_open": True})
    assert t.get("/api/v1/orders/" + str(o["id"])).json()["status"] == "FILLED"


def test_stale_and_validation(world):
    clients, sid, _ = world
    t = clients["TRADER"]
    with Session.begin() as db:
        q = db.scalar(select(PriceTick))
        q.recorded_at = now() - timedelta(days=2)
    assert order(t, sid)["status"] == "REJECTED"
    for qty in [0, -1, 1.5, True, "3"]:
        assert (
            t.post(
                "/api/v1/orders",
                json={
                    "stock_id": sid,
                    "side": "BUY",
                    "type": "MARKET",
                    "quantity": qty,
                    "idempotency_key": "validate123",
                },
            ).status_code
            == 422
        )


def test_concurrent_duplicate_and_payload_conflict(world):
    clients, sid, users = world
    uid = users["TRADER"].id
    data = OrderInput(
        stock_id=sid,
        side="BUY",
        type="MARKET",
        quantity=10,
        idempotency_key="same-retry-key",
    )

    def submit(_):
        with Session.begin() as db:
            return trading.place(db, db.get(User, uid), data).id

    with ThreadPoolExecutor(max_workers=6) as pool:
        ids = list(pool.map(submit, range(6)))
    assert len(set(ids)) == 1
    assert Decimal(wallet(clients["TRADER"])["cash_total"]) == 99000
    r = clients["TRADER"].post(
        "/api/v1/orders", json={**data.model_dump(mode="json"), "quantity": 11}
    )
    assert r.status_code == 409


def test_cancel_fill_race(world):
    clients, sid, users = world
    t = clients["TRADER"]
    o = order(t, sid, type="LIMIT", limit_price="95")

    def cancel():
        return t.post(f"/api/v1/orders/{o['id']}/cancel").status_code

    def fill():
        return tick(clients["MARKET_OPERATOR"], sid, 95)

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(cancel)
        b = pool.submit(fill)
        assert a.result() in [200, 409]
        b.result()
    final = t.get("/api/v1/orders/" + str(o["id"])).json()
    assert final["status"] in ["FILLED", "CANCELLED"]
    assert Decimal(wallet(t)["cash_reserved"]) == 0
    assert len(t.get("/api/v1/trades").json()) == (
        1 if final["status"] == "FILLED" else 0
    )


def test_forced_rollback(world, monkeypatch):
    clients, sid, users = world

    def fail(*args):
        raise RuntimeError("injected audit failure")

    monkeypatch.setattr(trading, "notify", fail)
    with pytest.raises(RuntimeError):
        with Session.begin() as db:
            trading.place(
                db,
                db.get(User, users["TRADER"].id),
                OrderInput(
                    stock_id=sid,
                    side="BUY",
                    type="MARKET",
                    quantity=10,
                    idempotency_key="rollback-test",
                ),
            )
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(Order)) == 0
        assert db.scalar(select(func.count()).select_from(Trade)) == 0
    assert Decimal(wallet(clients["TRADER"])["cash_total"]) == 100000


def test_watchlist_notifications_admin(world):
    clients, sid, users = world
    t = clients["TRADER"]
    a = clients["ADMIN"]
    wid = t.get("/api/v1/watchlists").json()[0]["id"]
    for _ in range(2):
        assert t.post(f"/api/v1/watchlists/{wid}/items/{sid}").status_code == 200
    assert len(t.get("/api/v1/watchlists").json()[0]["items"]) == 1
    assert (
        clients["OTHER"].delete(f"/api/v1/watchlists/{wid}/items/{sid}").status_code
        == 404
    )
    o = order(t, sid)
    n = t.get("/api/v1/notifications").json()[0]
    assert (
        clients["OTHER"].patch("/api/v1/notifications/" + str(n["id"])).status_code
        == 404
    )
    assert t.patch("/api/v1/notifications/" + str(n["id"])).json()["read_at"]
    assert t.get("/api/v1/orders?symbol=OTHER").json() == []
    assert (
        t.get("/api/v1/orders?symbol=DEMO&side=BUY&status=FILLED").json()[0]["id"]
        == o["id"]
    )
    assert all("password_hash" not in x for x in a.get("/api/v1/admin/users").json())
    assert a.get("/api/v1/admin/audit?action=ORDER_FILLED").json()
    pending = order(t, sid, type="LIMIT", limit_price="90")
    assert (
        a.patch(
            "/api/v1/admin/users/" + str(users["TRADER"].id), json={"active": False}
        ).status_code
        == 200
    )
    assert t.get("/api/v1/wallet").status_code == 403
    with Session() as db:
        assert db.get(Order, pending["id"]).status == "CANCELLED"


def test_registration_credit_once(world):
    c = world[0]["OTHER"]
    body = {"email": "new@example.com", "password": "AnotherPassword123!"}
    assert c.post("/api/v1/auth/register", json=body).status_code == 201
    assert c.post("/api/v1/auth/register", json=body).status_code == 409
    r = c.post("/api/v1/auth/login", json=body)
    c.headers["X-CSRF-Token"] = r.json()["csrf"]
    assert Decimal(wallet(c)["cash_total"]) == 100000
    assert len(c.get("/api/v1/wallet/ledger").json()) == 1


def test_cost_formula():
    assert trading.average_cost(10, Decimal(100), 5, Decimal(95)) == Decimal(
        "98.33333333"
    )


def test_concurrent_distinct_orders_cannot_overspend(world):
    clients, sid, users = world
    uid = users["TRADER"].id

    def submit(i):
        with Session.begin() as db:
            return trading.place(
                db,
                db.get(User, uid),
                OrderInput(
                    stock_id=sid,
                    side="BUY",
                    type="MARKET",
                    quantity=600,
                    idempotency_key=f"distinct-{i}",
                ),
            ).status

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, range(2)))
    assert sorted(results) == ["FILLED", "REJECTED"]
    assert Decimal(wallet(clients["TRADER"])["cash_total"]) == 40000


def test_sell_reservations_and_duplicate_tick(world):
    clients, sid, _ = world
    t = clients["TRADER"]
    op = clients["MARKET_OPERATOR"]
    order(t, sid)
    pending = order(t, sid, side="SELL", type="LIMIT", quantity=7, limit_price="110")
    assert order(t, sid, side="SELL", quantity=4)["status"] == "REJECTED"
    assert t.post(f"/api/v1/orders/{pending['id']}/cancel").status_code == 200
    assert t.get("/api/v1/portfolio").json()["positions"][0]["available_qty"] == 10
    pending = order(t, sid, side="SELL", type="LIMIT", quantity=7, limit_price="110")
    body = {"stock_id": sid, "price": "110", "event_key": "repeat-tick-123"}
    a = op.post("/api/v1/operator/ticks", json=body)
    b = op.post("/api/v1/operator/ticks", json=body)
    assert a.json()["id"] == b.json()["id"]
    assert (
        op.post("/api/v1/operator/ticks", json={**body, "price": "111"}).status_code
        == 409
    )
    assert len(t.get("/api/v1/trades").json()) == 2
    assert t.get("/api/v1/portfolio").json()["positions"][0]["qty"] == 3


def test_catalog_and_disabled_stock(world):
    clients, sid, _ = world
    a = clients["ADMIN"]
    t = clients["TRADER"]
    op = clients["MARKET_OPERATOR"]
    body = {"symbol": "NEW", "name": "New Company", "sector": "Energy"}
    r = a.post("/api/v1/admin/stocks", json=body)
    assert r.status_code == 200
    ident = r.json()["id"]
    assert a.post("/api/v1/admin/stocks", json=body).status_code == 409
    assert (
        a.patch(
            "/api/v1/admin/stocks/" + str(ident), json={**body, "name": "Renamed"}
        ).json()["name"]
        == "Renamed"
    )
    assert order(t, ident)["status"] == "REJECTED"
    assert (
        a.patch(
            "/api/v1/admin/stocks/" + str(sid),
            json={
                "symbol": "DEMO",
                "name": "Demo",
                "sector": "Industrial",
                "active": False,
            },
        ).status_code
        == 200
    )
    assert order(t, sid)["status"] == "REJECTED"
    assert (
        op.post(
            "/api/v1/operator/ticks",
            json={"stock_id": sid, "price": "100", "event_key": "disabled-tick"},
        ).status_code
        == 404
    )


def test_registration_then_immediate_login_commit(world):
    # Browser regression counterpart: auth must not be returned until registration commits.
    c = world[0]["OTHER"]
    body = {"email": "commit@example.com", "password": "CommitPassword123!"}
    assert c.post("/api/v1/auth/register", json=body).status_code == 201
    with Session() as db:
        assert db.scalar(select(User).where(User.email == body["email"])) is not None
    assert c.post("/api/v1/auth/login", json=body).status_code == 200
