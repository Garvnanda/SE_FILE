import os, sys, uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Tests use a separate database, never the demo database.
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://tradesphere:tradesphere@127.0.0.1:54329/tradesphere_test"
)
import pytest
from sqlalchemy import text
from fastapi.testclient import TestClient
from app.main import app, create_user, attempts
from app.db import engine, Session
from app.models import Base, Stock, PriceTick, MarketSession


@pytest.fixture(autouse=True)
def clean():
    with engine.begin() as c:
        for table in reversed(Base.metadata.sorted_tables):
            c.execute(table.delete())
    attempts.clear()
    from app.security import write_throttle

    write_throttle.entries.clear()


@pytest.fixture
def world():
    with Session.begin() as db:
        users = {
            r: create_user(db, r.lower() + "@example.com", "TestPassword123!", r)
            for r in ["TRADER", "ADMIN", "MARKET_OPERATOR"]
        }
        users["OTHER"] = create_user(db, "other@example.com", "TestPassword123!")
        s = Stock(symbol="DEMO", name="Demo", sector="Industrials")
        db.add(s)
        db.flush()
        sid = s.id
        db.add(PriceTick(stock_id=sid, price="100"))
        db.add(MarketSession(is_open=True))
    clients = {}
    for role, u in users.items():
        c = TestClient(app)
        r = c.post(
            "/api/v1/auth/login",
            json={"email": u.email, "password": "TestPassword123!"},
        )
        assert r.status_code == 200, r.text
        c.headers["X-CSRF-Token"] = r.json()["csrf"]
        clients[role] = c
    return clients, sid, users
