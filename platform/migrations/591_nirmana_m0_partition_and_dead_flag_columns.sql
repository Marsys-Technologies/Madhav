-- 591_nirmana_m0_partition_and_dead_flag_columns.sql
--
-- NIRMĀṆA ELEVATION — Track M0, task M0-T47.
-- Add the two `asset_registry` columns ruling D-39 part 4 authorised:
--   (a) `natural_key_partition` — the co-writer partition declaration (plan v3.0 Phase 0.4,
--       plan v4 §14.1 "semantic de-duplication with declared co-writer partitions",
--       ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9 / §10.3, contract rule C-25, M0 exit
--       criterion 5 "multi-producer partitions = 0").
--   (b) `dead_flag` — the registered-but-dead flag (plan v3.0 Phase 0.8a "Registered-but-dead
--       flagged (`bg_gochara_citation_resolution`)", v3.0 §3.6, M0 exit criterion 8
--       "active assets with neither build coverage nor a dead flag = 0", guard rule X-03).
--
-- ============================================================================
-- STATUS AT AUTHORING: **AUTHORED, NOT APPLIED.**
--   Nothing in this file has been executed against any database. Every observation
--   quoted below was obtained on a READ-ONLY session
--   (`SET default_transaction_read_only = on`; SELECT only). Applying it is a
--   production write and is ADHIKĀRIN's to authorise — exactly the sequence 590
--   followed (authored at M0-T2, applied at M0-T12B under D-20). The author
--   (KĀRAKA, M0-T47) has no authority to apply it and did not (charter H7 /
--   invariant I16). This header is not a record of application; the tracked
--   runner's `_migrations_applied` ledger is the only record of that.
-- ============================================================================
--
-- AUTHORITY
--   D-39 part 4 (ADHIKĀRIN, 2026-08-23T09:25:50Z) — "CONFIRMED: all three are M0's.
--   Both need a column, and by D-4's reasoning a Phase-0 step that names the thing has
--   named the change that creates it, so the columns are inside the plan's naming and
--   NOT reserved by P5 — subject to D-4's standing conditions (additive only, mechanical
--   backfill only, NULL where not derivable, verify applied, never edit after,
--   PARĪKṢAKA verifies)."
--
--   This file supersedes ASSET_CATALOGUE_CONTRACT_v1_0.md §10.3's holding that these
--   columns must not be added yet. §10.3 was written before D-39 and reasoned that the
--   plan did not name them; D-39 part 4 independently re-derived the named-field test and
--   found that it does. §10.3's underlying §N.8 worry is answered below, not waved away.
--
-- NUMBER + PATH CHOICE — checked against BOTH the tree and the production ledger
--   Directory: 587, 588, 589 and 590 all live in `platform/migrations/`, NOT in
--              `platform/supabase/migrations/` (whose highest numbered file is 586).
--              Verified by listing both directories, 2026-08-23. This file therefore
--              goes in `platform/migrations/`, next to its 590 precedent.
--   Working tree: no file numbered 591 exists anywhere in the repository
--              (`find . -name '591*'` returns nothing outside node_modules/.git).
--   Production `_migrations_applied` ledger (READ-ONLY SELECT, 2026-08-23):
--              max id 450, 450 rows, highest applied number **590**
--              (`590_nirmana_m0_catalogue_contract_columns.sql`, applied
--              2026-08-23T05:36:13.833986+00:00, id 450). Nothing numbered 591 is
--              recorded. 591 is free in the tree and in the ledger.
--
-- LIVE STATE THIS MIGRATION WAS AUTHORED AGAINST (READ-ONLY, 2026-08-23)
--   `public.asset_registry`: 128 rows, **40 columns** (36 original + the four migration
--   590 added: domain, rung, superseded_by, data_disposition — all live).
--   NEITHER of the two columns below exists, and no existing column carries either
--   meaning under a different name. Checked, column by column:
--     * `target_table` names the table, never a partition within it.
--     * `clear_tables` is a rebuild-scope array (1 row sets it); not a partition.
--     * `count_sql` is a serving query, not a declaration — see the backfill section.
--     * `has_writer` (boolean, NOT NULL, default false) is NOT the dead flag and must not
--       be read as one: 7 live rows carry has_writer=false and 5 of them DO have
--       `asset_throughput` coverage (bg_ephemeris_engine, bg_nakshatra_medical,
--       bg_panchanga, bg_sarvatobhadra_grid, bg_transit_engine). It answers "is a writer
--       registered", not "is this asset declared dead". It is additionally wrong on 2
--       rows against the live @register AST scan (D-25; bg_nakshatra_medical,
--       bg_transit_engine), so even the proxy reading is unsound.
--     * `is_active=false` / `catalog_status='RETIRED'` mean "has exited service" — a
--       different lifecycle state, and already X-03's exemption. Exactly 1 row each
--       (`ka_gochara_sweep`).
--     * `platform/scripts/governance/asset_catalogue_declared_cowriters.json` declares
--       co-writer GROUP MEMBERSHIP for rule X-01 and states in its own text that it does
--       NOT assert partition disjointness ("partition_declared": false on all five
--       groups, "No partition column exists"). It is not a duplicate of (a).
--   Live CHECK constraints on asset_registry at authoring time: asset_kind
--   (data|service|artifact), asset_type (data|service), catalog_status
--   (CURRENT|DRAFT|RETIRED), data_disposition, domain, layer, rung, scope,
--   service_health, storage_type, superseded_by_not_self; plus FK
--   superseded_by -> asset_registry(asset_id) and PK (asset_id).
--   **This migration changes NONE of them.** The `source` catalog/kind question
--   (G1-BLOCKED / SOURCE-BLOCKED, contract §10.1) stays exactly where it was.
--
-- ---------------------------------------------------------------------------
-- (a) `natural_key_partition` — WHAT IT IS
--
--   The de-duplication invariant is one authoritative producer per
--   (`target_table` × generation × natural-key partition) — never one per table
--   (contract §4.9). Five tables carry more than one registry producer, measured live
--   2026-08-23:
--       bodha_msr_signals     7  (bo_arudha, bo_laksana, bo_laksana_rerank,
--                                 bo_nakshatra_semantic, bo_special_lagna,
--                                 bo_sudarshana, bo_vargottama_dhana)
--       chart_facts           5  (ga_ayurdaya, ga_nakshatra, ga_panchanga,
--                                 ga_positions, ga_sensitive_degree)
--       brahma_class_priors   2  (bg_class_lifetime_counts, bg_class_priors)
--       classical_text_chunks 2  (bg_text_index, bg_texts)
--       kala_gochara_windows  2  (ka_gochara, ka_gochara_sweep — the latter RETIRED)
--                            --
--                            18 co-writer rows
--
--   The column holds a **boolean SQL predicate over the row's own `target_table`**
--   naming the slice this writer owns — e.g. `fact_category = 'ayurdaya'`. That shape is
--   chosen deliberately over a free-form label: a predicate is EVALUABLE, so a future
--   detector can test pairwise disjointness for real
--   (`SELECT count(*) FROM <target_table> WHERE (<p_a>) AND (<p_b>)` must be 0), which
--   is the only way contract rule C-25 stops being `not_checkable`. A label would give
--   C-25 a column to read and still no way to be wrong — the §N.8 defect wearing a
--   schema change's clothes.
--
--   **This migration does NOT make C-25 checkable and must not be reported as having
--   done so.** It creates the place the declaration can live. Writing the declarations
--   is per-asset work; building the disjointness detector is separate again. C-25 stays
--   `not_checkable` until BOTH exist.
--
-- (b) `dead_flag` — WHAT IT IS
--
--   Nullable BOOLEAN, deliberately three-state:
--       NULL   — never adjudicated. The state every row is born in and the state all 128
--                are in after this migration.
--       true   — declared registered-but-dead: this asset is active in the registry and
--                nothing builds it, and that is KNOWN and DECLARED, not an accident.
--       false  — declared alive: a build is expected, so an absence of build coverage is
--                a genuine finding.
--   NULL is NOT "alive". A row that has never been adjudicated must keep counting as a
--   violation, which is why there is no `DEFAULT false` here: a default would write a
--   positive claim ("this asset is fine") that no detector produced, onto all 128 rows
--   at once — CLAUDE.md §N.8, the exact defect this campaign exists to remove.
--
-- ---------------------------------------------------------------------------
-- BACKFILL — THERE IS NONE, AND THAT IS THE FINDING, NOT AN OMISSION
--
--   D-4's standing conditions require a MECHANICAL backfill and NULL where a value is
--   not derivable. Both columns fall on the NULL side, and the evidence was measured
--   rather than assumed:
--
--   (a) natural_key_partition — 128/128 NULL.
--       The only candidate mechanical source is `count_sql`, and it does not carry the
--       declaration. Measured live over all 18 co-writer rows: 14 carry a discriminating
--       predicate beyond `chart_id` (fact_category / signal_type_class / fact_kind /
--       generation), and **4 carry none at all** —
--           bo_laksana_rerank (bodha_msr_signals) — filters on
--               `graph_node_strength_contribution_jsonb IS NOT NULL`, i.e. it re-ranks
--               rows other writers inserted; that is not a disjoint insert partition.
--           bg_class_priors (brahma_class_priors) — `SELECT COUNT(*) FROM
--               brahma_class_priors`, the WHOLE table, overlapping its co-writer.
--           bg_text_index (classical_text_chunks) — `count(DISTINCT topic_tag) … WHERE
--               embedding IS NOT NULL`, a distinct-count over the whole table.
--           bg_texts (classical_text_chunks) — counts two whole tables added together.
--       So a count_sql-derived backfill is neither total (4 of 18 fall to NULL anyway)
--       nor sound (it would be a serving query re-read as a declaration — §N.7 item 1/3,
--       a proxy standing in for the claim, and §N.5's rule that a value must be
--       REFERENCED rather than re-derived). Guessing the remaining 14 from string
--       extraction would be H6. They stay NULL and are written by whoever declares them.
--
--   (b) dead_flag — 128/128 NULL.
--       "Registered but dead" is a DECLARATION (charter G1: provision / demote / retire —
--       v3.0 §3.6, "never leave a CURRENT asset that nothing can build"), not a
--       derivation. It also cannot be computed in SQL at all: it needs the @register AST
--       scan, which lives outside the database, and its only in-database proxy
--       (`has_writer`) is measurably wrong on 2 rows.
--       For the record, the population a declaration would have to address — measured
--       live 2026-08-23, active + non-source + no `asset_throughput` row, which is
--       exactly guard rule X-03's detector:
--           bg_gochara_citation_resolution  CURRENT · data · R0 · has_writer=false
--           lel_events                      DRAFT   · data · R5 · has_writer=false
--       Both are already named in v3.0 §3.6 and contract §7 as G1 decisions that this
--       task does not make and this migration does not encode.
--
--   THIS FILE CONTAINS ZERO `UPDATE` STATEMENTS. That is structural, greppable, and is
--   the honest form of "mechanical backfill only, NULL where not derivable".
--
-- ---------------------------------------------------------------------------
-- WHY AN ALL-NULL COLUMN IS NOT THE §N.8 EMPTY SIGNAL contract §10.3 FEARED
--
--   §N.8's prohibition is on a signal that READS GREEN with no detector behind it. NULL
--   here reads as "not declared", and both criteria are written so that NULL keeps
--   counting AGAINST the catalogue:
--     * criterion 5 stays FAIL/not-measurable while any co-writer's partition is NULL;
--     * criterion 8 / X-03 keep reporting their 2 violations while dead_flag is NULL,
--       because NULL is not `true`.
--   Neither column can manufacture a pass. What they remove is the structural
--   impossibility — today the campaign is asked to declare things it has nowhere to
--   declare, so the criteria cannot reach zero even in principle.
--
-- WHAT THIS MIGRATION DELIBERATELY DOES NOT DO
--   * It does NOT edit `platform/scripts/governance/check_asset_catalogue_contract.py`.
--     Teaching X-03 to exempt `dead_flag = true` would make something PASS that
--     previously FAILED — a WEAKENING CI edit under D-41 part 2, presumptively H3, and
--     it requires ADHIKĀRIN's ruling. Until that ruling, this column changes no gate's
--     verdict in either direction.
--   * It does NOT set any value. See the backfill section.
--   * It does NOT change any existing column, CHECK, FK, index or default, and does not
--     touch `catalog_status`, `asset_kind` or the `source` question (contract §10.1).
--   * It does NOT touch `platform/scripts/seed/asset_registry_seed.ts`. Both new columns
--     are consequently ABSENT from the seed's INSERT and DO UPDATE SET lists, which is
--     the already-proven durable class (`domain`, `rung`, `has_substeps`,
--     `integrity_check_sql` are all absent the same way) — a re-seed cannot revert a
--     value written here. Stated as a property of what was NOT edited, not as a claim
--     that anything was verified about the seed's behaviour at runtime.
--   * It touches NO asset data (invariant I14) and NO table other than asset_registry.
--   * It does NOT make C-25 checkable, and nothing downstream should read it as doing so.
--
-- IDEMPOTENT: ADD COLUMN IF NOT EXISTS; constraints added only when absent; no UPDATE
--   exists to re-run, so a second apply cannot overwrite a declaration someone has since
--   written by hand.
-- REVERSIBLE: `ALTER TABLE asset_registry
--                DROP COLUMN IF EXISTS natural_key_partition,
--                DROP COLUMN IF EXISTS dead_flag;`
--   — no data outside these two columns is altered, and both are empty at apply time.

BEGIN;

-- ---------------------------------------------------------------------------
-- 1. Columns
-- ---------------------------------------------------------------------------

ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS natural_key_partition text;
ALTER TABLE asset_registry ADD COLUMN IF NOT EXISTS dead_flag             boolean;

COMMENT ON COLUMN asset_registry.natural_key_partition IS
  'Co-writer partition declaration (Nirmana plan v3.0 Phase 0.4; ASSET_CATALOGUE_CONTRACT_v1_0.md §4.9). A boolean SQL predicate over this row''s target_table naming the slice this writer owns, e.g. "fact_category = ''ayurdaya''". REQUIRED for every producer of a co-written target_table; NULL means the partition has not been declared, never that the writer owns the whole table. Held as an evaluable predicate so pairwise disjointness can one day be tested for real (contract rule C-25); the detector does not exist yet and C-25 stays not_checkable until it does.';
COMMENT ON COLUMN asset_registry.dead_flag IS
  'Registered-but-dead declaration (Nirmana plan v3.0 Phase 0.8a / §3.6; M0 exit criterion 8; guard rule X-03). THREE-STATE: NULL = never adjudicated (the default state; still counts as a violation); true = declared registered-but-dead, i.e. active in the registry with nothing that builds it, known and declared; false = declared alive, a build is expected so its absence is a real finding. Setting true is a charter G1 disposition recorded in DECISIONS.jsonl, never a derivation. NOT the same as has_writer (a writer''s existence), is_active or catalog_status=RETIRED (exit from service).';

-- ---------------------------------------------------------------------------
-- 2. Value constraints
--    (NULL permitted on both — the contract's presence requirements are conditional and
--     are enforced by the CI guard, not by NOT NULL, so an unadjudicated field can stay
--     honestly empty. Same discipline as migration 590 §2.)
-- ---------------------------------------------------------------------------

DO $$
BEGIN
  -- A declared partition must be non-blank. A whitespace-only string would satisfy
  -- "IS NOT NULL" while declaring nothing, which is precisely the empty signal.
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_natural_key_partition_nonblank'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_natural_key_partition_nonblank
      CHECK (natural_key_partition IS NULL OR btrim(natural_key_partition) <> '');
  END IF;

  -- A partition is a slice OF a table. A row with no target_table has no table to
  -- partition, so a declaration there is meaningless rather than merely unused.
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_natural_key_partition_needs_table'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_natural_key_partition_needs_table
      CHECK (natural_key_partition IS NULL OR target_table IS NOT NULL);
  END IF;

  -- A RETIRED / inactive asset has EXITED service; "registered but dead" is a statement
  -- about an asset still registered as live. Declaring both at once is a contradiction,
  -- and the lifecycle exit is already expressed by catalog_status + data_disposition
  -- (migration 590). Guarding it here keeps the two vocabularies from overlapping.
  IF NOT EXISTS (SELECT 1 FROM pg_constraint
                 WHERE conname = 'asset_registry_dead_flag_not_retired'
                   AND conrelid = 'public.asset_registry'::regclass) THEN
    ALTER TABLE asset_registry
      ADD CONSTRAINT asset_registry_dead_flag_not_retired
      CHECK (dead_flag IS NOT TRUE
             OR (catalog_status <> 'RETIRED' AND is_active IS NOT FALSE));
  END IF;
END $$;

-- ---------------------------------------------------------------------------
-- 3. Backfill — NONE. Intentionally. See the header: neither value is mechanically
--    derivable, and D-4's standing conditions require NULL rather than a guess (H6).
--    There is deliberately no UPDATE statement anywhere in this file.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- 4. Verification — the migration fails rather than reporting a silent partial apply.
--    (CLAUDE.md §N.4: never trust a migration runner's success report without a check
--     the migration itself performs. The claim this block asserts is exactly what this
--     migration is responsible for — the two columns and the three constraints EXIST
--     afterwards — and nothing more. It deliberately does NOT assert anything about the
--     columns' contents beyond REPORTING them, because this migration writes no content
--     and a later G1 declaration must not make a re-run fail.)
-- ---------------------------------------------------------------------------

DO $$
DECLARE
  n_cols        int;
  n_constraints int;
  n_rows        int;
  n_part        int;
  n_dead_true   int;
  n_dead_false  int;
BEGIN
  SELECT count(*) INTO n_cols
    FROM information_schema.columns
   WHERE table_schema = 'public' AND table_name = 'asset_registry'
     AND column_name IN ('natural_key_partition', 'dead_flag');

  SELECT count(*) INTO n_constraints
    FROM pg_constraint
   WHERE conrelid = 'public.asset_registry'::regclass
     AND conname IN ('asset_registry_natural_key_partition_nonblank',
                     'asset_registry_natural_key_partition_needs_table',
                     'asset_registry_dead_flag_not_retired');

  IF n_cols <> 2 OR n_constraints <> 3 THEN
    RAISE EXCEPTION
      'migration 591 did not apply: % of 2 columns present, % of 3 constraints present',
      n_cols, n_constraints;
  END IF;

  SELECT count(*)                                        INTO n_rows       FROM asset_registry;
  SELECT count(*) FILTER (WHERE natural_key_partition IS NOT NULL) INTO n_part   FROM asset_registry;
  SELECT count(*) FILTER (WHERE dead_flag IS TRUE)       INTO n_dead_true  FROM asset_registry;
  SELECT count(*) FILTER (WHERE dead_flag IS FALSE)      INTO n_dead_false FROM asset_registry;

  RAISE NOTICE
    'migration 591: both columns and all three constraints present on % asset_registry rows; natural_key_partition declared on %, dead_flag true on %, false on %, NULL (unadjudicated) on % — this migration wrote none of them',
    n_rows, n_part, n_dead_true, n_dead_false, n_rows - n_dead_true - n_dead_false;
END $$;

COMMIT;
