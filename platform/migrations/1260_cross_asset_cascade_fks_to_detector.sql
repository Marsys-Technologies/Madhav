-- 1260_cross_asset_cascade_fks_to_detector.sql
--
-- Suvarna (SS ruling N-99, Q-L4-03, widened by SS to cross-ASSET; N-105; SS migration review): a rebuild of asset A must
-- never silently delete asset B's rows. Replaces seven ON DELETE CASCADE foreign keys between assets with NO reference
-- constraint, and gives the five L4 tables that lose their ONLY deletion path an OWNERSHIP link to charts instead:
--
--   phala_anchors.convergence_id  -> kala_convergence.convergence_id   phala_anchors_convergence_id_fkey    (L4 -> L3)
--   kala_darshana.convergence_id  -> kala_convergence.convergence_id   kala_darshana_convergence_id_fkey    (L3 -> L3)
--   kala_obstruction.convergence_id -> kala_convergence.convergence_id kala_obstruction_convergence_id_fkey  (L3 -> L3)
--   phala_pramana.anchor_id       -> phala_anchors.anchor_id           phala_pramana_anchor_id_fkey         (L4 -> L4)
--   phala_sankrama.source_anchor_id -> phala_anchors.anchor_id         phala_sankrama_source_anchor_id_fkey (L4 -> L4)
--   phala_sodhana.anchor_id       -> phala_anchors.anchor_id           phala_sodhana_anchor_id_fkey         (L4 -> L4)
--   phala_suddha_sodhana.anchor_id -> phala_anchors.anchor_id          phala_suddha_sodhana_anchor_id_fkey  (L4 -> L4)
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (no BEGIN/COMMIT here). Schema-only: seven DROP CONSTRAINTs and
-- five ADD CONSTRAINTs (chart_id -> charts(id) ON DELETE CASCADE). NO DB OBJECT IS CREATED (no view, no function): the
-- orphan detector is a plain read-only query shipped as files (see THE DETECTOR). amjis_app owns all thirteen tables
-- involved (pg_class.relowner, read 2026-10-03) and has no CREATE on schema public, so nothing here needs it. NO DATA IS
-- CHANGED OR DELETED. Every column, every index and every row stays. Precedent for the drop: migration 1214 (F-3, N-32).
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
-- DESIGN CHOICE: DROP the constraints; keep the columns and their indexes; the detector is plain read-only SQL (no DB object).
-- Reasons, with evidence:
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
--   is no longer refused. The detector (THE DETECTOR, below) makes that visible; the owning writers each delete-then-insert their
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
-- SERVING EFFECT AT APPLY: none expected for serving or building. Evidence: no registry column is touched (so the live
--   trigger nirmana_registry_receipt_invalidation does not fire and no asset_freshness row changes); no data row is
--   written; no table or column is altered or renamed; no function, view or privilege is created or changed. Readers of these
--   tables read rows, not constraints; no view, rule or other object depends on the seven constraints (pg_depend lists only
--   each constraint's own internal RI triggers). Observable differences: (a) future DELETEs on the parents no longer cascade
--   (the point); (b) INSERTs of children with a missing parent are no longer refused; (c) CHART DELETION now reaches the five
--   L4 tables through their own chart_id link (below) instead of through kala_convergence; (d) the governance cascade-closure
--   tooling (platform/scripts/nirmana/cascade_check.sql, the footprint loader) reads the live catalogue and stops reporting
--   these cascades.
--
-- CHART DELETION (SS review H2; this is why the migration also ADDS five constraints). phala_anchors and its four children
--   (phala_pramana, phala_sankrama, phala_sodhana, phala_suddha_sodhana) have NO foreign key to charts. Today a chart delete
--   (platform/src/app/api/charts/[id]/route.ts:87-107 relies on it) reaches them only through charts -> kala_convergence
--   (kala_convergence_chart_id_fkey, CASCADE) -> phala_anchors_convergence_id_fkey -> the children. Dropping the convergence
--   key would leave their rows behind on chart deletion: a PRIVACY regression. So this migration adds, on those five tables,
--     FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE
--   which is an OWNERSHIP link (a row belongs to a chart), not a cross-asset one: a rebuild of any asset deletes only its own
--   chart-scoped rows by its own DELETE ... WHERE chart_id, and no asset's rebuild can cascade into another's. Verified first,
--   read-only, 2026-10-03: chart_id EXISTS on all five, is NOT NULL on all five, and is populated and resolves to a real
--   charts row for every row (phala_anchors 60, phala_pramana 60, phala_sankrama 630, phala_sodhana 41, phala_suddha_sodhana
--   60: 0 NULL, 0 without a charts row), so the constraints validate with no backfill. Side benefit: the 7 anchors with a NULL
--   convergence_id (53 of 60 carry one) were reachable by NO deletion path today and now are. The migration RAISES (and
--   changes nothing) if any of the five lacks chart_id, has it nullable, or holds a row whose chart is missing: it does not
--   invent a derivation. The constraints are validated (not NOT VALID); the tables are small.
--   Pre-existing and NOT fixed here (reported to SS): phala_muhurta, phala_mitigation and phala_phaladesa also have no FK to
--   charts, and mimamsa_* none either; they are not reached by chart deletion today and are not after this migration.
--
-- THE DETECTOR (no DB object; read-only; REPORTED, NEVER BUILD-BLOCKING): platform/scripts/nirmana/cross_asset_reference_orphans.sql
--   (two SELECTs) run by platform/scripts/nirmana/cross_asset_reference_orphans.py (READ ONLY transaction; exit 0 whether or
--   not orphans exist; exit 2 only if the query cannot run or does not return the seven references; exit 3 only with
--   --require-nonvacuous when a reference has zero referencing child rows). Statement 1 returns ALWAYS exactly seven rows (one
--   per reference), so an empty or unreadable child reads child_rows_with_reference = 0 and a zero orphan count is visibly
--   vacuous. Statement 2 gives the per-(reference, chart) counts. W7 / S-L3 pre/post check:
--     DATABASE_URL=... python3 platform/scripts/nirmana/cross_asset_reference_orphans.py
--   An orphan is a MISSING parent row; a parent on a different chart is not reported. It sees a child that exists and points at
--   nothing, not a child that was deleted. ph_nimitta's former cross-asset integrity terms moved to their owners in migration
--   1259 (PR #3019); this detector, not those checks, is what reports the dangling references.
--
-- LOCK-WAIT RISK (same as 1214; read before merging). DROP CONSTRAINT on a foreign key takes ACCESS EXCLUSIVE on the child
--   table and also locks the referenced table (its RI triggers are removed); ADD FOREIGN KEY takes SHARE ROW EXCLUSIVE on the
--   child AND on charts (validation scans the child; milliseconds at these sizes) and blocks concurrent writes to charts for
--   that time. SET LOCAL lock_timeout = '5s' makes a blocked attempt fail loudly rather than queue behind (and stall) every
--   reader, but scripts/migrate.ts has no retry: a long open read on any table involved during the deploy fails that deploy
--   until it is re-run. Merge in an idle window.
--
-- ACTIVE RUNS (ENFORCED, not advisory): the first DO block RAISES, changing nothing, if build_runs holds a run that is not
--   completed/failed/stopped (planned, running or paused) for any of ka_sangam, ka_kala_darshana, ka_vighnakara,
--   ka_bhavishya_lekha, ph_nimitta, ph_pramana, ph_sodhana, ph_suddha_sodhana, ph_sankrama. 0 on 2026-10-03.
--
-- GUARDS (raise rather than skip; a silent skip would let a database that lacks the property look migrated):
--   * every named table must exist as an ordinary table; the child, parent and chart_id columns must exist, chart_id NOT NULL;
--   * no row of the five tables may reference a missing chart;
--   * each of the seven constraints must be ABSENT (already dropped: NOTICE, idempotent) or PRESENT WITH EXACTLY the expected
--     definition (pg_get_constraintdef text, schema qualification normalised) on the expected child table; anything else
--     RAISES and changes nothing;
--   * each of the five chart constraints must be ABSENT (added) or PRESENT WITH EXACTLY the expected definition;
--   * post-check (asserting, RAISES): none of the seven remains and no cascading FK between a child and its parent remains; each
--     of the five chart constraints exists, is a foreign key to charts(id) on chart_id, convalidated, ON DELETE CASCADE, not
--     deferrable; the number of foreign keys in public changed by exactly (added - dropped) (nothing else changed).
--
-- NOT DONE HERE: the SET NULL links (phala_anchors.bhavishya_id, kala_bhavishya.convergence_id, phala_muhurta /
--   phala_mitigation linked_anchor_id, phala_sankrama.mitigation_ref, phala_mitigation.initiation_muhurta_ref);
--   chart_fact_identity -> chart_facts (G-IDX step); the charts-row-delete cascades of other tables (including the
--   muhurta/mitigation/phaladesa/mimamsa gap above); any rebuild; any data repair; any writer change; updating the docs that
--   still list these keys as CASCADE (00_ARCHITECTURE/briefs/nirmana/l3_autonomous/KALA_IO_USE_MATRIX_v1_0.md and its edges
--   fixture, historical evidence snapshots); the ph_nimitta/ph_pratikara integrity-check changes (migration 1259, PR #3019,
--   which gives the moved terms their owners).
--
-- VERIFICATION BY PRODUCTION STRUCTURE (CLAUDE.md N.4, Trap 103: never trust a deploy log). After the deploy, as
-- suvarna_reader, expect zero rows from:
--   SELECT conname FROM pg_constraint WHERE conname IN ('phala_anchors_convergence_id_fkey',
--     'kala_darshana_convergence_id_fkey','kala_obstruction_convergence_id_fkey','phala_pramana_anchor_id_fkey',
--     'phala_sankrama_source_anchor_id_fkey','phala_sodhana_anchor_id_fkey','phala_suddha_sodhana_anchor_id_fkey');
-- five validated cascading chart links:
--   SELECT conrelid::regclass, conname, convalidated, confdeltype, pg_get_constraintdef(oid) FROM pg_constraint
--    WHERE conname IN ('phala_anchors_chart_id_fkey','phala_pramana_chart_id_fkey','phala_sankrama_chart_id_fkey',
--                      'phala_sodhana_chart_id_fkey','phala_suddha_sodhana_chart_id_fkey') ORDER BY 1;
--      -- 5 rows, convalidated t, confdeltype c, FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE
-- 222 foreign keys in public (224 on 2026-10-03, minus seven, plus five):
--   SELECT count(*) FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace WHERE c.contype = 'f' AND n.nspname = 'public';
-- and the detector: seven rows, orphan_rows 0 on today's data (the python script above).
--
-- ROLLBACK (not executed by migrate.ts): for each of the seven rows of the list below: ALTER TABLE <child> ADD CONSTRAINT <name>
-- FOREIGN KEY (<col>) REFERENCES <parent>(<col>) ON DELETE CASCADE; (it validates every existing row, so it fails while any orphan
-- exists; use NOT VALID then VALIDATE after repairing). Re-adding the cascade re-creates the hazard. The five chart constraints
-- are an ownership link and should stay.

SET LOCAL lock_timeout = '5s';

DO $runs$
DECLARE n_active int; v_assets text;
BEGIN
    SELECT count(*), string_agg(DISTINCT a.asset_id, ', ') INTO n_active, v_assets
      FROM public.build_runs r JOIN public.build_run_assets a ON a.run_id = r.id
     WHERE a.asset_id IN ('ka_sangam', 'ka_kala_darshana', 'ka_vighnakara', 'ka_bhavishya_lekha', 'ph_nimitta', 'ph_pramana',
                          'ph_sodhana', 'ph_suddha_sodhana', 'ph_sankrama')
       AND r.state NOT IN ('completed', 'failed', 'stopped');
    IF n_active > 0 THEN
        RAISE EXCEPTION '1260: % active build run(s) (planned/running/paused) for %; refusing to change foreign keys under a running build', n_active, v_assets;
    END IF;
END
$runs$;

DO $mig$
DECLARE
    -- THE ONE PLACE EACH LIST LIVES. Unqualified names in schema public.
    -- Seven references dropped: constraint | child table | child column | parent table | parent column.
    refs text[] := ARRAY[
        'phala_anchors_convergence_id_fkey|phala_anchors|convergence_id|kala_convergence|convergence_id',
        'kala_darshana_convergence_id_fkey|kala_darshana|convergence_id|kala_convergence|convergence_id',
        'kala_obstruction_convergence_id_fkey|kala_obstruction|convergence_id|kala_convergence|convergence_id',
        'phala_pramana_anchor_id_fkey|phala_pramana|anchor_id|phala_anchors|anchor_id',
        'phala_sankrama_source_anchor_id_fkey|phala_sankrama|source_anchor_id|phala_anchors|anchor_id',
        'phala_sodhana_anchor_id_fkey|phala_sodhana|anchor_id|phala_anchors|anchor_id',
        'phala_suddha_sodhana_anchor_id_fkey|phala_suddha_sodhana|anchor_id|phala_anchors|anchor_id'
    ];
    -- Five ownership links added: constraint | table. Each is FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE.
    chart_links text[] := ARRAY[
        'phala_anchors_chart_id_fkey|phala_anchors',
        'phala_pramana_chart_id_fkey|phala_pramana',
        'phala_sankrama_chart_id_fkey|phala_sankrama',
        'phala_sodhana_chart_id_fkey|phala_sodhana',
        'phala_suddha_sodhana_chart_id_fkey|phala_suddha_sodhana'
    ];
    chart_def constant text := 'FOREIGN KEY (chart_id) REFERENCES charts(id) ON DELETE CASCADE';
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
    added        int := 0;
    n            int;
    bad          bigint;
BEGIN
    SELECT count(*) INTO fk_before
      FROM pg_constraint c JOIN pg_namespace ns ON ns.oid = c.connamespace
     WHERE c.contype = 'f' AND ns.nspname = 'public';

    -- Guard pass 1: the seven references (tables, columns, state of every constraint), BEFORE anything is changed.
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

    -- Guard pass 2: the five chart links. STOP (raise) rather than invent a derivation.
    IF to_regclass('public.charts') IS NULL OR NOT EXISTS (
         SELECT 1 FROM pg_index i WHERE i.indrelid = 'public.charts'::regclass AND i.indisprimary
            AND (SELECT attname FROM pg_attribute WHERE attrelid = i.indrelid AND attnum = i.indkey[0]) = 'id') THEN
        RAISE EXCEPTION '1260: public.charts(id) primary key not found';
    END IF;
    FOREACH r IN ARRAY chart_links LOOP
        f := string_to_array(r, '|');
        con := f[1]; child := f[2];
        child_oid := to_regclass(format('public.%I', child));
        IF child_oid IS NULL THEN
            RAISE EXCEPTION '1260: public.% does not exist', child;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = child_oid AND attname = 'chart_id' AND NOT attisdropped) THEN
            RAISE EXCEPTION '1260: public.% has no chart_id column; cannot add the ownership link and will not invent a derivation', child;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = child_oid AND attname = 'chart_id' AND NOT attisdropped AND attnotnull) THEN
            RAISE EXCEPTION '1260: public.%.chart_id is nullable; rows with a NULL chart would never be reached by chart deletion', child;
        END IF;
        EXECUTE format('SELECT count(*) FROM public.%I c WHERE NOT EXISTS (SELECT 1 FROM public.charts h WHERE h.id = c.chart_id)', child) INTO bad;
        IF bad > 0 THEN
            RAISE EXCEPTION '1260: public.% holds % row(s) whose chart_id has no charts row; report, do not backfill', child, bad;
        END IF;
        SELECT regexp_replace(pg_get_constraintdef(c.oid), ' public\.', ' ', 'g') INTO cdef
          FROM pg_constraint c WHERE c.conrelid = child_oid AND c.conname = con;
        IF cdef IS NOT NULL AND cdef IS DISTINCT FROM chart_def THEN
            RAISE EXCEPTION '1260: % on public.% exists but is not the expected chart link (found: %; expected: %)', con, child, cdef, chart_def;
        END IF;
    END LOOP;

    -- Add pass FIRST (so the tables are never without a deletion path inside this transaction), then the drop pass.
    FOREACH r IN ARRAY chart_links LOOP
        f := string_to_array(r, '|');
        con := f[1]; child := f[2];
        IF NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conrelid = format('public.%I', child)::regclass AND c.conname = con) THEN
            EXECUTE format('ALTER TABLE public.%I ADD CONSTRAINT %I FOREIGN KEY (chart_id) REFERENCES public.charts(id) ON DELETE CASCADE', child, con);
            added := added + 1;
        ELSE
            RAISE NOTICE '1260: % already present on public.%; nothing to add', con, child;
        END IF;
    END LOOP;

    FOREACH r IN ARRAY refs LOOP
        f := string_to_array(r, '|');
        con := f[1]; child := f[2];
        IF EXISTS (SELECT 1 FROM pg_constraint c
                    WHERE c.conrelid = format('public.%I', child)::regclass AND c.conname = con AND c.contype = 'f') THEN
            EXECUTE format('ALTER TABLE public.%I DROP CONSTRAINT %I', child, con);
            dropped := dropped + 1;
        END IF;
    END LOOP;

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
    FOREACH r IN ARRAY chart_links LOOP
        f := string_to_array(r, '|');
        con := f[1]; child := f[2];
        IF NOT EXISTS (SELECT 1 FROM pg_constraint c
                        WHERE c.conrelid = format('public.%I', child)::regclass AND c.conname = con AND c.contype = 'f'
                          AND c.confrelid = 'public.charts'::regclass AND c.convalidated AND c.confdeltype = 'c'
                          AND NOT c.condeferrable AND c.confupdtype = 'a'
                          AND c.conkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = c.conrelid AND attname = 'chart_id')]::smallint[]
                          AND c.confkey = ARRAY[(SELECT attnum FROM pg_attribute WHERE attrelid = 'public.charts'::regclass AND attname = 'id')]::smallint[]) THEN
            RAISE EXCEPTION '1260: chart link % on public.% is missing, not validated, not ON DELETE CASCADE, or not on chart_id -> charts(id)', con, child;
        END IF;
    END LOOP;
    SELECT count(*) INTO fk_after
      FROM pg_constraint c JOIN pg_namespace ns ON ns.oid = c.connamespace
     WHERE c.contype = 'f' AND ns.nspname = 'public';
    IF fk_after <> fk_before - dropped + added THEN
        RAISE EXCEPTION '1260: foreign keys in public went from % to % but % were dropped and % added (something else changed)',
            fk_before, fk_after, dropped, added;
    END IF;
    RAISE NOTICE '1260: dropped % of % cross-asset constraints, added % of % chart links', dropped, array_length(refs, 1), added, array_length(chart_links, 1);
END
$mig$;
