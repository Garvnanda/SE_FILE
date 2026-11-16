import sys
from pathlib import Path

sys.path.insert(0, "backend")
from app.models import Base
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql

lines = [
    '"""Frozen initial PostgreSQL schema. Do not edit after applying."""',
    "from alembic import op",
    "revision='0001'",
    "down_revision=None",
    "branch_labels=None",
    "depends_on=None",
    "def upgrade():",
]
for t in Base.metadata.sorted_tables:
    lines.append(
        "    op.execute("
        + repr(str(CreateTable(t).compile(dialect=postgresql.dialect())))
        + ")"
    )
    for i in t.indexes:
        lines.append(
            "    op.execute("
            + repr(str(CreateIndex(i).compile(dialect=postgresql.dialect())))
            + ")"
        )
lines.append("def downgrade():")
for t in reversed(Base.metadata.sorted_tables):
    lines.append("    op.drop_table(" + repr(t.name) + ")")
Path("backend/alembic/versions/0001_initial.py").write_text("\n".join(lines) + "\n")
