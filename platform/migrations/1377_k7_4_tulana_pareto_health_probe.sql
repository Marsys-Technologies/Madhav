-- 1377_k7_4_tulana_pareto_health_probe.sql
-- K7-4 / R-6: replace only Tulana's independent DB-free probe oracle.
-- Allocated by scripts/ci/migration_number_guard.ts --next (1377).
-- ROUTINE-OK: one idempotent registry UPDATE; no DDL or transaction ownership.
-- Existing 849 SQL remains immutable. Probe type and dispatch interface are retained.
UPDATE asset_registry SET health_probe = $hp$
{
  "probe_type": "tulana_ranking_forensic",
  "contract_version": "k7-4:pareto:v1",
  "date_from": "2026-10-13",
  "date_to": "2027-01-11",
  "windows": [
    {
      "chart_id": "fixture",
      "window_id": "A",
      "field_snapshot_id": "fixture",
      "window_start": "2026-10-20",
      "window_end": "2026-11-30",
      "confidence_tier": "structural_prior"
    },
    {
      "chart_id": "fixture",
      "window_id": "B",
      "field_snapshot_id": "fixture",
      "window_start": "2026-11-02",
      "window_end": "2026-11-30",
      "confidence_tier": "concurrent"
    }
  ],
  "expected_order": [
    "B",
    "A"
  ],
  "expected_front": [
    "A",
    "B"
  ],
  "expected_relation": "incomparable",
  "expected_reason": "unavailable",
  "expected_axes": {
    "nearest": "A_better",
    "strongest": "unavailable",
    "most_robust": "B_better"
  }
}
$hp$::jsonb
WHERE asset_id = 'ka_tulana';
