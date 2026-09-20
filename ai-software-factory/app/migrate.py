from pathlib import Path
from sqlalchemy import text
from .db import engine

ROOT = Path(__file__).resolve().parent.parent

def apply_migrations():
    migration_dir = ROOT / "db" / "migrations"
    if not migration_dir.exists():
        return
    with engine.begin() as conn:
        for path in sorted(migration_dir.glob("*.sql")):
            sql = path.read_text(encoding="utf-8")
            for statement in (part.strip() for part in sql.split(";")):
                if statement:
                    conn.execute(text(statement))
