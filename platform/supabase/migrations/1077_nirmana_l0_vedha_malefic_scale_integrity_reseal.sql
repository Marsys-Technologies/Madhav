-- Migration 1077: reseal bg_vedha_malefic_scale's frozen integrity contract
-- after L0 repair item 5's content correction.
--
-- Migration 611 pinned bg_vedha_malefic_scale as a closed, governed-rebuild
-- static table: any semantic content change fails its integrity_check_sql
-- closed by design ("PRESERVE + GOVERNED REBUILD... any count-preserving
-- semantic mutation fails closed"). L0 repair item 5 (this same repair
-- session) deliberately made exactly such a mutation: every row's
-- effect_description now explicitly disambiguates this PG353 battle-context
-- scale from Adh. XXVI's other PG349 general-transit scale (CLAUDE.md §N.7:
-- narration/citation correctness is a content change the frozen-hash
-- discipline is SUPPOSED to catch, not silently absorb). This migration is
-- the required governed reseal: it re-pins integrity_check_sql to the new,
-- reviewed content's hash, following exactly migration 611's own guarded
-- pattern. Row count is unchanged (still 5); only effect_description text
-- changed, so this is a pure content reseal, not a floor or shape change.
--
-- New hash independently computed and verified against production
-- (amjis-postgres) after item 5's writer ran, via the exact same query
-- migration 611 uses (string_agg of the same six columns, jsonb-encoded,
-- newline-joined in table_version/malefic_count order, sha256, hex).
--
-- Registry metadata only; transaction ownership belongs to migrate.ts.

DO $$
DECLARE
  registry_row asset_registry%ROWTYPE;
  changed_rows integer := 0;
  prior_vedha_check constant text := $check$
SELECT
  (SELECT count(*) = 5 FROM bg_vedha_malefic_scale)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(table_version,malefic_count,effect_grade,
      effect_description,source_citation,verse_ref)::text,
    E'\n' ORDER BY table_version COLLATE "C",malefic_count
  ),''),'UTF8')),'hex') =
    '9ee5d8436059fa96d5fa60d8be6d0cc25cc8865e1013ef1bed8ff6810342ff1c'
  FROM bg_vedha_malefic_scale)
$check$;
  new_vedha_check constant text := $check$
SELECT
  (SELECT count(*) = 5 FROM bg_vedha_malefic_scale)
  AND (SELECT encode(sha256(convert_to(COALESCE(string_agg(
    jsonb_build_array(table_version,malefic_count,effect_grade,
      effect_description,source_citation,verse_ref)::text,
    E'\n' ORDER BY table_version COLLATE "C",malefic_count
  ),''),'UTF8')),'hex') =
    '2c226c8f29553f1b9363bd2721916115ccf67400342a03cbdff199d5a6f3e1ea'
  FROM bg_vedha_malefic_scale)
$check$;
BEGIN
  SELECT * INTO registry_row
  FROM asset_registry WHERE asset_id = 'bg_vedha_malefic_scale' FOR UPDATE;

  IF NOT FOUND OR (
    registry_row.integrity_check_sql = prior_vedha_check
  ) IS NOT TRUE THEN
    RAISE EXCEPTION
      'migration 1077 refuses: bg_vedha_malefic_scale integrity_check_sql does not match migration 611''s applied contract (already resealed, or 611 never applied)';
  END IF;

  UPDATE asset_registry
  SET integrity_check_sql = new_vedha_check
  WHERE asset_id = 'bg_vedha_malefic_scale';

  GET DIAGNOSTICS changed_rows = ROW_COUNT;
  IF changed_rows <> 1 THEN
    RAISE EXCEPTION 'migration 1077 expected 1 row, updated %', changed_rows;
  END IF;

  IF NOT EXISTS (
    SELECT 1 FROM asset_registry
    WHERE asset_id = 'bg_vedha_malefic_scale'
      AND integrity_check_sql = new_vedha_check
  ) THEN
    RAISE EXCEPTION 'migration 1077 postflight registry mismatch';
  END IF;
END $$;

-- =============================================================================
-- VERIFY (falsifier — run after apply):
--   SELECT (asset_registry.integrity_check_sql)::text = 'DO $$...$$' -- inspect manually, or:
--   -- simplest live check: execute the stored integrity_check_sql itself and
--   -- confirm it now returns true:
--   \gexec
--   SELECT integrity_check_sql FROM asset_registry WHERE asset_id = 'bg_vedha_malefic_scale' \gexec
--   -- expect: t
--
-- DOWN (manual rollback — restores migration 611's original contract):
--   BEGIN;
--   UPDATE asset_registry SET integrity_check_sql = $$<prior_vedha_check from migration 611>$$
--     WHERE asset_id = 'bg_vedha_malefic_scale';
--   COMMIT;
-- =============================================================================
