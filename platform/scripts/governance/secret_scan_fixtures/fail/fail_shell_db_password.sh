#!/usr/bin/env bash
# Seeded failure fixture — SAMAPTI-SEC-001 shapes #3 and #4.
#
# Two shell shapes from the same incident that the pre-2026-07-30 pattern set
# missed even where scope permitted:
#
#   #3  DB_PASS="<literal>"      — the variable name `DB_PASS` was absent from
#       the (PGPASSWORD|DB_PASSWORD|DATABASE_PASSWORD) alternation, and
#       `PASS` is not one of (password|passwd|pwd) in the generic pattern.
#       Real occurrence: .../build_orchestrator/scripts/apply_migration.sh:7
#
#   #4  PGPASSWORD="<literal>" psql ...  — the old pattern's value class
#       `[^$[:space:]"']` required the value's FIRST character to be unquoted,
#       so any DOUBLE-QUOTED value slipped straight through.
#       Real occurrence: .../build_orchestrator/scripts/preflight.sh:17
#
# Both credentials below are SYNTHETIC — randomly generated for this fixture on
# 2026-07-30, never used against any system, unrelated to any real credential.
#
# Expected: trips pattern id `env_password_assign` (both lines).

DB_PASS="SYNTH8VGhwWmtSMHVDaTdOZlFyMlhF"

PGPASSWORD="SYNTH5RXBLbndHM3lTdmJEOWNoTUpZ" psql -h 127.0.0.1 -p 5433 \
  -U synthetic_fixture_user -d synthetic_fixture_db -c "SELECT 1;"
