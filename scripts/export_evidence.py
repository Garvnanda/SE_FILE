import sys, json, csv, platform, hashlib, time, statistics, re
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, "backend")
from sqlalchemy import select, text
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql
from app.db import Session
from app.models import Base, User, Order, Trade, Portfolio, Wallet, Holding
from app.main import app, row
import httpx

out = Path("docs")
ev = out / "evidence"
(out / "openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
sql = []
md = [
    "# Implemented PostgreSQL schema",
    "",
    "Revision: 0001. Generated from actual ORM mapping. Numeric values are fixed precision; timestamps are timezone-aware. See migration for the frozen DDL.",
    "",
]
for t in Base.metadata.sorted_tables:
    sql.append(str(CreateTable(t).compile(dialect=postgresql.dialect())) + ";")
    for idx in t.indexes:
        sql.append(str(CreateIndex(idx).compile(dialect=postgresql.dialect())) + ";")
    md += [
        "## " + t.name,
        "",
        "| Field | Type | Nullable | Key / references |",
        "|---|---|---|---|",
    ]
    for c in t.columns:
        keys = (["PK"] if c.primary_key else []) + [
            "FK " + str(f.target_fullname) for f in c.foreign_keys
        ]
        md.append(
            f"| {c.name} | {c.type.compile(dialect=postgresql.dialect())} | {c.nullable} | {', '.join(keys)} |"
        )
    md += (
        [
            "",
            "Constraints: "
            + "; ".join(
                str(c) if not hasattr(c, "sqltext") else str(c.sqltext) for c in []
            ),
        ]
        if False
        else [""]
    )
    for constraint in t.constraints:
        if type(constraint).__name__ == "UniqueConstraint":
            md.append(
                "- UNIQUE (" + ", ".join(c.name for c in constraint.columns) + ")"
            )
        if hasattr(constraint, "sqltext"):
            md.append("- CHECK " + str(constraint.sqltext))
    md += [""]
md += ["## Entity relationships", "", "```mermaid", "erDiagram"]
for t in Base.metadata.sorted_tables:
    md.append("  " + t.name + " {")
    for c in t.columns:
        md.append(
            "    "
            + (
                "numeric"
                if "NUMERIC" in str(c.type)
                else "datetime"
                if "DATETIME" in str(c.type)
                else "int"
                if "INTEGER" in str(c.type)
                else "boolean"
                if "BOOLEAN" in str(c.type)
                else "string"
            )
            + " "
            + c.name
            + (" PK" if c.primary_key else " FK" if c.foreign_keys else "")
        )
    md.append("  }")
    for fk in t.foreign_keys:
        md.append(
            "  " + fk.column.table.name + " ||--o{ " + t.name + " : " + fk.parent.name
        )
md += [
    "```",
    "",
    "The generated FK graph shows parent references, not every unique participation rule. User -> portfolio and portfolio -> wallet are unique (0..1 globally); order -> trade is 0..1 by unique order_id. Consult UNIQUE constraints above when drawing the final conceptual ERD.",
]
(out / "schema.md").write_text("\n".join(md), encoding="utf-8")
(out / "schema.sql").write_text("\n".join(sql), encoding="utf-8")
with Session() as db:
    version = db.scalar(text("SELECT version()"))
    u = db.scalar(
        select(User)
        .join(Order, Order.user_id == User.id)
        .where(User.email.like("demo%@example.com"))
        .order_by(User.id.desc())
    )
    if u:
        p = db.scalar(select(Portfolio).where(Portfolio.user_id == u.id))
        w = db.scalar(select(Wallet).where(Wallet.portfolio_id == p.id))
        snap = {
            "user": {"id": u.id, "role": u.role},
            "portfolio": row(p),
            "wallet": row(w),
            "holdings": [
                row(x)
                for x in db.scalars(select(Holding).where(Holding.portfolio_id == p.id))
            ],
            "orders": [
                row(x) for x in db.scalars(select(Order).where(Order.user_id == u.id))
            ],
            "trades": [
                row(x) for x in db.scalars(select(Trade).where(Trade.user_id == u.id))
            ],
        }
        (ev / "object-snapshot.json").write_text(
            json.dumps(snap, indent=2), encoding="utf-8"
        )
(ev / "environment.json").write_text(
    json.dumps(
        {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "postgresql": version,
            "migration": "0001",
            "database": "tradesphere; tests isolated in tradesphere_test",
            "deployment": "localhost only; no Docker",
        },
        indent=2,
    ),
    encoding="utf-8",
)
accounts = json.loads(Path(".runtime/demo-accounts.json").read_text())
with httpx.Client(base_url="http://127.0.0.1:8000") as c:
    r = c.post("/api/v1/auth/login", json=accounts["TRADER"])
    r.raise_for_status()
    times = []
    for _ in range(60):
        start = time.perf_counter()
        r = c.get("/api/v1/stocks")
        r.raise_for_status()
        times.append((time.perf_counter() - start) * 1000)
    (ev / "benchmark.json").write_text(
        json.dumps(
            {
                "endpoint": "GET /api/v1/stocks",
                "requests": 60,
                "dataset": "four seeded instruments, local server",
                "p95_ms": sorted(times)[56],
                "mean_ms": statistics.mean(times),
                "target_ms": 1000,
                "target_met": sorted(times)[56] < 1000,
                "caveat": "Sequential local sample only; not production load test",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
source = {}
for root in ["backend", "frontend/src", "scripts"]:
    for p in Path(root).rglob("*"):
        if (
            p.is_file()
            and "__pycache__" not in str(p)
            and p.suffix in [".py", ".tsx", ".css", ".ps1"]
        ):
            source[str(p).replace("\\", "/")] = hashlib.sha256(
                p.read_bytes()
            ).hexdigest()
(ev / "manifest.json").write_text(
    json.dumps(
        {
            "captured_at": datetime.now(timezone.utc).isoformat(),
            "sha256": source,
            "git_revision_note": "No release commit created by agent; hashes identify observed source",
        },
        indent=2,
    ),
    encoding="utf-8",
)
print(
    "Exported OpenAPI, schema, runtime/object evidence, benchmark and source manifest."
)
