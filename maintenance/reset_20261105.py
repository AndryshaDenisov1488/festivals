"""Explicit, offline data migration: build a fresh DB without changing its source.

Use a verified SQLite backup as --source, never the live database. The generated
DB must be checked before a stopped-service cutover. No messages are sent.
"""
import argparse
import json
import re
import sqlite3
from datetime import date
from pathlib import Path

ID_FLOOR = 1_000_000_000
KEYS = {
    "tournaments": "tournament_id",
    "registrations": "registration_id",
    "registration_cancellations": "cancellation_id",
    "judge_payments": "payment_id",
    "tournament_budgets": "budget_id",
}
TABLES = {*KEYS, "users", "alembic_version"}
MONTHS = {11: "Ноябрь", 12: "Декабрь"}


def build(source: Path, destination: Path, manifest: Path) -> dict:
    if destination.exists():
        raise ValueError("Destination already exists; refusing to overwrite")
    records = json.loads(manifest.read_text(encoding="utf-8"))
    if not records:
        raise ValueError("Empty schedule")
    seen = set()
    for row in records:
        day = date.fromisoformat(row["date"])
        if not date(2026, 11, 10) <= day <= date(2026, 12, 31):
            raise ValueError("Date outside authorized period")
        if len(row["name"].strip()) < 3:
            raise ValueError("Invalid tournament name")
        key = (row["date"], row["name"].strip().casefold())
        if key in seen:
            raise ValueError("Duplicate tournament")
        seen.add(key)

    with sqlite3.connect(source.resolve().as_uri() + "?mode=ro", uri=True) as src:
        if src.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Source integrity check failed")
        schema = src.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
            "ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"
        ).fetchall()
        if {n for t, n, _ in schema if t == "table"} != TABLES:
            raise ValueError("Unexpected schema: review before resetting")
        versions = src.execute("SELECT version_num FROM alembic_version").fetchall()
        if versions != [("0005_payment_reminder_responses",)]:
            raise ValueError("Unexpected Alembic revision")
        for table, key in KEYS.items():
            maximum = src.execute(f'SELECT COALESCE(MAX("{key}"), 0) FROM "{table}"').fetchone()[0]
            if maximum >= ID_FLOOR:
                raise ValueError("Reserved ID range overlaps source")
        try:
            with sqlite3.connect(destination) as dst:
                for kind, name, sql in schema:
                    if kind == "table" and name in KEYS:
                        key = KEYS[name]
                        sql, count = re.subn(
                            rf"\b{key}\s+INTEGER\s+NOT NULL",
                            f"{key} INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT", sql, count=1,
                        )
                        if count != 1:
                            raise ValueError(f"Unexpected primary key definition: {name}")
                        sql, count = re.subn(rf",\s*PRIMARY KEY \({key}\)", "", sql, count=1)
                        if count != 1:
                            raise ValueError(f"Unexpected primary key constraint: {name}")
                    dst.execute(sql)
                dst.executemany("INSERT INTO alembic_version VALUES (?)", versions)
                for table in KEYS:
                    dst.execute("INSERT INTO sqlite_sequence(name, seq) VALUES (?, ?)", (table, ID_FLOOR))
                for row in sorted(records, key=lambda r: (r["date"], r["name"])):
                    day = date.fromisoformat(row["date"])
                    dst.execute("INSERT INTO tournaments(month,date,name) VALUES (?,?,?)",
                                (MONTHS[day.month], day.isoformat(), row["name"].strip()))
                assert dst.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
                assert dst.execute("SELECT COUNT(*) FROM tournaments").fetchone()[0] == len(records)
                assert dst.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                assert not dst.execute("PRAGMA foreign_key_check").fetchall()
        except Exception:
            if destination.exists():
                destination.unlink()
            raise
    return {"tournaments": len(records), "users": 0, "id_floor": ID_FLOOR}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.source, args.destination, args.manifest)))
