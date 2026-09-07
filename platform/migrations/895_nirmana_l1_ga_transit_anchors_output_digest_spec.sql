-- 895_nirmana_l1_ga_transit_anchors_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 207: `ga_transit_anchors`' orphaned-generation trap (#2224) is
-- resolved (fix #2307 merged and deployed). Closes the fleet-wide `asset_output_digest_specs`
-- gap for `ga_transit_anchors`, authored before its first-ever campaign dispatch.
--
-- Spec design verified against live data before authoring:
--   * `ga_transit_anchors` already carries a genuine DB UNIQUE constraint,
--     `ga_transit_anchors_natural_key (chart_id, ayanamsha_id, graha)` -- no live
--     collision-check reasoning needed, the DB itself enforces this key's uniqueness.
--   * Live-checked (not assumed): 0 NULLs across all 3 key columns for the canonical chart's
--     45 live rows (matches the asset's own target floor 45/45).
--   * `id` (PK, serial) and `build_id` (a per-rebuild identifier despite being TEXT-typed, not
--     UUID) are excluded from `value_columns`. `computed_at` (wall-clock write timestamp)
--     excluded for the same reason.
--   * Every other column is genuine transit-anchor content and is included.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_transit_anchors',
  'b2804f0531934aca3e5a82ed36271288944423a99081e8fefc8d0f97cabf85a0',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"ga_transit_anchors","relation":"ga_transit_anchors","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id","graha"],"value_columns":["chart_id","ayanamsha_id","graha","natal_sign","natal_house_from_moon","natal_degree_absolute"]}]}'::jsonb
);

COMMIT;
