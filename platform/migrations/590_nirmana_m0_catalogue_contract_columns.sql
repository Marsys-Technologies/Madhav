-- 590_nirmana_m0_catalogue_contract_columns.sql
--
-- NIRMĀṆA ELEVATION — Track M0, task M0-T2.
-- Add the four Asset Catalogue Contract columns to asset_registry and mechanically
-- backfill the two that are derivable without judgment.
--
-- ============================================================================
-- STATUS AT AUTHORING: **AUTHORED, NOT APPLIED.**
--   Nothing in this file has been executed against any database. Applying it is
--   gated on an ADHIKĀRIN ruling (charter §1 / P5) that had been requested and had
--   not returned when this file was written. The author (KĀRAKA, M0-T2) has no
--   authority to apply it and did not (charter H7 / invariant I16).
--   Do not treat this header as a record of application. The tracked runner's
--   ledger is the only record of that.
-- ============================================================================
--
-- NUMBER CHOICE — checked against BOTH the tree and the production ledger
--   Working tree:  max numbered file is 589 in platform/migrations/ and 586 in
--                  platform/supabase/migrations/. 590 is free in both.
--   Production `_migrations_applied` ledger (read-only SELECT, 2026-08-23):
--                  the highest applied number is 588, claimed by
--                  `588_samiksha_digest_journal.sql` (applied 2026-08-22 23:42:20Z) —
--                  a file that is NOT in this working tree. Nothing numbered 589-595
--                  is recorded. 590 is therefore free in the ledger as well.
--   Number 588 is doubly claimed (that ledger row plus this branch's
--   `588_remove_asset_build_protection.sql`); 590 avoids the collision entirely.
--   `migrate.ts` de-duplicates by filename, not by number, so a distinct filename is
--   what actually matters — but a fresh number keeps the audit trail readable.
--
-- WHY
--   NIRMANA_ELEVATION_PLAN_v4_0.md §3 adds two registration fields to the catalogue
--   contract carried from v3.0 §3:
--     `domain` — shared | chart. The planner's split axis (§6.2). Named per I9;
--                derived 1:1 from today's `scope`. `scope` is retained as a legacy
--                column until the rename migration, then dropped from serving paths.
--     `rung`   — R0..R5, the layer-ladder position (§8.4), derived from `layer`.
--   and v3.0 §3.2's lifecycle model requires two tombstone fields that were never
--   given columns:
--     `superseded_by`     — the resolvable successor pointer that turns RETIRED into
--                           SUPERSEDED_BY(x). Expressed as RETIRED + pointer rather
--                           than a fourth catalog_status value, so the existing
--                           catalog_status CHECK is NOT touched by this migration.
--     `data_disposition`  — mandatory on exit:
--                           RETAINED_AS_CAPITAL | SUPERSEDED_IN_PLACE | DROPPABLE.
--
--   Verified live 2026-08-23 via information_schema.columns: none of the four
--   columns exists on public.asset_registry (36 columns, 128 rows).
--
--   The contract these columns serve is written out, per kind and per field, at
--   00_ARCHITECTURE/control/ASSET_CATALOGUE_CONTRACT_v1_0.md.
--
-- DERIVATION — stated explicitly, and mechanical in both cases (no judgment)
--
--   domain  <-  scope        (asset_registry.scope is NOT NULL and CHECK-constrained
--                             to exactly these two values, so the mapping is total)
--       'global'      -> 'shared'      44 rows as of 2026-08-23
--       'per_chart'   -> 'chart'       84 rows as of 2026-08-23
--                                     ---
--                                     128
--
--   rung    <-  layer        (asset_registry.layer is NOT NULL and CHECK-constrained
--                             to exactly these six values, so the mapping is total)
--       'brahmagyan'  -> 'R0'  (L0)    40 rows
--       'ganita'      -> 'R1'  (L1)    19 rows
--       'bodha'       -> 'R2'  (L2)    22 rows
--       'kala'        -> 'R3'  (L3)    23 rows
--       'phala'       -> 'R4'  (L4)     9 rows
--       'mimamsa'     -> 'R5'  (L5)    15 rows
--                                     ---
--                                     128
--
--   WHY `layer` AND NOT `layer_index`:
--     `layer_index` is nullable and measurably dirty — 15 NULLs, plus 6 rows carrying
--     a bare digit ('0','1','2','3') instead of the 'Lx' form. Deriving `rung` from it
--     would leave 15 assets un-runged and propagate the dirt. `layer` is NOT NULL with
--     a CHECK covering exactly six values, so deriving from it cannot fail. Repairing
--     `layer_index`/`layer_name` is a separate M0 item and does not gate this one.
--
--   NO ASSET IS LEFT NULL BY EITHER BACKFILL, and no asset required a judgment call:
--   both inputs are NOT NULL with CHECK constraints that enumerate exactly the value
--   sets mapped above. If a future value were added to either CHECK without extending
--   the CASE here, the corresponding row would fall to NULL rather than to a guess —
--   which is why the verification block at the end fails loudly on any NULL.
--
-- WHAT THIS MIGRATION DELIBERATELY DOES NOT DO (each is a parked question, not an
-- oversight — see ASSET_CATALOGUE_CONTRACT_v1_0.md §10):
--   * It does NOT add 'source' to asset_registry_asset_kind_check. The contract needs
--     that value (v3.0 §3.4/§3.6, `lel_events`), but relaxing a CHECK is a schema change
--     the plan does not name -> charter P5, ADHIKĀRIN's call.
--   * It does NOT add a fourth catalog_status value. SUPERSEDED is represented as
--     RETIRED + superseded_by.
--   * It does NOT backfill `data_disposition` for the one RETIRED asset
--     (`ka_gochara_sweep`). Its disposition is almost certainly RETAINED_AS_CAPITAL —
--     charter P1 names its 38,287 v1 rows as unrecoverable except from the 2026-08-23
--     snapshot — but "almost certainly" is a guess, and a guess written into a lifecycle
--     field is fabrication (H6). It stays NULL until ADHIKĀRIN rules (G1).
--   * It does NOT add columns for the natural-key partition declaration, the authority
--     pointer, `protected_generations`, or the consumer map. Those are contract
--     requirements with no plan-named migration; a column nothing can fill reads as a
--     present-but-empty signal, which CLAUDE.md §N.8 forbids.
--   * It does NOT drop, rename or rewrite `scope`. The rename lands in M1 behind a
--     compatibility window (plan §6.1). Until then both columns coexist and C-18
--     asserts they agree.
--   * It touches NO asset data (invariant I14) and NO table other than asset_registry.
--
-- ASSETS LEFT NULL, EXPLICITLY:
--   domain           : none  (all 128 derive)
--   rung             : none  (all 128 derive)
--   superseded_by    : all 128 — nothing in the catalogue currently names a successor;
--                      `ka_gochara_sweep` is superseded in substance by
--                      `ka_gochara_v3_century_materialize`, but recording that is a
--                      lifecycle ruling (G1), not a mechanical derivation.
--   data_disposition : all 128, including the one RETIRED row — see above.
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS; constraints added only when absent; the
--   backfills are guarded by `WHERE <col> IS NULL` so re-running never overwrites a
--   value a later ruling set by hand.
-- REVERSIBLE: `ALTER TABLE asset_registry DROP COLUMN IF EXISTS domain, rung,
--   superseded_by, data_disposition;` — no data outside these four columns is altered.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Columns
-- ---------------------------------------------------------------------------

ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS domain           text;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS rung             text;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS superseded_by    text;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS data_disposition text;

COMMENT ON COLUMN asset_registry.domain IS
  'shared | chart. The planner split axis (Nirmana plan v4 §6.2). Derived 1:1 from scope: global->shared, per_chart->chart. Supersedes scope on serving paths after the M1 rename.';
COMMENT ON COLUMN asset_registry.rung IS
  'R0..R5, the layer-ladder position (Nirmana plan v4 §8.4). Derived from layer: brahmagyan->R0, ganita->R1, bodha->R2, kala->R3, phala->R4, mimamsa->R5.';
COMMENT ON COLUMN asset_registry.superseded_by IS
  'asset_id of the successor that replaced this asset. Non-null only on catalog_status=RETIRED; together they express the SUPERSEDED_BY(x) lifecycle state (contract §3).';
COMMENT ON COLUMN asset_registry.data_disposition IS
  'RETAINED_AS_CAPITAL | SUPERSEDED_IN_PLACE | DROPPABLE. Mandatory on exit from service; NULL for any asset that is not RETIRED (contract §3.1).';

-- ---------------------------------------------------------------------------
-- 2. Value constraints (NULL permitted on all four — the contract's presence
--    requirements are conditional and are enforced by the CI guard, not by NOT NULL,
--    so that an unruled lifecycle field can stay honestly empty.)
-- ---------------------------------------------------------------------------

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_domain_check'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_domain_check
      CHECK (domain IS NULL OR domain IN ('shared','chart'));
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_rung_check'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_rung_check
      CHECK (rung IS NULL OR rung IN ('R0','R1','R2','R3','R4','R5'));
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_data_disposition_check'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_data_disposition_check
      CHECK (data_disposition IS NULL
             OR data_disposition IN ('RETAINED_AS_CAPITAL','SUPERSEDED_IN_PLACE','DROPPABLE'));
  END IF;

  -- superseded_by must resolve to a real asset. A self-reference is nonsense and is
  -- excluded. NOT VALID is deliberately NOT used: the column is empty at apply time,
  -- so the FK validates instantly and is trustworthy from the first row.
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_superseded_by_fkey'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_superseded_by_fkey
      FOREIGN KEY (superseded_by) REFERENCES asset_registry(asset_id)
      ON DELETE RESTRICT;
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_superseded_by_not_self'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_superseded_by_not_self
      CHECK (superseded_by IS NULL OR superseded_by <> asset_id);
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 3. Mechanical backfill — domain from scope
-- ---------------------------------------------------------------------------

UPDATE asset_registry
   SET domain = CASE scope
                  WHEN 'global'    THEN 'shared'
                  WHEN 'per_chart' THEN 'chart'
                END
 WHERE domain IS NULL;

-- ---------------------------------------------------------------------------
-- 4. Mechanical backfill — rung from layer  (L0->R0 .. L5->R5)
-- ---------------------------------------------------------------------------

UPDATE asset_registry
   SET rung = CASE layer
                WHEN 'brahmagyan' THEN 'R0'   -- L0
                WHEN 'ganita'     THEN 'R1'   -- L1
                WHEN 'bodha'      THEN 'R2'   -- L2
                WHEN 'kala'       THEN 'R3'   -- L3
                WHEN 'phala'      THEN 'R4'   -- L4
                WHEN 'mimamsa'    THEN 'R5'   -- L5
              END
 WHERE rung IS NULL;

-- superseded_by and data_disposition are intentionally NOT backfilled. Every value
-- either of them could take is a lifecycle ruling, not a derivation. See the header.

-- ---------------------------------------------------------------------------
-- 5. Verification — the migration fails rather than reporting a silent partial apply.
--    (CLAUDE.md §N.4: never trust a migration runner's success report without a check
--     the migration itself performs.)
-- ---------------------------------------------------------------------------

DO $$
DECLARE
  null_domain   int;
  null_rung     int;
  bad_domain    int;
  bad_rung      int;
BEGIN
  SELECT count(*) INTO null_domain FROM asset_registry WHERE domain IS NULL;
  SELECT count(*) INTO null_rung   FROM asset_registry WHERE rung   IS NULL;

  SELECT count(*) INTO bad_domain FROM asset_registry
   WHERE domain IS DISTINCT FROM (CASE scope WHEN 'global' THEN 'shared'
                                             WHEN 'per_chart' THEN 'chart' END);

  SELECT count(*) INTO bad_rung FROM asset_registry
   WHERE rung IS DISTINCT FROM (CASE layer WHEN 'brahmagyan' THEN 'R0' WHEN 'ganita' THEN 'R1'
                                           WHEN 'bodha' THEN 'R2' WHEN 'kala' THEN 'R3'
                                           WHEN 'phala' THEN 'R4' WHEN 'mimamsa' THEN 'R5' END);

  IF null_domain > 0 OR null_rung > 0 OR bad_domain > 0 OR bad_rung > 0 THEN
    RAISE EXCEPTION
      'migration 590 backfill incomplete: % null domain, % null rung, % mis-derived domain, % mis-derived rung',
      null_domain, null_rung, bad_domain, bad_rung;
  END IF;

  RAISE NOTICE 'migration 590: domain and rung derived for all % asset_registry rows',
    (SELECT count(*) FROM asset_registry);
END $$;

COMMIT;
