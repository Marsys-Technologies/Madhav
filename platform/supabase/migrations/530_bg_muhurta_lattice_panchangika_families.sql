-- Migration 530: bg_muhurta_lattice — widen factor_family for the W4 pāñcāṅgika/lagna families
-- =============================================================================
-- ṢAḌ-DARŚANA Wave W4, Lane R (YAJÑA-SETU), DESIGN RULING R-1
-- (00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/KALA_W4_UPAYA_DESIGN_v1_0.md
--  §3.1, v1.1) — plus registry items 6 and 7, folded into the same lane because they
-- structurally depend on exactly the atoms this migration admits.
--
-- WHAT THIS CHANGES, AND WHY IT IS NOT OPTIONAL
-- ---------------------------------------------
-- Migration 484 pinned `factor_family` to four values:
--     CHECK (factor_family IN ('agnivasa','combination_yoga','kalam','ghati_muhurta'))
-- Design §3.1 scored the canned W4 Mode-2 fixture's six constraints against that
-- lattice and found THREE had no atoms to search over:
--   * `hora_lord = Guru`     — census row day_part/hora_lord was `computed`, but its
--                              evidence_pointer named panchang_engine's compute_hora
--                              FUNCTION, not this table.
--   * `vara = Guru-vara`     — no `vara` family existed at all; vāra appeared only
--                              inside combination_yoga interaction detail.
--   * the item-6 activity join — bg_muhurta_activity_rules keys on integer factor_id
--                              while lattice candidates carried limb NAMES only.
-- Elevation §9 Stage 1 makes coverage a property of the CONSTRUCTION: the horizon is
-- partitioned by every boundary event of every factor, so "no sampling interval exists
-- inside which a 90-minute window could hide." A Mode-2 search that sampled pañcāṅga
-- per candidate would reintroduce exactly the sampling interval that guarantee exists
-- to abolish. Hence: new atoms, not a new sampler.
--
-- FIVE NEW FAMILIES (writer: pipeline/orchestrator/writers/bg_muhurta_lattice.py):
--   5. hora       — 24 planetary hours per sunrise→next-sunrise cycle
--                   (timings.compute_hora; VS / Horā Sāra, cited inline in source).
--   6. vara       — sunrise-to-sunrise weekday; detail.factor_id = compute_vara(...).id
--                   (shastra_tables §7 VARA_NAMES key, 1..7).
--   7. nakshatra  — sunrise nakṣatra; detail.factor_id = compute_nakshatra(...).id (1..27).
--   8. tithi      — sunrise tithi;     detail.factor_id = compute_tithi(...).id (1..30).
--   9. lagna      — registry item 7: the 12 rising-sign spans per day at the reference
--                   location, found by real bisection over lagna.compute_lagna's
--                   ascendant_sign_id, each carrying the lagna lord (SIGN_LORDS) and all
--                   nine grahas' sidereal sign_ids at the span start. NO dignity or
--                   dṛṣṭi verdict is stored (§N.5) — the authorities are
--                   bg_dignity_reference and BPHS Ch.26, resolved at query time.
--
-- THE ID PROVENANCE RAIL (ADJUDICATION-10, binding — this is what unblocks item 6).
-- Families 6–8 carry `detail.factor_id` read directly from panchang_engine's own
-- numbered tables, which is the SAME source bg_muhurta_activity_rules.factor_id was
-- populated from (shastra_tables.EVENT_TABLES, materialized verbatim by
-- bg_parihara_rules.build_activity_rule_rows). The item-6 join therefore rests on ONE
-- deterministic source. ADJUDICATION-10 accepted the axis's exclusion on condition that
-- it stay explicit; design §3.3's RAIL permits re-enabling it ONLY if the emitter
-- genuinely carries the id from panchang_engine. It does. A hand-written name→id map
-- would be a B.10 fabrication and a gate failure.
--
-- DEFERRED, BY NAME (design §3.1's own clause: "If Lane R defers them, the census must
-- say so by name"): `nityayoga` and `karana` lattice families are NOT materialized here.
-- The census records both as not_computed with the reason
-- ("lattice family not materialized"), see bg_parihara_rules.CENSUS_ROWS. No W4 fixture
-- constraint names either as a lattice atom — the fixture's `karana NOT IN (vishti)`
-- clause resolves against the already-materialized combination_yoga/bhadra span.
--
-- `nakshatra_tara_bala` STAYS not_computed in the global census. Design §3.1: "that
-- disposition is correct and must not be 'fixed'." Tārā-bala is chart-personal by
-- construction and is evaluated at query time against the chart's own janma-nakṣatra
-- fact_id. Two dispositions, two scopes, both honest.
--
-- Idempotency: ALTER … DROP CONSTRAINT IF EXISTS + ADD CONSTRAINT is safe to re-run.
-- No data is rewritten; the four original families remain valid, so every existing row
-- still satisfies the widened CHECK (a strict superset — the constraint can only
-- become more permissive, never reject a row that previously passed).
--
-- target_floor is deliberately NOT set to a predicted number here (§N.4 — floors are
-- aspirational, never fabricated). It is set to the ACHIEVED count after the production
-- L0 rebuild, in a follow-up UPDATE; the current value (91,477) is the live-verified
-- four-family count and remains a TRUE floor until then, because the rolling horizon
-- only ever widens and rows are never deleted.
-- =============================================================================

BEGIN;

ALTER TABLE bg_muhurta_lattice
    DROP CONSTRAINT IF EXISTS bg_muhurta_lattice_factor_family_check;

ALTER TABLE bg_muhurta_lattice
    ADD CONSTRAINT bg_muhurta_lattice_factor_family_check
    CHECK (factor_family IN (
        'agnivasa', 'combination_yoga', 'kalam', 'ghati_muhurta',
        'hora', 'vara', 'nakshatra', 'tithi', 'lagna'
    ));

COMMENT ON COLUMN bg_muhurta_lattice.factor_family IS
  'One of: agnivasa, combination_yoga, kalam, ghati_muhurta (migration 484) plus '
  'hora, vara, nakshatra, tithi, lagna (migration 530, ṢAḌ-DARŚANA W4 ruling R-1). '
  'nityayoga and karana are deliberately NOT materialized as lattice families — see '
  'bg_muhurta_factor_census rows panchangika/nityayoga_lattice_family and '
  'panchangika/karana_lattice_family for the named deferral.';

COMMENT ON COLUMN bg_muhurta_lattice.factor_key IS
  'Family-specific sub-type key, e.g. "agni_vasa" (agnivasa family); '
  '"sarvartha_siddhi"/"amrit_siddhi"/"bhadra"/etc (combination_yoga); '
  '"rahu_kalam"/"abhijit"/etc (kalam); "1:Rudra"/"16:Girisha"/etc (ghati_muhurta); '
  '"hora_jupiter"/etc (hora); "guruvara"/etc (vara); "bharani"/etc (nakshatra); '
  '"krishna_ashtami"/etc (tithi); "karka"/"simha"/etc (lagna). For the vara/nakshatra/ '
  'tithi families the canonical INTEGER id lives in detail.factor_id, read straight '
  'from panchang_engine (compute_vara/compute_nakshatra/compute_tithi .id) — the same '
  'id space bg_muhurta_activity_rules.factor_id uses. That shared provenance is what '
  'makes the item-6 join deterministic rather than hand-mapped (B.10).';

-- ── bg_parihara_rules: census row count moved 50 -> 58 in this PR ────────────
-- Eight new census rows: two named lattice-family deferrals (nityayoga, karana),
-- three muhūrta-lagna rows (item 7: span computed / strength computed at query
-- time / lagna-śuddhi doctrine not_in_corpus), two rite-specific rows (item 6:
-- the id join computed, the frozen-engine Pareto axis disclosed as an honest
-- partial), and one parihāra-scope corpus finding (the Bṛhat Saṃhitā Adh. C
-- sl.3-4 conditional Viṣṭi exception, recorded with its chunk_id and verbatim
-- text but deliberately NOT encoded as a rule row — see the census note).
--
-- New deterministic floor = 60 parihāra-graph rows (live brahma_dosha_catalog,
-- unchanged) + 329 activity rows (exact, unchanged) + 58 census rows = 447.
-- Per §N.4 this is a floor, not a target: the 329 + 58 = 387 portion is a hard
-- deterministic count; the parihāra-graph portion tracks live catalogue content.
UPDATE asset_registry
   SET target_floor = 447,
       volume_explanation =
         'Live-verified 2026-07-30 and re-counted 2026-08-02 (ṢAḌ-DARŚANA W4 '
         'Lane R): 60 parihara-graph condition rows (26 doshas in '
         'brahma_dosha_catalog carry a real, non-placeholder citation, '
         'flattening to 60 individual cancellation-condition rows) + 329 '
         'activity-rule rows (exact, deterministic — sum of tithi/nakshatra/vara '
         'entries across panchang_engine''s 8 EVENT_TABLES) + 58 census rows '
         '(exact — len(CENSUS_ROWS); 50 before W4, +8 for the ruling R-1 named '
         'deferrals, the item-6 join + frozen-axis partial, the item-7 '
         'muhurta-lagna trio, and the Brihat Samhita Adh. C sl.3-4 conditional '
         'Vishti finding) = 447. The 329 + 58 = 387 portion is a hard '
         'deterministic floor; the parihara-graph portion depends on '
         'brahma_dosha_catalog''s live content and was confirmed via a direct '
         'read-only query against production, not fabricated or estimated.'
 WHERE asset_id = 'bg_parihara_rules';

COMMIT;

-- =============================================================================
-- DOWN (manual rollback — note this is LOSSY if v2 rows have been written):
--   BEGIN;
--   DELETE FROM bg_muhurta_lattice
--     WHERE factor_family IN ('hora','vara','nakshatra','tithi','lagna');
--   ALTER TABLE bg_muhurta_lattice
--     DROP CONSTRAINT IF EXISTS bg_muhurta_lattice_factor_family_check;
--   ALTER TABLE bg_muhurta_lattice
--     ADD CONSTRAINT bg_muhurta_lattice_factor_family_check
--     CHECK (factor_family IN ('agnivasa','combination_yoga','kalam','ghati_muhurta'));
--   COMMIT;
-- =============================================================================
