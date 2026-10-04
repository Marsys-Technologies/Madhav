-- 1275_chart_delete_reaches_phala_and_mimamsa_per_chart_tables.sql
--
-- Suvarna (SS ruling N-108): PRIVACY GAP -- every per-chart row must leave when its chart is deleted. Adds
--     FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE
-- (an OWNERSHIP link: a row belongs to a chart) to the 29 tables below, and RE-CREATES the one existing chart link that does not cascade
-- (mimamsa_pool_contributions, ON DELETE NO ACTION -> CASCADE; SS N-108 addendum). Schema-only: 29 ADD CONSTRAINTs and 1 guarded
-- DROP+ADD of the same constraint name. NO DB OBJECT IS CREATED,
-- NO DATA IS CHANGED OR DELETED. Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here).
--
-- HELD. Own draft PR (suvarna/land/TI-mig-1275-001). Number 1275 allocated by SS. Merge only AFTER S-L1 and only on SS's review.
-- LAND TOGETHER WITH 1265 (the frozen-row guard on mimamsa_predictions, PR #3033), in the same window, AFTER the append-only
-- writer change. WHY TOGETHER: 1265 refuses every DELETE of a mimamsa_predictions row except a consent-withdrawal one; the cascade
-- this migration adds is a DELETE of those rows. Without a chart-deletion exception in 1265's guard, deleting a chart would then
-- FAIL (the whole route transaction rolls back, nothing lost, but the chart cannot be deleted). See THE 1265 REQUIREMENT.
--
-- THE GAP (catalogue, suvarna_reader, 2026-10-03). The chart-delete route (platform/src/app/api/charts/[id]/route.ts:87-107) deletes
-- a few tables by hand and then DELETE FROM charts, relying on ON DELETE CASCADE foreign keys for everything else. These 29 tables
-- carry a chart_id column (NOT NULL on every one) and have NO foreign key to charts and no FK path to it, so their rows survive the
-- chart's deletion: phala_muhurta 183, phala_mitigation 1,277, phala_phaladesa 26, and the L5 mimamsa_* tables (the largest:
-- mimamsa_fact_adjustment 123,272 and mimamsa_signal_adjustment 100,275 rows). Per-chart row counts of the 29 on 2026-10-03 are in
-- the PR body; today every row of every table resolves to a real charts row (0 unresolved).
--
-- THE RELINK (SS N-108 addendum). public.mimamsa_pool_contributions (owner amjis_app; id uuid PK, chart_id uuid NOT NULL, event_classes, weights,
--   priors_version, pool_consent, contributed_at; no triggers; no table references it) carries mimamsa_pool_contributions_chart_id_fkey =
--   FOREIGN KEY (chart_id) REFERENCES charts(id)  (NO ACTION, validated, not deferrable). In one transaction the migration accepts exactly
--   three states of that constraint: that definition (it is dropped and re-added with ON DELETE CASCADE, same name), the cascading
--   definition (already done: NOTICE), or absent (added). ANY OTHER definition RAISES. Drop and add run back to back inside the one
--   transaction, so the table is never without a link; the post-check asserts confdeltype = 'c', validated, not deferrable.
--
-- THE 29 (all owned by amjis_app, the migration runner; routine path, no owner-path package is needed for this migration):
--   phala_*   : phala_muhurta, phala_mitigation, phala_phaladesa
--   brahma_*  : prospective_ledger (29 rows: 18 + 11), mimamsa_prediction_ledger (5 rows) -- ADDED (coordinator, from the reworked 1265): the L5 frozen-history
--               guards of 1265 cover both, and both had no charts link, so a chart delete left their rows behind
--   mimamsa_* : adjudication_log, anchor_adjustment, attribution, calibration, calibration_snapshot, convergence_adjustment,
--               discoveries, event_provenance, export_log, fact_adjustment, insight_embeddings, insight_units, intervention_ledger,
--               journal, load_bearing, manifestation_grammar, manifestation_sets, multipliers, predictions, qa_eval, reliability,
--               resonance_feedback, signal_adjustment, snapshot_cosign
-- EXCLUDED, with reasons (every mimamsa_* table in public was enumerated):
--   mimamsa_negative_controls, mimamsa_signal_families   global reference tables (no chart_id, no per-chart row)
--   mimamsa_preferences                                  keyed by user_id/channel_id, not by chart
--   (mimamsa_pool_contributions is NOT excluded any more: it already had a chart_id FK to charts, ON DELETE NO ACTION, 0 rows today,
--                                                        which would BLOCK a chart delete once it held a row. SS N-108 addendum: this migration
--                                                        changes that one FK to ON DELETE CASCADE, in a single guarded step, see THE RELINK.)
--   *__ssv_20260728a/b shadow copies (mimamsa_calibration__ssv_..., mimamsa_insight_units__ssv_... x2, mimamsa_journal__ssv_...,
--     mimamsa_load_bearing__ssv_..., mimamsa_manifestation_grammar__ssv_..., mimamsa_multipliers__ssv_..., mimamsa_predictions__ssv_...,
--     mimamsa_qa_eval__ssv_...)                          chart_id is NULLABLE on every one (the migration's own standard RAISES on a
--                                                        nullable chart_id: it will not guess); they hold copies of per-chart subject rows
--                                                        (e.g. 292 prediction rows) and ALSO leak on chart deletion. Reported for an SS ruling
--                                                        (drop the snapshots, or backfill and link); NOT touched here.
-- Everything else in the catalogue that has a chart_id and no charts link (about 120 further tables: bodha_*, chart_facts, chart_dashas,
-- ga_*, kala_*, l1_/l2_data_plane_*, pariprashna_*, ...; several owned by data_plane_l1_owner / data_plane_l2_owner) is OUT of scope by
-- SS's list and is reported in the PR and in /Users/Dev/suvarna-evidence/S_L1/mig1275_chart_id_all.txt, with owners: the ones owned by
-- another role need an OWNER-PATH package (executor on the D6 pattern; SQL NOT under platform/migrations), not this migration.
--
-- THE 1265 REQUIREMENT (frozen-row guard must ALLOW the cascade from deleting the chart itself and refuse every other DELETE).
--   Deleting a chart is the strongest form of consent withdrawal. 1265's FIRST-DRAFT guard (head eb2432707; reworked in 06e668944 to carry this discriminator) allows a DELETE only when the chart has
--   a chart_subject_consent row in state 'withdrawn' and no open dispute. A chart delete does not satisfy that (and chart_subject_consent
--   itself is deleted by the same cascade, in an unspecified order), so it would be refused. DISCRIMINATOR, proved on PostgreSQL 15 and 17
--   in this PR's tests: inside the RI cascade the parent charts row is already deleted when the child's BEFORE DELETE row trigger runs, so
--       NOT EXISTS (SELECT 1 FROM public.charts WHERE id = OLD.chart_id)
--   is true for the cascade and false for every direct DELETE of a prediction (its chart exists; after this migration it cannot be
--   otherwise). It cannot be spoofed by a role without superuser/ownership: to make it true outside the cascade one must delete the charts
--   row first without the RI cascade, which needs session_replication_role = replica (superuser) or to disable the RI trigger (owner),
--   and either of those can disable the guard itself. pg_trigger_depth() is NOT a safe discriminator: any role that can create a trigger or
--   call a plpgsql function from a trigger reaches the same depth as the RI action; the tests demonstrate that spoof succeeding.
--   The guard must evaluate the discriminator for DELETE only, and fire for the 29 tables only where a guard exists. With the reworked 1265
--   (PR #3033 head 06e668944, owner-path package) four of them carry DELETE guards: mimamsa_predictions, mimamsa_manifestation_sets,
--   brahma_prospective_ledger, brahma_mimamsa_prediction_ledger; the other 25 have none. 1265's helper l5_frozen_chart_cascade_authorizes
--   is SECURITY DEFINER (owner amjis_app) because charts has row-level security ON on live: under the invoker's rights a role that no
--   policy lets see the chart would read 'absent' and a direct delete would be authorized.
--
-- STANDING CONSTRAINT (SS): NO FORCE ROW LEVEL SECURITY ON charts WITHOUT FIRST REVISITING THE 1265 GUARD. relforcerowsecurity on public.charts
--   is false on live (relrowsecurity true). This migration checks it in its pre-flight and RAISES if it is true (with FORCE the owner would not
--   see its own charts rows: the validation below and the discriminator would misread every chart as absent). Read-only verify query:
--     SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = 'public.charts'::regclass;   -- t | f
--
-- ORDER (hard): S-L1 -> PR #3040 (append-only mi_bhavisya writer) + migration 1259 -> 1265 (owner-path frozen-row guards) -> 1275 (this) -> any L5
--   rebuild. 1265 and 1275 land in the same window; either order of those two was tested to apply (a 1265 self-test on an existing chart), but
--   the stated order is the one to run.
--
-- ORDER / LOCKS. ADD FOREIGN KEY takes SHARE ROW EXCLUSIVE on the child and on charts, held to the end of this transaction (one
--   migrate.ts transaction), and validates the child. MEASURED on disposable PostgreSQL 15 and 17 with production-sized synthetic data
--   (123,272 + 100,275 + 1,277 rows in the three largest tables, 2 charts, every table's chart_id indexed): the whole file, validation
--   included, ran in 0.06-0.09 s; the cascade of a chart delete over ~113,000 rows took 0.04-0.05 s. charts is write-blocked for that time. SET LOCAL lock_timeout = '5s' makes a
--   blocked attempt fail loudly instead of queueing; migrate.ts has no retry, so a long open read/write on any table involved during the
--   deploy fails that deploy until it is re-run. NOT VALID + VALIDATE would gain nothing here: the locks of the ADD are held to commit
--   either way, and the tables are small. Child chart_id indexes already lead on every one of the 29 (the cascade DELETE uses them).
--
-- ACTIVE RUNS (ENFORCED, not advisory): the first DO block RAISES, changing nothing, if build_runs holds a run that is not
--   completed/failed/stopped (planned, running or paused) for any mi_* asset or for ph_muhurta, ph_pratikara, ph_phaladesa. 0 on 2026-10-03.
--
-- GUARDS (raise rather than skip; a silent skip would let a database that lacks the property look migrated; no invented derivation):
--   * every table must exist as an ordinary table in public; the migration user must own it (or be a member of its owner), because ADD
--     CONSTRAINT needs table ownership (a table owned by another role is an OWNER-PATH item, not this file's);
--   * chart_id must exist and be NOT NULL; no row may reference a missing chart (report, never backfill);
--   * the constraint must be ABSENT (added) or PRESENT WITH EXACTLY the expected definition (idempotent re-run); for the relink table also the
--     previous NO ACTION definition (replaced);
--   * post-check (asserting, RAISES): each constraint (the 29 and the relinked one) exists, is a foreign key to charts(id) on chart_id, convalidated, ON DELETE CASCADE,
--     not deferrable; the number of foreign keys in public rose by exactly (added - dropped).
--
-- SERVING EFFECT AT APPLY: none. No registry column is touched (nirmana_registry_receipt_invalidation does not fire), no data row is
--   written, no object created, no privilege changed. Behaviour after apply: deleting a chart now also deletes its rows in these tables;
--   an INSERT with a chart_id that has no charts row is refused on these tables (the writers insert only for existing charts); the
--   governance cascade-closure tooling reports the new cascades.
--
-- NOT DONE HERE: the __ssv_ shadow tables; the ~120 other
--   per-chart tables without a charts link (report); the chart-delete route's own list; 1265's guard change; tombstones for the deleted
--   rows (consent/withdrawal.ts writes them for the consent path; a chart delete is the owner removing the chart).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy, as suvarna_reader, expect 29 rows,
-- convalidated t, confdeltype c, definition FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE:
--   SELECT conrelid::regclass, conname, convalidated, confdeltype, pg_get_constraintdef(oid) FROM pg_constraint
--    WHERE conname LIKE '%\_chart\_id\_fkey' AND conrelid IN (<the 29 tables>, mimamsa_pool_contributions) AND confrelid = 'charts'::regclass ORDER BY 1;
--     -- 30 rows, all convalidated t, confdeltype c (mimamsa_pool_contributions was a)
--   SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace WHERE c.contype = 'f' AND n.nspname = 'public';
--     -- 224 + 29 = 253 (the relink is net 0; 1260, if applied first, adds net -2: 251)
--
-- ROLLBACK (not executed by migrate.ts): ALTER TABLE <table> DROP CONSTRAINT <table>_chart_id_fkey; for each of the 29; for mimamsa_pool_contributions drop and
-- re-add it as FOREIGN KEY (chart_id) REFERENCES charts(id) (NO ACTION). Doing so re-opens the
-- privacy gap; it should only be done if a chart delete is blocked by a frozen-row guard and 1265 cannot yet be changed.

SET LOCAL lock_timeout = '5s';

DO $runs$
DECLARE n_active int; v_assets text;
BEGIN
    SELECT count(*), string_agg(DISTINCT a.asset_id, ', ') INTO n_active, v_assets
      FROM public.build_runs r JOIN public.build_run_assets a ON a.run_id = r.id
     WHERE (a.asset_id LIKE 'mi\_%' OR a.asset_id IN ('ph_muhurta', 'ph_pratikara', 'ph_phaladesa'))
       AND r.state NOT IN ('completed', 'failed', 'stopped');
    IF n_active > 0 THEN
        RAISE EXCEPTION '1275: % active build run(s) (planned/running/paused) for %; refusing to add foreign keys under a running build', n_active, v_assets;
    END IF;
END
$runs$;

DO $mig$
DECLARE
    -- THE ONE PLACE THE TABLE LIST LIVES. Unqualified names in schema public. Constraint name = <table>_chart_id_fkey.
    tables text[] := ARRAY[
        'phala_muhurta',
        'phala_mitigation',
        'phala_phaladesa',
        'mimamsa_adjudication_log',
        'mimamsa_anchor_adjustment',
        'mimamsa_attribution',
        'mimamsa_calibration',
        'mimamsa_calibration_snapshot',
        'mimamsa_convergence_adjustment',
        'mimamsa_discoveries',
        'mimamsa_event_provenance',
        'mimamsa_export_log',
        'mimamsa_fact_adjustment',
        'mimamsa_insight_embeddings',
        'mimamsa_insight_units',
        'mimamsa_intervention_ledger',
        'mimamsa_journal',
        'mimamsa_load_bearing',
        'mimamsa_manifestation_grammar',
        'mimamsa_manifestation_sets',
        'mimamsa_multipliers',
        'mimamsa_predictions',
        'mimamsa_qa_eval',
        'mimamsa_reliability',
        'mimamsa_resonance_feedback',
        'mimamsa_signal_adjustment',
        'mimamsa_snapshot_cosign',
        'brahma_prospective_ledger',
        'brahma_mimamsa_prediction_ledger'
    ];
    -- The one existing link whose action is changed (NO ACTION -> CASCADE), same constraint name.
    relink text[] := ARRAY[
        'mimamsa_pool_contributions'
    ];
    relink_old constant text := 'FOREIGN KEY (chart_id) REFERENCES charts(id)';
    expected constant text := 'FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE';
    tbl        text;
    con        text;
    rel        regclass;
    kind       "char";
    owner      oid;
    cdef       text;
    bad        bigint;
    fk_before  int;
    fk_after   int;
    added      int := 0;
    dropped    int := 0;
BEGIN
    SELECT count(*) INTO fk_before
      FROM pg_constraint c JOIN pg_namespace ns ON ns.oid = c.connamespace
     WHERE c.contype = 'f' AND ns.nspname = 'public';

    IF to_regclass('public.charts') IS NOT NULL AND (SELECT relforcerowsecurity FROM pg_class WHERE oid = 'public.charts'::regclass) THEN
        RAISE EXCEPTION '1275: public.charts has FORCE ROW LEVEL SECURITY; the standing constraint is no FORCE RLS on charts without first revisiting the 1265 guard (and the owner would not see its own chart rows here)';
    END IF;

    IF to_regclass('public.charts') IS NULL OR NOT EXISTS (
         SELECT 1 FROM pg_index i WHERE i.indrelid = 'public.charts'::regclass AND i.indisprimary
            AND (SELECT attname FROM pg_attribute WHERE attrelid = i.indrelid AND attnum = i.indkey[0]) = 'id') THEN
        RAISE EXCEPTION '1275: public.charts(id) primary key not found';
    END IF;

    -- Guard pass: every table, BEFORE anything is added. STOP (raise) rather than invent a derivation.
    FOREACH tbl IN ARRAY tables || relink LOOP
        con := tbl || '_chart_id_fkey';
        rel := to_regclass(format('public.%I', tbl));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1275: public.% does not exist', tbl;
        END IF;
        SELECT c.relkind, c.relowner INTO kind, owner FROM pg_class c WHERE c.oid = rel;
        IF kind NOT IN ('r', 'p') THEN
            RAISE EXCEPTION '1275: public.% is not an ordinary table (relkind %)', tbl, kind;
        END IF;
        IF NOT pg_has_role(current_user, owner, 'USAGE') THEN
            RAISE EXCEPTION '1275: % is neither the owner of public.% nor a member of its owner (%); ADD CONSTRAINT needs ownership: owner-path item, not this migration', current_user, tbl, pg_get_userbyid(owner);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'chart_id' AND NOT attisdropped) THEN
            RAISE EXCEPTION '1275: public.% has no chart_id column; cannot add the ownership link and will not invent a derivation', tbl;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = rel AND attname = 'chart_id' AND NOT attisdropped AND attnotnull) THEN
            RAISE EXCEPTION '1275: public.%.chart_id is nullable; rows with a NULL chart would never be reached by chart deletion', tbl;
        END IF;
        EXECUTE format('SELECT count(*) FROM public.%I c WHERE NOT EXISTS (SELECT 1 FROM public.charts h WHERE h.id = c.chart_id)', tbl) INTO bad;
        IF bad > 0 THEN
            RAISE EXCEPTION '1275: public.% holds % row(s) whose chart_id has no charts row; report, do not backfill', tbl, bad;
        END IF;
        SELECT regexp_replace(pg_get_constraintdef(c.oid), ' public\.', ' ', 'g') INTO cdef
          FROM pg_constraint c WHERE c.conrelid = rel AND c.conname = con;
        IF cdef IS NOT NULL AND cdef IS DISTINCT FROM expected AND NOT (tbl = ANY (relink) AND cdef = relink_old) THEN
            RAISE EXCEPTION '1275: % on public.% exists but is not the expected chart link (found: %; expected: %)', con, tbl, cdef, expected;
        END IF;
    END LOOP;

    -- Relink pass: the previous NO ACTION link is replaced (dropped here, re-added by the add pass below, same transaction).
    FOREACH tbl IN ARRAY relink LOOP
        con := tbl || '_chart_id_fkey';
        rel := format('public.%I', tbl)::regclass;
        SELECT regexp_replace(pg_get_constraintdef(c.oid), ' public\.', ' ', 'g') INTO cdef
          FROM pg_constraint c WHERE c.conrelid = rel AND c.conname = con;
        IF cdef = relink_old THEN
            EXECUTE format('ALTER TABLE public.%I DROP CONSTRAINT %I', tbl, con);
            dropped := dropped + 1;
        END IF;
    END LOOP;

    -- Add pass.
    FOREACH tbl IN ARRAY tables || relink LOOP
        con := tbl || '_chart_id_fkey';
        rel := format('public.%I', tbl)::regclass;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conrelid = rel AND c.conname = con) THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE', tbl, con);
            added := added + 1;
        ELSE
            RAISE NOTICE '1275: % already present on public.%; nothing to add', con, tbl;
        END IF;
    END LOOP;

    -- Post-check: never trust a silent no-op.
    FOREACH tbl IN ARRAY tables || relink LOOP
        con := tbl || '_chart_id_fkey';
        rel := format('public.%I', tbl)::regclass;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint c
                        WHERE c.conrelid = rel AND c.conname = con AND c.contype = 'f'
                          AND c.confrelid = 'public.charts'::regclass AND c.convalidated AND c.confdeltype = 'c'
                          AND NOT c.condeferrable AND c.confupdtype = 'a'
                          AND c.conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = c.conrelid AND attname = 'chart_id')]::smallint[]
                          AND c.confkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'public.charts'::regclass AND attname = 'id')]::smallint[]) THEN
            RAISE EXCEPTION '1275: chart link % on public.% is missing, not validated, not ON DELETE CASCADE, or not on chart_id -> charts(id)', con, tbl;
        END IF;
    END LOOP;
    SELECT count(*) INTO fk_after
      FROM pg_constraint c JOIN pg_namespace ns ON ns.oid = c.connamespace
     WHERE c.contype = 'f' AND ns.nspname = 'public';
    IF fk_after <> fk_before + added - dropped THEN
        RAISE EXCEPTION '1275: foreign keys in public went from % to % but % were added and % dropped (something else changed)', fk_before, fk_after, added, dropped;
    END IF;
    RAISE NOTICE '1275: added % chart links (% of them replacing a NO ACTION link); % tables + % relinked', added, dropped, array_length(tables, 1), array_length(relink, 1);
END
$mig$;
