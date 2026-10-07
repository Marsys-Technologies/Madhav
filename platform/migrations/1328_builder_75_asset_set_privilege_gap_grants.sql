-- 1328_builder_75_asset_set_privilege_gap_grants.sql
--
-- Suvarna (PRIVMAP, 2026-10-07): ONE migration that closes EVERY database-privilege gap the build-pipeline identity
-- `data_plane_builder` has for the 75-asset forced asset_set (L0 33 + L1 19 + L2 23) of production run
-- 981a51ec-f1d1-4d82-b8c6-a8dccc81b1cb. Grants only: nothing is created, altered, dropped or revoked; no data is touched.
--
-- WHY. The run failed five wave-0 assets with InsufficientPrivilege (bg_cohort, bg_dignity_reference, bg_ghatana,
-- bg_nakshatra, bg_prashna_rules) and BLOCKED 33 downstream assets. Those five are only the FIRST denied statement of each
-- writer: a static map of every table, view and sequence the 75 writers (and their asset-registry integrity_check_sql
-- and the output-digest specs the orchestrator reads) touch, evaluated with has_table_privilege / has_sequence_privilege
-- against production, found 26 relations and 12 sequences on which the builder lacks a privilege its assets need.
-- The five failures are the first hit of 5 of the affected assets; the rest (bg_parihara_rules, bg_texts, bg_yogas,
-- bg_remedies, bg_vidhi_floors, bg_vastu_directions, ga_prashna, bo_samvada) would have failed next. Full map with
-- file:line evidence: POST/PRIVMAP_1328.md.
--
-- WHAT. The builder holds `arwd` (SELECT/INSERT/UPDATE/DELETE, no TRUNCATE) on every L0 table that existed at the
-- ownership cutover (migration 1035/1036) and `rU` (SELECT, USAGE) on their serial sequences; tables created after it
-- (the 24 below plus 2 more) never received that. This file restores EXACTLY the privileges each asset's own statements
-- need (derived per verb: INSERT ... ON CONFLICT DO UPDATE => INSERT+UPDATE+SELECT; DELETE ... WHERE => DELETE+SELECT),
-- plus USAGE+SELECT on the 12 serial sequences behind the INSERT targets (identity columns need no sequence grant).
-- Not granted: TRUNCATE, REFERENCES, TRIGGER, any column-level privilege, GRANT OPTION, role membership, PUBLIC, and no
-- schema-wide ALL TABLES / ALL SEQUENCES.
--
-- OWNERSHIP. All 26 relations and 12 sequences are owned by `amjis_app`, the role migrate.ts authenticates as (same
-- authority as 1070/1225/1255), so the owner issues the GRANTs; no one-shot owner bootstrap is needed. A guard raises
-- BEFORE any grant if a listed object is missing, is the wrong kind, or is not owned by (or usable as) the current role.
--
-- GUARDS: role must exist; every relation must exist with the listed relkind in schema public; every sequence must exist
-- as relkind S; the current role must be able to grant on each (pg_has_role(owner,'USAGE')). Raise rather than skip.
-- GRANT ONLY IF ABSENT: each privilege is checked with has_table_privilege / has_sequence_privilege first (a re-run,
-- or an environment that already holds a grant, is a no-op).
-- POST-CHECK: every listed privilege is held afterwards; and none of TRUNCATE / REFERENCES / TRIGGER was left held on
-- any listed relation. Table-level post-check scope: effective privileges (direct, PUBLIC, inherited); not privileges
-- reachable only through a NOINHERIT membership, and on PostgreSQL 17 not MAINTAIN (production is 15.18).
--
-- DATA-DRIVEN: the relation list and the sequence list each appear exactly once (the two VALUES lists in the DO block).
-- ROLLBACK NOTE: never REVOKE (production may hold any of these independently of this file). To undo, author a new
-- reviewed migration against the then-current state.
-- ISOLATION: a database GRANT is not an IAM binding; data-plane-secret-isolation-preflight.ts checks project IAM roles
-- only; data-plane-ownership-preflight.ts L1/L2_ACTIVE_TABLES cover l1/l2 tables only. None of these 26 relations is in
-- either set.
-- PRIVACY NOTE: prashna_charts (chart-scoped horary data, 2 rows) is granted SELECT only because ga_prashna reads it on
-- EVERY chart (ga_writers/ga_prashna_writer.py:128); 1255 deferred it while ga_prashna was out of scope. If the
-- ruling is that ga_prashna stays out of scope, delete that one VALUES row and the asset must stay out of the set.
-- VERIFY AFTER APPLY by production structure, not the deploy log (Trap 103): run the verification SELECT in
-- POST/PRIVMAP_1328.md; it must return 0 rows.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).

SET LOCAL lock_timeout = '5s';

DO $$
DECLARE
    -- THE ONE PLACE THE RELATION LIST LIVES: (name in schema public, expected relkind, comma-separated privileges).
    r        record;
    p        text;
    rel      regclass;
    kind     "char";
    owner_oid oid;
    extra    text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
        RAISE EXCEPTION '1328: role data_plane_builder does not exist';
    END IF;

    -- Guard pass (nothing is granted until every object passes).
    FOR r IN SELECT * FROM (VALUES
        ('bg_avastha_schemes', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_combustion_orbs', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_graha_naisargika_friendship', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_motion_state_thresholds', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_muhurta_activity_rules', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_muhurta_factor_census', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_fructification_rules', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_lagna_methods', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_significators', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_special_techniques', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_tajik_yogas', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_synthetic_cohort', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('bg_synthetic_cohort_md', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('bg_vastu_direction_remedials', 'r', 'SELECT,INSERT,UPDATE'),
        ('brahma_activity_ontology', 'r', 'SELECT,INSERT,UPDATE'),
        ('brahma_yoga_source_chunks', 'r', 'SELECT,INSERT,DELETE'),
        ('classical_texts', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('nirmana_bg_texts_integrity_baselines', 'r', 'SELECT'),
        ('prashna_charts', 'r', 'SELECT'),
        ('reference_nakshatra', 'r', 'SELECT,INSERT,DELETE'),
        ('reference_nakshatra_matrix', 'r', 'SELECT,INSERT,DELETE'),
        ('reference_nakshatra_pada', 'r', 'SELECT,INSERT,DELETE'),
        ('remedy_review_queue', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('vidhi_intent_floors', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('vw_chart_digest', 'v', 'SELECT'),
        ('yoga_families', 'r', 'SELECT,INSERT')
    ) AS v(relname, expected_kind, privs) LOOP
        rel := to_regclass(format('public.%I', r.relname));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1328: public.% does not exist', r.relname;
        END IF;
        SELECT c.relkind, c.relowner INTO kind, owner_oid FROM pg_class c WHERE c.oid = rel;
        IF kind::text <> r.expected_kind THEN
            RAISE EXCEPTION '1328: public.% has relkind % (expected %)', r.relname, kind, r.expected_kind;
        END IF;
        IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN
            RAISE EXCEPTION '1328: current role % cannot grant on public.% (owner %); owner path required',
                current_user, r.relname, pg_get_userbyid(owner_oid);
        END IF;
    END LOOP;
    FOR r IN SELECT * FROM (VALUES
        ('bg_avastha_schemes_id_seq'),
        ('bg_combustion_orbs_id_seq'),
        ('bg_graha_naisargika_friendship_id_seq'),
        ('bg_motion_state_thresholds_id_seq'),
        ('bg_prashna_fructification_rules_id_seq'),
        ('bg_prashna_lagna_methods_id_seq'),
        ('bg_prashna_significators_id_seq'),
        ('bg_prashna_special_techniques_id_seq'),
        ('bg_prashna_tajik_yogas_id_seq'),
        ('bg_vastu_direction_remedials_id_seq'),
        ('reference_nakshatra_matrix_id_seq'),
        ('yoga_families_id_seq')
    ) AS v(seqname) LOOP
        rel := to_regclass(format('public.%I', r.seqname));
        IF rel IS NULL THEN
            RAISE EXCEPTION '1328: sequence public.% does not exist', r.seqname;
        END IF;
        SELECT c.relkind, c.relowner INTO kind, owner_oid FROM pg_class c WHERE c.oid = rel;
        IF kind <> 'S' THEN
            RAISE EXCEPTION '1328: public.% is not a sequence (relkind %)', r.seqname, kind;
        END IF;
        IF NOT pg_has_role(current_user, owner_oid, 'USAGE') THEN
            RAISE EXCEPTION '1328: current role % cannot grant on sequence public.% (owner %); owner path required',
                current_user, r.seqname, pg_get_userbyid(owner_oid);
        END IF;
    END LOOP;

    -- Grant pass: only what is absent.
    FOR r IN SELECT * FROM (VALUES
        ('bg_avastha_schemes', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_combustion_orbs', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_graha_naisargika_friendship', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_motion_state_thresholds', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_muhurta_activity_rules', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_muhurta_factor_census', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_fructification_rules', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_lagna_methods', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_significators', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_special_techniques', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_tajik_yogas', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_synthetic_cohort', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('bg_synthetic_cohort_md', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('bg_vastu_direction_remedials', 'r', 'SELECT,INSERT,UPDATE'),
        ('brahma_activity_ontology', 'r', 'SELECT,INSERT,UPDATE'),
        ('brahma_yoga_source_chunks', 'r', 'SELECT,INSERT,DELETE'),
        ('classical_texts', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('nirmana_bg_texts_integrity_baselines', 'r', 'SELECT'),
        ('prashna_charts', 'r', 'SELECT'),
        ('reference_nakshatra', 'r', 'SELECT,INSERT,DELETE'),
        ('reference_nakshatra_matrix', 'r', 'SELECT,INSERT,DELETE'),
        ('reference_nakshatra_pada', 'r', 'SELECT,INSERT,DELETE'),
        ('remedy_review_queue', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('vidhi_intent_floors', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('vw_chart_digest', 'v', 'SELECT'),
        ('yoga_families', 'r', 'SELECT,INSERT')
    ) AS v(relname, expected_kind, privs) LOOP
        rel := format('public.%I', r.relname)::regclass;
        FOREACH p IN ARRAY string_to_array(r.privs, ',') LOOP
            IF has_table_privilege('data_plane_builder', rel, p) THEN
                RAISE NOTICE '1328: data_plane_builder already holds % on public.%; no-op', p, r.relname;
            ELSE
                EXECUTE format('GRANT %s ON TABLE %s TO data_plane_builder', p, rel);
            END IF;
        END LOOP;
    END LOOP;
    FOR r IN SELECT * FROM (VALUES
        ('bg_avastha_schemes_id_seq'),
        ('bg_combustion_orbs_id_seq'),
        ('bg_graha_naisargika_friendship_id_seq'),
        ('bg_motion_state_thresholds_id_seq'),
        ('bg_prashna_fructification_rules_id_seq'),
        ('bg_prashna_lagna_methods_id_seq'),
        ('bg_prashna_significators_id_seq'),
        ('bg_prashna_special_techniques_id_seq'),
        ('bg_prashna_tajik_yogas_id_seq'),
        ('bg_vastu_direction_remedials_id_seq'),
        ('reference_nakshatra_matrix_id_seq'),
        ('yoga_families_id_seq')
    ) AS v(seqname) LOOP
        rel := format('public.%I', r.seqname)::regclass;
        FOREACH p IN ARRAY ARRAY['USAGE', 'SELECT'] LOOP
            IF has_sequence_privilege('data_plane_builder', rel, p) THEN
                RAISE NOTICE '1328: data_plane_builder already holds % on sequence public.%; no-op', p, r.seqname;
            ELSE
                EXECUTE format('GRANT %s ON SEQUENCE %s TO data_plane_builder', p, rel);
            END IF;
        END LOOP;
    END LOOP;

    -- Post-check: every listed privilege took effect, and nothing outside the stated scope is held.
    FOR r IN SELECT * FROM (VALUES
        ('bg_avastha_schemes', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_combustion_orbs', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_graha_naisargika_friendship', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_motion_state_thresholds', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_muhurta_activity_rules', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_muhurta_factor_census', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_fructification_rules', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_lagna_methods', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_significators', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_special_techniques', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_prashna_tajik_yogas', 'r', 'SELECT,INSERT,UPDATE'),
        ('bg_synthetic_cohort', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('bg_synthetic_cohort_md', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('bg_vastu_direction_remedials', 'r', 'SELECT,INSERT,UPDATE'),
        ('brahma_activity_ontology', 'r', 'SELECT,INSERT,UPDATE'),
        ('brahma_yoga_source_chunks', 'r', 'SELECT,INSERT,DELETE'),
        ('classical_texts', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('nirmana_bg_texts_integrity_baselines', 'r', 'SELECT'),
        ('prashna_charts', 'r', 'SELECT'),
        ('reference_nakshatra', 'r', 'SELECT,INSERT,DELETE'),
        ('reference_nakshatra_matrix', 'r', 'SELECT,INSERT,DELETE'),
        ('reference_nakshatra_pada', 'r', 'SELECT,INSERT,DELETE'),
        ('remedy_review_queue', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('vidhi_intent_floors', 'r', 'SELECT,INSERT,UPDATE,DELETE'),
        ('vw_chart_digest', 'v', 'SELECT'),
        ('yoga_families', 'r', 'SELECT,INSERT')
    ) AS v(relname, expected_kind, privs) LOOP
        rel := format('public.%I', r.relname)::regclass;
        FOREACH p IN ARRAY string_to_array(r.privs, ',') LOOP
            IF NOT has_table_privilege('data_plane_builder', rel, p) THEN
                RAISE EXCEPTION '1328: data_plane_builder lacks % on public.% after the grant', p, r.relname;
            END IF;
        END LOOP;
        SELECT string_agg(q, ', ' ORDER BY q) INTO extra
          FROM unnest(ARRAY['TRUNCATE','REFERENCES','TRIGGER']) q
         WHERE has_table_privilege('data_plane_builder', rel, q);
        IF extra IS NOT NULL THEN
            RAISE EXCEPTION '1328: data_plane_builder holds out-of-scope privilege(s) on public.%: %', r.relname, extra;
        END IF;
    END LOOP;
    FOR r IN SELECT * FROM (VALUES
        ('bg_avastha_schemes_id_seq'),
        ('bg_combustion_orbs_id_seq'),
        ('bg_graha_naisargika_friendship_id_seq'),
        ('bg_motion_state_thresholds_id_seq'),
        ('bg_prashna_fructification_rules_id_seq'),
        ('bg_prashna_lagna_methods_id_seq'),
        ('bg_prashna_significators_id_seq'),
        ('bg_prashna_special_techniques_id_seq'),
        ('bg_prashna_tajik_yogas_id_seq'),
        ('bg_vastu_direction_remedials_id_seq'),
        ('reference_nakshatra_matrix_id_seq'),
        ('yoga_families_id_seq')
    ) AS v(seqname) LOOP
        rel := format('public.%I', r.seqname)::regclass;
        IF NOT (has_sequence_privilege('data_plane_builder', rel, 'USAGE')
                AND has_sequence_privilege('data_plane_builder', rel, 'SELECT')) THEN
            RAISE EXCEPTION '1328: data_plane_builder lacks USAGE/SELECT on sequence public.% after the grant', r.seqname;
        END IF;
    END LOOP;
END $$;
