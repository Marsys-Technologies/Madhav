#!/usr/bin/env python3
"""
populate_sade_sati.py — Detect and insert Sade Sati cycles for a native.

Reads Saturn longitude from ephemeris_daily (col: sign, planet = 'Saturn'),
groups consecutive days where Saturn occupies the same sign, and identifies
runs covering the native's natal Moon sign ± one adjacent sign.

For Abhisek Mohanty (natal Moon = Aquarius):
  Rising  (severity 0.7) : Saturn in Capricorn
  Peak    (severity 1.0) : Saturn in Aquarius
  Setting (severity 0.7) : Saturn in Pisces

Usage:
  cd platform && python3 scripts/data/populate_sade_sati.py

Requires:
  DATABASE_URL in .env (or environment)
  ephemeris_daily populated with 1900-01-01 to 2100-12-31 Saturn rows

Exit codes:
  0 — success, ≥ 3 rows inserted
  1 — failure or fewer than 3 rows
"""
from __future__ import annotations

import os
import sys
import pathlib
from datetime import date

# Load .env.local if present
_env_path = pathlib.Path(__file__).parent.parent.parent / ".env.local"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set", file=sys.stderr)
    sys.exit(1)

NATIVE_ID = "abhisek_mohanty"
NATAL_MOON_SIGN = "Aquarius"

# Sade Sati phase classification for natal Moon = Aquarius
SADE_SATI_PHASES = {
    "Capricorn": ("rising",  0.7),
    "Aquarius":  ("peak",    1.0),
    "Pisces":    ("setting", 0.7),
}

def fetch_saturn_sign_runs(conn) -> list[tuple[str, date, date]]:
    """
    Return list of (sign, start_date, end_date) for consecutive Saturn sign runs
    in the range 1984-01-01 to 2100-12-31, restricted to Sade Sati signs.
    Uses island-detection SQL (gaps-and-islands via ROW_NUMBER difference).
    """
    signs = tuple(SADE_SATI_PHASES.keys())
    sql = """
        WITH ranked AS (
            SELECT
                date,
                sign,
                ROW_NUMBER() OVER (ORDER BY date) -
                ROW_NUMBER() OVER (PARTITION BY sign ORDER BY date) AS grp
            FROM ephemeris_daily
            WHERE planet = 'Saturn'
              AND sign = ANY(%s)
              AND date >= '1984-01-01'
              AND date <= '2100-12-31'
        )
        SELECT sign, MIN(date)::date AS start_date, MAX(date)::date AS end_date
        FROM ranked
        GROUP BY sign, grp
        ORDER BY start_date
    """
    cur = conn.cursor()
    cur.execute(sql, (list(signs),))
    rows = cur.fetchall()
    cur.close()
    return [(r[0], r[1], r[2]) for r in rows]


def insert_sade_sati_cycles(conn, runs: list[tuple[str, date, date]]) -> int:
    """
    Upsert sade_sati_cycles rows. Uses DELETE+INSERT per (native_id, start_date, saturn_sign)
    for idempotency (no unique constraint defined, so we truncate+reinsert on native_id).
    """
    cur = conn.cursor()
    cur.execute("DELETE FROM sade_sati_cycles WHERE native_id = %s", (NATIVE_ID,))
    deleted = cur.rowcount

    inserted = 0
    for (saturn_sign, start_date, end_date) in runs:
        phase, severity = SADE_SATI_PHASES[saturn_sign]
        cur.execute(
            """
            INSERT INTO sade_sati_cycles
              (native_id, start_date, end_date, phase, moon_sign, saturn_sign,
               severity_weight, computation_source)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (NATIVE_ID, start_date, end_date, phase, NATAL_MOON_SIGN,
             saturn_sign, severity, "ephemeris_daily"),
        )
        inserted += 1

    conn.commit()
    cur.close()
    print(f"Deleted {deleted} existing rows, inserted {inserted} new rows for {NATIVE_ID}.")
    return inserted


def verify_count(conn) -> int:
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM sade_sati_cycles WHERE native_id = %s", (NATIVE_ID,))
    count = cur.fetchone()[0]
    cur.close()
    return count


def main() -> None:
    conn = psycopg2.connect(DATABASE_URL)
    try:
        print(f"Fetching Saturn sign runs from ephemeris_daily for Sade Sati detection...")
        runs = fetch_saturn_sign_runs(conn)
        print(f"Detected {len(runs)} Saturn sign runs in Sade Sati signs (Capricorn/Aquarius/Pisces).")

        if len(runs) == 0:
            print("ERROR: no Saturn sign runs found. Is ephemeris_daily populated?", file=sys.stderr)
            sys.exit(1)

        for (sign, start, end) in runs[:5]:
            print(f"  {sign}: {start} → {end}")
        if len(runs) > 5:
            print(f"  ... and {len(runs) - 5} more")

        inserted = insert_sade_sati_cycles(conn, runs)
        count = verify_count(conn)
        print(f"sade_sati_cycles row count for {NATIVE_ID}: {count}")

        if count < 3:
            print(f"ERROR: expected ≥ 3 rows, got {count}", file=sys.stderr)
            sys.exit(1)

        print("Population complete ✓")
        sys.exit(0)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
