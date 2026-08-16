"""Production-foundation migration guard for P19.

This is intentionally additive: it does not modify p0_runtime.py or migrations.
It validates that the database reached the P19 head and that the core P10-P19
schema objects exist after a fresh Alembic upgrade.
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys

DB = "partnershub_p19_foundation.db"
EXPECTED_HEAD = "0013_p19_knowledge_base"


def main() -> int:
    subprocess.run(["alembic", "heads"], check=True)
    subprocess.run(["alembic", "current"], check=True)

    conn = sqlite3.connect(DB)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "select name from sqlite_master where type='table'"
            )
        }
        versions = {
            row[0] for row in conn.execute("select version_num from alembic_version")
        }
    finally:
        conn.close()

    required = {
        # P10/P11
        "followup_tasks",
        "renewal_reminders",
        "automation_runs",
        # P12/P13
        "prospect_intelligence",
        "business_reconciliation_snapshots",
        # P14/P15/P16
        "adaptive_agent_targets",
        "priya_ai_sessions",
        "provider_call_audits",
        # P18/P19
        "campaign_runs",
        "knowledge_sources",
        "knowledge_entries",
    }

    missing = sorted(required - tables)
    if missing:
        print("MISSING_TABLES=" + ",".join(missing))
        return 1

    if EXPECTED_HEAD not in versions:
        print("INVALID_ALEMBIC_HEAD=" + ",".join(sorted(versions)))
        return 1

    print("P10-P19 migration schema guard: PASS")
    print("Alembic head: " + EXPECTED_HEAD)
    return 0


if __name__ == "__main__":
    sys.exit(main())
