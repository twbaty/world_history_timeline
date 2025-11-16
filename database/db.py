from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import select, insert, update

from .schema import metadata, battles

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "world.db"

engine: Engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)

# Create tables if missing
metadata.create_all(engine)


def upsert_battle(record: dict):
    """Insert or update a battle record."""
    with engine.begin() as conn:
        existing = conn.execute(
            select(battles).where(battles.c.id == record["id"])
        ).fetchone()

        if existing is None:
            conn.execute(insert(battles).values(record))
            return "insert"

        # If exists, update
        conn.execute(
            update(battles)
            .where(battles.c.id == record["id"])
            .values(record)
        )
        return "update"


def get_battle(qid: str):
    with engine.begin() as conn:
        row = conn.execute(
            select(battles).where(battles.c.id == qid)
        ).fetchone()
        return dict(row) if row else None
