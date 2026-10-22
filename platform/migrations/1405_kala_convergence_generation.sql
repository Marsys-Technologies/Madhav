-- Migration 1405: kala_convergence is generation-scoped (SR-K9-WRITE-SCOPE F1, K9-WRITE-SCOPE audit).
-- migrate.ts owns the transaction. Additive, guarded, idempotent: a second application changes nothing.
--
-- Defect closed. ka_sangam rewrote kala_convergence IN PLACE for the whole chart, and the foreign keys onto
-- kala_convergence(convergence_id) cascade: kala_darshana, kala_obstruction and phala_anchors are ON DELETE CASCADE,
-- kala_bhavishya is ON DELETE SET NULL (production readback 2026-10-22T07:10Z, all NO ACTION on update, not deferrable).
-- A K9 candidate build therefore deleted SERVED rows of four tables outside the plan. After this migration the table
-- is partitioned by `generation`; a candidate build writes and deletes only its own generation, so the cascade can only
-- reach children of that same candidate's rows.
--
-- Stamp of the existing rows (the rule, stated with its evidence). Before this migration the table had no generation
-- column, and its writers (ka_sangam's chart-wide delete+insert, the brahmagyan.kala.convergence seed CLI) only ever
-- wrote the one served copy, so every row present now is the served 'legacy' partition. That rule holds only for a chart
-- that has never had a K9 candidate or a published head; for such a chart the rows could belong to the head or to a
-- candidate instead. The migration REFUSES (raises, nothing changed) if any chart that holds convergence rows also has a
-- row in kala_layer_candidate or kala_layer_head. Production readback: the canonical chart holds 0 convergence rows.
--
-- Served generation = the chart's published head generation, else 'legacy' (the same resolution the predicate readers
-- use). `kala_convergence_served` is that definition; the Python readers and ordinary rebuilds read the view, never the base
-- table (the TypeScript served tools carry the same predicate inline, valid before this migration is applied). The view is
-- SELECT c.*, fixed at creation: a later column on kala_convergence needs CREATE OR REPLACE VIEW (adding columns at the end).
--
-- Rollback (not run by the migrator; only while no candidate rows exist): DROP VIEW public.kala_convergence_served;
-- DROP INDEX public.uq_kala_convergence_generation_natural_key; ALTER TABLE public.kala_convergence DROP COLUMN generation;
-- the registry statements below are restored by re-applying 670's ka_sangam contract and un-retiring spec 980.
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

DO $stamp$
DECLARE
  ambiguous  bigint;
  duplicates bigint;
  stamped    bigint;
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_attribute
                  WHERE attrelid = 'public.kala_convergence'::regclass AND attname = 'generation' AND NOT attisdropped) THEN
    SELECT count(*) INTO ambiguous
      FROM (SELECT DISTINCT chart_id FROM public.kala_convergence) c
     WHERE EXISTS (SELECT 1 FROM public.kala_layer_candidate k WHERE k.chart_id = c.chart_id)
        OR EXISTS (SELECT 1 FROM public.kala_layer_head h WHERE h.chart_id = c.chart_id);
    IF ambiguous > 0 THEN
      RAISE EXCEPTION 'migration 1405 refused: % chart(s) hold kala_convergence rows AND a K9 candidate/head, so the rows cannot all be stamped legacy by rule; stamp them by hand first', ambiguous;
    END IF;

    SELECT count(*) INTO duplicates FROM (
      SELECT 1 FROM public.kala_convergence
       GROUP BY chart_id, horizon_tier, mode, peak_date, signal_id
      HAVING count(*) > 1) d;
    IF duplicates > 0 THEN
      RAISE EXCEPTION 'migration 1405 refused: % duplicate (chart, tier, mode, peak_date, signal) group(s) would break the widened natural key', duplicates;
    END IF;

    SELECT count(*) INTO stamped FROM public.kala_convergence;
    -- Constant default: a metadata-only change, existing rows read as 'legacy' without a rewrite.
    ALTER TABLE public.kala_convergence ADD COLUMN generation text NOT NULL DEFAULT 'legacy';
    EXECUTE format('COMMENT ON COLUMN public.kala_convergence.generation IS %L',
      'K9 candidate partition (migration 1405). legacy = the served copy that existed before the column; '
      || 'candidate:<build id> = a building K9 candidate; a published generation equals kala_layer_head.generation. '
      || 'Stamp measured at apply time: ' || stamped || ' existing row(s) stamped legacy, 0 charts with candidate/head ambiguity, 0 duplicate natural keys.');
  END IF;
END
$stamp$;

DO $check$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                  WHERE conrelid = 'public.kala_convergence'::regclass AND conname = 'kala_convergence_generation_check') THEN
    ALTER TABLE public.kala_convergence ADD CONSTRAINT kala_convergence_generation_check
      CHECK (generation ~ '^[A-Za-z0-9_.:-]+$' AND generation NOT IN ('current', 'published', 'retained'));
  END IF;
END
$check$;

-- The widened natural key. The table never had one (the surrogate convergence_id was the only key); the writer's own
-- dedup key is (mode, peak_date, signal_id) within a tier, so the key is that plus chart, tier and generation. NULL
-- columns never collide (PostgreSQL unique semantics), as for the writer.
CREATE UNIQUE INDEX IF NOT EXISTS uq_kala_convergence_generation_natural_key
  ON public.kala_convergence (chart_id, generation, horizon_tier, mode, peak_date, signal_id);

-- The served view. The base table keeps every generation; readers take the served one only.
CREATE OR REPLACE VIEW public.kala_convergence_served AS
SELECT c.*
  FROM public.kala_convergence c
 WHERE c.generation = COALESCE((SELECT h.generation FROM public.kala_layer_head h WHERE h.chart_id = c.chart_id), 'legacy');

COMMENT ON VIEW public.kala_convergence_served IS
  'Migration 1405: the rows of kala_convergence whose generation is the chart''s published head generation, else legacy. Every served or ordinary-rebuild reader reads this view; only a candidate build touches another generation of the base table.';

-- The view is readable by exactly the roles that read the base table (privileges are copied, not invented).
DO $grants$
DECLARE
  grantee_name text;
BEGIN
  FOR grantee_name IN
    SELECT DISTINCT CASE WHEN a.grantee = 0 THEN 'PUBLIC' ELSE quote_ident(r.rolname) END
      FROM pg_class c
      CROSS JOIN LATERAL aclexplode(c.relacl) a
      LEFT JOIN pg_roles r ON r.oid = a.grantee
     WHERE c.oid = 'public.kala_convergence'::regclass AND a.privilege_type = 'SELECT'
       AND (a.grantee = 0 OR r.rolname IS NOT NULL)
  LOOP
    EXECUTE format('GRANT SELECT ON public.kala_convergence_served TO %s', grantee_name);
  END LOOP;
END
$grants$;

-- ---------------------------------------------------------------------------------------------------------------------
-- Registry truth for ka_sangam (N.8: each signal must measure the claim it asserts, now that the table holds more than one
-- generation). Two statements, each guarded and idempotent; nothing else in asset_registry is touched.
--
-- NOT CHANGED, on purpose: count_sql ('SELECT count(*) FROM kala_convergence WHERE chart_id = $1'). The asset census reads it as a plain
-- single-table count of the target table (asset_census._count_scope_tail refuses a nested subselect or another relation), and the cockpit Clear
-- route derives its DELETE from it. A served-generation count would blind the census to ka_sangam's own rows; the count therefore still
-- includes a K9 candidate's rows while one exists (open point recorded in the PR).
--
-- TRIGGER EFFECT (real, intended; migration 596 nirmana_registry_receipt_invalidation, as 1397 states): changing
-- integrity_check_sql marks the asset_freshness rows of ka_sangam stale (registry_changed) until a governed build restores
-- them. Deploy with no ka_sangam build in flight.
--
-- (1) integrity_check_sql, conjunct (a) of the 670 contract: the accretion detector groups by the natural key. With two
--     generations present the SAME window legitimately exists once per generation, so the unscoped group is a false RED on
--     the first candidate build. The key gains generation, exactly as the unique index above. Every other conjunct is
--     row-wise and now also validates candidate rows. Refuses (changing nothing) if the stored text is neither the 670 form
--     nor the already-spliced form.
DO $registry$
DECLARE
  old_group constant text := 'GROUP BY chart_id, horizon_tier, mode, peak_date, signal_id';
  new_group constant text := 'GROUP BY chart_id, generation, horizon_tier, mode, peak_date, signal_id';
  stored text;
BEGIN
  SELECT integrity_check_sql INTO stored FROM public.asset_registry WHERE asset_id = 'ka_sangam' FOR UPDATE;
  IF NOT FOUND OR stored IS NULL THEN
    RAISE EXCEPTION '1405: ka_sangam has no registered integrity contract';
  END IF;
  IF position(new_group IN stored) = 0 THEN
    IF (length(stored) - length(replace(stored, old_group, ''))) / length(old_group) <> 1 THEN
      RAISE EXCEPTION '1405: ka_sangam integrity contract does not carry the 670 accretion conjunct exactly once';
    END IF;
    UPDATE public.asset_registry SET integrity_check_sql = replace(stored, old_group, new_group) WHERE asset_id = 'ka_sangam';
  END IF;
  SELECT integrity_check_sql INTO stored FROM public.asset_registry WHERE asset_id = 'ka_sangam';
  IF position(new_group IN stored) = 0 THEN
    RAISE EXCEPTION '1405: the generation-scoped accretion conjunct did not land';
  END IF;
END
$registry$;

-- (2) output-digest spec 980: the digest keys rows by (chart, tier, mode, peak_date, signal) and refuses duplicate keys; a
--     candidate generation repeats those keys. The replacement spec digests the served view (same key and value columns, same
--     chart pin), so the digest of the served partition is unchanged by a candidate build. The registry allows ONE current
--     spec per asset, so the 980 spec is RETIRED (not edited, not deleted), as 1399 did for ka_yojaka; past receipts keep their
--     FK to it. spec_sha256 by the real canonical_digest, validated by the real _validate_spec.
DO $digest$
DECLARE
  v_cur int; v_old int; v_new int;
BEGIN
  SELECT count(*) INTO v_cur FROM public.asset_output_digest_specs WHERE asset_id = 'ka_sangam' AND retired_at IS NULL;
  SELECT count(*) INTO v_old FROM public.asset_output_digest_specs
   WHERE asset_id = 'ka_sangam' AND retired_at IS NULL AND spec_sha256 = 'a0566b729d514d76e88dbd1c4135bf71e3396af00cb736267103ec6128aaf759';
  SELECT count(*) INTO v_new FROM public.asset_output_digest_specs
   WHERE asset_id = 'ka_sangam' AND retired_at IS NULL AND spec_sha256 = '1eb7f90d299c678805c78662da77eaca643a397d28874d90c0589d5459c48f16';
  IF v_cur = 0 THEN
    RAISE NOTICE '1405: ka_sangam has no current digest spec; nothing to replace';
    RETURN;
  END IF;
  IF v_cur <> 1 OR (v_old + v_new) <> 1 THEN
    RAISE EXCEPTION '1405: the live ka_sangam digest spec is neither spec 980 nor this migration''s spec (% current, % match 980, % match new)', v_cur, v_old, v_new;
  END IF;
  IF v_old = 1 THEN
    UPDATE public.asset_output_digest_specs SET retired_at = now()
     WHERE asset_id = 'ka_sangam' AND spec_sha256 = 'a0566b729d514d76e88dbd1c4135bf71e3396af00cb736267103ec6128aaf759' AND retired_at IS NULL;
    INSERT INTO public.asset_output_digest_specs (asset_id, spec_sha256, spec)
    VALUES ('ka_sangam', '1eb7f90d299c678805c78662da77eaca643a397d28874d90c0589d5459c48f16',
      '{"version":"nirmana-output-digest-spec-v1","components":[{"name":"kala_convergence","relation":"kala_convergence_served","key_columns":["chart_id","horizon_tier","mode","peak_date","signal_id"],"value_columns":["chart_id","window_start","window_end","convergence_score","constituent_factors","source_citation","signal_id","mode","peak_date","orb_strength","rarity_years","confidence_score","confidence_label","independent_current_count","is_off_dasha_discovery","horizon_tier","domain","confidence_label_relative","tier_basis"],"where_equals":{"chart_id":"482012f1-710e-4a25-994a-93821f5871aa"}}]}'::json)
    ON CONFLICT (asset_id, spec_sha256) DO NOTHING;
  END IF;
END
$digest$;
