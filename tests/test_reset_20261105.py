import json
import sqlite3

import pytest

from maintenance.reset_20261105 import ID_FLOOR, KEYS, build


@pytest.fixture
def inputs(tmp_path):
    source = tmp_path / "original.db"
    with sqlite3.connect(source) as db:
        for table, key in KEYS.items():
            if table == "tournaments":
                db.execute(f"CREATE TABLE {table} ({key} INTEGER NOT NULL, month VARCHAR NOT NULL, date DATE NOT NULL, name VARCHAR NOT NULL, PRIMARY KEY ({key}))")
            else:
                db.execute(f"CREATE TABLE {table} ({key} INTEGER NOT NULL, PRIMARY KEY ({key}))")
        db.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY)")
        db.execute("INSERT INTO users VALUES (123)")
        db.execute("INSERT INTO tournaments VALUES (1, 'Ноябрь', '2025-11-10', 'Старый')")
        db.execute("CREATE TABLE alembic_version (version_num VARCHAR PRIMARY KEY)")
        db.execute("INSERT INTO alembic_version VALUES ('0005_payment_reminder_responses')")
    manifest = tmp_path / "schedule.json"
    manifest.write_text(json.dumps([{"date": "2026-11-10", "name": "Морозово"}]), encoding="utf-8")
    return source, tmp_path / "new.db", manifest


def test_source_preserved_and_ids_never_reused(inputs):
    source, destination, manifest = inputs
    original = source.read_bytes()
    build(*inputs)
    assert source.read_bytes() == original
    with sqlite3.connect(destination) as db:
        assert db.execute("SELECT count(*) FROM users").fetchone()[0] == 0
        for table, key in KEYS.items():
            if table == "tournaments":
                first = db.execute(f"SELECT {key} FROM {table}").fetchone()[0]
                insert = "INSERT INTO tournaments(month,date,name) VALUES ('Декабрь','2026-12-01','Тест')"
            else:
                insert = f"INSERT INTO {table} DEFAULT VALUES"
                first = db.execute(insert).lastrowid
            assert first == ID_FLOOR + 1
            db.execute(f"DELETE FROM {table}")
            assert db.execute(insert).lastrowid == ID_FLOOR + 2
        assert not db.execute("PRAGMA foreign_key_check").fetchall()
    with pytest.raises(ValueError, match="already exists"):
        build(*inputs)


def test_refuse_out_of_period_or_duplicate(inputs):
    source, destination, manifest = inputs
    row = {"date": "2026-11-09", "name": "Морозово"}
    manifest.write_text(json.dumps([row]), encoding="utf-8")
    with pytest.raises(ValueError, match="outside"):
        build(*inputs)
    row["date"] = "2026-11-10"
    manifest.write_text(json.dumps([row, row]), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate"):
        build(*inputs)
    assert not destination.exists()
