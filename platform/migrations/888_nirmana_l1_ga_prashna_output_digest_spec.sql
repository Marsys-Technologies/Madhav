-- 888_nirmana_l1_ga_prashna_output_digest_spec.sql
--
-- NIRMĀṆA L1 Gaṇita — cycle 194: closes the fleet-wide `asset_output_digest_specs` gap for
-- `ga_prashna`. Target table `ga_prashna_judgment` currently holds 0 rows for the canonical
-- chart (F-E26: dormant by design, R-1 native ruling -- no active build-out, not a bug).
-- `key_columns: [chart_id, ayanamsha_id]` matches the table's own real UNIQUE constraint
-- (`ga_prashna_judgment_chart_id_ayanamsha_id_key`), excluding the unstable serial `id` PK.
-- An empty-set digest is a legitimate, honest result (SS N.6: an honest empty result is
-- reported, never silently substituted) -- this spec exists so a future non-dormant build
-- (if R-1 is ever revisited) has a working digest mechanism already in place, not just to
-- certify the current empty state.

BEGIN;

INSERT INTO asset_output_digest_specs (asset_id, spec_sha256, spec)
VALUES (
  'ga_prashna',
  '641a8bf4f1070cd29231d06b345d918a627d704af609b21cfe32ae00654b2785',
  '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"ga_prashna_judgment","relation":"ga_prashna_judgment","where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"},"key_columns":["chart_id","ayanamsha_id"],"value_columns":["chart_id","ayanamsha_id","question_class","querent_significator","quesited_significator","querent_longitude","quesited_longitude","longitudinal_gap","is_applying","tajik_yoga","judgment_text","fructification_value","fructification_unit","fructification_rule_id","lagna_rashi","classical_citation"]}]}'::jsonb
);

COMMIT;
