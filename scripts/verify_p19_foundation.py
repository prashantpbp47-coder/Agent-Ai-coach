#!/usr/bin/env python3
"""Deterministic P19 foundation smoke test.

Runs after migrations against the configured DATABASE_URL and verifies:
- application imports and route registration
- required P19 tables exist
- Alembic is at the P19 head
- health/search endpoints are registered and respond without provider calls

This script intentionally does not require real OpenAI/DeepSeek credentials.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sqlite_path(database_url: str) -> str | None:
    prefix = "sqlite:///"
    if database_url.startswith(prefix):
        return database_url[len(prefix):]
    return None


def main() -> int:
    import p0_runtime

    app = p0_runtime.app
    rules = {rule.rule for rule in app.url_map.iter_rules()}
    for route in ("/api/p19/health", "/api/p19/search"):
        check(route in rules or any(r.startswith(route + "/") for r in rules), f"missing route: {route}")

    database_url = os.getenv("DATABASE_URL", "sqlite:///partnershub_p19_foundation.db")
    path = sqlite_path(database_url)
    check(path is not None, f"verification script currently supports SQLite only: {database_url}")
    check(os.path.exists(path), f"database not found: {path}")

    with sqlite3.connect(path) as conn:
        tables = {row[0] for row in conn.execute("select name from sqlite_master where type='table'")}
        required = {"knowledge_sources", "knowledge_entries", "alembic_version"}
        check(required <= tables, f"missing tables: {sorted(required - tables)}")
        versions = {row[0] for row in conn.execute("select version_num from alembic_version")}
        check("0013_p19_knowledge_base" in versions, f"unexpected migration versions: {sorted(versions)}")

    # Flask test client avoids opening external network connections.
    with app.test_client() as client:
        health = client.get("/api/p19/health")
        check(health.status_code < 500, f"P19 health returned {health.status_code}")
        search = client.get("/api/p19/search?q=test")
        check(search.status_code < 500, f"P19 search returned {search.status_code}")

    print("P19 FOUNDATION VERIFICATION: PASS")
    print(f"Routes: /api/p19/health, /api/p19/search")
    print(f"Migration: 0013_p19_knowledge_base")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"P19 FOUNDATION VERIFICATION: FAIL — {exc}", file=sys.stderr)
        raise
