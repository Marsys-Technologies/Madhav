-- Migration 1153: ka_gochara sky-event substrate — convention, physical
--                 object, boundary sky events, the §6.1 CONTACT identity and
--                 its per-(chart × generation) ledger, the permanent
--                 publication seal, and the legacy-convention bridge
--                 (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§7/§10, FROZEN 2026-09-30).
--                 Round-3 rewrite per ASTRA_REVIEW_A5_1_MIGRATIONS v1_1
--                 (REJECT; F1–F11) under the steward rulings of 2026-09-30.
--                 1153–1157 were never applied anywhere, so this is an
--                 in-place rewrite of the same number.
-- Created: 2026-09-30. Author: pravaha/a5-migrations (Stream A, A5.1).
--
-- Numbering: 1153 sits inside this lane's granted block (1150–1159 per
-- ADK-0026 §4; 1150/1151/1152 are used). Verified free by a fresh scan of
-- every origin/* ref across BOTH platform/migrations/ and
-- platform/supabase/migrations/ (2026-09-30: the only 1153–1157 files on any
-- head are this PR's own). `npm run guard:migration-numbers` green.
--
-- ── Transaction ownership (round-1 amendment 2, kept closed) ───────────────
-- No BEGIN/COMMIT/ROLLBACK here. platform/scripts/migrate.ts owns ONE
-- transaction around (this file + the _migrations_applied ledger insert);
-- SET LOCAL is scoped to that transaction. The forced-failure test in
-- platform/tests/integration/gochara_a5_1_migrations.db.test.ts injects a
-- ledger-insert failure after EACH of 1153–1157 in turn and proves nothing of
-- the failed migration persists (tables AND standalone functions).
--
-- ── Effective ordered gate (F8/F9) ─────────────────────────────────────────
-- Order inside this file: (1) pinned schema + timeouts, (2) the PREFLIGHT
-- GATE — a DO block byte-identical to
-- platform/python-sidecar/scripts/kala_gochara_cutover/preflight_1153_sky_event_substrate.sql
-- (the static test asserts identity), which RAISES on any privilege gap,
-- missing/mis-keyed parent, untracked same-name collision (relations,
-- table-scoped triggers, functions by exact ARGUMENT TYPES — never by the
-- name-retaining pg_get_function_identity_arguments text) or prior ledger
-- entry, (3) the DDL, (4) POST-DDL DEFINITION VERIFICATION comparing the
-- actual catalog definitions (columns+types+nullability, every
-- PK/UNIQUE/FK/CHECK deparsed + validation state, every trigger deparsed,
-- every index deparsed, every function's signature/return/volatility/
-- language) against the contracted definitions embedded below. Because the
-- gate is INSIDE the file, the production deploy path (deploy.yml → the
-- general runner) observes it without any workflow change.
--   Outcomes, distinct and tested:
--     * tracked skip      — migrate.ts skips a file recorded in the ledger
--                           (hash-verified); nothing in this file runs.
--     * fresh apply       — gate passes, DDL creates, verification proves.
--     * untracked collision — gate RAISES ('relation_already_exists', …);
--                           a same-named object is never silently adopted.
--     * deliberate equivalent replay — an operator sets
--                           SET LOCAL ka_gochara.deliberate_replay = 'on';
--                           existence checks are skipped, IF NOT EXISTS /
--                           OR REPLACE re-assert the definitions and the
--                           verification block proves equivalence; any
--                           drifted definition (wrong CHECK body, missing
--                           PK, extra column) RAISES.
--
-- ── F1/F2/F4 — the contact identity model (documented; enforced below) ────
-- STABLE PHYSICAL IDENTITY vs CHART/GENERATION OWNERSHIP are two tables:
--   * ka_gochara_contact_identity — one row per contact id; contact_id =
--     hash(physical_object_id, occurrence_ordinal) EXACTLY as frozen (§6.1,
--     O-RX-1 identity bytes body|relation_kind|canonical_target|
--     convention_id|ordinal). No correction_seq: the round-2 extra hash
--     component is withdrawn (F4). UNIQUE (physical_object_id,
--     occurrence_ordinal). Insert-only, never deleted, TRUNCATE refused —
--     "once a contact id has been published it is never renumbered or
--     reused" holds for every id, whatever generation later holds it.
--   * ka_gochara_contact — the per-(chart_id, generation) LEDGER row that
--     owns the solved values (t_in/t_out/t_exact, method, uncertainties,
--     coverage). PRIMARY KEY (chart_id, generation, contact_id): the same
--     physical contact legitimately coexists in a retained published
--     generation and in a candidate rebuild (F1). The writer rebuilds a
--     CANDIDATE generation by per-(chart_id × generation) delete-then-insert
--     (CLAUDE.md §N.3); identities are re-used by hash, never re-minted.
--   Every reference to a contact is bound to the ownership scope: 1155's
--   transit records FK (chart_id, generation, contact_id, agent, relation,
--   object_id) → this ledger (F1/F7).
-- CORRECTION IDENTITY (F4) follows the frozen recipe, not a new one: a
--   correction changes a published non-NULL value (t_exact, longitude,
--   ordinal, target — §6.1). Under hash(physical_object_id, ordinal) a new id
--   arises exactly when the physical tuple changes: a corrected TARGET is a
--   new canonical_target ⇒ new physical object; a corrected solution of the
--   same tuple is a METHOD change ⇒ new convention_id (§7.2 inv 4: "a
--   tolerance or method change implies a new convention_id; contact ids hash
--   method_version") ⇒ new physical object. A same-tuple, same-convention
--   rewrite of a published t_exact is therefore NOT a representable state —
--   the UPDATE is refused by trigger and the writer must publish the
--   correction under a new convention. The supersedes edge links the retired
--   identity to its correction: the predecessor must be a DIFFERENT identity
--   of the SAME (body, relation_kind) — target and/or convention may differ —
--   a chain, never a tree (UNIQUE on supersedes_contact_id), never self, never
--   mutable. Retirement is derivable (superseded ⇒ retired); no mutable flag.
-- ENRICHMENT (§6.1 "enrichment vs correction"): an UPDATE may only fill a
--   NULL field or flip coverage.truncated true→false together with filling
--   t_exact; solver_method may change ONLY from 'clipped_truncated' as part
--   of that flip (F4 loophole closed: a non-placeholder method never changes
--   in place). truncated ⇔ (t_exact IS NULL) ⇔ (solver_method =
--   'clipped_truncated') is a CHECK on both the sky event and the ledger.
-- PUBLICATION PROTECTION (F2) follows PERMANENT publication history:
--   * ka_gochara_generation_seal (chart_id, generation, manifest_id) —
--     insert-only, never deleted, TRUNCATE refused; written automatically by
--     an AFTER trigger on kala_gochara_publication whenever a manifest row
--     becomes status='published' (and writable directly by the release
--     authority, in which case the BEFORE INSERT trigger verifies the
--     manifest IS published). A generation that was ever published stays
--     sealed through 'superseded' and 'rolled_back' — protection never
--     expires with the serving status.
--   * ka_gochara_generation_is_sealed(chart, generation) is the ONE predicate
--     every guard reads: seal row present OR a kala_gochara_publication row
--     with a non-candidate status / published_at (covers generations
--     published before this migration existed). It takes
--     pg_advisory_xact_lock(hashtext('ka_gochara_generation:'||chart),
--     hashtext(generation)) — the SAME lock the seal writer takes — so a
--     candidate rebuild and a concurrent publication SERIALIZE: whichever
--     commits first wins; a delete that raced a publish either completes
--     before the seal exists or sees it and is refused. This is the
--     publication/rebuild synchronization protocol.
--   * DELETE on a sealed generation's ledger rows is refused; INSERT (append
--     — partition extension inside the domain, O-RX-1 ordinal 4) and
--     enrichment stay permitted; TRUNCATE is refused unconditionally on every
--     table this family owns (PostgreSQL fires no row triggers on TRUNCATE).
-- LEGACY MAPPING (steward ruling): legacy kala_gochara_contacts rows (1081;
--   PK (chart_id, generation, contact_id TEXT "sha256:<hex>")) are NOT
--   migrated. Correspondence is BY GENERATION ONLY — a legacy row's
--   (chart_id, generation) scope equals a ledger row's (chart_id, generation)
--   scope; the legacy TEXT contact_id has no mapping into the new UUID
--   identity and is never reused.
-- CONVENTION BRIDGE (F7): kala_gochara_coverage carries the LEGACY 1081
--   convention vector; contacts carry the §6.1 sky convention.
--   ka_gochara_convention_bridge (kala_convention_id → sky_convention_id,
--   insert-only) is the explicit bridge; 1155's coverage-applicability guard
--   refuses a transit record whose coverage partition's convention is not
--   bridged to its contact's sky convention.
--
-- Encoded as:
--   * CONSTRAINT: event_kind 5-enum (§6.1); physical relation_kind = the 3
--     transit relations ∪ the 5 boundary kinds, and the composite FKs
--     (physical_object_id, body, relation_kind|event_kind, convention_id) →
--     physical object make an event's kind and a contact's relation agree
--     with the object they reference (F7 physical-relation consistency);
--     solver_method 3-enum (§7.1); ordinals ≥ 1; UNIQUE (physical_object_id,
--     occurrence_ordinal) on both identity tables; ordered convention domain;
--     coverage JSONB must CARRY an explicit boolean 'truncated'; truncated ⇔
--     t_exact NULL ⇔ clipped_truncated; every reported t_exact carries
--     longitude/δλ/δt/precision_regime (§7.2 inv 1); δλ/δt finite and ≥ 0,
--     longitude ∈ [0,360) (F11); station ⇒ swiss_refined (O-SM-3); body
--     domains (substrate excludes Moon — O-SS-4); canonical chart CHECK
--     (D-SCOPE) on the per-chart ledger; no self-supersession; supersession
--     chain uniqueness.
--   * TRIGGER: convention/object/identity/seal/bridge insert-only + TRUNCATE
--     refused; sky_event DELETE forbidden + enrichment-only UPDATE +
--     supersede-edge validation; contact ledger sealed-generation DELETE
--     refusal + enrichment-only UPDATE; identity supersede-edge validation;
--     publication → seal recording.
--   * COMMENT ONLY (writer behaviour, not SQL-checkable): the hash recipes;
--     canonical_target canonicalisation; ordinal assignment over the
--     FULL-domain ordered crossing set, forward-time partitions only,
--     append-only extension; loud failure on hash collision; Moon events
--     generated on demand with a moon_on_demand coverage record (O-SS-4).
--   * DELIBERATELY NOT ENCODED: the "0° seam root exists" / both-boundaries
--     search rules (§6.2) — solver-side invariants, no table shape here.
--
-- asset_registry: deliberately NOT registered (asset_registry.layer CHECK
-- admits no 'L2' value; contract tables of the already-registered ka_gochara
-- writer family — same disposition as 1081).
--
-- ROLLBACK (down-migration, dependents first; 1154–1157 must be rolled back
-- before this):
--   DROP TRIGGER IF EXISTS ka_gochara_publication_seal_record ON kala_gochara_publication;
--   DROP TABLE IF EXISTS ka_gochara_contact;
--   DROP TABLE IF EXISTS ka_gochara_convention_bridge;
--   DROP TABLE IF EXISTS ka_gochara_generation_seal;
--   DROP TABLE IF EXISTS ka_gochara_contact_identity;
--   DROP TABLE IF EXISTS ka_gochara_sky_event;
--   DROP TABLE IF EXISTS ka_gochara_physical_object;
--   DROP TABLE IF EXISTS ka_gochara_sky_convention;
--   DROP FUNCTION IF EXISTS ka_gochara_contact_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_contact_identity_supersede_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_generation_is_sealed(uuid, text);
--   DROP FUNCTION IF EXISTS ka_gochara_generation_seal_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_record_generation_seal();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_event_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_sky_event_supersede_guard();
--   DROP FUNCTION IF EXISTS ka_gochara_insert_only();
--   DROP FUNCTION IF EXISTS ka_gochara_refuse_truncate();
--   DROP FUNCTION IF EXISTS ka_gochara_verify_definitions(text, jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_jsonb_diff(text, jsonb, jsonb);
--   DROP FUNCTION IF EXISTS ka_gochara_describe_definitions(text[], text[]);
--   DROP FUNCTION IF EXISTS ka_gochara_norm_def(text);
--   DROP FUNCTION IF EXISTS ka_gochara_finite_nonneg_ok(double precision);
--   DROP FUNCTION IF EXISTS ka_gochara_finite_ok(double precision);
--   DROP FUNCTION IF EXISTS ka_gochara_text_array_ok(text[], integer);
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1153_sky_event_substrate.sql) ────────
DO $$
DECLARE
  replay   boolean := COALESCE(current_setting('ka_gochara.deliberate_replay', true), '') = 'on';
  failures text;
BEGIN
  WITH f(failure, detail) AS (
    -- (d) pinned schema + effective privileges
    SELECT 'schema_missing', 'public'
    WHERE to_regnamespace('public') IS NULL
    UNION ALL
    SELECT 'no_usage_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'USAGE')
    UNION ALL
    SELECT 'no_create_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'CREATE')
    UNION ALL
    SELECT 'no_references_privilege', p.t
    FROM (VALUES ('public.charts'),
                 ('public.kala_gochara_publication'),
                 ('public.kala_gochara_convention')) AS p(t)
    WHERE to_regclass(p.t) IS NOT NULL AND NOT has_table_privilege(p.t, 'REFERENCES')
    UNION ALL
    SELECT 'no_trigger_privilege', 'public.kala_gochara_publication'
    WHERE to_regclass('public.kala_gochara_publication') IS NOT NULL
      AND NOT has_table_privilege('public.kala_gochara_publication', 'TRIGGER')
    UNION ALL
    -- (a1) relation-namespace collisions (tables, indexes, sequences share pg_class)
    SELECT 'relation_already_exists', 'public.' || c.relname
    FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public'
      AND c.relname IN ('ka_gochara_sky_convention', 'ka_gochara_sky_convention_pkey',
                        'ka_gochara_physical_object', 'ka_gochara_physical_object_pkey',
                        'ka_gochara_physical_object_natural_uq', 'kgpo_identity_uq',
                        'ka_gochara_sky_event', 'ka_gochara_sky_event_pkey',
                        'ka_gochara_sky_event_ordinal_uq', 'kgse_supersedes_uq',
                        'ka_gochara_contact_identity', 'ka_gochara_contact_identity_pkey',
                        'ka_gochara_contact_identity_ordinal_uq', 'kgci_supersedes_uq',
                        'kgci_tuple_uq',
                        'ka_gochara_generation_seal', 'ka_gochara_generation_seal_pkey',
                        'ka_gochara_convention_bridge', 'ka_gochara_convention_bridge_pkey',
                        'ka_gochara_contact', 'ka_gochara_contact_pkey', 'kgc_reference_uq',
                        'idx_kgse_convention_time', 'idx_kgc_chart_gen', 'idx_kgc_object',
                        'idx_kgc_identity')
    UNION ALL
    -- (a2) trigger collisions, scoped to the intended table in public
    SELECT 'trigger_already_exists', 'public.' || c.relname || '.' || t.tgname
    FROM pg_trigger t
    JOIN pg_class c ON c.oid = t.tgrelid
    JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE NOT replay AND n.nspname = 'public' AND NOT t.tgisinternal
      AND ( (c.relname = 'ka_gochara_sky_convention'
               AND t.tgname IN ('ka_gochara_sky_convention_immutable',
                                'ka_gochara_sky_convention_no_truncate'))
         OR (c.relname = 'ka_gochara_physical_object'
               AND t.tgname IN ('ka_gochara_physical_object_immutable',
                                'ka_gochara_physical_object_no_truncate'))
         OR (c.relname = 'ka_gochara_sky_event'
               AND t.tgname IN ('ka_gochara_sky_event_supersede_check',
                                'ka_gochara_sky_event_mutation_guard',
                                'ka_gochara_sky_event_no_truncate'))
         OR (c.relname = 'ka_gochara_contact_identity'
               AND t.tgname IN ('ka_gochara_contact_identity_supersede_check',
                                'ka_gochara_contact_identity_immutable',
                                'ka_gochara_contact_identity_no_truncate'))
         OR (c.relname = 'ka_gochara_generation_seal'
               AND t.tgname IN ('ka_gochara_generation_seal_check',
                                'ka_gochara_generation_seal_immutable',
                                'ka_gochara_generation_seal_no_truncate'))
         OR (c.relname = 'ka_gochara_convention_bridge'
               AND t.tgname IN ('ka_gochara_convention_bridge_immutable',
                                'ka_gochara_convention_bridge_no_truncate'))
         OR (c.relname = 'ka_gochara_contact'
               AND t.tgname IN ('ka_gochara_contact_lifecycle_guard',
                                'ka_gochara_contact_no_truncate'))
         OR (c.relname = 'kala_gochara_publication'
               AND t.tgname = 'ka_gochara_publication_seal_record') )
    UNION ALL
    -- (a3) function collisions by EXACT ARGUMENT TYPES (F8: the identity-
    -- arguments text retains parameter names and is not a signature)
    SELECT 'function_already_exists',
           'public.' || p.proname || '(' || array_to_string(e.argtypes, ',') || ')'
    FROM (VALUES
            ('ka_gochara_refuse_truncate',                ARRAY[]::text[]),
            ('ka_gochara_insert_only',                    ARRAY[]::text[]),
            ('ka_gochara_text_array_ok',                  ARRAY['text[]','integer']),
            ('ka_gochara_finite_ok',                      ARRAY['double precision']),
            ('ka_gochara_finite_nonneg_ok',               ARRAY['double precision']),
            ('ka_gochara_norm_def',                       ARRAY['text']),
            ('ka_gochara_describe_definitions',           ARRAY['text[]','text[]']),
            ('ka_gochara_jsonb_diff',                     ARRAY['text','jsonb','jsonb']),
            ('ka_gochara_verify_definitions',             ARRAY['text','jsonb']),
            ('ka_gochara_sky_event_supersede_guard',      ARRAY[]::text[]),
            ('ka_gochara_sky_event_guard',                ARRAY[]::text[]),
            ('ka_gochara_contact_identity_supersede_guard', ARRAY[]::text[]),
            ('ka_gochara_record_generation_seal',         ARRAY[]::text[]),
            ('ka_gochara_generation_seal_guard',          ARRAY[]::text[]),
            ('ka_gochara_generation_is_sealed',           ARRAY['uuid','text']),
            ('ka_gochara_contact_guard',                  ARRAY[]::text[])
         ) AS e(fname, argtypes)
    JOIN pg_proc p ON p.proname = e.fname
    JOIN pg_namespace n ON n.oid = p.pronamespace AND n.nspname = 'public'
    WHERE NOT replay
      AND (SELECT COALESCE(array_agg(format_type(u.oid, NULL) ORDER BY u.ord), '{}')
           FROM unnest(p.proargtypes) WITH ORDINALITY AS u(oid, ord)) = e.argtypes
    UNION ALL
    -- (b1) in-database parents exist
    SELECT 'parent_table_missing', p.t
    FROM (VALUES ('charts'), ('kala_gochara_publication'), ('kala_gochara_convention')) AS p(t)
    WHERE to_regclass('public.' || p.t) IS NULL
    UNION ALL
    -- (b2) parent columns exist with the expected types (expected side named)
    SELECT 'parent_column_missing_or_type',
           e.t || '.' || e.col || ' expected ' || e.typ
    FROM (VALUES ('charts',                   'id',           'uuid'),
                 ('kala_gochara_publication', 'manifest_id',  'uuid'),
                 ('kala_gochara_publication', 'chart_id',     'uuid'),
                 ('kala_gochara_publication', 'generation',   'text'),
                 ('kala_gochara_publication', 'status',       'text'),
                 ('kala_gochara_publication', 'published_at', 'timestamp with time zone'),
                 ('kala_gochara_convention',  'convention_id','text')) AS e(t, col, typ)
    LEFT JOIN pg_attribute a
      ON a.attrelid = to_regclass('public.' || e.t) AND a.attname = e.col AND NOT a.attisdropped
    WHERE a.attname IS NULL OR format_type(a.atttypid, a.atttypmod) IS DISTINCT FROM e.typ
    UNION ALL
    -- (b3) parent PK/UNIQUE definitions verified against pg_constraint
    SELECT 'parent_key_missing', e.t || ' must carry a PK/UNIQUE over ' || e.cols::text
    FROM (VALUES ('charts',                   ARRAY['id']),
                 ('kala_gochara_publication', ARRAY['manifest_id']),
                 ('kala_gochara_publication', ARRAY['chart_id','generation']),
                 ('kala_gochara_convention',  ARRAY['convention_id'])) AS e(t, cols)
    WHERE to_regclass('public.' || e.t) IS NOT NULL
      AND NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        WHERE c.conrelid = to_regclass('public.' || e.t) AND c.contype IN ('p','u')
          AND (SELECT array_agg(a.attname::text ORDER BY a.attname)
               FROM unnest(c.conkey) k JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k)
              = (SELECT array_agg(x ORDER BY x) FROM unnest(e.cols) x))
    UNION ALL
    -- (c) ledger lookup, wildcard-safe (starts_with, not LIKE)
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE NOT replay AND to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1153_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1153 BLOCKED — migration 1153 must NOT be applied:% %', E'\n', failures;
  END IF;
  IF replay THEN
    RAISE NOTICE 'preflight 1153: deliberate replay — existence checks skipped; definitions are verified post-DDL';
  END IF;
  RAISE NOTICE 'preflight 1153: all checks passed';
END;
$$;

-- ── 0. Shared helpers (this family; reused by 1154–1157) ──────────────────

-- TRUNCATE bypasses every row trigger and is generation-blind: refused on
-- every table this family owns (F2).
CREATE OR REPLACE FUNCTION public.ka_gochara_refuse_truncate()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION 'TRUNCATE refused on % (GOCHARA_DESIGN_SPECS_v1_4 §6.1 publication immutability; CLAUDE.md §N.3): TRUNCATE is generation-blind and bypasses the row guards — rebuild a CANDIDATE generation with a scoped DELETE', TG_TABLE_NAME;
END;
$$;

-- Generic insert-only guard (registries, identities, seals, bridges).
CREATE OR REPLACE FUNCTION public.ka_gochara_insert_only()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION '% is insert-only (GOCHARA_DESIGN_SPECS_v1_4 %): % not permitted; a change is a NEW row (new id / new version / new convention), never an edit',
    TG_TABLE_NAME, COALESCE(TG_ARGV[0], '§6.1'), TG_OP;
END;
$$;

-- text[] whose elements are all non-NULL, non-blank, with at least p_min elements.
CREATE OR REPLACE FUNCTION public.ka_gochara_text_array_ok(a text[], p_min integer)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT a IS NOT NULL
     AND COALESCE(cardinality(a), 0) >= p_min
     AND NOT EXISTS (SELECT 1 FROM unnest(a) e WHERE e IS NULL OR btrim(e) = '');
$$;

-- Finite (not NaN, not ±infinity) — NULL passes; callers decide NULL policy.
CREATE OR REPLACE FUNCTION public.ka_gochara_finite_ok(x double precision)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT x IS NULL
      OR (NOT (x = 'NaN'::double precision)
          AND x > '-infinity'::double precision
          AND x < 'infinity'::double precision);
$$;

-- Finite and non-negative (F11: `>= 0` alone admits NaN and +infinity).
CREATE OR REPLACE FUNCTION public.ka_gochara_finite_nonneg_ok(x double precision)
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT x IS NULL
      OR (NOT (x = 'NaN'::double precision)
          AND x >= 0
          AND x < 'infinity'::double precision);
$$;

-- ── 0b. Definition verification (F9) — describe / diff / verify ───────────
-- Normalisation makes deparsed definitions comparable across PostgreSQL
-- majors: lower-case, strip the deparser's explicit casts, schema prefix,
-- whitespace and parentheses. A CHECK body, key column list, FK target and
-- actions, trigger timing/events/level/function/WHEN, index definition and
-- function signature/return/volatility/language all survive normalisation;
-- `CHECK (true)` standing in for a real body does not.
CREATE OR REPLACE FUNCTION public.ka_gochara_norm_def(p text)
RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT regexp_replace(
           regexp_replace(
             regexp_replace(lower(p),
               '::(timestamp with time zone|double precision|text\[\]|tstzrange\[\]|text|integer|real|boolean|numeric|uuid|jsonb|tstzrange|regclass)',
               '', 'g'),
             'public\.', '', 'g'),
           '[\s()]', '', 'g');
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_describe_definitions(p_tables text[], p_functions text[])
RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE
  tbl    text;
  rel    regclass;
  tables jsonb := '{}'::jsonb;
  funcs  jsonb := '{}'::jsonb;
  fsig   text;
  foid   regprocedure;
  cols   jsonb; cons jsonb; trgs jsonb; idxs jsonb; fdef jsonb;
BEGIN
  FOREACH tbl IN ARRAY COALESCE(p_tables, '{}') LOOP
    rel := to_regclass('public.' || tbl);
    IF rel IS NULL THEN
      tables := tables || jsonb_build_object(tbl, 'MISSING');
      CONTINUE;
    END IF;
    SELECT COALESCE(jsonb_object_agg(a.attname,
             jsonb_build_array(format_type(a.atttypid, a.atttypmod), a.attnotnull)), '{}'::jsonb)
      INTO cols
    FROM pg_attribute a
    WHERE a.attrelid = rel AND a.attnum > 0 AND NOT a.attisdropped;
    SELECT COALESCE(jsonb_object_agg(c.conname,
             jsonb_build_array(c.contype::text,
                               public.ka_gochara_norm_def(pg_get_constraintdef(c.oid)),
                               c.convalidated)), '{}'::jsonb)
      INTO cons
    FROM pg_constraint c
    WHERE c.conrelid = rel AND c.contype IN ('c','f','p','u','x');
    SELECT COALESCE(jsonb_object_agg(t.tgname,
             jsonb_build_array(public.ka_gochara_norm_def(pg_get_triggerdef(t.oid)),
                               t.tgenabled::text)), '{}'::jsonb)
      INTO trgs
    FROM pg_trigger t
    WHERE t.tgrelid = rel AND NOT t.tgisinternal;
    SELECT COALESCE(jsonb_object_agg(ic.relname,
             public.ka_gochara_norm_def(pg_get_indexdef(i.indexrelid))), '{}'::jsonb)
      INTO idxs
    FROM pg_index i JOIN pg_class ic ON ic.oid = i.indexrelid
    WHERE i.indrelid = rel;
    tables := tables || jsonb_build_object(tbl, jsonb_build_object(
      'columns', cols, 'constraints', cons, 'triggers', trgs, 'indexes', idxs));
  END LOOP;

  FOREACH fsig IN ARRAY COALESCE(p_functions, '{}') LOOP
    foid := to_regprocedure('public.' || fsig);
    IF foid IS NULL THEN
      funcs := funcs || jsonb_build_object(fsig, 'MISSING');
      CONTINUE;
    END IF;
    SELECT jsonb_build_array(format_type(p.prorettype, NULL), p.provolatile::text,
                             l.lanname::text, p.prosecdef, p.prokind::text)
      INTO fdef
    FROM pg_proc p JOIN pg_language l ON l.oid = p.prolang
    WHERE p.oid = foid;
    funcs := funcs || jsonb_build_object(fsig, fdef);
  END LOOP;

  RETURN jsonb_build_object('tables', tables, 'functions', funcs);
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_jsonb_diff(p_path text, p_expected jsonb, p_actual jsonb)
RETURNS text[] LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
  problems text[] := '{}';
  k text;
BEGIN
  IF jsonb_typeof(p_expected) = 'object' AND jsonb_typeof(p_actual) = 'object' THEN
    FOR k IN
      SELECT DISTINCT key FROM (
        SELECT jsonb_object_keys(p_expected) AS key
        UNION ALL
        SELECT jsonb_object_keys(p_actual)
      ) u ORDER BY key
    LOOP
      IF NOT (p_expected ? k) THEN
        problems := problems || (p_path || '.' || k || ': UNEXPECTED (not in the contracted definition): ' || (p_actual -> k)::text);
      ELSIF NOT (p_actual ? k) THEN
        problems := problems || (p_path || '.' || k || ': MISSING; expected ' || (p_expected -> k)::text);
      ELSE
        problems := problems || public.ka_gochara_jsonb_diff(p_path || '.' || k, p_expected -> k, p_actual -> k);
      END IF;
    END LOOP;
  ELSIF p_expected IS DISTINCT FROM p_actual THEN
    problems := problems || (p_path || ': expected ' || p_expected::text || ' actual ' || COALESCE(p_actual::text, 'NULL'));
  END IF;
  RETURN problems;
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_verify_definitions(p_tag text, p_expected jsonb)
RETURNS void LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  tbls     text[];
  fns      text[];
  actual   jsonb;
  problems text[];
BEGIN
  SELECT COALESCE(array_agg(k ORDER BY k), '{}') INTO tbls
  FROM jsonb_object_keys(COALESCE(p_expected -> 'tables', '{}'::jsonb)) k;
  SELECT COALESCE(array_agg(k ORDER BY k), '{}') INTO fns
  FROM jsonb_object_keys(COALESCE(p_expected -> 'functions', '{}'::jsonb)) k;
  actual := public.ka_gochara_describe_definitions(tbls, fns);
  problems := public.ka_gochara_jsonb_diff(p_tag, p_expected, actual);
  IF COALESCE(cardinality(problems), 0) > 0 THEN
    RAISE EXCEPTION 'migration % post-DDL verification failed (amendment 8 / F9 definition drift):%  %',
      p_tag, E'\n', array_to_string(problems, E'\n  ');
  END IF;
  RAISE NOTICE 'migration %: definitions verified (% tables, % functions)',
    p_tag, cardinality(tbls), cardinality(fns);
END;
$$;

-- ── 1. Convention (§6.1 substrate dimensions + ordinal-domain pinning) ─────

CREATE TABLE IF NOT EXISTS public.ka_gochara_sky_convention (
  convention_id        TEXT PRIMARY KEY,         -- "sha256:<hex>" over the canonical
                                                 --   substrate vector (§6.1)
  ephemeris_generation TEXT NOT NULL,
  ayanamsha            TEXT NOT NULL,
  node_convention      TEXT NOT NULL,
  grid                 TEXT NOT NULL,
  method_version       TEXT NOT NULL,            -- §7.2 inv 4: tolerance/method change ⇒
                                                 --   new convention_id
  domain_start         TIMESTAMPTZ NOT NULL,     -- ordinal-domain pinning (§6.1)
  domain_end           TIMESTAMPTZ NOT NULL,
  created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgsc_domain_ordered_ck CHECK (domain_start < domain_end)
);

COMMENT ON TABLE public.ka_gochara_sky_convention IS
  'Sky-event substrate convention (GOCHARA_DESIGN_SPECS_v1_4 §6.1): one substrate per '
  '(ephemeris/convention generation, ayanāṃśa, node convention, grid, method version) '
  'plus the ordinal domain (domain_start/domain_end) that pins occurrence ordinals to '
  'the FULL-domain ordered crossing set. A backward partition is a new convention_id. '
  'Insert-only (trigger); TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_sky_convention_immutable ON public.ka_gochara_sky_convention;
CREATE TRIGGER ka_gochara_sky_convention_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_sky_convention
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§6.1/§7.2 inv 4');
DROP TRIGGER IF EXISTS ka_gochara_sky_convention_no_truncate ON public.ka_gochara_sky_convention;
CREATE TRIGGER ka_gochara_sky_convention_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_sky_convention
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 2. Physical object (§6.1 canonical physical-object identity) ───────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_physical_object (
  physical_object_id  UUID PRIMARY KEY,          -- hash(body, relation_kind,
                                                 --   canonical_target, convention_id);
                                                 --   writer-computed (§6.1)
  body                TEXT NOT NULL,             -- the transiting body whose crossing
                                                 --   the object describes
  relation_kind       TEXT NOT NULL,             -- transit relation (contacts) or
                                                 --   boundary kind (sky events)
  canonical_target    TEXT NOT NULL,             -- canonicalised BEFORE any role/label:
                                                 --   'point:<λ full precision>' /
                                                 --   'span:<sign>' / 'star:<index>' (§6.1)
  convention_id       TEXT NOT NULL REFERENCES public.ka_gochara_sky_convention(convention_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgpo_body_domain_ck CHECK (body IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgpo_relation_kind_ck CHECK (relation_kind IN
    ('residence','aspect','conjunction',
     'sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant')),
  CONSTRAINT kgpo_target_form_ck CHECK (
    canonical_target ~ '^point:([0-9]|[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9])(\.[0-9]+)?$'
    OR canonical_target ~ '^span:[a-z0-9_]+$'
    OR canonical_target ~ '^star:([1-9]|1[0-9]|2[0-7])$'),
  CONSTRAINT ka_gochara_physical_object_natural_uq
    UNIQUE (body, relation_kind, canonical_target, convention_id),
  -- FK target for the composite consistency FKs of ka_gochara_sky_event and
  -- ka_gochara_contact (F7): an event/contact can never disagree with its
  -- physical object on body, relation kind or convention.
  CONSTRAINT kgpo_identity_uq
    UNIQUE (physical_object_id, body, relation_kind, convention_id)
);

COMMENT ON TABLE public.ka_gochara_physical_object IS
  'Canonical physical object (GOCHARA_DESIGN_SPECS_v1_4 §6.1): label-independent physical '
  'identity (v3.0 #27); one object per (body, relation_kind, canonical_target, '
  'convention_id). A retrograde re-crossing of one target is a second CONTACT of this one '
  'object, never a second object (O-RX-1). Canonical identity bytes: '
  'body|relation_kind|canonical_target|convention_id|ordinal. Hash-collision handling: the '
  'build fails loudly, no silent dedup (§6.1). Insert-only (trigger); TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_physical_object_immutable ON public.ka_gochara_physical_object;
CREATE TRIGGER ka_gochara_physical_object_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_physical_object
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§6.1 publication immutability');
DROP TRIGGER IF EXISTS ka_gochara_physical_object_no_truncate ON public.ka_gochara_physical_object;
CREATE TRIGGER ka_gochara_physical_object_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_physical_object
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 3. Sky event — BOUNDARY EVENTS ONLY (§6.1 + §7.1) ─────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_sky_event (
  event_id            UUID PRIMARY KEY,          -- hash(physical_object_id,
                                                 --   occurrence_ordinal) — the frozen
                                                 --   recipe, no extra component (F4)
  physical_object_id  UUID NOT NULL,
  convention_id       TEXT NOT NULL,
  body                TEXT NOT NULL,             -- MUST equal the object's body (FK)
  event_kind          TEXT NOT NULL,             -- MUST equal the object's relation_kind (FK)
  occurrence_ordinal  INTEGER NOT NULL,          -- 1-based index inside the ordered
                                                 --   crossing set of the same physical
                                                 --   tuple, over the FULL convention domain
  t_exact             TIMESTAMPTZ,               -- NULL iff truncated (coverage.truncated)
  longitude           DOUBLE PRECISION,
  solver_method       TEXT NOT NULL,
  delta_lambda        REAL,
  delta_t             REAL,
  precision_regime    TEXT,
  coverage            JSONB NOT NULL,            -- MUST carry boolean 'truncated'
  supersedes_event_id UUID REFERENCES public.ka_gochara_sky_event(event_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT ka_gochara_sky_event_object_fk
    FOREIGN KEY (physical_object_id, body, event_kind, convention_id)
    REFERENCES public.ka_gochara_physical_object (physical_object_id, body, relation_kind, convention_id),
  CONSTRAINT kgse_event_kind_ck CHECK (event_kind IN
    ('sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant')),
  CONSTRAINT kgse_body_domain_ck CHECK (body IN
    ('sun','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
    -- O-SS-4: the global substrate holds NO materialised Moon rows; Moon
    -- boundary events are generated on demand (per-chart, with a
    -- moon_on_demand coverage record), never persisted here.
  CONSTRAINT kgse_ordinal_ck CHECK (occurrence_ordinal >= 1),
  CONSTRAINT ka_gochara_sky_event_ordinal_uq
    UNIQUE (physical_object_id, occurrence_ordinal),
  CONSTRAINT kgse_solver_method_ck CHECK (solver_method IN
    ('arc_index_bracket','swiss_refined','clipped_truncated')),
  CONSTRAINT kgse_coverage_shape_ck
    CHECK (jsonb_typeof(coverage) = 'object'
           AND coverage ? 'truncated'
           AND jsonb_typeof(coverage -> 'truncated') = 'boolean'),
  CONSTRAINT kgse_t_exact_iff_truncated_ck
    CHECK ((t_exact IS NULL) = (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgse_truncated_method_ck
    CHECK ((coverage ->> 'truncated')::boolean = (solver_method = 'clipped_truncated')),
    -- F4: 'clipped_truncated' is exactly the placeholder of a truncated row
  CONSTRAINT kgse_exact_precision_ck
    CHECK (t_exact IS NULL
           OR (longitude IS NOT NULL AND delta_lambda IS NOT NULL
               AND delta_t IS NOT NULL AND precision_regime IS NOT NULL)),
    -- §7.2 inv 1: every REPORTED t_exact carries its uncertainties and regime
  CONSTRAINT kgse_longitude_range_ck
    CHECK (longitude IS NULL OR (longitude >= 0 AND longitude < 360)),
  CONSTRAINT kgse_uncertainty_finite_ck
    CHECK (public.ka_gochara_finite_nonneg_ok(delta_lambda) IS TRUE
           AND public.ka_gochara_finite_nonneg_ok(delta_t) IS TRUE),
    -- F11: uncertainties are finite and non-negative
  CONSTRAINT kgse_station_refined_ck
    CHECK (event_kind <> 'station' OR solver_method = 'swiss_refined'), -- O-SM-3
  CONSTRAINT kgse_no_self_supersede_ck
    CHECK (supersedes_event_id IS NULL OR supersedes_event_id <> event_id),
  CONSTRAINT kgse_supersedes_uq UNIQUE (supersedes_event_id)
    -- a chain, never a tree: an event is superseded at most once
);

COMMENT ON TABLE public.ka_gochara_sky_event IS
  'Boundary-event substrate (GOCHARA_DESIGN_SPECS_v1_4 §6.1, §7.1): the five boundary '
  'kinds ONLY. Transit contacts live in ka_gochara_contact_identity + ka_gochara_contact. '
  'Identity: event_id = hash(physical_object_id, occurrence_ordinal). Correction identity '
  '(F4): a corrected reading is a NEW event of the same (body, kind) under a corrected '
  'target or a new convention, linked by supersedes_event_id (chain, never a tree; never '
  'self; never mutable); a row is retired iff another row supersedes it. Publication '
  'immutability (trigger): DELETE forbidden; UPDATE may only fill NULL fields, flipping '
  'truncated→exact with them; TRUNCATE refused.';

-- Supersede-edge validation (F4): the predecessor must be a DIFFERENT event
-- of the SAME (body, event_kind) — its target and/or convention may differ —
-- and must not already be superseded.
CREATE OR REPLACE FUNCTION public.ka_gochara_sky_event_supersede_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  pred_body text; pred_kind text;
BEGIN
  IF NEW.supersedes_event_id IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT p.body, p.event_kind INTO pred_body, pred_kind
  FROM public.ka_gochara_sky_event p
  WHERE p.event_id = NEW.supersedes_event_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ka_gochara_sky_event supersede edge invalid (§6.1): predecessor % does not exist',
      NEW.supersedes_event_id;
  END IF;
  IF pred_body <> NEW.body OR pred_kind <> NEW.event_kind THEN
    RAISE EXCEPTION 'ka_gochara_sky_event supersede edge invalid (§6.1 correction): predecessor % is (%, %) but the correction is (%, %) — a correction re-solves the SAME body and kind under a corrected target or a new convention (§7.2 inv 4)',
      NEW.supersedes_event_id, pred_body, pred_kind, NEW.body, NEW.event_kind;
  END IF;
  IF EXISTS (SELECT 1 FROM public.ka_gochara_sky_event s
             WHERE s.supersedes_event_id = NEW.supersedes_event_id) THEN
    RAISE EXCEPTION 'ka_gochara_sky_event % is already superseded (§6.1): supersession history is a chain, never a tree',
      NEW.supersedes_event_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_sky_event_supersede_check ON public.ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_supersede_check
  BEFORE INSERT ON public.ka_gochara_sky_event
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sky_event_supersede_guard();

-- Publication immutability + enrichment-only UPDATE (§6.1; F4): identity
-- fields never change; any published non-NULL value never changes in place;
-- the only permitted writes are NULL → value fills and the truncated → exact
-- flip (t_exact filled, truncated flag flips, solver_method leaves the
-- 'clipped_truncated' placeholder — and ONLY that placeholder).
CREATE OR REPLACE FUNCTION public.ka_gochara_sky_event_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE flip boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    RAISE EXCEPTION 'ka_gochara_sky_event is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §6.1): DELETE forbidden; a correction retires an event via a superseding row, never by deletion';
  END IF;
  flip := OLD.t_exact IS NULL AND NEW.t_exact IS NOT NULL
      AND (OLD.coverage ->> 'truncated')::boolean
      AND NOT (NEW.coverage ->> 'truncated')::boolean
      AND OLD.solver_method = 'clipped_truncated'
      AND NEW.solver_method <> 'clipped_truncated'
      AND (OLD.coverage - 'truncated') = (NEW.coverage - 'truncated');
  IF NEW.event_id            <> OLD.event_id
     OR NEW.physical_object_id <> OLD.physical_object_id
     OR NEW.occurrence_ordinal <> OLD.occurrence_ordinal
     OR NEW.convention_id      <> OLD.convention_id
     OR NEW.body               <> OLD.body
     OR NEW.event_kind         <> OLD.event_kind THEN
    RAISE EXCEPTION 'ka_gochara_sky_event identity fields are immutable (§6.1): a change to id/ordinal/target/convention is a correction — mint a new id with a supersedes edge, never UPDATE';
  END IF;
  IF (OLD.t_exact IS NOT NULL AND NEW.t_exact IS DISTINCT FROM OLD.t_exact)
     OR (OLD.longitude IS NOT NULL AND NEW.longitude IS DISTINCT FROM OLD.longitude)
     OR (OLD.delta_lambda IS NOT NULL AND NEW.delta_lambda IS DISTINCT FROM OLD.delta_lambda)
     OR (OLD.delta_t IS NOT NULL AND NEW.delta_t IS DISTINCT FROM OLD.delta_t)
     OR (OLD.precision_regime IS NOT NULL AND NEW.precision_regime IS DISTINCT FROM OLD.precision_regime)
     OR (OLD.supersedes_event_id IS NOT NULL AND NEW.supersedes_event_id IS DISTINCT FROM OLD.supersedes_event_id)
     OR (OLD.supersedes_event_id IS NULL AND NEW.supersedes_event_id IS NOT NULL) THEN
    RAISE EXCEPTION 'ka_gochara_sky_event published non-NULL values are immutable (§6.1 enrichment-vs-correction): changing one is a correction (new id + supersedes edge), not an UPDATE';
  END IF;
  IF NEW.solver_method <> OLD.solver_method AND NOT flip THEN
    RAISE EXCEPTION 'ka_gochara_sky_event.solver_method may only leave the clipped_truncated placeholder as part of the truncated→exact enrichment flip (§6.1, §7.2 inv 4): any other method change is a new convention';
  END IF;
  IF NEW.coverage IS DISTINCT FROM OLD.coverage AND NOT flip THEN
    RAISE EXCEPTION 'ka_gochara_sky_event.coverage is immutable except the truncated→exact enrichment flip (§6.1)';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_sky_event_mutation_guard ON public.ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_mutation_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_sky_event
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_sky_event_guard();
DROP TRIGGER IF EXISTS ka_gochara_sky_event_no_truncate ON public.ka_gochara_sky_event;
CREATE TRIGGER ka_gochara_sky_event_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_sky_event
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 4. Contact IDENTITY — stable, global, never renumbered (§6.1; F1/F4) ───

CREATE TABLE IF NOT EXISTS public.ka_gochara_contact_identity (
  contact_id            UUID PRIMARY KEY,        -- hash(physical_object_id,
                                                 --   occurrence_ordinal) — frozen recipe
  physical_object_id    UUID NOT NULL REFERENCES public.ka_gochara_physical_object(physical_object_id),
  occurrence_ordinal    INTEGER NOT NULL,
  supersedes_contact_id UUID REFERENCES public.ka_gochara_contact_identity(contact_id),
  created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgci_ordinal_ck CHECK (occurrence_ordinal >= 1),
  CONSTRAINT ka_gochara_contact_identity_ordinal_uq
    UNIQUE (physical_object_id, occurrence_ordinal),
  CONSTRAINT kgci_no_self_supersede_ck
    CHECK (supersedes_contact_id IS NULL OR supersedes_contact_id <> contact_id),
  CONSTRAINT kgci_supersedes_uq UNIQUE (supersedes_contact_id),
    -- a chain, never a tree
  -- FK target for the ledger's tuple-consistency FK: a ledger row can never
  -- disagree with its identity on (physical_object_id, occurrence_ordinal).
  CONSTRAINT kgci_tuple_uq UNIQUE (contact_id, physical_object_id, occurrence_ordinal)
);

COMMENT ON TABLE public.ka_gochara_contact_identity IS
  'Contact identity (GOCHARA_DESIGN_SPECS_v1_4 §6.1 NK-2; F1/F4): contact_id = '
  'hash(physical_object_id, occurrence_ordinal), one row per identity, GLOBAL (no '
  'chart/generation) — the stable physical identity that generation-scoped ledger rows '
  '(ka_gochara_contact) reference and share. Never renumbered, never reused, never '
  'deleted (insert-only trigger; TRUNCATE refused). Correction: a new identity of the same '
  '(body, relation_kind) under a corrected target or a new convention, linked by '
  'supersedes_contact_id (chain, never a tree; never self); retired iff superseded.';

CREATE OR REPLACE FUNCTION public.ka_gochara_contact_identity_supersede_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  pred_body text; pred_rel text; new_body text; new_rel text;
BEGIN
  IF NEW.supersedes_contact_id IS NULL THEN
    RETURN NEW;
  END IF;
  SELECT o.body, o.relation_kind INTO pred_body, pred_rel
  FROM public.ka_gochara_contact_identity i
  JOIN public.ka_gochara_physical_object o ON o.physical_object_id = i.physical_object_id
  WHERE i.contact_id = NEW.supersedes_contact_id;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'ka_gochara_contact_identity supersede edge invalid (§6.1): predecessor % does not exist',
      NEW.supersedes_contact_id;
  END IF;
  SELECT o.body, o.relation_kind INTO new_body, new_rel
  FROM public.ka_gochara_physical_object o
  WHERE o.physical_object_id = NEW.physical_object_id;
  IF pred_body IS DISTINCT FROM new_body OR pred_rel IS DISTINCT FROM new_rel THEN
    RAISE EXCEPTION 'ka_gochara_contact_identity supersede edge invalid (§6.1 correction): predecessor % is (%, %) but the correction is (%, %) — a correction re-solves the SAME body and relation under a corrected target or a new convention (§7.2 inv 4)',
      NEW.supersedes_contact_id, pred_body, pred_rel, new_body, new_rel;
  END IF;
  IF EXISTS (SELECT 1 FROM public.ka_gochara_contact_identity s
             WHERE s.supersedes_contact_id = NEW.supersedes_contact_id) THEN
    RAISE EXCEPTION 'ka_gochara_contact_identity % is already superseded (§6.1): supersession history is a chain, never a tree',
      NEW.supersedes_contact_id;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_contact_identity_supersede_check ON public.ka_gochara_contact_identity;
CREATE TRIGGER ka_gochara_contact_identity_supersede_check
  BEFORE INSERT ON public.ka_gochara_contact_identity
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_contact_identity_supersede_guard();
DROP TRIGGER IF EXISTS ka_gochara_contact_identity_immutable ON public.ka_gochara_contact_identity;
CREATE TRIGGER ka_gochara_contact_identity_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_contact_identity
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§6.1 publication immutability — an id is never renumbered or reused');
DROP TRIGGER IF EXISTS ka_gochara_contact_identity_no_truncate ON public.ka_gochara_contact_identity;
CREATE TRIGGER ka_gochara_contact_identity_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_contact_identity
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 5. Permanent publication seal + the ONE sealed-generation predicate (F2)

CREATE TABLE IF NOT EXISTS public.ka_gochara_generation_seal (
  chart_id    UUID NOT NULL,
  generation  TEXT NOT NULL,
  manifest_id UUID NOT NULL REFERENCES public.kala_gochara_publication(manifest_id),
  sealed_at   TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation)
);

COMMENT ON TABLE public.ka_gochara_generation_seal IS
  'Permanent publication history (F2): one row per (chart_id, generation) that was EVER '
  'published. Written automatically by ka_gochara_publication_seal_record when a '
  'kala_gochara_publication row becomes status=published, or directly by the release '
  'authority (the BEFORE INSERT guard verifies the manifest is published). Never '
  'updated, deleted or truncated: protection of published contact ids, records and '
  'windows follows this row, not the manifest''s later serving status '
  '(superseded/rolled_back stay sealed). Also the RESTRICT anchor that keeps a published '
  'manifest row from being deleted.';

CREATE OR REPLACE FUNCTION public.ka_gochara_generation_seal_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  -- serialize with any in-flight candidate rebuild of the same generation
  PERFORM pg_advisory_xact_lock(hashtext('ka_gochara_generation:' || NEW.chart_id::text),
                                hashtext(NEW.generation));
  IF NOT EXISTS (
    SELECT 1 FROM public.kala_gochara_publication p
    WHERE p.manifest_id = NEW.manifest_id
      AND p.chart_id = NEW.chart_id AND p.generation = NEW.generation
      AND p.status = 'published'
  ) THEN
    RAISE EXCEPTION 'ka_gochara_generation_seal refused: manifest % is not a published manifest of (chart %, generation %) — a seal records a real publication, never a claim (CLAUDE.md §N.8)',
      NEW.manifest_id, NEW.chart_id, NEW.generation;
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_generation_seal_check ON public.ka_gochara_generation_seal;
CREATE TRIGGER ka_gochara_generation_seal_check
  BEFORE INSERT ON public.ka_gochara_generation_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_generation_seal_guard();
DROP TRIGGER IF EXISTS ka_gochara_generation_seal_immutable ON public.ka_gochara_generation_seal;
CREATE TRIGGER ka_gochara_generation_seal_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_generation_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§6.1/§10.1 — publication history is permanent');
DROP TRIGGER IF EXISTS ka_gochara_generation_seal_no_truncate ON public.ka_gochara_generation_seal;
CREATE TRIGGER ka_gochara_generation_seal_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_generation_seal
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- Automatic seal recording on publication (the D-FLIP route of 1081 is an
-- UPDATE of kala_gochara_publication.status). Additive AFTER trigger on the
-- same-family manifest table; it writes nothing for candidate rows.
CREATE OR REPLACE FUNCTION public.ka_gochara_record_generation_seal()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF NEW.status = 'published' THEN
    INSERT INTO public.ka_gochara_generation_seal (chart_id, generation, manifest_id)
    VALUES (NEW.chart_id, NEW.generation, NEW.manifest_id)
    ON CONFLICT (chart_id, generation) DO NOTHING;
  END IF;
  RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_publication_seal_record ON public.kala_gochara_publication;
CREATE TRIGGER ka_gochara_publication_seal_record
  AFTER INSERT OR UPDATE OF status ON public.kala_gochara_publication
  FOR EACH ROW WHEN (NEW.status = 'published')
  EXECUTE FUNCTION public.ka_gochara_record_generation_seal();

-- The one predicate every guard reads. VOLATILE: it takes the serialization
-- lock shared with the seal writer.
CREATE OR REPLACE FUNCTION public.ka_gochara_generation_is_sealed(p_chart_id uuid, p_generation text)
RETURNS boolean LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  PERFORM pg_advisory_xact_lock(hashtext('ka_gochara_generation:' || p_chart_id::text),
                                hashtext(p_generation));
  RETURN EXISTS (
           SELECT 1 FROM public.ka_gochara_generation_seal s
           WHERE s.chart_id = p_chart_id AND s.generation = p_generation)
      OR EXISTS (
           SELECT 1 FROM public.kala_gochara_publication p
           WHERE p.chart_id = p_chart_id AND p.generation = p_generation
             AND (p.status <> 'candidate' OR p.published_at IS NOT NULL));
END;
$$;

COMMENT ON FUNCTION public.ka_gochara_generation_is_sealed(uuid, text) IS
  'TRUE iff (chart_id, generation) was ever published: a ka_gochara_generation_seal row '
  'exists, or the kala_gochara_publication manifest carries a non-candidate status / a '
  'published_at (generations published before 1153). Takes the per-generation advisory '
  'transaction lock shared with the seal writer, so a rebuild and a publication serialize.';

-- ── 6. Legacy-convention bridge (F7) ──────────────────────────────────────

CREATE TABLE IF NOT EXISTS public.ka_gochara_convention_bridge (
  kala_convention_id TEXT PRIMARY KEY REFERENCES public.kala_gochara_convention(convention_id),
  sky_convention_id  TEXT NOT NULL REFERENCES public.ka_gochara_sky_convention(convention_id),
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.ka_gochara_convention_bridge IS
  'Explicit bridge (F7) from the LEGACY 1081 convention vector carried by '
  'kala_gochara_coverage.convention_id to the §6.1 sky convention carried by contacts. A '
  'coverage partition is applicable to a transit record only when its convention is '
  'bridged to the contact''s sky convention (enforced by 1155''s coverage-applicability '
  'guard). Insert-only; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_convention_bridge_immutable ON public.ka_gochara_convention_bridge;
CREATE TRIGGER ka_gochara_convention_bridge_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_convention_bridge
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('§7.2 inv 4 — a convention change is a new convention');
DROP TRIGGER IF EXISTS ka_gochara_convention_bridge_no_truncate ON public.ka_gochara_convention_bridge;
CREATE TRIGGER ka_gochara_convention_bridge_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_convention_bridge
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 7. Contact LEDGER — per-(chart × generation) ownership (§6.1/§10; F1) ─

CREATE TABLE IF NOT EXISTS public.ka_gochara_contact (
  chart_id            UUID NOT NULL REFERENCES public.charts(id),
  generation          TEXT NOT NULL,             -- '4.1'/'5.0'…; lifecycle scope (§N.3)
  contact_id          UUID NOT NULL REFERENCES public.ka_gochara_contact_identity(contact_id),
  physical_object_id  UUID NOT NULL,
  occurrence_ordinal  INTEGER NOT NULL,
  convention_id       TEXT NOT NULL,
  body                TEXT NOT NULL,             -- transiting body = the record's agent;
                                                 --   Moon allowed: Moon-on-demand contacts
                                                 --   persist per-chart inside admitted
                                                 --   windows with moon_on_demand coverage
  relation_kind       TEXT NOT NULL,             -- the transit relations of §1.1
  t_in                TIMESTAMPTZ NOT NULL,      -- in-orb interval start as observed inside
                                                 --   the solved partition (clipped at the
                                                 --   partition start if already in orb)
  t_out               TIMESTAMPTZ,               -- NULL only while truncated at the
                                                 --   partition end (N3)
  t_exact             TIMESTAMPTZ,               -- NULL iff truncated (coverage.truncated)
  solver_method       TEXT NOT NULL,
  delta_lambda        REAL,
  delta_t             REAL,
  precision_regime    TEXT,
  coverage            JSONB NOT NULL,            -- MUST carry boolean 'truncated'
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, contact_id),
  CONSTRAINT ka_gochara_contact_identity_fk
    FOREIGN KEY (contact_id, physical_object_id, occurrence_ordinal)
    REFERENCES public.ka_gochara_contact_identity (contact_id, physical_object_id, occurrence_ordinal),
  CONSTRAINT ka_gochara_contact_object_fk
    FOREIGN KEY (physical_object_id, body, relation_kind, convention_id)
    REFERENCES public.ka_gochara_physical_object (physical_object_id, body, relation_kind, convention_id),
  CONSTRAINT kgc_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
    -- D-SCOPE disposition: the frozen contract serves the canonical chart
    -- only; widening requires a migration.
  CONSTRAINT kgc_body_domain_ck CHECK (body IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  CONSTRAINT kgc_relation_kind_ck CHECK (relation_kind IN
    ('residence','aspect','conjunction')),
  CONSTRAINT kgc_ordinal_ck CHECK (occurrence_ordinal >= 1),
  -- FK target for 1155's transit-record reference (F1/F7): a record binds to
  -- the OWNED ledger row and its agent/relation/object must agree with it.
  CONSTRAINT kgc_reference_uq
    UNIQUE (chart_id, generation, contact_id, body, relation_kind, physical_object_id),
  CONSTRAINT kgc_solver_method_ck CHECK (solver_method IN
    ('arc_index_bracket','swiss_refined','clipped_truncated')),
  CONSTRAINT kgc_coverage_shape_ck
    CHECK (jsonb_typeof(coverage) = 'object'
           AND coverage ? 'truncated'
           AND jsonb_typeof(coverage -> 'truncated') = 'boolean'),
  CONSTRAINT kgc_t_exact_iff_truncated_ck
    CHECK ((t_exact IS NULL) = (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgc_truncated_method_ck
    CHECK ((coverage ->> 'truncated')::boolean = (solver_method = 'clipped_truncated')),
  CONSTRAINT kgc_t_out_unless_truncated_ck
    CHECK (t_out IS NOT NULL OR (coverage ->> 'truncated')::boolean),
  CONSTRAINT kgc_exact_precision_ck
    CHECK (t_exact IS NULL
           OR (delta_lambda IS NOT NULL AND delta_t IS NOT NULL
               AND precision_regime IS NOT NULL)),
  CONSTRAINT kgc_uncertainty_finite_ck
    CHECK (public.ka_gochara_finite_nonneg_ok(delta_lambda) IS TRUE
           AND public.ka_gochara_finite_nonneg_ok(delta_t) IS TRUE),
  CONSTRAINT kgc_time_order_ck
    CHECK (t_exact IS NULL
           OR (t_in <= t_exact AND (t_out IS NULL OR t_exact <= t_out))),
  CONSTRAINT kgc_span_order_ck
    CHECK (t_out IS NULL OR t_in < t_out)
);

COMMENT ON TABLE public.ka_gochara_contact IS
  'Transit-contact LEDGER (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§10; F1): the per-(chart_id × '
  'generation) OWNERSHIP row of a stable contact identity (ka_gochara_contact_identity) '
  'carrying the solved values — physical tuple + occurrence ordinal + relation kind, '
  'residence intervals and truncated spans (t_in/t_out/t_exact ruled nullable, N3). PK '
  '(chart_id, generation, contact_id): one physical contact coexists in a retained '
  'published generation and a candidate rebuild. Writer: per-(chart_id × generation) '
  'delete-then-insert of CANDIDATE generations (CLAUDE.md §N.3); a sealed generation '
  'refuses DELETE (ka_gochara_generation_is_sealed — permanent, serialized with '
  'publication); UPDATE is enrichment-only always; TRUNCATE refused. Legacy '
  'kala_gochara_contacts rows (TEXT contact_id) are NOT migrated — correspondence is by '
  '(chart_id, generation) scope only; legacy ids are never reused.';

CREATE OR REPLACE FUNCTION public.ka_gochara_contact_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE flip boolean;
BEGIN
  IF TG_OP = 'DELETE' THEN
    IF public.ka_gochara_generation_is_sealed(OLD.chart_id, OLD.generation) THEN
      RAISE EXCEPTION 'ka_gochara_contact is publication-immutable (GOCHARA_DESIGN_SPECS_v1_4 §6.1/§10.1): (chart_id %, generation %) is SEALED (was published) — DELETE refused; a correction mints a new identity with a supersedes edge and a rebuild is a new generation',
        OLD.chart_id, OLD.generation;
    END IF;
    RETURN OLD;
  END IF;
  flip := OLD.t_exact IS NULL AND NEW.t_exact IS NOT NULL
      AND (OLD.coverage ->> 'truncated')::boolean
      AND NOT (NEW.coverage ->> 'truncated')::boolean
      AND OLD.solver_method = 'clipped_truncated'
      AND NEW.solver_method <> 'clipped_truncated'
      AND (OLD.coverage - 'truncated') = (NEW.coverage - 'truncated');
  IF NEW.chart_id            <> OLD.chart_id
     OR NEW.generation         <> OLD.generation
     OR NEW.contact_id         <> OLD.contact_id
     OR NEW.physical_object_id <> OLD.physical_object_id
     OR NEW.occurrence_ordinal <> OLD.occurrence_ordinal
     OR NEW.convention_id      <> OLD.convention_id
     OR NEW.body               <> OLD.body
     OR NEW.relation_kind      <> OLD.relation_kind THEN
    RAISE EXCEPTION 'ka_gochara_contact identity fields are immutable (§6.1): a change to chart/generation/id/ordinal/target/relation is a correction — mint a new identity with a supersedes edge, never UPDATE';
  END IF;
  IF NEW.t_in IS DISTINCT FROM OLD.t_in
     OR (OLD.t_out IS NOT NULL AND NEW.t_out IS DISTINCT FROM OLD.t_out)
     OR (OLD.t_exact IS NOT NULL AND NEW.t_exact IS DISTINCT FROM OLD.t_exact)
     OR (OLD.delta_lambda IS NOT NULL AND NEW.delta_lambda IS DISTINCT FROM OLD.delta_lambda)
     OR (OLD.delta_t IS NOT NULL AND NEW.delta_t IS DISTINCT FROM OLD.delta_t)
     OR (OLD.precision_regime IS NOT NULL AND NEW.precision_regime IS DISTINCT FROM OLD.precision_regime) THEN
    RAISE EXCEPTION 'ka_gochara_contact published non-NULL values are immutable (§6.1 enrichment-vs-correction): changing one is a correction (new identity + supersedes edge, under a corrected target or a new convention), not an UPDATE';
  END IF;
  IF NEW.solver_method <> OLD.solver_method AND NOT flip THEN
    RAISE EXCEPTION 'ka_gochara_contact.solver_method may only leave the clipped_truncated placeholder as part of the truncated→exact enrichment flip (§6.1, §7.2 inv 4): any other method change is a new convention';
  END IF;
  IF NEW.coverage IS DISTINCT FROM OLD.coverage AND NOT flip THEN
    RAISE EXCEPTION 'ka_gochara_contact.coverage is immutable except the truncated→exact enrichment flip (§6.1)';
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS ka_gochara_contact_lifecycle_guard ON public.ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_lifecycle_guard
  BEFORE UPDATE OR DELETE ON public.ka_gochara_contact
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_contact_guard();
DROP TRIGGER IF EXISTS ka_gochara_contact_no_truncate ON public.ka_gochara_contact;
CREATE TRIGGER ka_gochara_contact_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_contact
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 8. Serving/read shapes ────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_kgse_convention_time ON public.ka_gochara_sky_event
  (convention_id, body, event_kind, t_exact);
CREATE INDEX IF NOT EXISTS idx_kgc_chart_gen ON public.ka_gochara_contact
  (chart_id, generation, relation_kind, t_exact);
CREATE INDEX IF NOT EXISTS idx_kgc_object ON public.ka_gochara_contact
  (physical_object_id, occurrence_ordinal);
CREATE INDEX IF NOT EXISTS idx_kgc_identity ON public.ka_gochara_contact
  (contact_id);

-- ── 9. Post-DDL definition verification (F9) ───────────────────────────────
-- Helper self-tests first (a validator that returns SQL NULL is not a
-- validator — F5), then the full definition comparison.
DO $$
BEGIN
  IF NOT (public.ka_gochara_finite_nonneg_ok('NaN'::double precision) IS FALSE
          AND public.ka_gochara_finite_nonneg_ok('infinity'::double precision) IS FALSE
          AND public.ka_gochara_finite_nonneg_ok(-0.5) IS FALSE
          AND public.ka_gochara_finite_nonneg_ok(0) IS TRUE
          AND public.ka_gochara_finite_nonneg_ok(NULL) IS TRUE
          AND public.ka_gochara_finite_ok('-infinity'::double precision) IS FALSE
          AND public.ka_gochara_finite_ok(-1) IS TRUE
          AND public.ka_gochara_text_array_ok(ARRAY[NULL]::text[], 1) IS FALSE
          AND public.ka_gochara_text_array_ok(ARRAY[' ']::text[], 1) IS FALSE
          AND public.ka_gochara_text_array_ok('{}'::text[], 1) IS FALSE
          AND public.ka_gochara_text_array_ok('{}'::text[], 0) IS TRUE
          AND public.ka_gochara_text_array_ok(NULL::text[], 0) IS FALSE
          AND public.ka_gochara_text_array_ok(ARRAY['a']::text[], 1) IS TRUE
          AND public.ka_gochara_norm_def('CHECK ((x >= (0)::double precision))') = 'checkx>=0') THEN
    RAISE EXCEPTION 'migration 1153 post-DDL verification failed (amendment 8): helper self-test failed';
  END IF;
END;
$$;

-- The seal-recording trigger lives on 1081's kala_gochara_publication, whose
-- full definition is 1081's to verify; this block verifies exactly the one
-- object 1153 adds there (deparsed definition + enabled state).
DO $$
DECLARE actual text;
BEGIN
  SELECT public.ka_gochara_norm_def(pg_get_triggerdef(t.oid)) || '|' || t.tgenabled::text
    INTO actual
  FROM pg_trigger t
  WHERE t.tgrelid = to_regclass('public.kala_gochara_publication')
    AND t.tgname = 'ka_gochara_publication_seal_record' AND NOT t.tgisinternal;
  IF actual IS DISTINCT FROM public.ka_gochara_norm_def(
       'CREATE TRIGGER ka_gochara_publication_seal_record AFTER INSERT OR UPDATE OF status '
       'ON public.kala_gochara_publication FOR EACH ROW WHEN ((new.status = ''published''::text)) '
       'EXECUTE FUNCTION public.ka_gochara_record_generation_seal()') || '|O' THEN
    RAISE EXCEPTION 'migration 1153 post-DDL verification failed (amendment 8 / F9 definition drift): kala_gochara_publication.ka_gochara_publication_seal_record: actual %', COALESCE(actual, 'MISSING');
  END IF;
END;
$$;

DO $$
BEGIN
  PERFORM public.ka_gochara_verify_definitions('1153', $expected$
{
  "functions": {
    "ka_gochara_contact_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_contact_identity_supersede_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_describe_definitions(text[],text[])": [
      "jsonb",
      "s",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_finite_nonneg_ok(double precision)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_finite_ok(double precision)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_generation_is_sealed(uuid,text)": [
      "boolean",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_generation_seal_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_insert_only()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_jsonb_diff(text,jsonb,jsonb)": [
      "text[]",
      "i",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_norm_def(text)": [
      "text",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_record_generation_seal()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_refuse_truncate()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_sky_event_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_sky_event_supersede_guard()": [
      "trigger",
      "v",
      "plpgsql",
      false,
      "f"
    ],
    "ka_gochara_text_array_ok(text[],integer)": [
      "boolean",
      "i",
      "sql",
      false,
      "f"
    ],
    "ka_gochara_verify_definitions(text,jsonb)": [
      "void",
      "v",
      "plpgsql",
      false,
      "f"
    ]
  },
  "tables": {
    "ka_gochara_contact": {
      "columns": {
        "body": [
          "text",
          true
        ],
        "chart_id": [
          "uuid",
          true
        ],
        "contact_id": [
          "uuid",
          true
        ],
        "convention_id": [
          "text",
          true
        ],
        "coverage": [
          "jsonb",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "delta_lambda": [
          "real",
          false
        ],
        "delta_t": [
          "real",
          false
        ],
        "generation": [
          "text",
          true
        ],
        "occurrence_ordinal": [
          "integer",
          true
        ],
        "physical_object_id": [
          "uuid",
          true
        ],
        "precision_regime": [
          "text",
          false
        ],
        "relation_kind": [
          "text",
          true
        ],
        "solver_method": [
          "text",
          true
        ],
        "t_exact": [
          "timestamp with time zone",
          false
        ],
        "t_in": [
          "timestamp with time zone",
          true
        ],
        "t_out": [
          "timestamp with time zone",
          false
        ]
      },
      "constraints": {
        "ka_gochara_contact_chart_id_fkey": [
          "f",
          "foreignkeychart_idreferenceschartsid",
          true
        ],
        "ka_gochara_contact_contact_id_fkey": [
          "f",
          "foreignkeycontact_idreferenceska_gochara_contact_identitycontact_id",
          true
        ],
        "ka_gochara_contact_identity_fk": [
          "f",
          "foreignkeycontact_id,physical_object_id,occurrence_ordinalreferenceska_gochara_contact_identitycontact_id,physical_object_id,occurrence_ordinal",
          true
        ],
        "ka_gochara_contact_object_fk": [
          "f",
          "foreignkeyphysical_object_id,body,relation_kind,convention_idreferenceska_gochara_physical_objectphysical_object_id,body,relation_kind,convention_id",
          true
        ],
        "ka_gochara_contact_pkey": [
          "p",
          "primarykeychart_id,generation,contact_id",
          true
        ],
        "kgc_body_domain_ck": [
          "c",
          "checkbody=anyarray['sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu']",
          true
        ],
        "kgc_canonical_chart_ck": [
          "c",
          "checkchart_id='482012f1-710e-4a25-994a-93821f5871aa'",
          true
        ],
        "kgc_coverage_shape_ck": [
          "c",
          "checkjsonb_typeofcoverage='object'andcoverage?'truncated'andjsonb_typeofcoverage->'truncated'='boolean'",
          true
        ],
        "kgc_exact_precision_ck": [
          "c",
          "checkt_exactisnullordelta_lambdaisnotnullanddelta_tisnotnullandprecision_regimeisnotnull",
          true
        ],
        "kgc_ordinal_ck": [
          "c",
          "checkoccurrence_ordinal>=1",
          true
        ],
        "kgc_reference_uq": [
          "u",
          "uniquechart_id,generation,contact_id,body,relation_kind,physical_object_id",
          true
        ],
        "kgc_relation_kind_ck": [
          "c",
          "checkrelation_kind=anyarray['residence','aspect','conjunction']",
          true
        ],
        "kgc_solver_method_ck": [
          "c",
          "checksolver_method=anyarray['arc_index_bracket','swiss_refined','clipped_truncated']",
          true
        ],
        "kgc_span_order_ck": [
          "c",
          "checkt_outisnullort_in<t_out",
          true
        ],
        "kgc_t_exact_iff_truncated_ck": [
          "c",
          "checkt_exactisnull=coverage->>'truncated'",
          true
        ],
        "kgc_t_out_unless_truncated_ck": [
          "c",
          "checkt_outisnotnullorcoverage->>'truncated'",
          true
        ],
        "kgc_time_order_ck": [
          "c",
          "checkt_exactisnullort_in<=t_exactandt_outisnullort_exact<=t_out",
          true
        ],
        "kgc_truncated_method_ck": [
          "c",
          "checkcoverage->>'truncated'=solver_method='clipped_truncated'",
          true
        ],
        "kgc_uncertainty_finite_ck": [
          "c",
          "checkka_gochara_finite_nonneg_okdelta_lambdaistrueandka_gochara_finite_nonneg_okdelta_tistrue",
          true
        ]
      },
      "indexes": {
        "idx_kgc_chart_gen": "createindexidx_kgc_chart_genonka_gochara_contactusingbtreechart_id,generation,relation_kind,t_exact",
        "idx_kgc_identity": "createindexidx_kgc_identityonka_gochara_contactusingbtreecontact_id",
        "idx_kgc_object": "createindexidx_kgc_objectonka_gochara_contactusingbtreephysical_object_id,occurrence_ordinal",
        "ka_gochara_contact_pkey": "createuniqueindexka_gochara_contact_pkeyonka_gochara_contactusingbtreechart_id,generation,contact_id",
        "kgc_reference_uq": "createuniqueindexkgc_reference_uqonka_gochara_contactusingbtreechart_id,generation,contact_id,body,relation_kind,physical_object_id"
      },
      "triggers": {
        "ka_gochara_contact_lifecycle_guard": [
          "createtriggerka_gochara_contact_lifecycle_guardbeforedeleteorupdateonka_gochara_contactforeachrowexecutefunctionka_gochara_contact_guard",
          "O"
        ],
        "ka_gochara_contact_no_truncate": [
          "createtriggerka_gochara_contact_no_truncatebeforetruncateonka_gochara_contactforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_contact_identity": {
      "columns": {
        "contact_id": [
          "uuid",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "occurrence_ordinal": [
          "integer",
          true
        ],
        "physical_object_id": [
          "uuid",
          true
        ],
        "supersedes_contact_id": [
          "uuid",
          false
        ]
      },
      "constraints": {
        "ka_gochara_contact_identity_ordinal_uq": [
          "u",
          "uniquephysical_object_id,occurrence_ordinal",
          true
        ],
        "ka_gochara_contact_identity_physical_object_id_fkey": [
          "f",
          "foreignkeyphysical_object_idreferenceska_gochara_physical_objectphysical_object_id",
          true
        ],
        "ka_gochara_contact_identity_pkey": [
          "p",
          "primarykeycontact_id",
          true
        ],
        "ka_gochara_contact_identity_supersedes_contact_id_fkey": [
          "f",
          "foreignkeysupersedes_contact_idreferenceska_gochara_contact_identitycontact_id",
          true
        ],
        "kgci_no_self_supersede_ck": [
          "c",
          "checksupersedes_contact_idisnullorsupersedes_contact_id<>contact_id",
          true
        ],
        "kgci_ordinal_ck": [
          "c",
          "checkoccurrence_ordinal>=1",
          true
        ],
        "kgci_supersedes_uq": [
          "u",
          "uniquesupersedes_contact_id",
          true
        ],
        "kgci_tuple_uq": [
          "u",
          "uniquecontact_id,physical_object_id,occurrence_ordinal",
          true
        ]
      },
      "indexes": {
        "ka_gochara_contact_identity_ordinal_uq": "createuniqueindexka_gochara_contact_identity_ordinal_uqonka_gochara_contact_identityusingbtreephysical_object_id,occurrence_ordinal",
        "ka_gochara_contact_identity_pkey": "createuniqueindexka_gochara_contact_identity_pkeyonka_gochara_contact_identityusingbtreecontact_id",
        "kgci_supersedes_uq": "createuniqueindexkgci_supersedes_uqonka_gochara_contact_identityusingbtreesupersedes_contact_id",
        "kgci_tuple_uq": "createuniqueindexkgci_tuple_uqonka_gochara_contact_identityusingbtreecontact_id,physical_object_id,occurrence_ordinal"
      },
      "triggers": {
        "ka_gochara_contact_identity_immutable": [
          "createtriggerka_gochara_contact_identity_immutablebeforedeleteorupdateonka_gochara_contact_identityforeachrowexecutefunctionka_gochara_insert_only'§6.1publicationimmutability—anidisneverrenumberedorreused'",
          "O"
        ],
        "ka_gochara_contact_identity_no_truncate": [
          "createtriggerka_gochara_contact_identity_no_truncatebeforetruncateonka_gochara_contact_identityforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_contact_identity_supersede_check": [
          "createtriggerka_gochara_contact_identity_supersede_checkbeforeinsertonka_gochara_contact_identityforeachrowexecutefunctionka_gochara_contact_identity_supersede_guard",
          "O"
        ]
      }
    },
    "ka_gochara_convention_bridge": {
      "columns": {
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "kala_convention_id": [
          "text",
          true
        ],
        "sky_convention_id": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_convention_bridge_kala_convention_id_fkey": [
          "f",
          "foreignkeykala_convention_idreferenceskala_gochara_conventionconvention_id",
          true
        ],
        "ka_gochara_convention_bridge_pkey": [
          "p",
          "primarykeykala_convention_id",
          true
        ],
        "ka_gochara_convention_bridge_sky_convention_id_fkey": [
          "f",
          "foreignkeysky_convention_idreferenceska_gochara_sky_conventionconvention_id",
          true
        ]
      },
      "indexes": {
        "ka_gochara_convention_bridge_pkey": "createuniqueindexka_gochara_convention_bridge_pkeyonka_gochara_convention_bridgeusingbtreekala_convention_id"
      },
      "triggers": {
        "ka_gochara_convention_bridge_immutable": [
          "createtriggerka_gochara_convention_bridge_immutablebeforedeleteorupdateonka_gochara_convention_bridgeforeachrowexecutefunctionka_gochara_insert_only'§7.2inv4—aconventionchangeisanewconvention'",
          "O"
        ],
        "ka_gochara_convention_bridge_no_truncate": [
          "createtriggerka_gochara_convention_bridge_no_truncatebeforetruncateonka_gochara_convention_bridgeforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_generation_seal": {
      "columns": {
        "chart_id": [
          "uuid",
          true
        ],
        "generation": [
          "text",
          true
        ],
        "manifest_id": [
          "uuid",
          true
        ],
        "sealed_at": [
          "timestamp with time zone",
          true
        ]
      },
      "constraints": {
        "ka_gochara_generation_seal_manifest_id_fkey": [
          "f",
          "foreignkeymanifest_idreferenceskala_gochara_publicationmanifest_id",
          true
        ],
        "ka_gochara_generation_seal_pkey": [
          "p",
          "primarykeychart_id,generation",
          true
        ]
      },
      "indexes": {
        "ka_gochara_generation_seal_pkey": "createuniqueindexka_gochara_generation_seal_pkeyonka_gochara_generation_sealusingbtreechart_id,generation"
      },
      "triggers": {
        "ka_gochara_generation_seal_check": [
          "createtriggerka_gochara_generation_seal_checkbeforeinsertonka_gochara_generation_sealforeachrowexecutefunctionka_gochara_generation_seal_guard",
          "O"
        ],
        "ka_gochara_generation_seal_immutable": [
          "createtriggerka_gochara_generation_seal_immutablebeforedeleteorupdateonka_gochara_generation_sealforeachrowexecutefunctionka_gochara_insert_only'§6.1/§10.1—publicationhistoryispermanent'",
          "O"
        ],
        "ka_gochara_generation_seal_no_truncate": [
          "createtriggerka_gochara_generation_seal_no_truncatebeforetruncateonka_gochara_generation_sealforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_physical_object": {
      "columns": {
        "body": [
          "text",
          true
        ],
        "canonical_target": [
          "text",
          true
        ],
        "convention_id": [
          "text",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "physical_object_id": [
          "uuid",
          true
        ],
        "relation_kind": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_physical_object_convention_id_fkey": [
          "f",
          "foreignkeyconvention_idreferenceska_gochara_sky_conventionconvention_id",
          true
        ],
        "ka_gochara_physical_object_natural_uq": [
          "u",
          "uniquebody,relation_kind,canonical_target,convention_id",
          true
        ],
        "ka_gochara_physical_object_pkey": [
          "p",
          "primarykeyphysical_object_id",
          true
        ],
        "kgpo_body_domain_ck": [
          "c",
          "checkbody=anyarray['sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu']",
          true
        ],
        "kgpo_identity_uq": [
          "u",
          "uniquephysical_object_id,body,relation_kind,convention_id",
          true
        ],
        "kgpo_relation_kind_ck": [
          "c",
          "checkrelation_kind=anyarray['residence','aspect','conjunction','sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant']",
          true
        ],
        "kgpo_target_form_ck": [
          "c",
          "checkcanonical_target~'^point:[0-9]|[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9]\\.[0-9]+?$'orcanonical_target~'^span:[a-z0-9_]+$'orcanonical_target~'^star:[1-9]|1[0-9]|2[0-7]$'",
          true
        ]
      },
      "indexes": {
        "ka_gochara_physical_object_natural_uq": "createuniqueindexka_gochara_physical_object_natural_uqonka_gochara_physical_objectusingbtreebody,relation_kind,canonical_target,convention_id",
        "ka_gochara_physical_object_pkey": "createuniqueindexka_gochara_physical_object_pkeyonka_gochara_physical_objectusingbtreephysical_object_id",
        "kgpo_identity_uq": "createuniqueindexkgpo_identity_uqonka_gochara_physical_objectusingbtreephysical_object_id,body,relation_kind,convention_id"
      },
      "triggers": {
        "ka_gochara_physical_object_immutable": [
          "createtriggerka_gochara_physical_object_immutablebeforedeleteorupdateonka_gochara_physical_objectforeachrowexecutefunctionka_gochara_insert_only'§6.1publicationimmutability'",
          "O"
        ],
        "ka_gochara_physical_object_no_truncate": [
          "createtriggerka_gochara_physical_object_no_truncatebeforetruncateonka_gochara_physical_objectforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_sky_convention": {
      "columns": {
        "ayanamsha": [
          "text",
          true
        ],
        "convention_id": [
          "text",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "domain_end": [
          "timestamp with time zone",
          true
        ],
        "domain_start": [
          "timestamp with time zone",
          true
        ],
        "ephemeris_generation": [
          "text",
          true
        ],
        "grid": [
          "text",
          true
        ],
        "method_version": [
          "text",
          true
        ],
        "node_convention": [
          "text",
          true
        ]
      },
      "constraints": {
        "ka_gochara_sky_convention_pkey": [
          "p",
          "primarykeyconvention_id",
          true
        ],
        "kgsc_domain_ordered_ck": [
          "c",
          "checkdomain_start<domain_end",
          true
        ]
      },
      "indexes": {
        "ka_gochara_sky_convention_pkey": "createuniqueindexka_gochara_sky_convention_pkeyonka_gochara_sky_conventionusingbtreeconvention_id"
      },
      "triggers": {
        "ka_gochara_sky_convention_immutable": [
          "createtriggerka_gochara_sky_convention_immutablebeforedeleteorupdateonka_gochara_sky_conventionforeachrowexecutefunctionka_gochara_insert_only'§6.1/§7.2inv4'",
          "O"
        ],
        "ka_gochara_sky_convention_no_truncate": [
          "createtriggerka_gochara_sky_convention_no_truncatebeforetruncateonka_gochara_sky_conventionforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ]
      }
    },
    "ka_gochara_sky_event": {
      "columns": {
        "body": [
          "text",
          true
        ],
        "convention_id": [
          "text",
          true
        ],
        "coverage": [
          "jsonb",
          true
        ],
        "created_at": [
          "timestamp with time zone",
          true
        ],
        "delta_lambda": [
          "real",
          false
        ],
        "delta_t": [
          "real",
          false
        ],
        "event_id": [
          "uuid",
          true
        ],
        "event_kind": [
          "text",
          true
        ],
        "longitude": [
          "double precision",
          false
        ],
        "occurrence_ordinal": [
          "integer",
          true
        ],
        "physical_object_id": [
          "uuid",
          true
        ],
        "precision_regime": [
          "text",
          false
        ],
        "solver_method": [
          "text",
          true
        ],
        "supersedes_event_id": [
          "uuid",
          false
        ],
        "t_exact": [
          "timestamp with time zone",
          false
        ]
      },
      "constraints": {
        "ka_gochara_sky_event_object_fk": [
          "f",
          "foreignkeyphysical_object_id,body,event_kind,convention_idreferenceska_gochara_physical_objectphysical_object_id,body,relation_kind,convention_id",
          true
        ],
        "ka_gochara_sky_event_ordinal_uq": [
          "u",
          "uniquephysical_object_id,occurrence_ordinal",
          true
        ],
        "ka_gochara_sky_event_pkey": [
          "p",
          "primarykeyevent_id",
          true
        ],
        "ka_gochara_sky_event_supersedes_event_id_fkey": [
          "f",
          "foreignkeysupersedes_event_idreferenceska_gochara_sky_eventevent_id",
          true
        ],
        "kgse_body_domain_ck": [
          "c",
          "checkbody=anyarray['sun','mars','mercury','jupiter','venus','saturn','rahu','ketu']",
          true
        ],
        "kgse_coverage_shape_ck": [
          "c",
          "checkjsonb_typeofcoverage='object'andcoverage?'truncated'andjsonb_typeofcoverage->'truncated'='boolean'",
          true
        ],
        "kgse_event_kind_ck": [
          "c",
          "checkevent_kind=anyarray['sign_ingress','nakshatra_ingress','kakshya_crossing','station','eclipse_instant']",
          true
        ],
        "kgse_exact_precision_ck": [
          "c",
          "checkt_exactisnullorlongitudeisnotnullanddelta_lambdaisnotnullanddelta_tisnotnullandprecision_regimeisnotnull",
          true
        ],
        "kgse_longitude_range_ck": [
          "c",
          "checklongitudeisnullorlongitude>=0andlongitude<360",
          true
        ],
        "kgse_no_self_supersede_ck": [
          "c",
          "checksupersedes_event_idisnullorsupersedes_event_id<>event_id",
          true
        ],
        "kgse_ordinal_ck": [
          "c",
          "checkoccurrence_ordinal>=1",
          true
        ],
        "kgse_solver_method_ck": [
          "c",
          "checksolver_method=anyarray['arc_index_bracket','swiss_refined','clipped_truncated']",
          true
        ],
        "kgse_station_refined_ck": [
          "c",
          "checkevent_kind<>'station'orsolver_method='swiss_refined'",
          true
        ],
        "kgse_supersedes_uq": [
          "u",
          "uniquesupersedes_event_id",
          true
        ],
        "kgse_t_exact_iff_truncated_ck": [
          "c",
          "checkt_exactisnull=coverage->>'truncated'",
          true
        ],
        "kgse_truncated_method_ck": [
          "c",
          "checkcoverage->>'truncated'=solver_method='clipped_truncated'",
          true
        ],
        "kgse_uncertainty_finite_ck": [
          "c",
          "checkka_gochara_finite_nonneg_okdelta_lambdaistrueandka_gochara_finite_nonneg_okdelta_tistrue",
          true
        ]
      },
      "indexes": {
        "idx_kgse_convention_time": "createindexidx_kgse_convention_timeonka_gochara_sky_eventusingbtreeconvention_id,body,event_kind,t_exact",
        "ka_gochara_sky_event_ordinal_uq": "createuniqueindexka_gochara_sky_event_ordinal_uqonka_gochara_sky_eventusingbtreephysical_object_id,occurrence_ordinal",
        "ka_gochara_sky_event_pkey": "createuniqueindexka_gochara_sky_event_pkeyonka_gochara_sky_eventusingbtreeevent_id",
        "kgse_supersedes_uq": "createuniqueindexkgse_supersedes_uqonka_gochara_sky_eventusingbtreesupersedes_event_id"
      },
      "triggers": {
        "ka_gochara_sky_event_mutation_guard": [
          "createtriggerka_gochara_sky_event_mutation_guardbeforedeleteorupdateonka_gochara_sky_eventforeachrowexecutefunctionka_gochara_sky_event_guard",
          "O"
        ],
        "ka_gochara_sky_event_no_truncate": [
          "createtriggerka_gochara_sky_event_no_truncatebeforetruncateonka_gochara_sky_eventforeachstatementexecutefunctionka_gochara_refuse_truncate",
          "O"
        ],
        "ka_gochara_sky_event_supersede_check": [
          "createtriggerka_gochara_sky_event_supersede_checkbeforeinsertonka_gochara_sky_eventforeachrowexecutefunctionka_gochara_sky_event_supersede_guard",
          "O"
        ]
      }
    }
  }
}
$expected$::jsonb);
END;
$$;
