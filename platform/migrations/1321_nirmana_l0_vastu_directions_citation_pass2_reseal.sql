-- Migration 1321: reseal bg_vastu_directions' integrity pin and registry description after Citation Pass 2
-- (decision OS-2026-10-05-CITATIONS; PASS2_DECISIONS.tsv, one row: direction = Southwest).
--
-- DATA (seed edit, platform/python-sidecar/brahmagyan/l0_vastu_directions.py, written by the next governed rebuild of bg_vastu_directions):
-- the Southwest / Rahu row's classical_citation was the bare label "Vastu Shastra tradition (Nairitya corner)" (not a citation). Pass 2 re-read
-- Muhurta Chintamani Gocara-prakarana v.9 tika (muhurta_chintamani:PG66:C1: Rahu's gomeda in the nairritya = south-west) and the Hora Sara Ch.2
-- direction table (hora_sara:PG16:C1-PG17:C1) and decided the K1 string now in the seed. favorable_color stays NULL (no source; not invented).
-- Nothing else changes: still 8 direction rows and 24 remedial rows; the other seven directions and every remedial row are byte-identical.
--
-- THIS MIGRATION (registry metadata only; the reseal pattern of 612 / 1078 / 1221):
--   (1) integrity_check_sql: the pinned content hash of bg_vastu_directions (1d18e307f87f...) becomes the hash of the rebuilt content (27155f5759d7...),
--       by a GUARDED replace() of the stored text (the old hash must occur exactly once; the remedials half of the check, whose rows do not change,
--       is untouched). The pre hash reproduces migration 612's applied pin and the post hash is the one pinned here, both re-derived on a
--       disposable Postgres by tests/l0/test_citation_pass2_vastu.py.
--   (2) english_description (cosmetic, outside the decision): names the one direction whose source is no longer Mayamata Ch.6 (migration 643's text otherwise
--       byte-identical). It is updated ONLY when the stored text is exactly migration 643's; any other text is left as stored with a NOTICE (a cosmetic field
--       never blocks a deploy).
--
-- SERVING EFFECT AT APPLY (binding for every migration PR). `UPDATE ... SET integrity_check_sql` fires the live trigger
-- nirmana_registry_receipt_invalidation (migration 596): AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql,
-- target_floor, asset_kind, asset_type, scope, has_writer, is_active, target_table, FOR EACH ROW WHEN (old.* IS DISTINCT FROM new.*), function
-- nirmana_invalidate_registry_receipts(), which sets asset_freshness.freshness_state = 'stale' (reason registry_changed) WHERE asset_id = NEW.asset_id.
-- So applying this STALES bg_vastu_directions' asset_freshness rows (whatever rows exist for that asset id); the rebuild that follows writes fresh
-- receipts. No other asset is touched. A re-run is a no-op (the UPDATE is skipped, the trigger does not fire).
--
-- ORDER: apply this migration, then run the governed rebuild of bg_vastu_directions (dispatch tool, expected-change mode). Until the rebuild runs the
-- stored check reads FALSE (the pin describes rows not yet written); do NOT rebuild first. IDEMPOTENT and SURGICAL: each step is skipped when already
-- applied; an unrecognised prior state is REFUSED. 612 / 643 are applied and never edited (CLAUDE.md N.4). Transaction ownership belongs to migrate.ts.

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  old_hash constant text := '1d18e307f87fa65932cb96ea4cff1dc8487262986ff5de4c969ab0b48497bb07';
  new_hash constant text := '27155f5759d7443900f3bb41bfa24356a7d4a68ba23086af0c1a6cf11eca90a2';
  prior_description constant text :=
    'Classical Vastu Shastra direction-graha associations: 8 compass directions each mapped to a ruling graha, secondary graha, element, favorable color, and classical citation (Mayamata Ch.6). Also seeds bg_vastu_direction_remedials (24 rows) with 2-3 remedies per direction.';
  new_description constant text :=
    'Classical Vastu Shastra direction-graha associations: 8 compass directions each mapped to a ruling graha, secondary graha, element, favorable color, and classical citation (Mayamata Ch.6 for seven directions; Southwest/Rahu cites Muhurta Chintamani Gocara-prakarana v.9 with the Hora Sara Ch.2 direction table as analogue, Citation Pass 2 OS-2026-10-05-CITATIONS; Southwest favorable_color stays NULL, no source). Also seeds bg_vastu_direction_remedials (24 rows) with 2-3 remedies per direction.';
  hits integer;
BEGIN
  SELECT * INTO registry_row FROM asset_registry WHERE asset_id = 'bg_vastu_directions' FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'migration 1321 refuses: bg_vastu_directions is not in asset_registry';
  END IF;
  IF registry_row.integrity_check_sql IS NULL THEN
    RAISE EXCEPTION 'migration 1321 refuses: bg_vastu_directions has no integrity_check_sql';
  END IF;

  -- (1) the pinned hash
  hits := (length(registry_row.integrity_check_sql) - length(replace(registry_row.integrity_check_sql, old_hash, ''))) / length(old_hash);
  IF hits = 1 THEN
    UPDATE asset_registry
       SET integrity_check_sql = replace(integrity_check_sql, old_hash, new_hash)
     WHERE asset_id = 'bg_vastu_directions';
  ELSIF hits = 0 AND position(new_hash IN registry_row.integrity_check_sql) > 0 THEN
    NULL;   -- already resealed
  ELSE
    RAISE EXCEPTION 'migration 1321 refuses: the stored integrity_check_sql carries the old pin % times (expected exactly once) and not the new pin', hits;
  END IF;

  -- (2) the description
  IF registry_row.english_description = prior_description THEN
    UPDATE asset_registry SET english_description = new_description WHERE asset_id = 'bg_vastu_directions';
  ELSIF registry_row.english_description IS DISTINCT FROM new_description THEN
    RAISE NOTICE 'migration 1321: bg_vastu_directions english_description is neither migration 643''s text nor the resealed text; left as stored (cosmetic field, never blocks a deploy)';
  END IF;

  -- postflight
  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
     WHERE asset_id = 'bg_vastu_directions'
       AND position(new_hash IN integrity_check_sql) > 0
       AND position(old_hash IN integrity_check_sql) = 0
  ) THEN
    RAISE EXCEPTION 'migration 1321 postflight mismatch';
  END IF;
END $$;

-- VERIFY (after the rebuild): SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_vastu_directions' \gexec  -- expect t
--   SELECT classical_citation FROM bg_vastu_directions WHERE direction = 'Southwest';  -- expect the K1 string
-- DOWN (manual): replace(integrity_check_sql, new_hash, old_hash) and restore english_description to migration 643's text.
