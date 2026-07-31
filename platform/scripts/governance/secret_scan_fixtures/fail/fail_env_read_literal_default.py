# Seeded failure fixture — SAMAPTI-SEC-001 shape #6, the PATTERN-AXIS case.
#
# This is the shape that proves the scanner had TWO independent gaps, not one.
#
#   Gap 1 (WHERE it looks): the old scanner read an allowlist of 8 targets, so
#       credentials under 00_ARCHITECTURE/ and platform/migrations/__tests__/
#       were never read at all. Covered by fixtures #1-#5.
#
#   Gap 2 (WHAT it recognises): THIS shape. `platform/scripts/` was ALREADY one
#       of the 8 allowlisted targets — the scanner read the file every run — and
#       still never flagged
#           platform/scripts/governance/v13_production_gate.py:13
#       because the credential is the FALLBACK DEFAULT of an env read:
#           PW = os.environ.get("DB_PASSWORD", "<literal>")
#       The old pattern keyed on a literal `DB_PASSWORD=` assignment; here the
#       variable name is a quoted argument, so nothing matched. Worse, the
#       scanner's env-indirection tolerance forgives any match containing
#       `os.environ` — so even a matching pattern would have been waived.
#       `env_read_literal_default` is therefore exempt from that tolerance.
#
# A file can be inside the scanned set and still hide a live credential. Path
# coverage and shape coverage are orthogonal; both must be proven.
#
# All credentials below are SYNTHETIC — randomly generated for this fixture on
# 2026-07-30, never used against any system, unrelated to any real credential.
#
# Expected: trips pattern id `env_read_literal_default`.

import os

# Python — os.environ.get with a literal fallback (the v13_production_gate shape).
PW = os.environ.get("DB_PASSWORD", "SYNTH6QldMdmpZOHRLc0YyeG5SNGFI")

# Python — os.getenv variant.
TOKEN = os.getenv("SERVICE_AUTH_TOKEN", "SYNTH1WkdyTnBFN3ZNaEwzY1F4YlU")

# The same idea in TypeScript, for the platform/ and platform-mcp/ trees:
#   const pw = process.env.DB_PASSWORD || 'SYNTH9SGtEbjRSeVdxQTJmVnpMNw'
#   const k  = process.env.API_KEY ?? "SYNTH0TWVJeDVuQjhoRnJLM3dQZFM"
JS_EQUIVALENTS = """
const pw = process.env.DB_PASSWORD || 'SYNTH9SGtEbjRSeVdxQTJmVnpMNw'
const k  = process.env.API_KEY ?? "SYNTH0TWVJeDVuQjhoRnJLM3dQZFM"
"""
