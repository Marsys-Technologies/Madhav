-- Migration 1320: reseal bg_transit_rules' integrity pin after Citation Pass 2
-- (decision OS-2026-10-05-CITATIONS; PASS2_DECISIONS.tsv, the six Rahu/Ketu house-vedha rows).
--
-- WHAT CHANGED IN THE DATA (seed edit, platform/python-sidecar/brahmagyan/l0_transit.py, applied by the next governed rebuild of bg_transit_rules): the six
-- favourable rows Rahu/Ketu x houses 3/6/11 had `classical_citation` = a long UNSOURCED label (L0 repair item 3). Pass 2 (OS-2026-10-05-CITATIONS) read
-- Phaladeepika Adh. XXVI sl.2 (phaladeepika:PG321:C1: the nodes act like the Sun) and sl.24 (phaladeepika:PG331:C1: Rahu's results by house) and found the
-- TRANSIT RESULT sourced; only the vedha partner house is an inference. SS ruled, via Pravaha, FORM (b): the citation stays a split text that STARTS with
-- UNSOURCED (the vedha loader requires it) and carries the K1 transit result after it:
--   UNSOURCED (vedha partner: inference, not in the cited verses) -- transit result: Phaladipika Adh. XXVI, Sl. 2 / 24 (both verses, both loci) [machine locus <locus>] "<excerpt>"
-- `rule_notes` of the six rows carry the decided clause. No row is added or removed: still 76 rows (43 favourable + 26 unfavourable + 7 double_transit),
-- ids unchanged; rule_type, primary_house, vedha_house and the 3 + 3 shape are exactly as before.
--
-- LOADER COMPATIBILITY (proved offline, tests/l0/test_citation_pass2_transit.py): services/gochara_rules/vedha_derive.py pairs_from_rows (line 129) accepts a node
-- vedha row only when its citation starts with UNSOURCED; the rebuilt rows load without error (36 classical pairs + 3 Rahu + 3 Ketu rows, census total 42) and the
-- pair mapping is identical before and after. The citation text sits INSIDE the loader's pairs_content_digest (line 90; the L0 binding of the AM-16 input
-- vector, services/gochara_kernel/input_vector.py:74), so that digest changes by construction when the rebuild runs. ka_vedha_gochara derives its stamps from the
-- UNSOURCED prefix, so they stay unsourced. Census: the split text is read through the declared `split_citation` of bg_transit_rules' source declaration (the
-- transit result must resolve to a corpus chunk); the vedha partner is a KNOWN FINDING until the owner rules ND-NODE-VEDHA.
--
-- WHAT THIS MIGRATION DOES (registry metadata only, ONE column; the same reseal pattern as migrations 1078 / 1221):
--   integrity_check_sql: the pinned content hash of bg_transit_rules (1dbdd265cf0e...) becomes the hash of the
--       rebuilt content (dce17ed02e1b...), by a GUARDED replace() of the live text (the old hash must occur exactly once;
--       the rest of the stored check is not touched by the replace; the postflight verifies only: the new hash present, the old hash absent,
--       target_floor = 76, and the test asserts the whole stored text equals the 1078 text with that one hash substituted). The new hash is computed by the
--       same query migration 613 uses, over the seed rows plus migration 397's seven double_transit rows, and the test
--       (tests/l0/test_citation_pass2_transit.py) re-derives it on a disposable Postgres: the PRE hash reproduces the
--       applied pin from 1078 (so the reconstruction is faithful) and the POST hash is the one pinned here.
-- english_description is deliberately NOT touched (SS / Pravaha rule: leave it UNCHANGED): migration 1079's text says the six rows are declared UNSOURCED because
-- the served corpus carries no house-transit vedha doctrine for the nodes, which stays true under form (b) (the VEDHA PARTNER is still unsourced; only the transit result
-- is now cited), and platform/scripts/seed/asset_registry_seed.ts carries the same text, so changing the registry copy would make the two disagree.
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). `UPDATE ... SET integrity_check_sql` fires the live trigger
-- nirmana_registry_receipt_invalidation (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
-- target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*), function
-- nirmana_invalidate_registry_receipts(), which sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
-- So applying this STALES bg_transit_rules' asset_freshness rows (whatever rows exist for that asset id). The transit rebuild that
-- follows writes fresh receipts. No other asset is touched (the trigger is keyed on NEW.asset_id). A re-run is a no-op (the UPDATE is skipped, the
-- trigger does not fire).
--
-- ORDER OF APPLICATION: apply this migration, then run the governed rebuild of bg_transit_rules (dispatch tool,
-- expected-change mode). Until the rebuild runs the stored check reads FALSE (the pin describes rows not yet written);
-- the rebuild's own post-write integrity check is then TRUE. Do NOT run the rebuild first (its post-write check would fail).
-- A rebuild that leaves the table unchanged would read FALSE by design: the pin now describes the corrected rows.
--
-- IDEMPOTENT and SURGICAL: the step is skipped when already applied; a live text that is neither the expected prior state
-- nor the already-applied state is REFUSED (never overwritten). 1078 and 1079 are applied and are never edited (CLAUDE.md N.4).
-- Transaction ownership belongs to platform/scripts/migrate.ts.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  old_hash constant text := '1dbdd265cf0e04edd26aebde054f34d9034be38bfabc8102085b0127196a598d';
  new_hash constant text := 'dce17ed02e1ba05eb4db5d0a46777a70c1f5832160fa3add253f7119bbf7ea8d';
  hits integer;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_transit_rules' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 1320 refuses: bg_transit_rules is not in asset_registry';
  END IF;
  IF registry_row.integrity_check_sql IS NULL THEN
    RAISE EXCEPTION 'migration 1320 refuses: bg_transit_rules has no integrity_check_sql';
  END IF;

  -- (1) the pinned hash
  hits := (length(registry_row.integrity_check_sql) - length(replace(registry_row.integrity_check_sql, old_hash, ''))) / length(old_hash);
  IF hits = 1 THEN
    UPDATE asset_registry
       SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash)
     WHERE asset_id = 'bg_transit_rules';
  ELSIF hits = 0 AND position(new_hash IN registry_row.integrity_check_sql) > 0 THEN
    NULL;   -- already resealed
  ELSE
    RAISE EXCEPTION 'migration 1320 refuses: the stored integrity_check_sql carries the old pin % times (expected exactly once) and not the new pin', hits;
  END IF;

  -- postflight
  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_transit_rules'
       AND position(new_hash IN integrity_check_sql) > 0
       AND position(old_hash IN integrity_check_sql) = 0
       AND target_floor = 76
  ) THEN
    RAISE EXCEPTION 'migration 1320 postflight mismatch';
  END IF;
END $$;

-- VERIFY (falsifier, after the rebuild): SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_transit_rules' \gexec  -- expect t
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'UNSOURCED%';                        -- expect 6 (form (b): the six node rows still START with UNSOURCED)
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'UNSOURCED (vedha partner:%';        -- expect 6
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation LIKE 'Phaladipika Adh. XXVI, Sloka%';     -- expect 36 (unchanged)
--   SELECT count(*) FROM bg_transit_rules WHERE classical_citation = 'BPHS Ch.29 (Gochara Phala — Transit Results)';  -- expect 19 (unchanged)
-- DOWN (manual): replace(integrity_check_sql, new_hash, old_hash).
