-- 1267_asset_registry_rider_producer_relation.sql
--
-- Suvarna Track I, item TI-L0-08 (finding CF-02, SS ruling Q6 of 2026-10-01; number 1267 allocated by SS):
-- the REGISTRY SIDE of the rider relation, so a sibling's dispatch can count for a rider ("producer_covered").
--
--   * ADDS one nullable column  asset_registry.producer_asset_id  (text, self-referencing FK, not-self CHECK);
--   * SETS it for the three riders that the declarations file already marks `kind: rider` and the frozen T0
--     manifest already marks `execution_obligation: producer_covered` with the same producer ids:
--         bg_nakshatra_medical -> bg_medical_mappings   (writers/bg_medical_mappings.py:26, same class)
--         bg_sign_medical      -> bg_medical_mappings   (writers/bg_medical_mappings.py:25, same class)
--         bg_transit_engine    -> bg_transit_rules      (writers/bg_transit_rules.py:12, second @register)
--   * NOTHING ELSE: no row other than those three is written, no existing column is altered, no data is touched.
--
-- CONCERN
--   Census Build.exercised reads FAIL for bg_sign_medical ("registered with a writer and never dispatched": the one
--   L0 asset with a writer and no build_run_assets row) and will read the same for bg_nakshatra_medical and
--   bg_transit_engine once TI-L0-07 (1266) flips their has_writer. They are riders: their rows are written by the
--   producer's writer class, so the producer's dispatch IS their dispatch. SS Q6: "a sibling's dispatch counts
--   (producer_covered) when the registry declares the rider relation". Until now the registry had NO place to declare
--   it: asset_kind is CHECK-limited to data/service/artifact (no 'rider'), superseded_by is a lifecycle FK with the
--   opposite meaning (a replaced asset), and depends_on is a build-ORDER edge (a rider does not read its producer;
--   it is written by the same pass). The relation exists only in the declarations file (kind: rider) and in the T0
--   manifest JSON (producer_id). This migration gives the registry its own, queryable, FK-checked copy.
--
-- DESIGN CHOICE FOR SS (flagged): a new nullable column is the minimal registry-side declaration that does not
-- overload an existing column. Alternatives considered and NOT taken: (a) widen asset_kind with 'rider' (changes a
-- CHECK that every kind-reading consumer assumes closed, and the declarations file already owns `kind`); (b) reuse
-- superseded_by (wrong meaning); (c) write nothing and keep the relation only in the T0 manifest (then the
-- registry cannot answer the question Q6 asks of it). If SS prefers (c), return the number unused.
--
-- NO READER YET: nothing reads producer_asset_id until the inspector (Track E, asset_census.py) or the dispatch
-- gate learns to. So the serving and verdict effect of this file by itself is NONE; it is the precondition for
-- the census to count the producer's dispatch for the rider. Verified by grep at authoring (origin/main 6758c39b1):
-- no `SELECT *`/to_jsonb(asset_registry) consumer exists in platform, platform-mcp or the sidecar, so an added
-- column changes no response shape or digest.
--
-- SERVING EFFECT AT APPLY
--   * Does NOT fire nirmana_registry_receipt_invalidation: its column list is depends_on, natural_key_partition,
--     health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, scope, has_writer, is_active,
--     target_table; ADD COLUMN is not an UPDATE and the UPDATE below does not name any of them. NO asset goes stale.
--   * No data, no served surface, no freshness row changes.
--   * Takes ACCESS EXCLUSIVE on asset_registry for the ALTERs (brief; SET LOCAL lock_timeout = 5s fails fast).
--
-- GUARDS (every one raises rather than skip; a missing rider row in a fresh bootstrap is skipped with a NOTICE)
--   * the producer row must exist, be active, asset_kind = 'data' and has_writer = true (a producer without a
--     writer cannot cover anything) - otherwise RAISE (dependency trap);
--   * the rider row must have target_table = its own id and asset_kind = 'data' (the audited identity);
--   * an existing non-NULL producer_asset_id that differs from the audited one is DRIFT: RAISE, never overwrite;
--   * the self-referencing FK (ON DELETE RESTRICT) and the not-self CHECK are added only if absent
--     (pg_constraint lookup), so a re-run is a no-op.
--   A post-check re-reads the three rows and the column/constraint catalog and raises unless all are as intended.
--
-- PRIVILEGE (P2 rule, W1_PRIVILEGE_AUDIT): runs as amjis_app, the OWNER of asset_registry. ALTER TABLE ... ADD
-- COLUMN / ADD CONSTRAINT / COMMENT need table ownership, NOT CREATE on schema public; the FK references the same
-- table (owner holds REFERENCES). No CREATE FUNCTION/TRIGGER/TABLE/INDEX (those would need CREATE on schema public
-- and would fail for the routine runner; the FK and CHECK create no schema object of their own). No GRANT: the
-- table-level SELECT grants (suvarna_reader, role_web_serve, ...) already cover the new column. Proven as amjis_app
-- (NOSUPERUSER, NOINHERIT, USAGE but no CREATE on schema public).
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS; constraints guarded by a catalog lookup; assignments skip when equal.
--
-- NOT DONE HERE
--   * The inspector/gate reading the column (Track E path; asset_census.py is verdict-moving and held for SS).
--   * The seed literal / a declarations-file cross-check (asset_registry_seed.ts and asset_declarations.json are
--     owned by PR #2984). The seed's INSERT lists an explicit column set, so the new nullable column is simply left
--     NULL on a fresh bootstrap until a follow-up seeds it; a re-seed does not touch it.
--   * Dispatch of any rider or producer; has_writer flips (migration 1266); any rider beyond the three audited.
--
-- ROLLBACK (ops reference, not executed): ALTER TABLE asset_registry DROP COLUMN producer_asset_id; (drops both
-- constraints with it). A new reviewed migration against the then-current state; never edit this file after apply.
--
-- VERIFY AFTER APPLY by production structure, not the deploy log (Trap 103):
--   SELECT asset_id, producer_asset_id FROM asset_registry WHERE producer_asset_id IS NOT NULL ORDER BY 1;
--     -- bg_nakshatra_medical|bg_medical_mappings, bg_sign_medical|bg_medical_mappings, bg_transit_engine|bg_transit_rules
--   SELECT conname FROM pg_constraint WHERE conrelid = 'asset_registry'::regclass AND conname LIKE 'asset_registry_producer%';
--     -- asset_registry_producer_asset_id_fkey, asset_registry_producer_not_self
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS producer_asset_id text;

COMMENT ON COLUMN asset_registry.producer_asset_id IS
    'Rider relation (SS Q6, TI-L0-08): NULL for an asset with its own build; for a RIDER, the asset_id whose writer class also registers and writes this asset, so the producer''s dispatch counts for it (producer_covered). Not a build-order edge (see depends_on) and not a lifecycle link (see superseded_by).';

DO $m1267$
DECLARE
    v_rider    text;
    v_producer text;
    v_kind     text;
    v_target   text;
    v_current  text;
    p_active   boolean;
    p_kind     text;
    p_writer   boolean;
    v_rows     bigint;
BEGIN
    -- constraints, added only when absent
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                    WHERE conrelid = 'public.asset_registry'::regclass AND conname = 'asset_registry_producer_asset_id_fkey') THEN
        ALTER TABLE asset_registry
            ADD CONSTRAINT asset_registry_producer_asset_id_fkey
            FOREIGN KEY (producer_asset_id) REFERENCES asset_registry(asset_id) ON DELETE RESTRICT;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                    WHERE conrelid = 'public.asset_registry'::regclass AND conname = 'asset_registry_producer_not_self') THEN
        ALTER TABLE asset_registry
            ADD CONSTRAINT asset_registry_producer_not_self
            CHECK (producer_asset_id IS NULL OR producer_asset_id <> asset_id);
    END IF;

    -- the three audited riders
    FOREACH v_rider IN ARRAY ARRAY['bg_nakshatra_medical', 'bg_sign_medical', 'bg_transit_engine'] LOOP
        v_producer := CASE v_rider WHEN 'bg_transit_engine' THEN 'bg_transit_rules' ELSE 'bg_medical_mappings' END;

        SELECT asset_kind, target_table, producer_asset_id
          INTO v_kind, v_target, v_current
          FROM asset_registry WHERE asset_id = v_rider FOR UPDATE;
        IF NOT FOUND THEN
            RAISE NOTICE '1267: rider % is not in asset_registry; skipped', v_rider;
            CONTINUE;
        END IF;
        IF v_kind IS DISTINCT FROM 'data' OR v_target IS DISTINCT FROM v_rider THEN
            RAISE EXCEPTION '1267: rider % has drifted from the audited state (asset_kind=%, target_table=%); refusing to declare the relation',
                v_rider, v_kind, v_target;
        END IF;

        SELECT is_active, asset_kind, has_writer INTO p_active, p_kind, p_writer
          FROM asset_registry WHERE asset_id = v_producer;
        IF NOT FOUND OR p_active IS DISTINCT FROM true OR p_kind IS DISTINCT FROM 'data' OR p_writer IS DISTINCT FROM true THEN
            RAISE EXCEPTION '1267: producer % of rider % is missing, inactive, not a data asset, or has no writer (is_active=%, asset_kind=%, has_writer=%)',
                v_producer, v_rider, p_active, p_kind, p_writer;
        END IF;

        IF v_current IS NULL THEN
            UPDATE asset_registry SET producer_asset_id = v_producer
             WHERE asset_id = v_rider AND producer_asset_id IS NULL;
            GET DIAGNOSTICS v_rows = ROW_COUNT;
            IF v_rows <> 1 THEN
                RAISE EXCEPTION '1267: setting producer_asset_id of % touched % rows, expected 1', v_rider, v_rows;
            END IF;
        ELSIF v_current = v_producer THEN
            RAISE NOTICE '1267: % already declares producer %; skipped', v_rider, v_producer;
        ELSE
            RAISE EXCEPTION '1267: rider % already declares producer % (audited: %); refusing to overwrite',
                v_rider, v_current, v_producer;
        END IF;
    END LOOP;

    -- Post-check: re-read the catalog and the three rows, never trust a silent no-op.
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = 'asset_registry'
                      AND column_name = 'producer_asset_id' AND data_type = 'text' AND is_nullable = 'YES') THEN
        RAISE EXCEPTION '1267: asset_registry.producer_asset_id is not a nullable text column after the migration';
    END IF;
    IF (SELECT count(*) FROM pg_constraint
         WHERE conrelid = 'public.asset_registry'::regclass
           AND conname IN ('asset_registry_producer_asset_id_fkey', 'asset_registry_producer_not_self')) <> 2 THEN
        RAISE EXCEPTION '1267: the producer_asset_id FK / not-self CHECK are not both present after the migration';
    END IF;
    IF EXISTS (SELECT 1 FROM asset_registry r
                WHERE r.asset_id IN ('bg_nakshatra_medical', 'bg_sign_medical', 'bg_transit_engine')
                  AND r.producer_asset_id IS DISTINCT FROM CASE r.asset_id WHEN 'bg_transit_engine' THEN 'bg_transit_rules' ELSE 'bg_medical_mappings' END) THEN
        RAISE EXCEPTION '1267: a rider does not declare its audited producer after the migration';
    END IF;
END
$m1267$;
