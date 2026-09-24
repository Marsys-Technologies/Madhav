-- Migration 1075: bg_ephemeris_engine health probe — degree-level mean-node anchor.
-- L0 repair item 6 (native-authorized, KALA_DELEGATED_DECISIONS_v1_0.md D-E item 6;
-- Kimi K3 desktop review finding [P], KIMI_K3_CLOSE_REVIEW_KSHETRA_v1_0.md §(C)1).
--
-- WHY: migration 624 anchors the MEAN_NODE Rahu check at SIGN level only
-- (expected_mean_node_rahu_sign: 2). At the forensic instant JD 2445735.717361,
-- TRUE node longitude = 50.049248 deg and MEAN node longitude = 49.033044 deg —
-- both fall in sign 2 (Vrishabha), only the pada differs (0.049248 deg / 177.3
-- arcsec past the Rohini pada-4 boundary). A sign-level check therefore PROVABLY
-- CANNOT detect a true-vs-mean node-frame mixup at this instant (CLAUDE.md §N.8:
-- a signal with no code path that could make it read false is null, not green).
-- This migration adds a DEGREE-LEVEL companion check with a tight arcsecond
-- tolerance, alongside (not replacing) the existing sign-level check.
--
-- 624 IS APPLIED and is NEVER edited (CLAUDE.md §N.4). This is a NEW migration
-- that supersedes it by adding fields to the same JSONB health_probe contract;
-- the DO $$ guard below requires the row to already carry 624's own canonical
-- probe/description (word for word) before it will touch anything, so this
-- migration refuses to run out of order or against an unknown contract.
--
-- Companion code change (same PR): platform/python-sidecar/pipeline/orchestrator/
-- service_probes.py — Check 3 (`sidereal_mean_node_rahu_invariant`) now also
-- asserts the degree-level longitude within tolerance, so the new anchor is a
-- real, currently-running detector and not decorative JSON (§N.8).
--
-- Transaction ownership belongs to migrate.ts.

BEGIN;

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  -- Exact values 624 (applied) left the row in — the guard below refuses to run
  -- against anything else, including a row some OTHER migration already moved on.
  prior_canonical_description constant text :=
    'Swiss Ephemeris (pyswisseph) with the pinned SHA-256-verified sepl_18/semo_18/seas_18 corpus for file-backed sidereal planetary positions. Foundation for all computational Jyotish in MARSYS-JIS. Lahiri ayanamsha canonical. MEAN_NODE convention: Rahu (ascending node).';
  prior_canonical_probe constant jsonb := $json$
    {
      "probe_type": "ephemeris_engine",
      "forensic_jd": 2445735.717361111,
      "expected_sun_sign": 10,
      "expected_mean_node_rahu_sign": 2,
      "ayanamsha": "lahiri",
      "node_mode": "mean",
      "allowed_ephemeris_backends": ["swiss_ephemeris_file"],
      "ephemeris_file_sha256": {
        "sepl_18.se1": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
        "semo_18.se1": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
        "seas_18.se1": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2"
      },
      "note": "JD = 1984-02-05 10:43 IST = 05:13 UTC. Sun in Makara; mean-node Rahu in Vrishabha under sidereal Lahiri."
    }
  $json$::jsonb;
  -- New: prior_canonical_probe plus a degree-level anchor. expected_mean_node_
  -- rahu_longitude_deg = 49.033044 (swe.MEAN_NODE, sidereal Lahiri, at the same
  -- forensic_jd 624 already pins), reproduced independently by two sessions to
  -- 6-7 significant figures (this L0 repair session's own brief, Kimi K3's
  -- desktop re-run: "MEAN = 49.033044deg", matching L1's served RAH_MEAN fact
  -- 49.0330441 to 7 s.f.). Tolerance 10 arcsec (0.002778 deg) — MEAN_NODE is an
  -- analytic Swiss Ephemeris computation (no file-backed numerical noise), so
  -- this margin is generous against implementation float precision while still
  -- being roughly 640x tighter than the 177.3 arcsec true-vs-mean separation
  -- this anchor exists to catch.
  canonical_probe constant jsonb :=
    prior_canonical_probe || $json$
    {
      "expected_mean_node_rahu_longitude_deg": 49.033044,
      "mean_node_longitude_tolerance_arcsec": 10
    }
    $json$::jsonb;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry
  WHERE asset_id = 'bg_ephemeris_engine'
  FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.english_description = prior_canonical_description
    AND registry_row.health_probe = prior_canonical_probe
  ) IS NOT TRUE THEN
    RAISE EXCEPTION 'migration 1075 refuses: bg_ephemeris_engine health_probe does not match migration 624''s applied contract (already superseded, or 624 never applied)';
  END IF;

  UPDATE asset_registry
  SET health_probe = canonical_probe
  WHERE asset_id = 'bg_ephemeris_engine';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1075 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_ephemeris_engine'
      AND health_probe = canonical_probe
      AND (health_probe ->> 'expected_mean_node_rahu_longitude_deg')::numeric = 49.033044
      AND (health_probe ->> 'mean_node_longitude_tolerance_arcsec')::numeric = 10
  ) THEN
    RAISE EXCEPTION 'migration 1075 postflight registry mismatch';
  END IF;
END $$;

COMMIT;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT health_probe -> 'expected_mean_node_rahu_longitude_deg' AS deg,
--          health_probe -> 'mean_node_longitude_tolerance_arcsec' AS tol_arcsec
--     FROM asset_registry WHERE asset_id = 'bg_ephemeris_engine';
--   -- expect: deg = 49.033044, tol_arcsec = 10
--
-- DOWN (manual rollback — restores exactly migration 624's contract, no data loss
-- beyond the two added JSON keys):
--   BEGIN;
--   UPDATE asset_registry
--      SET health_probe = health_probe - 'expected_mean_node_rahu_longitude_deg'
--                                       - 'mean_node_longitude_tolerance_arcsec'
--    WHERE asset_id = 'bg_ephemeris_engine';
--   COMMIT;
-- =============================================================================
