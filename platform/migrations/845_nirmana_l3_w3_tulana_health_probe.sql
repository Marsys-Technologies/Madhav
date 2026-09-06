-- 845_nirmana_l3_w3_tulana_health_probe.sql
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
-- `ka_dasha_kala` remains genuinely out of scope for a DB-free probe (ruled
-- D-CND-34, #2071): its own `KaDashaKalaService.query()` reads `chart_dashas`
-- through `db_conn` inside `tree_walk.walk_eligible_intervals`, and the
-- authenticated `nirmana_probe.py` route has zero DB infrastructure by design
-- — giving it one is a live security-posture decision, not an engineering
-- call. It gets its own DB-free PROXY-check probe (migration 811) instead.
--
-- RENUMBERED 764→810 (this session, same cycle it was first authored):
-- 764 was claimed independently by L2's own 760-779 range
-- (`764_bo_cgm_paths_volume_formula.sql`, merged first) — a genuine cross-
-- lane collision `scripts/ci/migration_number_guard.ts`'s E2 check caught on
-- this PR's own CI (`FAIL [E2 NEW-COLLISION] migration number 764 is claimed
-- 2 times`). Fixed at the root by renumbering to 810 (comfortably above the
-- highest number in use campaign-wide at the time, 802) rather than
-- disclosing/allowlisting the collision — this migration had not been
-- applied anywhere yet, so renumbering is safe (CLAUDE.md's "never edit an
-- applied migration" rule does not apply). The self-assigned-range
-- convention (this session's own 670-679, now 810+) is a coordination
-- courtesy, not a guarantee; the guard is the actual authority.
--
-- RENUMBERED AGAIN 810→842 (next cycle): 810 was independently claimed by
-- L1's own already-merged 810_nirmana_l1_ga_structural_integrity_contract_
-- houcompstrength.sql — another genuine cross-lane collision, same E2 gate.
-- Renumbered to 842 rather than 841 (the guard's own suggestion) because a
-- SIBLING open L3 PR (#2079, ka_dasha_kala's proxy probe) had already claimed
-- 841 for itself on its own branch in the same cycle; picking a distinct
-- number avoids the two PRs colliding with each other once both land.
--
-- RENUMBERED A THIRD TIME 842→845 (next cycle): 842 was independently
-- claimed by L1's own already-merged 842_..._bhava_bala_backfill.sql —
-- another genuine cross-lane collision, same E2 gate. Renumbered to 845
-- rather than the guard's own suggested 844, since sibling PR #2079 had
-- already claimed 844 on its own branch in this same cycle (its own second
-- renumber, 841->844, for the identical reason).
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
