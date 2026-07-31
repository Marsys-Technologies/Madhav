#!/usr/bin/env python3
"""
build_ephemeris_1900_2150.py — Stream B bulk ephemeris build runner.

Builds 1900-01-01 to 2150-12-31 × 9 bodies = 825,084 rows.
Uses COPY-based bulk insert for speed (~15-30 min expected).

Usage:
    DATABASE_URL=... python3 build_ephemeris_1900_2150.py

Progress is logged every 500 days. Safe to interrupt and restart (idempotent).
"""
import logging
import os
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

if not os.environ.get("DATABASE_URL"):
    raise SystemExit("ERROR: DATABASE_URL env var required (e.g. postgresql://user:pass@127.0.0.1:5433/db via Cloud SQL Auth Proxy)")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brahmagyan.l0_ephemeris import (
    BUILD_END,
    BUILD_START,
    VOLUME_FLOOR,
    build_ephemeris,
    check_volume,
)
from datetime import date

def main():
    t0 = time.time()
    logger.info("=== L0FR Stream B — Ephemeris Bulk Build ===")
    logger.info("Range: %s to %s", BUILD_START, BUILD_END)
    logger.info("Target: %d rows (%d days × 9 bodies)", VOLUME_FLOOR, (BUILD_END - BUILD_START).days + 1)

    # Check current state
    pre = check_volume()
    logger.info("Pre-build: %d rows (status=%s)", pre["actual_rows"], pre["status"])

    if pre["actual_rows"] >= VOLUME_FLOOR:
        logger.info("Volume floor already met. Running final check only.")
        post = check_volume()
        print_summary(post, 0, time.time() - t0)
        return 0

    # Run the build
    logger.info("Starting bulk compute...")
    try:
        result = build_ephemeris(
            start=BUILD_START,
            end=BUILD_END,
            batch_days=500,
        )
        logger.info("Build complete: %d rows inserted in %.1fs", result["rows_inserted"], result["elapsed_seconds"])
    except Exception as exc:
        logger.error("Build failed: %s", exc)
        return 1

    # Final volume check
    post = check_volume()
    elapsed = time.time() - t0
    print_summary(post, result["rows_inserted"], elapsed)

    if post["actual_rows"] >= VOLUME_FLOOR:
        logger.info("✓ VOLUME FLOOR MET: %d >= %d", post["actual_rows"], VOLUME_FLOOR)
        return 0
    else:
        logger.error("✗ VOLUME FLOOR NOT MET: %d < %d", post["actual_rows"], VOLUME_FLOOR)
        return 1


def print_summary(check, inserted, elapsed):
    logger.info("=== FINAL SUMMARY ===")
    logger.info("Total rows: %d", check["actual_rows"])
    logger.info("Floor: %d", check["floor"])
    logger.info("Status: %s", check["status"])
    logger.info("Date range: %s to %s", check.get("date_range", {}).get("min"), check.get("date_range", {}).get("max"))
    logger.info("Birth date check (1984-02-05 Sun): %s", check["birth_date_check"])
    logger.info("Saturn 2050 check: %s", check.get("saturn_2050_check", "N/A"))
    logger.info("Source citation nulls: %d", check["source_citation_check"]["null_count"])
    logger.info("Rows inserted this run: %d", inserted)
    logger.info("Total elapsed: %.1fs", elapsed)


if __name__ == "__main__":
    sys.exit(main())
