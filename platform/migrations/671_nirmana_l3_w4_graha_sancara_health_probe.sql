-- 671_nirmana_l3_w4_graha_sancara_health_probe.sql
--
-- NIRMĀṆA L3 Kāla — W4 EXECUTE. Populates `asset_registry.health_probe` for
-- `ka_graha_sancara`, the F-L3-15 gap found while attempting this asset's first real
-- Nirmana `probe_accepted` dispatch: `health_probe` was NULL, and
-- `requireProbeProvenance`/`normalizeDetectorEvidence`
-- (platform/src/lib/nirmana-elevation/definitions.ts) both hard-require a non-null
-- registry contract before a probe-obligation asset can ever pass `probe_accepted`.
--
-- The contract below is consumed by a NEW, INDEPENDENT probe implementation
-- (`_probe_graha_sancara`, platform/python-sidecar/pipeline/orchestrator/service_probes.py)
-- and its route allowlist entry (platform/python-sidecar/routers/nirmana_probe.py) —
-- not a reuse of `pipeline/orchestrator/writers/ka_graha_sancara.py`'s own self-test,
-- per the same implementer != certifier discipline the two existing L0 probes
-- (bg_panchanga, bg_ephemeris_engine) already follow. Both call the same canonical
-- `services.ka_graha_sancara.engine.get_ephemeris` surface; this one is invoked fresh
-- by the Nirmana probe route, independent of whatever the writer already recorded
-- into `selftest_detail`.
--
-- `forensic_birth_instant`/`forensic_ayanamsha` drive `get_ephemeris(..., force_live=True)`
-- — the ONLY path that answers a birth-INSTANT question; PATH-A (`ephemeris_daily`) is
-- day-grade (computed at 12:00 UT) and yields the WRONG sign for this exact anchor
-- (L3-W3 M3). `force_live=True` also keeps this probe DB-free (skips the `db_conn` read
-- entirely), matching the "in-process Python library, no network endpoint" class the
-- other two L3-service probes belong to. `forensic_expected_moon_sign` is the FORENSIC
-- anchor from CLAUDE.md §B (Moon = Purva Bhadrapada nakshatra, Aquarius sign) — verified
-- live at the M3 fix: PATH-B gives Moon at 324.4787° sidereal = Aquarius, matching.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET health_probe = $hp$
{
  "probe_type": "graha_sancara_forensic",
  "forensic_birth_instant": "1984-02-05T10:43:00",
  "forensic_ayanamsha": "lahiri",
  "forensic_expected_moon_sign": "Aquarius"
}
$hp$::jsonb
WHERE asset_id = 'ka_graha_sancara';
