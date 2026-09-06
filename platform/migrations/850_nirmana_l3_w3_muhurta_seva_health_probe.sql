-- 850_nirmana_l3_w3_muhurta_seva_health_probe.sql
--
-- RENUMBERED (676 → 850, after intermediate self-inflicted attempts at 843/846
-- were superseded by this rebase): 676 collided with L1's own
-- `676_nirmana_l3_n5_muhurta_seva_depends_on.sql` (an unrelated, already-landed
-- L1 file reusing this number on origin/main) — L1's concurrent migration
-- allocation in this range moves fast enough that a filename-only reservation
-- goes stale between rebases. Renumbered upward per CLAUDE.md's surgical-
-- migration discipline (never allowlist a real collision); 850 chosen to also
-- avoid #2079's already-claimed 848 (ka_dasha_kala) and the merged #2070's 849
-- (ka_tulana) — see L3_STATE.md for the cross-sibling-PR serialization note.
--
-- NIRMĀṆA L3 Kāla — W3. Populates `asset_registry.health_probe` for
-- `ka_muhurta_seva`, the next F-L3-15 slice after `ka_graha_sancara`
-- (migration 671): `health_probe` was NULL, and
-- `requireProbeProvenance`/`normalizeDetectorEvidence`
-- (platform/src/lib/nirmana-elevation/definitions.ts) both hard-require a
-- non-null registry contract before a probe-obligation asset can ever pass
-- `probe_accepted`.
--
-- The contract below is consumed by a NEW, INDEPENDENT probe implementation
-- (`_probe_muhurta_seva`, platform/python-sidecar/pipeline/orchestrator/service_probes.py)
-- and its route allowlist entry (platform/python-sidecar/routers/nirmana_probe.py) —
-- not a reuse of `services/ka_muhurta_seva/writer.py`'s own self-test, per the
-- same implementer != certifier discipline the other three probes already
-- follow. `KaMuhurtaSevaService.score()` is DB-free (composes
-- `panchang_engine.compute_panchang` + `muhurat.finder.score_muhurat`), the
-- same "in-process Python library, no network endpoint" class this probe
-- architecture is built for — unlike `ka_dasha_kala`/`ka_tulana`'s own
-- remaining F-L3-15 gap, which is out of scope here (see the probe module's
-- own comment on why).
--
-- Ground truth computed directly against the FORENSIC birth date/location
-- through this module's own compute_panchang/score_muhurat import path
-- (independently re-derived, not copied from bg_panchanga's already-passing
-- probe): 1984-02-05, lat 20.27, lon 85.84, tz +330min → Tithi = Shukla
-- Tritiya, Nakshatra = Purva Bhadrapada (CLAUDE.md §B FORENSIC anchors,
-- matching `_PANCHANGA_SPEC` in tests/test_service_probes.py). Scoring
-- "vivah" with a native_chart carrying birth_nakshatra_id=25 (Purva
-- Bhadrapada — the FORENSIC anchor) activates the Tara Bala native overlay:
-- score_with_native=33.0 vs score_without_native=28.000000000000004 — a
-- real, non-trivial difference proving the overlay parameter is genuinely
-- read, not silently ignored.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.

UPDATE asset_registry SET health_probe = $hp$
{
  "probe_type": "muhurta_seva_forensic",
  "forensic_date": "1984-02-05",
  "forensic_lat": 20.27,
  "forensic_lon": 85.84,
  "forensic_tz_offset_minutes": 330,
  "forensic_event": "vivah",
  "forensic_birth_nakshatra_id": 25,
  "forensic_expected_tithi": "Shukla Tritiya",
  "forensic_expected_nakshatra": "Purva Bhadrapada",
  "forensic_expected_score_with_native": 33.0,
  "forensic_expected_score_without_native": 28.000000000000004
}
$hp$::jsonb
WHERE asset_id = 'ka_muhurta_seva';
