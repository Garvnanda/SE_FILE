from pathlib import Path
import importlib.util
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from app.main import app
from app.db import Settings, settings, Session
from app.models import AuthSession, User
from app.security import RateLimit, _hash_slots, hash_password


def test_disabled_sessions_stay_revoked_after_reenable(world):
    clients, _, users = world
    admin, trader = clients["ADMIN"], clients["TRADER"]
    path = "/api/v1/admin/users/" + str(users["TRADER"].id)
    assert admin.patch(path, json={"active": False}).status_code == 200
    assert admin.patch(path, json={"active": True}).status_code == 200
    assert trader.get("/api/v1/wallet").status_code == 401


def test_production_origin_cookie_headers(world, monkeypatch):
    monkeypatch.setattr(settings, "environment", "production")
    monkeypatch.setattr(settings, "cookie_secure", True)
    monkeypatch.setattr(settings, "public_origin", "https://tradesphere.example.com")
    client = TestClient(app, base_url="https://tradesphere.example.com")
    body = {"email": "trader@example.com", "password": "TestPassword123!"}
    assert (
        client.post(
            "/api/v1/auth/login", json=body, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    r = client.post(
        "/api/v1/auth/login", json=body, headers={"Origin": settings.public_origin}
    )
    assert r.status_code == 200
    cookie = r.headers["set-cookie"].lower()
    assert "secure" in cookie and "httponly" in cookie and "samesite=strict" in cookie
    assert r.headers["cache-control"] == "no-store"
    assert "frame-ancestors 'none'" in r.headers["content-security-policy"]
    assert "max-age=" in r.headers["strict-transport-security"]


def test_limits_before_parsing_and_registration_switch(world, monkeypatch):
    client = world[0]["OTHER"]
    assert client.post("/api/v1/auth/register", content="x" * 16385).status_code == 413
    monkeypatch.setattr(settings, "allow_registration", False)
    assert (
        client.post(
            "/api/v1/auth/register",
            json={"email": "closed@example.com", "password": "TestPassword123!"},
        ).status_code
        == 403
    )


def test_rate_limit_bounds_and_hash_slots():
    limiter = RateLimit(2, max_keys=1)
    limiter.check("a")
    limiter.check("a")
    with pytest.raises(Exception) as exc:
        limiter.check("a")
    assert exc.value.status_code == 429
    with pytest.raises(Exception) as exc:
        limiter.check("b")
    assert exc.value.status_code == 429
    assert len(limiter.entries) == 1
    _hash_slots.acquire()
    _hash_slots.acquire()
    try:
        with pytest.raises(Exception) as exc:
            hash_password("StrongPassword123!")
        assert exc.value.status_code == 429
    finally:
        _hash_slots.release()
        _hash_slots.release()


def test_production_settings_fail_closed_and_render_url():
    with pytest.raises(ValueError):
        Settings(_env_file=None, environment="production", cookie_secure=False)
    s = Settings(
        _env_file=None,
        environment="production",
        cookie_secure=True,
        public_origin="https://demo.onrender.com",
        database_url="postgresql://user:password@host/db",
    )
    assert s.database_url.startswith("postgresql+psycopg://")


def test_session_cap(world):
    c = world[0]["OTHER"]
    for _ in range(7):
        assert (
            c.post(
                "/api/v1/auth/login",
                json={"email": "other@example.com", "password": "TestPassword123!"},
            ).status_code
            == 200
        )
    with Session() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(AuthSession)
                .where(AuthSession.user_id == world[2]["OTHER"].id)
            )
            == 5
        )


def test_production_bootstrap_idempotent_and_no_role_escalation(world):
    spec = importlib.util.spec_from_file_location(
        "seed_production",
        Path(__file__).resolve().parents[2] / "scripts/seed_production.py",
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    env = {
        "ADMIN_EMAIL": "newadmin@example.com",
        "ADMIN_PASSWORD": "UniqueAdminPassword123!",
        "OPERATOR_EMAIL": "newoperator@example.com",
        "OPERATOR_PASSWORD": "UniqueOperatorPassword123!",
    }
    with Session.begin() as db:
        module.bootstrap(db, env)
    with Session.begin() as db:
        old = db.scalar(
            select(User).where(User.email == env["ADMIN_EMAIL"])
        ).password_hash
        module.bootstrap(db, env)
        assert (
            db.scalar(
                select(User).where(User.email == env["ADMIN_EMAIL"])
            ).password_hash
            == old
        )
    with pytest.raises(ValueError):
        with Session.begin() as db:
            module.bootstrap(db, {**env, "ADMIN_EMAIL": "trader@example.com"})
