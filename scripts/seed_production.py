"""Idempotent production bootstrap. Never writes or prints credentials."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from pydantic import TypeAdapter, EmailStr
from sqlalchemy import select
from app.db import Session
from app.models import User, Stock, PriceTick, MarketSession
from app.main import create_user
from app.trading import lock_market


def bootstrap(db, environ):
    accounts = []
    for role, prefix in [("ADMIN", "ADMIN"), ("MARKET_OPERATOR", "OPERATOR")]:
        email = str(
            TypeAdapter(EmailStr).validate_python(environ.get(prefix + "_EMAIL", ""))
        ).lower()
        password = environ.get(prefix + "_PASSWORD", "")
        if not 16 <= len(password) <= 128:
            raise ValueError("Bootstrap passwords must be 16–128 characters")
        accounts.append((role, email, password))
    if accounts[0][1] == accounts[1][1] or accounts[0][2] == accounts[1][2]:
        raise ValueError("Privileged accounts must have distinct emails and passwords")
    lock_market(db)
    for role, email, password in accounts:
        user = db.scalar(select(User).where(User.email == email))
        if user and user.role != role:
            raise ValueError("Bootstrap email is already assigned to a different role")
        if not user:
            create_user(db, email, password, role)
    for symbol, name, sector, price in [
        ("DEMO", "Demo Industries", "Industrials", "100"),
        ("NOVA", "Nova Systems", "Technology", "245"),
        ("VERD", "Verdant Energy", "Energy", "180"),
        ("AXIS", "Axis Robotics", "Technology", "325"),
    ]:
        if not db.scalar(select(Stock).where(Stock.symbol == symbol)):
            stock = Stock(symbol=symbol, name=name, sector=sector)
            db.add(stock)
            db.flush()
            db.add(PriceTick(stock_id=stock.id, price=price))
    if not db.scalar(select(MarketSession)):
        db.add(MarketSession(is_open=True))


if __name__ == "__main__":
    try:
        with Session.begin() as db:
            bootstrap(db, os.environ)
    except ValueError:
        # Pydantic errors can echo input: never log environment values.
        raise SystemExit(
            "Bootstrap configuration invalid: check privileged emails, distinct 16–128 character passwords, and existing account roles."
        ) from None
    print("Production bootstrap complete; existing accounts/data preserved.")
