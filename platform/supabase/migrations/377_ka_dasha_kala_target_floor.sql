-- Migration 377: set target_floor=0 on ka_dasha_kala
--
-- ka_dasha_kala is a per_chart service writer that runs a self-test and writes
-- 0 data rows by design. Without target_floor=0 the orchestrator's
-- zero_rows_is_complete logic marks it 'dormant' instead of 'lit', which blocks
-- the preflight check when building ka_sangam (READY_STATES = ['lit','service_ok']).
-- The other ka_* services (ka_gochara, ka_graha_sancara, ka_muhurta_seva) are
-- global scope, so they run with chart_id=NULL and are always lit. ka_dasha_kala
-- is per_chart and needs the explicit target_floor=0 declaration.

UPDATE asset_registry
SET target_floor = 0
WHERE asset_id = 'ka_dasha_kala';
