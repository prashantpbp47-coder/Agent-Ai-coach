#!/usr/bin/env python3
"""Deterministic P19 foundation smoke verification.

Runs after migrations and verifies:
- application imports and route registration
- required P19 tables exist
- Alembic is at the P19 head
- P19 health/search endpoints respond without external provider calls

The verifier deliberately normalizes relative SQLite paths before importing
Flask so the SQLAlchemy engine and direct schema inspection use the same DB.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def normalize_database_url() -> tuple[str, Path | None]:
    database_url = os.getenv(
        "DATABASE_URL",
        "sqlite:///partnershub_p19_foundation.db",
    )
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        return database_url, None

    raw = database_url[len(prefix):]
    path = Path(raw)
    if not path.is_absolute():
        path = ROOT / path
        database_url = f"sqlite:///{path}"
        os.environ["DATABASE_URL"] = database_url
    return database_url, path


def main() -> int:
    database_url, db_path = normalize_database_url()
    check(
        db_path is not None,
        f"P19 smoke verifier currently supports SQLite only: {database_url}",
    )
    check(db_path.exists(), f"database not found: {db_path}")

    # Import only after DATABASE_URL has been normalized, because
    # register_foundation() initializes Flask-SQLAlchemy from that setting.
    import p0_runtime

    app = p0_runtime.app
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    for route in ("/api/p19/health", "/api/p19/search"):
        check(
            route in rules or any(r.startswith(route + "/") for r in rules),
            f"missing route: {route}",
        )

    with sqlite3.connect(db_path) as conn:
        tables = {
            row[0]
            for row in conn.execute(
                "select name from sqlite_master where type='table'"
            )
        }
        required = {"knowledge_sources", "knowledge_entries", "alembic_version"}
        check(required <= tables, f"missing tables: {sorted(required - tables)}")

        versions = {
            row[0]
            for row in conn.execute("select version_num from alembic_version")
        }
        check(
            versions == {"0013_p19_knowledge_base"},
            f"unexpected migration versions: {sorted(versions)}",
        )

    # Flask test client avoids external network connections and provider calls.
    with app.test_client() as client:
        health = client.get("/api/p19/health")
        check(
            health.status_code < 500,
            f"P19 health returned {health.status_code}: {health.get_data(as_text=True)}",
        )
        search = client.get("/api/p19/search?q=test")
        check(
            search.status_code < 500,
            f"P19 search returned {search.status_code}: {search.get_data(as_text=True)}",
        )

    print("P19 FOUNDATION VERIFICATION: PASS")
    print("Routes: /api/p19/health, /api/p19/search")
    print("Migration: 0013_p19_knowledge_base")
    print(f"Database: {db_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"P19 FOUNDATION VERIFICATION: FAIL — {exc}", file=sys.stderr)
        raise
