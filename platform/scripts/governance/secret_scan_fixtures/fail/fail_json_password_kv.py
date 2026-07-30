# Seeded failure fixture — SAMAPTI-SEC-001 shape #5.
#
# The migration test shape: a connection-parameter dict with a JSON-style
# "password": "<literal>" entry. Real occurrences:
#   platform/migrations/__tests__/test_mig_124.py  (and 125, 126, 127)
# — all four sit under platform/migrations/, a tree the old 8-entry
# SCAN_TARGETS allowlist never reached.
#
# The credential below is SYNTHETIC — randomly generated for this fixture on
# 2026-07-30, never used against any system, unrelated to any real credential.
#
# Expected: trips pattern id `json_password_kv`.

CONN = {
    "host": "127.0.0.1",
    "port": 5433,
    "user": "synthetic_fixture_user",
    "password": "SYNTH3TmpXcTVoRVlBOGtQdjFiU2Rv",
    "dbname": "synthetic_fixture_db",
}
