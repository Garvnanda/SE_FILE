import sys, secrets, json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from sqlalchemy import select
from app.db import Session
from app.models import User, Stock, PriceTick, MarketSession
from app.main import create_user
from app.trading import lock_market

path = Path(".runtime/demo-accounts.json")
accounts = (
    json.loads(path.read_text())
    if path.exists()
    else {
        role: {"email": email, "password": secrets.token_urlsafe(18)}
        for role, email in [
            ("ADMIN", "admin@example.com"),
            ("MARKET_OPERATOR", "operator@example.com"),
            ("TRADER", "trader@example.com"),
        ]
    }
)
with Session.begin() as db:
    lock_market(db)
    for role, creds in accounts.items():
        if not db.scalar(select(User).where(User.email == creds["email"])):
            create_user(db, creds["email"], creds["password"], role)
    for symbol, name, sector, price in [
        ("DEMO", "Demo Industries", "Industrials", "100"),
        ("NOVA", "Nova Systems", "Technology", "245"),
        ("VERD", "Verdant Energy", "Energy", "180"),
        ("AXIS", "Axis Robotics", "Technology", "325"),
    ]:
        if not db.scalar(select(Stock).where(Stock.symbol == symbol)):
            s = Stock(symbol=symbol, name=name, sector=sector)
            db.add(s)
            db.flush()
            db.add(PriceTick(stock_id=s.id, price=price))
    if not db.scalar(select(MarketSession)):
        db.add(MarketSession(is_open=True))
path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(accounts, indent=2))
print(
    "Seed complete. Local demo credentials: .runtime/demo-accounts.json (not committed)."
)
