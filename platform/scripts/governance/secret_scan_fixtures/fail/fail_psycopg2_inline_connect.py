# Seeded failure fixture — SAMAPTI-SEC-001 shape #1.
#
# This reproduces the EXACT shape of the credential leak that defeated the
# pre-2026-07-30 scanner: an inline database-connection call carrying a literal
# password kwarg, in a file outside the old 8-entry SCAN_TARGETS allowlist.
# Real occurrence: 00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/hard_gates_check.sh:46
#
# The credential below is SYNTHETIC — randomly generated for this fixture on
# 2026-07-30, never used against any system, and unrelated to any real
# credential. It exists only so --self-test can prove the scanner still catches
# this shape. Do NOT replace it with an env read; the point is the literal.
#
# Expected: trips pattern id `quoted_password_kv`.

import psycopg2

conn = psycopg2.connect(
    host="127.0.0.1",
    port=5433,
    user="synthetic_fixture_user",
    password='SYNTH7QmVzd3JmTndKb1BsMHhVYlk4Y2E',
    dbname="synthetic_fixture_db",
)

# Same shape, single-line, comma-separated kwargs (no space after the comma) —
# the boundary case the old `[[:space:];,(]` character class handled only by
# accident.
conn2 = psycopg2.connect(host="127.0.0.1",port=5433,user="synthetic_fixture_user",password='SYNTH2RkhtY3BUeVdxSjNuRHZBNzFzTGc',dbname="synthetic_fixture_db")
