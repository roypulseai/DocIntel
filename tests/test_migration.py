"""Tests for the history vector migration (scripts/migrate_history_vectors.py)."""
import json
import os
import sqlite3
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from scripts.migrate_history_vectors import migrate  # noqa: E402

SCHEMA = """
CREATE TABLE analyses (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name   TEXT NOT NULL,
    source_kind   TEXT NOT NULL,
    created_at    REAL NOT NULL,
    summary       TEXT,
    category      TEXT,
    confidence    REAL,
    sentiment     TEXT,
    entity_count  INTEGER,
    result_json   TEXT NOT NULL,
    vector_store_json TEXT
)
"""


def _make_db(path, rows):
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    for row in rows:
        conn.execute(
            "INSERT INTO analyses (source_name, source_kind, created_at, result_json, vector_store_json)"
            " VALUES (?, ?, ?, ?, ?)",
            row,
        )
    conn.commit()
    conn.close()


def test_migration_rebuilds_null_vector_rows():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        # Two rows of old data where no per-doc vectors were saved (NULL).
        _make_db(
            db,
            [
                ("doc.md", "md", 1.0, json.dumps({"text": "Missing vector row text."}), None),
                ("doc2.md", "md", 1.0, json.dumps({"text": "Also missing vectors."}), None),
            ],
        )

        stats = migrate(db)
        assert stats["failed"] == 0
        assert stats["rebuilt"] == 2

        conn = sqlite3.connect(db)
        rows = conn.execute(
            "SELECT source_name, vector_store_json FROM analyses ORDER BY id"
        ).fetchall()
        conn.close()
        assert len(rows) == 2
        for name, blob in rows:
            data = json.loads(blob)
            assert data["chunks"], f"{name} should have rebuilt chunks"
            assert set(data["sources"]) == {name}, f"{name} should be single-doc"


def test_migration_fails_gracefully_on_missing_text():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        _make_db(db, [("doc.md", "md", 1.0, json.dumps({"text": ""}), None)])
        stats = migrate(db)
        assert stats["skipped"] == 1
        assert stats["failed"] == 0


def test_migration_skips_existing_valid_stores_unless_force():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "test.db")
        _make_db(db, [("doc.md", "md", 1.0, json.dumps({"text": "Some content."}), None)])
        # First run rebuilds the row.
        first = migrate(db)
        assert first["rebuilt"] == 1 and first["skipped"] == 0

        # Second run (default) must skip the now-valid single-doc store.
        second = migrate(db)
        assert second["rebuilt"] == 0 and second["skipped"] == 1

        # Forced run must rebuild even though a store already exists.
        forced = migrate(db, force=True)
        assert forced["rebuilt"] == 1
