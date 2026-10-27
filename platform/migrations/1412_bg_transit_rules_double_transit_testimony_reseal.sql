-- Migration 1412: retire the 7 migration-owned Jupiter–Saturn `double_transit` rows of bg_transit_rules
-- (status retired_pending_reauthor — the rule is SWITCHED OFF, ruling FOURQ-CLOSURE-20261027), strike their
-- non-existent citation for an honest attribution, and reseal the integrity pin.
--
-- WHY. The provenance audit DOUBLE-TRANSIT-PROVENANCE-20261027 (DOUBLE_TRANSIT_PROVENANCE_v0_1.md) found (a) no classical
-- source for the rule in the corpus: the "Phaladeepika ch.26 §double-gochara" passage migration 397 cited for these seven
-- rows does not exist (migration 565 recorded the CORPUS_GAP; three independent reviews 2026-09-29; the sealed Pravāha v3.0
-- doctrine labels the rule modern K.N. Rao practice, uncited_extension), and (b) one confirmed instance of the rule's
-- detection logic being widened so a known specimen of the native would fire (2026-07-20). The panel closure
-- FOURQ-CLOSURE-20261027 switches the rule OFF entirely: not evaluated, not served, not scored; re-admission only via a
-- panel-verified classical citation and a forward-only test.
--
-- WHAT THIS MIGRATION DOES (the ONLY way these rows can change: they are migration-owned — brahmagyan/l0_transit.py
-- F-145 never emits or retires a double_transit row — so no writer run is involved and none is triggered):
--   1. bg_transit_rules, the 7 rows WHERE rule_type = 'double_transit' (ids, rule_type, graha, primary_house, vedha_house
--      and phala UNCHANGED; the row count stays 7 and the table stays 76 = 43 + 26 + 7, so the shape checks of migrations
--      613/1078 and the registry count_sql are untouched):
--        classical_citation := 'RETIRED_PENDING_REAUTHOR (FOURQ-CLOSURE-20261027) — ' || the honest attribution
--                              (the attribution is byte-identical to services/gochara_grammar/citations.py
--                              DOUBLE_TRANSIT_COMMENTARIAL_ATTRIBUTION; the prefix is citations.RETIRED_CITATION_PREFIX);
--        rule_notes         := the retired_pending_reauthor marker (both ruling ids, the disposition) prepended to the
--                              existing note.
--      STATUS COLUMN / CHECK CONSTRAINTS: bg_transit_rules (migration 266 + 397) has NO status or provenance column and
--      no enum; its CHECK constraints are rule_type IN (favourable, unfavourable, vedha, double_transit) — untouched: the
--      rows stay rule_type 'double_transit' so the frozen count stays 7 — and the house ranges. classical_citation is
--      free text NOT NULL, rule_notes free text nullable, so nothing rejects the new value; the status therefore rides as
--      a machine-readable citation PREFIX (the precedent: the node vedha rows START with UNSOURCED, migration 1320).
--      Every consumer that reads bg_transit_rules for serving skips a row whose citation starts with the prefix (and,
--      independently, any rule_type 'double_transit' row — so a database that has not yet applied this migration serves
--      none either): services/ka_gochara_resonance/writer.py `_is_retired_rule`. The vedha loader
--      (services/gochara_rules/vedha_derive.py) reads rows WHERE vedha_house IS NOT NULL only — the seven rows have none.
--   2. asset_registry.integrity_check_sql for bg_transit_rules: the content hash pinned by migration 1320 (dce17ed0...)
--      becomes the hash of the content after step 1 (19cf8768...), by the same GUARDED replace() migration 1320 used.
--      Both hashes were computed with migration 613's exact query on a disposable Postgres holding the seed rows
--      (brahmagyan/l0_transit.py BG_TRANSIT_RULES, post Citation Pass 2) plus migration 397's seven rows: the PRE hash
--      reproduces 1320's pin exactly (so the reconstruction is faithful) and the POST hash is the one pinned here — both
--      re-derived by tests/l0/test_migration_1412_double_transit_testimony.py on every run.
--   3. asset_registry.english_description for bg_transit_rules: migration 1079's text says the seven rows cite "Saravali or
--      Jataka Parijata"; after step 1 that is false (CLAUDE.md §N.7 narration fidelity), so it is replaced by a text that
--      states the new citation census. platform/scripts/seed/asset_registry_seed.ts carries the same text (the two must
--      agree — migration 1320's parity rule; the seed's upsert writes english_description) and is updated in the same commit.
--
-- ORDER / REBUILD. No rebuild and no backfill is triggered or required (the owner's stop order on Gochara 5.0 candidate
-- regeneration is in force): the stored check reads TRUE as soon as the live 69 writer-owned rows carry the post-Citation-
-- Pass-2 seed (the state migration 1320 already pins); if that governed rebuild has not yet run, the check stays FALSE
-- for exactly the reason 1320 documents and becomes TRUE when it does. The UPDATE of asset_registry fires the
-- migration-596 freshness trigger (bg_transit_rules' asset_freshness rows read 'stale', reason registry_changed) — a flag,
-- not a build.
--
-- IDEMPOTENT and SURGICAL: a second run finds the new pin and the retired rows and changes nothing; a live state that is
-- neither the expected prior state nor the applied state is REFUSED (never overwritten). Migrations 397, 565, 613, 1078,
-- 1079 and 1320 are applied and are never edited (CLAUDE.md §N.4). Transaction ownership belongs to platform/scripts/migrate.ts.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  prior_pin constant text := 'dce17ed02e1ba05eb4db5d0a46777a70c1f5832160fa3add253f7119bbf7ea8d';
  new_pin constant text := '19cf876871e4c33b85e410484d263dcfa9b0e99c90805c54dae09ee04e6ebbbb';
  struck_prefix constant text := 'Phaladeepika ch.26 §double-gochara';
  retired_prefix constant text := 'RETIRED_PENDING_REAUTHOR';
  attribution constant text :=
    'Modern practice (K.N. Rao school, 20th c.); no page-anchored classical statement in corpus (migration 565 CORPUS_GAP); sole joint precedent claimed: Phaladīpikā XVII.12 — unverified';
  retired_citation constant text :=
    'RETIRED_PENDING_REAUTHOR (FOURQ-CLOSURE-20261027) — Modern practice (K.N. Rao school, 20th c.); no page-anchored classical statement in corpus (migration 565 CORPUS_GAP); sole joint precedent claimed: Phaladīpikā XVII.12 — unverified';
  retired_note constant text :=
    'retired_pending_reauthor: P4 switched off (ruling FOURQ-CLOSURE-20261027; provenance DOUBLE-TRANSIT-PROVENANCE-20261027) — not served, not scored; re-admission only via a panel-verified classical citation and a forward-only test.';
  prior_description constant text :=
    '76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit. Citation state after the 2026-09 L0 repair, measured not asserted: 36 favourable-with-vedha rows carry page-anchored Phaladipika Adh. XXVI citations (PG322:C1/PG323:C1); 6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED (the served corpus carries no house-transit vedha doctrine for the nodes); 19 rows (18 unfavourable + 1 favourable with no vedha pair) STILL carry the refuted "BPHS Ch.29" — they lie outside the repair''s row-by-row verified predicate and were deliberately not re-cited on an unverified basis; the remaining 15 cite Phaladeepika Ch.26, Adh. XXVI slokas 2/8/21, Saravali or Jataka Parijata.';
  new_description constant text :=
    '76 classical transit rules: 43 favourable, 26 unfavourable, 7 double-transit (RETIRED). Citation state after the 2026-09 L0 repair and the 2026-10-27 switch-off of the Jupiter–Saturn double transit, measured not asserted: 36 favourable-with-vedha rows carry page-anchored Phaladipika Adh. XXVI citations (PG322:C1/PG323:C1); 6 Rahu/Ketu favourable-with-vedha rows are declared UNSOURCED (the served corpus carries no house-transit vedha doctrine for the nodes); 19 rows (18 unfavourable + 1 favourable with no vedha pair) STILL carry the refuted "BPHS Ch.29" — they lie outside the repair''s row-by-row verified predicate and were deliberately not re-cited on an unverified basis; 8 cite Phaladeepika Ch.26 or Adh. XXVI slokas 2/8/21; the 7 double_transit rows are RETIRED_PENDING_REAUTHOR (migration 1412, ruling FOURQ-CLOSURE-20261027): their non-existent "Phaladeepika ch.26 §double-gochara" citation (migration 565 CORPUS_GAP) is struck for an attribution to modern practice (K.N. Rao school), and they are not served and not scored.';
  hits integer;
  n integer;
BEGIN
  IF retired_citation <> retired_prefix || ' (FOURQ-CLOSURE-20261027) — ' || attribution THEN
    RAISE EXCEPTION 'migration 1412 refuses: its own retired_citation constant does not compose from prefix + attribution';
  END IF;

  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 1412 refuses: bg_transit_rules is not in asset_registry';
  END IF;
  IF registry_row.integrity_check_sql IS NULL THEN
    RAISE EXCEPTION 'migration 1412 refuses: bg_transit_rules has no integrity_check_sql';
  END IF;
  hits := (length(registry_row.integrity_check_sql) - length(replace(registry_row.integrity_check_sql, prior_pin, ''))) / length(prior_pin);

  IF hits = 1 THEN
    -- first apply: the seven rows must be in their pre-change state and the description must be migration 1079's
    SELECT count(*) INTO n FROM bg_transit_rules WHERE rule_type = 'double_transit';
    IF n <> 7 THEN
      RAISE EXCEPTION 'migration 1412 refuses: expected 7 double_transit rows, found %', n;
    END IF;
    SELECT count(*) INTO n FROM bg_transit_rules
     WHERE rule_type = 'double_transit' AND classical_citation LIKE struck_prefix || '%';
    IF n <> 7 THEN
      RAISE EXCEPTION 'migration 1412 refuses: expected all 7 double_transit rows to carry the struck citation, found %', n;
    END IF;
    SELECT count(*) INTO n FROM bg_transit_rules WHERE classical_citation LIKE retired_prefix || '%';
    IF n <> 0 THEN
      RAISE EXCEPTION 'migration 1412 refuses: % row(s) already carry the retired prefix while the registry still holds the prior pin', n;
    END IF;
    IF registry_row.english_description IS DISTINCT FROM prior_description THEN
      RAISE EXCEPTION 'migration 1412 refuses: bg_transit_rules english_description is not migration 1079''s text';
    END IF;

    UPDATE bg_transit_rules
       SET classical_citation = retired_citation,
           rule_notes = retired_note || COALESCE(' ' || rule_notes, '')
     WHERE rule_type = 'double_transit';
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n <> 7 THEN
      RAISE EXCEPTION 'migration 1412 expected to update 7 rows, updated %', n;
    END IF;

    UPDATE asset_registry
       SET integrity_check_sql = replace(integrity_check_sql, prior_pin, new_pin),
           english_description = new_description
     WHERE asset_id = 'bg_transit_rules';
    GET DIAGNOSTICS n = ROW_COUNT;
    IF n <> 1 THEN
      RAISE EXCEPTION 'migration 1412 expected 1 registry row, updated %', n;
    END IF;
  ELSIF hits = 0 AND position(new_pin IN registry_row.integrity_check_sql) > 0 THEN
    NULL;   -- already applied; the postflight below re-verifies the rows and the registry
  ELSE
    RAISE EXCEPTION 'migration 1412 refuses: the stored integrity_check_sql carries the prior pin % times (expected exactly once) and not the new pin', hits;
  END IF;

  -- postflight (both branches): shape unchanged, exactly the seven rows retired, citation struck, pin resealed,
  -- description truthful
  IF NOT EXISTS (
    SELECT 1 FROM bg_transit_rules
    HAVING count(*) = 76
       AND count(*) FILTER (WHERE rule_type = 'favourable') = 43
       AND count(*) FILTER (WHERE rule_type = 'unfavourable') = 26
       AND count(*) FILTER (WHERE rule_type = 'double_transit') = 7
       AND count(*) FILTER (WHERE rule_type = 'double_transit' AND classical_citation = retired_citation) = 7
       AND count(*) FILTER (WHERE rule_type = 'double_transit' AND rule_notes LIKE retired_note || '%') = 7
       AND count(*) FILTER (WHERE classical_citation LIKE retired_prefix || '%') = 7
       AND count(*) FILTER (WHERE classical_citation LIKE '%double-gochara%') = 0
  ) THEN
    RAISE EXCEPTION 'migration 1412 postflight: bg_transit_rules is not in the retired state (76 = 43 + 26 + 7; exactly the 7 double_transit rows RETIRED_PENDING_REAUTHOR with the attribution; none citing the struck passage)';
  END IF;
  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_transit_rules'
       AND position(new_pin IN integrity_check_sql) > 0
       AND position(prior_pin IN integrity_check_sql) = 0
       AND english_description = new_description
       AND target_floor = 76
  ) THEN
    RAISE EXCEPTION 'migration 1412 postflight registry mismatch';
  END IF;
END $$;

-- VERIFY (falsifier, after apply; once the live 69 writer-owned rows carry the post-Citation-Pass-2 seed the stored
-- check itself must hold):
--   SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_rules' \gexec   -- expect t
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE '%double-gochara%';     -- expect 0
--   SELECT count(*) FROM bg_transit_rules WHERE rule_type = 'double_transit';                   -- expect 7
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'RETIRED_PENDING_REAUTHOR%';  -- expect 7
--   SELECT count(*) FROM bg_transit_rules WHERE rule_notes LIKE 'retired_pending_reauthor:%';   -- expect 7
-- DOWN (manual): restore the seven rows' migration-397 classical_citation / rule_notes text, then
--   UPDATE asset_registry SET integrity_check_sql = replace(integrity_check_sql, new_pin, prior_pin),
--     english_description = <migration 1079's truthful_description> WHERE asset_id = 'bg_transit_rules';
