-- 811_nirmana_l3_w3_dasha_kala_proxy_probe.sql
--
-- NIRMĀṆA L3 Kāla — W3. Populates `asset_registry.health_probe` for
-- `ka_dasha_kala`, F-L3-15's fourth and final slice.
--
-- Ruled D-CND-34 (#2071, in response to a filed adjudication rather than a
-- unilateral choice): `ka_dasha_kala` cannot get the same DB-free architecture
-- the other three L3 service probes use. `KaDashaKalaService.query()` reads
-- `chart_dashas` through `db_conn` inside `tree_walk.walk_eligible_intervals`,
-- and `run_health_probe()` has no `db_conn` parameter — by design, since the
-- authenticated `nirmana_probe.py` route this dispatches through has zero DB
-- infrastructure today. Adding one would expand that route's security surface
-- for every asset probed through it, a live risk-acceptance decision the
-- ruling holds is never a session's own call (new standing principle,
-- D-CND-34: "closing a coverage gap that would require expanding a live,
-- authenticated, externally-reachable route's security surface is a
-- risk-acceptance decision, not an engineering-coverage decision").
--
-- Ruling: Option (B) — a DB-free PROXY check. Required condition: the probe's
-- own checks must disclose their narrow scope, never imply live-DB
-- correctness was confirmed (§N.8 Earned-Signal Principle). This probe
-- verifies exactly two things: (1) the single canonical implementation
-- (`KaDashaKalaService`, `tree_walk.walk_eligible_intervals`) still imports
-- cleanly, and (2) the documented 7-system constant set
-- (`tree_walk.ALL_DASHA_SYSTEMS`) has not silently drifted — a system
-- renamed, removed, or an 8th one added would fail this. It does NOT verify
-- `chart_dashas` correctness, the tree-walk pruning logic, or anything
-- DB-backed; every check in `_probe_dasha_kala` (service_probes.py) carries
-- an explicit `scope` field saying so.
--
-- The contract below is consumed by a NEW, INDEPENDENT probe implementation
-- (`_probe_dasha_kala`, platform/python-sidecar/pipeline/orchestrator/service_probes.py)
-- and its route allowlist entry (platform/python-sidecar/routers/nirmana_probe.py) —
-- not a reuse of `services/ka_dasha_kala/writer.py`'s own self-test, per the
-- same implementer != certifier discipline the other three probes follow.
--
-- `expected_systems` is the registry-owned contract (not hardcoded in the
-- probe module) — the exact 7-system set service.py's own docstring names:
-- "All 7 systems (vimshottari, yogini, ashtottari, chara_karaka, naisargika,
-- mudda, kalachakra) are queried. KP is a Vimshottari sub-level dimension
-- (kp_sublevel column) -- NOT a standalone system."
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET health_probe = $hp$
{
  "probe_type": "dasha_kala_proxy_integrity",
  "expected_systems": [
    "vimshottari",
    "yogini",
    "ashtottari",
    "chara_karaka",
    "naisargika",
    "mudda",
    "kalachakra"
  ]
}
$hp$::jsonb
WHERE asset_id = 'ka_dasha_kala';
