from pathlib import Path
import json, sys

sys.path.insert(0, "backend")
from app.db import Session
from app.models import User
from sqlalchemy import select

p = Path(".runtime/demo-accounts.json")
accounts = json.loads(p.read_text())
with Session.begin() as db:
    for cred in accounts.values():
        u = db.scalar(select(User).where(User.email == cred["email"]))
        cred["email"] = cred["email"].replace("@tradesphere.test", "@example.com")
        if u:
            u.email = cred["email"]
p.write_text(json.dumps(accounts, indent=2))
p = Path("scripts/seed_demo.py")
p.write_text(p.read_text().replace("@tradesphere.test", "@example.com"))
