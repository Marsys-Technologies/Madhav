-- 764_nirmana_l3_w3_tulana_health_probe.sql
--
-- NIRMĀṆA L3 Kāla — W3. Populates `asset_registry.health_probe` for
-- `ka_tulana`, F-L3-15's third slice. Corrects a scoping error made in this
-- migration's own F-L3-15 predecessor (#2065's PR description): ka_tulana was
-- described there as needing live DB access alongside ka_dasha_kala. It does
-- not — `KaTulanaService.rank_windows()`/`.compare()` are PURE ranking logic
-- over already-computed `WindowInput` records the caller supplies ("No DB
-- writes, No commit/rollback" per services/ka_tulana/ranker.py's own module
-- docstring, no `db_conn` anywhere in the class). This is DB-free by
-- construction, the same architecture class the other three probes
-- (bg_panchanga, bg_ephemeris_engine, ka_graha_sancara) are built for.
--
-- `ka_dasha_kala` remains genuinely out of scope: its own
-- `KaDashaKalaService.query()` reads `chart_dashas` through `db_conn` inside
-- `tree_walk.walk_eligible_intervals`, a real architecture question for a
-- future slice (`run_health_probe()` has no `db_conn` parameter).
--
-- NEW MIGRATION RANGE: the previously-assigned 670-679 range is now fully
-- consumed (670-679 all claimed across this session's cycles). This
-- migration opens 764-773 as this session's next self-assigned block — 764
-- confirmed unclaimed via `gh search code`/`gh search` (empty results across
-- both merged content and open-PR titles/bodies) before use, following the
-- same "collision-free by construction" discipline the 670-679 range
-- documented for itself.
--
-- The contract below is consumed by a NEW, INDEPENDENT probe implementation
-- (`_probe_tulana`, platform/python-sidecar/pipeline/orchestrator/service_probes.py)
-- and its route allowlist entry (platform/python-sidecar/routers/nirmana_probe.py) —
-- not a reuse of `services/ka_tulana/writer.py`'s own self-test, per the same
-- implementer != certifier discipline the other three probes already follow.
--
-- Ground truth computed directly against two FIXED, synthetic WindowInput
-- records (not fetched from any real chart) through this module's own
-- KaTulanaService import path: I-11 composite weights (convergence=0.40,
-- rarity=0.25, confidence=0.20, proximity=0.15) applied to
-- window_a(convergence=0.8, rarity_years=15.0, confidence=high,
-- peak=2026-01-01) and window_b(convergence=0.5, rarity_years=5.0,
-- confidence=moderate, peak=2026-06-01), scored against reference_date
-- 2026-01-01, yield composite_a=0.795, composite_b≈0.4234 — window_a wins
-- both rank_windows() and compare(), with compare()'s decisive_factor
-- correctly attributing the win to proximity_factor (the largest per-factor
-- delta between the two windows).
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET health_probe = $hp$
{
  "probe_type": "tulana_ranking_forensic",
  "forensic_reference_date": "2026-01-01",
  "forensic_window_a": {
    "window_id": "test-window-a",
    "mode": "A",
    "peak_date": "2026-01-01",
    "convergence_score": 0.8,
    "confidence_label": "high",
    "rarity_years": 15.0
  },
  "forensic_window_b": {
    "window_id": "test-window-b",
    "mode": "A",
    "peak_date": "2026-06-01",
    "convergence_score": 0.5,
    "confidence_label": "moderate",
    "rarity_years": 5.0
  },
  "forensic_expected_composite_a": 0.795,
  "forensic_expected_composite_b": 0.4234,
  "forensic_expected_winner_window_id": "test-window-a",
  "forensic_expected_decisive_factor": "proximity_factor"
}
$hp$::jsonb
WHERE asset_id = 'ka_tulana';
