-- 1260_cross_asset_cascade_fks_to_detector.sql
--
-- Suvarna (SS ruling N-99, Q-L4-03, widened by SS to cross-ASSET): a rebuild of asset A must never silently delete
-- asset B's rows. Replaces seven ON DELETE CASCADE foreign keys with NO reference constraint, and adds a
-- read-only DETECTOR (two views) that reports, per reference, every child row whose parent row is missing.
--
--   phala_anchors.convergence_id  -> kala_convergence.convergence_id   phala_anchors_convergence_id_fkey    (L4 -> L3)
--   kala_darshana.convergence_id  -> kala_convergence.convergence_id   kala_darshana_convergence_id_fkey    (L3 -> L3)
--   kala_obstruction.convergence_id -> kala_convergence.convergence_id kala_obstruction_convergence_id_fkey  (L3 -> L3)
--   phala_pramana.anchor_id       -> phala_anchors.anchor_id           phala_pramana_anchor_id_fkey         (L4 -> L4)
--   phala_sankrama.source_anchor_id -> phala_anchors.anchor_id         phala_sankrama_source_anchor_id_fkey (L4 -> L4)
--   phala_sodhana.anchor_id       -> phala_anchors.anchor_id           phala_sodhana_anchor_id_fkey         (L4 -> L4)
--   phala_suddha_sodhana.anchor_id -> phala_anchors.anchor_id          phala_suddha_sodhana_anchor_id_fkey  (L4 -> L4)
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Schema-only: seven
-- DROP CONSTRAINTs and two CREATE VIEWs. NO DATA IS CHANGED OR DELETED (dropping a foreign key deletes nothing).
-- Every column, every index and every row stays. Precedent: migration 1214 (F-3, N-32), which dropped the five
-- kala_* keys into bodha_msr_signals for the same reason.
--
-- HELD. Own draft PR (suvarna/land/TI-mig-1260-001). Number 1260 allocated by SS. Merge only AFTER S-L1 and only on
-- SS's review. MERGE = APPLY at the next deploy (migrate.ts runs on every deploy, before that deploy's images
-- roll). Must be applied BEFORE any L3 (ka_sangam) or L4 (ph_nimitta) rebuild: until then a ka_sangam delete
-- (writers/ka_sangam.py plan_substeps: DELETE FROM kala_convergence WHERE chart_id = ...) still cascades into
-- phala_anchors (-> the four L4 children), kala_darshana and kala_obstruction.
--
-- WHY (the mechanism, from the catalogue, 2026-10-03, suvarna_reader).
--   * Seven FKs, all ON DELETE CASCADE, all validated, none deferrable, ON UPDATE NO ACTION, MATCH SIMPLE.
--     A delete of kala_convergence rows deletes phala_anchors, kala_darshana, kala_obstruction rows, and the
--     phala_anchors delete deletes phala_pramana, phala_sankrama, phala_sodhana, phala_suddha_sodhana rows.
--   * The ka_sangam writer clears the chart's kala_convergence with a plain DELETE before it re-inserts, and
--     ph_nimitta clears phala_anchors the same way. So an ordinary upstream rebuild destroyed another asset's rows
--     (A.L4: 135 of 139 anchors absent, consistent with this cascade; no delete event was read, see Q-L4-03).
--   * History: migration 363 changed phala_anchors_convergence_id_fkey from SET NULL to CASCADE because SET NULL
--     piled up NULL-convergence rows that collided on phala_anchors_natural_key (COALESCE(convergence_id,-1)).
--     Migration 680 later made anchor_id deterministic precisely so L4 identity survives upstream rebuilds; a
--     cascade defeats that.
--
-- DESIGN CHOICE: DROP the constraints; keep the columns and their indexes; add the detector. Reasons, with evidence:
--   (1) RESTRICT / NO ACTION would make the parent's delete-then-insert rebuild FAIL (loudly) whenever children
--       exist, and they always exist in the normal flow: production today holds kala_darshana 750 rows,
--       kala_obstruction 747 (701 with a reference), phala_anchors 60 (53 with a reference), all referencing
--       kala_convergence (20,497 rows). ka_sangam's DELETE runs first and would be refused, so no upstream asset
--       could ever be rebuilt before its downstream children had been deleted by hand: that BLOCKS the orchestrator's
--       "rebuild upstream, then downstream in wave order" flow. Not acceptable for the three kala_convergence keys.
--   (2) DEFERRABLE INITIALLY DEFERRED does not help either. The check would move to COMMIT, but kala_convergence
--       ids are bigserial (new ids on every re-insert, never reused) so the old references cannot be satisfied by
--       the re-inserted rows and the rebuild would fail at commit instead. For phala_anchors the ids are
--       deterministic (migration 680) so a same-transaction delete+reinsert of identical anchors WOULD satisfy a
--       deferred check, but any anchor that legitimately disappears (a changed L3) would still make the whole
--       ph_nimitta transaction fail at commit, with children still present, which blocks legitimate rebuilds too.
--   (3) SET NULL is a MUTATION of the child (the child silently loses its pointer; SS lists SET NULL as out of scope)
--       and is exactly what migration 363 abandoned (natural-key collisions on NULL).
--   (4) DROP matches the F-3 precedent (1214), and the rest of the system already tolerates dangling pointers by
--       design where it cannot own them (C13: phala_anchors.signal_id has no FK; migration 683).
--   Cost of DROP, stated: a child row can now point at a parent that no longer exists, and an INSERT of such a child
--   is no longer refused. The detector below makes that visible; the owning writers each delete-then-insert their
--   own rows per chart (ph_pramana.py:56, ph_sodhana.py:53, ph_suddha_sodhana.py:46, ph_sankrama.py:78,
--   ka_kala_darshana.py:19, ka_vighnakara.py:218, ph_nimitta.py:129), so stale children are replaced when their own
--   asset is rebuilt. Residual risk: a bigserial sequence reset could let a stale convergence_id silently re-bind to
--   a different parent (not done anywhere in this repo; flagged, not guarded).
--
-- EFFECT ON THE EXISTING WRITERS' delete-then-insert (read from the code, not assumed):
--   * ka_sangam: DELETE FROM kala_convergence WHERE chart_id = %s runs in plan_substeps, in the orchestrator's
--     ambient transaction, then the substeps re-insert (new bigserial ids). After 1260 the delete succeeds and
--     deletes ONLY kala_convergence rows. Children keep their old convergence_id values (now orphans, reported by
--     the detector) until ka_kala_darshana, ka_vighnakara and ph_nimitta are rebuilt in wave order.
--   * ph_nimitta: DELETE FROM phala_anchors WHERE chart_id = %s then INSERT. anchor_id is deterministic, so an
--     anchor that reappears gets the SAME id and its surviving children re-attach with no work; only anchors that
--     truly disappeared leave orphan children.
--   * The four L4 children and the two L3 children each clear only their own rows before re-inserting, so they
--     never depended on the cascade for correctness; the cascade only deleted them too early.
--
-- ORPHANS TODAY (production, suvarna_reader, 2026-10-03): 0 on all seven references (child rows with a non-NULL
-- reference / orphan rows): phala_anchors 53/0, kala_darshana 750/0, kala_obstruction 701/0, phala_pramana 60/0,
-- phala_sankrama 630/0, phala_sodhana 41/0, phala_suddha_sodhana 60/0. A NO ACTION/RESTRICT re-creation would have
-- validated cleanly on today's data (no existing violation); that is not what blocks it, the rebuild flow is.
--
-- TRIGGER SCAN (SS ask; production catalogue, suvarna_reader, 2026-10-03; one line per table; looks for
-- cascade-by-trigger, i.e. a trigger or a function that deletes from these tables):
--   kala_convergence: no user trigger | kala_darshana: no user trigger | kala_obstruction: no user trigger |
--   phala_anchors: one user trigger, phala_anchors_identity_biu (BEFORE INSERT, sets anchor_id; deletes nothing) |
--   phala_pramana, phala_sankrama, phala_sodhana, phala_suddha_sodhana: no user trigger.
--   No rewrite rule on any of the eight tables; no event trigger in the database; no function in any non-system
--   schema (auth, nirmana_evidence, public) whose body matches (DELETE FROM|TRUNCATE) <one of the eight tables>.
--   The only other things on these tables are the internal RI triggers of the seven FKs, which this migration
--   removes. BLIND SPOTS: dynamic SQL built with format()/EXECUTE (a regex on the function body cannot see a
--   table name assembled at run time); application code (the Python writers above are read, other clients are
--   not); schemas other than the three listed; objects the reader cannot see; deletes issued by a superuser
--   session (they bypass nothing here, but are invisible to this scan).
--
-- SERVING EFFECT AT APPLY: none expected. Evidence: no registry column is touched (so the live trigger
--   nirmana_registry_receipt_invalidation does not fire and no asset_freshness row changes); no data row is
--   written; no table or column is altered or renamed; no function or privilege changes. Readers of these tables
--   read rows, not constraints; no view, rule or other object depends on the seven constraints (pg_depend lists
--   only each constraint's own internal RI triggers). The only observable differences are (a) future DELETEs on
--   the parents no longer cascade (the point), (b) INSERTs of children with a missing parent are no longer
--   refused, (c) the governance cascade-closure tooling (platform/scripts/nirmana/cascade_check.sql, the footprint
--   loader) reads the live catalogue and will stop reporting these cascades.
--
-- THE DETECTOR (read-only; SECURITY INVOKER, so it grants nothing and shows a caller only what the caller can read):
--   vw_cross_asset_reference_orphans_by_chart  one row per (reference, chart_id) that has any child row with a
--       non-NULL reference: child_rows_with_reference, orphan_rows.
--   vw_cross_asset_reference_orphans           ALWAYS exactly seven rows (one per reference, from a fixed list, so an
--       empty or unreadable child table reads 0 child_rows_with_reference, never "no row"): child_rows_with_reference,
--       orphan_rows, orphan_chart_count.
--   Pre/post check for W7 / S-L3 (expect 7 rows; orphan_rows = 0 before a rebuild; compare after):
--     SELECT reference_name, child_rows_with_reference, orphan_rows FROM vw_cross_asset_reference_orphans ORDER BY 1;
--   NON-VACUITY: a clean result is meaningful only where child_rows_with_reference > 0 for that reference (a table
--   the caller cannot read, or an emptied table, also reads orphan_rows = 0). An orphan is a child row whose
--   referenced parent row does not exist; a parent that exists on a DIFFERENT chart is not reported.
--
-- LOCK-WAIT RISK (same as 1214; read before merging). DROP CONSTRAINT on a foreign key takes ACCESS EXCLUSIVE on the
-- child table and also locks the referenced table (its RI triggers are removed); here kala_convergence and
-- phala_anchors are each referenced by several children. SET LOCAL lock_timeout = '5s' makes a blocked attempt fail
-- loudly rather than queue behind (and stall) every reader, but scripts/migrate.ts has no retry: a long open read on
-- any of the eight tables during the deploy makes that deploy fail until it is re-run. MERGE ONLY WITH: no build_runs
-- in planned/running/paused (0 on 2026-10-03 for ka_sangam, ka_kala_darshana, ka_vighnakara, ka_bhavishya_lekha and
-- the five ph_ writers touching these tables), an idle deploy window, no long reads on the eight tables.
--
-- GUARDS (raise rather than skip; a silent skip would let a database that lacks the property look migrated):
--   * every named table must exist as an ordinary table; the child and parent columns must exist;
--   * each constraint must be ABSENT (already dropped: NOTICE, idempotent) or PRESENT WITH EXACTLY the expected
--     definition (pg_get_constraintdef text, schema qualification normalised) on the expected child table;
--     anything else RAISES and changes nothing;
--   * post-check: none of the seven remains, the number of foreign keys in public fell by exactly the number
--     dropped (nothing else was dropped), both views exist with security_invoker, the summary view returns exactly
--     the seven references, and no cascading FK from a child table to its parent remains.
--
-- NOT DONE HERE: the SET NULL links (phala_anchors.bhavishya_id, kala_bhavishya.convergence_id, phala_muhurta /
-- phala_mitigation linked_anchor_id, phala_sankrama.mitigation_ref, phala_mitigation.initiation_muhurta_ref);
-- chart_fact_identity -> chart_facts (G-IDX step); the charts-row-delete cascades (chart deletion, not rebuild);
-- any rebuild; any data repair; any writer change; updating the docs that still list these keys as CASCADE
-- (00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_IO_USE_MATRIX_v1_0.md and its edges fixture, historical
-- evidence snapshots); the ph_nimitta integrity terms (a1)-(a4) over the four L4 children (see migration 1259's PR:
-- once the cascade is gone they are the only thing that can read an orphan).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy, as
-- suvarna_reader, expect zero rows from:
--   SELECT conname FROM pg_constraint WHERE conname IN ('phala_anchors_convergence_id_fkey',
--     'kala_darshana_convergence_id_fkey','kala_obstruction_convergence_id_fkey','phala_pramana_anchor_id_fkey',
--     'phala_sankrama_source_anchor_id_fkey','phala_sodhana_anchor_id_fkey','phala_suddha_sodhana_anchor_id_fkey');
-- and expect 7 rows (orphan_rows 0 on today's data) from the pre/post-check query above, and 217 foreign keys in
-- public (224 on 2026-10-03 minus seven):
--   SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace WHERE c.contype = 'f' AND n.nspname = 'public';
--
-- ROLLBACK (not executed by migrate.ts): ALTER TABLE <child> ADD CONSTRAINT <name> FOREIGN KEY (<col>) REFERENCES
-- <parent>(<col>) ON DELETE CASCADE; for each row of the list below (it validates every existing row, so it fails
-- while any orphan exists; use NOT VALID then VALIDATE after repairing). Re-adding the cascade re-creates the hazard.

SET LOCAL lock_timeout = '5s';

DO $mig$
DECLARE
    -- THE ONE PLACE THE REFERENCE LIST LIVES: constraint | child table | child column | parent table | parent column.
    -- Unqualified names in schema public. The guard, the drop, both views and the post-check all iterate it.
    refs text[] := ARRAY[
        'phala_anchors_convergence_id_fkey|phala_anchors|convergence_id|kala_convergence|convergence_id',
        'kala_darshana_convergence_id_fkey|kala_darshana|convergence_id|kala_convergence|convergence_id',
        'kala_obstruction_convergence_id_fkey|kala_obstruction|convergence_id|kala_convergence|convergence_id',
        'phala_pramana_anchor_id_fkey|phala_pramana|anchor_id|phala_anchors|anchor_id',
        'phala_sankrama_source_anchor_id_fkey|phala_sankrama|source_anchor_id|phala_anchors|anchor_id',
        'phala_sodhana_anchor_id_fkey|phala_sodhana|anchor_id|phala_anchors|anchor_id',
        'phala_suddha_sodhana_anchor_id_fkey|phala_suddha_sodhana|anchor_id|phala_anchors|anchor_id'
    ];
    r            text;
    f            text[];
    con          text;
    child        text;
    ccol         text;
    parent       text;
    pcol         text;
    child_oid    regclass;
    parent_oid   regclass;
    kind         "char";
    cdef         text;
    expected     text;
    fk_before    int;
    fk_after     int;
    dropped      int := 0;
    by_chart_sql text := '';
    values_sql   text := '';
    n            int;
    opts         text[];
BEGIN
    SELECT count(*) INTO fk_before
      FROM pg_constraint c JOIN pg_namespace ns ON ns.oid = c.connamespace
     WHERE c.contype = 'f' AND ns.nspname = 'public';

    -- Guard pass: tables, columns and the state of every constraint, BEFORE anything is dropped.
    FOREACH r IN ARRAY refs LOOP
        f := string_to_array(r, '|');
        con := f[1]; child := f[2]; ccol := f[3]; parent := f[4]; pcol := f[5];
        FOREACH n IN ARRAY ARRAY[2, 4] LOOP
            child_oid := to_regclass(format('public.%I', f[n]));
            IF child_oid IS NULL THEN
                RAISE EXCEPTION '1260: public.% does not exist', f[n];
            END IF;
            SELECT relkind INTO kind FROM pg_class WHERE oid = child_oid;
            IF kind NOT IN ('r', 'p') THEN
                RAISE EXCEPTION '1260: public.% is not an ordinary table (relkind %)', f[n], kind;
            END IF;
        END LOOP;
        child_oid  := format('public.%I', child)::regclass;
        parent_oid := format('public.%I', parent)::regclass;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = child_oid AND attname = ccol AND NOT attisdropped) THEN
            RAISE EXCEPTION '1260: column public.%.% does not exist', child, ccol;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = parent_oid AND attname = pcol AND NOT attisdropped) THEN
            RAISE EXCEPTION '1260: column public.%.% does not exist', parent, pcol;
        END IF;
        expected := format('FOREIGN KEY (%I) REFERENCES %I(%I) ON DELETE CASCADE', ccol, parent, pcol);
        SELECT regexp_replace(pg_get_constraintdef(c.oid), ' public\.', ' ', 'g') INTO cdef
          FROM pg_constraint c WHERE c.conrelid = child_oid AND c.conname = con AND c.contype = 'f';
        IF cdef IS NULL THEN
            RAISE NOTICE '1260: % is already absent on public.%; nothing to drop', con, child;
        ELSIF cdef IS DISTINCT FROM expected THEN
            RAISE EXCEPTION '1260: % on public.% is not the constraint this migration was written against (found: %; expected: %)',
                con, child, cdef, expected;
        END IF;
    END LOOP;

    -- Drop pass (only constraints that are present; the guard above proved their definition).
    FOREACH r IN ARRAY refs LOOP
        f := string_to_array(r, '|');
        con := f[1]; child := f[2];
        IF EXISTS (SELECT 1 FROM pg_constraint c
                    WHERE c.conrelid = format('public.%I', child)::regclass AND c.conname = con AND c.contype = 'f') THEN
            EXECUTE format('ALTER TABLE public.%I DROP CONSTRAINT %I', child, con);
            dropped := dropped + 1;
        END IF;
    END LOOP;

    -- The detector. Built from the same list, so a reference cannot be dropped without being detected.
    FOREACH r IN ARRAY refs LOOP
        f := string_to_array(r, '|');
        con := f[1]; child := f[2]; ccol := f[3]; parent := f[4]; pcol := f[5];
        by_chart_sql := by_chart_sql
            || CASE WHEN by_chart_sql = '' THEN '' ELSE E'\nUNION ALL\n' END
            || format('SELECT %L::text AS reference_name, %L::text AS child_table, %L::text AS child_column, '
                      '%L::text AS parent_table, %L::text AS parent_column, c.chart_id, '
                      'count(*) AS child_rows_with_reference, count(*) FILTER (WHERE p.%I IS NULL) AS orphan_rows '
                      'FROM public.%I c LEFT JOIN public.%I p ON p.%I = c.%I '
                      'WHERE c.%I IS NOT NULL GROUP BY c.chart_id',
                      con, child, ccol, parent, pcol, pcol, child, parent, pcol, ccol, ccol);
        values_sql := values_sql
            || CASE WHEN values_sql = '' THEN '' ELSE ', ' END
            || format('(%L, %L, %L, %L, %L)', con, child, ccol, parent, pcol);
    END LOOP;

    EXECUTE 'CREATE OR REPLACE VIEW public.vw_cross_asset_reference_orphans_by_chart WITH (security_invoker = true) AS '
            || by_chart_sql;
    EXECUTE 'CREATE OR REPLACE VIEW public.vw_cross_asset_reference_orphans WITH (security_invoker = true) AS '
            || 'SELECT r.reference_name, r.child_table, r.child_column, r.parent_table, r.parent_column, '
            || 'COALESCE(sum(b.child_rows_with_reference), 0)::bigint AS child_rows_with_reference, '
            || 'COALESCE(sum(b.orphan_rows), 0)::bigint AS orphan_rows, '
            || 'count(b.chart_id) FILTER (WHERE b.orphan_rows > 0) AS orphan_chart_count '
            || 'FROM (VALUES ' || values_sql || ') AS r(reference_name, child_table, child_column, parent_table, parent_column) '
            || 'LEFT JOIN public.vw_cross_asset_reference_orphans_by_chart b ON b.reference_name = r.reference_name '
            || 'GROUP BY r.reference_name, r.child_table, r.child_column, r.parent_table, r.parent_column';
    COMMENT ON VIEW public.vw_cross_asset_reference_orphans_by_chart IS
        'Migration 1260. Per (reference, chart): child rows whose parent row is missing, for the seven references whose ON DELETE CASCADE foreign keys 1260 removed. Read-only; SECURITY INVOKER. A zero is meaningful only where child_rows_with_reference > 0.';
    COMMENT ON VIEW public.vw_cross_asset_reference_orphans IS
        'Migration 1260. Always seven rows (one per reference): child_rows_with_reference, orphan_rows, orphan_chart_count. Pre/post check for W7 / S-L3. Read-only; SECURITY INVOKER. A zero orphan_rows is meaningful only where child_rows_with_reference > 0.';

    -- Post-check: never trust a silent no-op.
    FOREACH r IN ARRAY refs LOOP
        f := string_to_array(r, '|');
        IF EXISTS (SELECT 1 FROM pg_constraint c
                    WHERE c.conrelid = format('public.%I', f[2])::regclass AND c.conname = f[1]) THEN
            RAISE EXCEPTION '1260: constraint % still exists on public.% after the drop', f[1], f[2];
        END IF;
        IF EXISTS (SELECT 1 FROM pg_constraint c
                    WHERE c.contype = 'f' AND c.confdeltype = 'c'
                      AND c.conrelid = format('public.%I', f[2])::regclass
                      AND c.confrelid = format('public.%I', f[4])::regclass) THEN
            RAISE EXCEPTION '1260: a cascading foreign key from public.% to public.% still exists', f[2], f[4];
        END IF;
    END LOOP;
    SELECT count(*) INTO fk_after
      FROM pg_constraint c JOIN pg_namespace ns ON ns.oid = c.connamespace
     WHERE c.contype = 'f' AND ns.nspname = 'public';
    IF fk_after <> fk_before - dropped THEN
        RAISE EXCEPTION '1260: foreign keys in public went from % to % but % were meant to be dropped (something else changed)',
            fk_before, fk_after, dropped;
    END IF;
    FOREACH r IN ARRAY ARRAY['vw_cross_asset_reference_orphans_by_chart', 'vw_cross_asset_reference_orphans'] LOOP
        SELECT c.reloptions INTO opts FROM pg_class c
         WHERE c.oid = to_regclass(format('public.%I', r)) AND c.relkind = 'v';
        IF opts IS NULL OR NOT ('security_invoker=true' = ANY (opts)) THEN
            RAISE EXCEPTION '1260: view public.% is missing or is not security_invoker', r;
        END IF;
    END LOOP;
    SELECT count(DISTINCT reference_name) INTO n FROM public.vw_cross_asset_reference_orphans;
    IF n <> array_length(refs, 1)
       OR (SELECT count(*) FROM public.vw_cross_asset_reference_orphans) <> array_length(refs, 1) THEN
        RAISE EXCEPTION '1260: the summary view does not return exactly the % references', array_length(refs, 1);
    END IF;
    RAISE NOTICE '1260: dropped % of % constraints; orphan rows now: %', dropped, array_length(refs, 1),
        (SELECT string_agg(reference_name || '=' || orphan_rows, ', ' ORDER BY reference_name)
           FROM public.vw_cross_asset_reference_orphans);
END
$mig$;
