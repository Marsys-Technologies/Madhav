-- 1308_gochara_near_miss_storage.sql
--
-- Pravāha (ND-P2-20261005 rules 1 and 2; FINAL_BUILD_SCOPE v1.1 FB-25, FB-27, FB-28), 2026-10-05. Author: pravaha stream D (builder side).
-- STATUS: HOLD — second protected window, AFTER 1305 (G12), 1306 (G8) and 1307 (publication CHECK).
--
-- WHAT IT ADDS: storage for the SEPARATE kind `near_miss`. Three NEW tables, their triggers (existing guard functions only), indexes and
-- grants. NOTHING ELSE:
--   * no existing table is altered, no existing function or trigger is replaced, no existing row is touched, no applied migration is edited;
--   * no function is created at all (every trigger below calls a function 1153/1155 already created);
--   * nothing here is read by the scored path: no contact, record, window, coverage, digest, completeness or seal object refers to these
--     tables (ND-P2 rule 2: a near-miss never enters a support union, P4 influence, an evaluated candidate, a peak, a rank, a candidate
--     count or coverage accounting).
--
-- WHAT A NEAR-MISS IS (ND-P2 rule 1): a certified, complete, ROOTLESS point-contact stretch with POSITIVE clearance — the transiting body
-- enters the admission band of a ray level of a point target, turns round inside it and leaves without ever reaching the ray level. EVERY
-- such stretch belongs to this kind. Unresolved geometry stays unresolved: it is refused by the builder and is never a row here.
--
-- WHAT A ROW OF ka_gochara_near_miss IS (ND-P2 rule 2): the near-miss AND the standalone, lower-standing, UNSCORED interval it opens — one
-- row, [t_in, t_out). `standing` is the closed value 'near_miss' (categorical, lower than a contact; no numeric weight is invented);
-- `score` is NULL by CHECK with `score_reason = 'near_miss_unscored'`; `proximity` = 1 - clearance/orb is GEOMETRIC and is named proximity,
-- never strength. `junction` (ND-P2 rule 1) lists the sign ingresses and nakshatra ingresses of the transiting body and the MD/AD
-- boundaries inside [t_in, t_out) with their source identities and a completeness state per kind; it means "contains a junction", admits
-- nothing and scores nothing (missing coverage is 'unknown', never empty).
--
-- THE THREE TABLES
--   ka_gochara_near_miss_object   GLOBAL, insert-only (the physical-object pattern of 1153). Natural key (body, relation_kind,
--                                 canonical_target, orb_policy_id, convention_id): an orb change is a NEW object, never a renumbering (FB-25).
--                                 Its own identity namespace: nothing references ka_gochara_physical_object or ka_gochara_contact_identity,
--                                 so no existing contact identity changes by one byte.
--   ka_gochara_near_miss          chart x generation occurrence rows. PK (chart_id, generation, near_miss_id); the ordinal is over the
--                                 FULL-DOMAIN ordered near-miss set of the object (FB-25). Rows are written once (UPDATE refused) and
--                                 replaced whole by a scoped DELETE of an UNSEALED generation (CLAUDE.md §N.3); a sealed generation
--                                 refuses INSERT and DELETE; TRUNCATE refused.
--   ka_gochara_near_miss_search   one row per (chart, generation, object) searched: the horizon, the count, searched_complete and the
--                                 layer version. An object with no near-miss therefore has a VERIFIED-EMPTY result (FB-28), and a
--                                 generation with no search row has the layer OFF. Same write discipline as the occurrence table.
--
-- GUARDS (the 1155:869-908 trio, existing functions): BEFORE UPDATE OR DELETE statement lock (ka_gochara_chart_statement_lock), the row
-- write guard ka_gochara_chart_write_guard('no_update') (chart family key, sealed-generation refusal, UPDATE refused), and the TRUNCATE
-- refusal. The object table carries the 1153 substrate trio (chart context before INSERT, insert-only, no TRUNCATE).
--
-- GRANTS (to the roles that EXIST; a role that is absent is NAMED in a NOTICE, as in 1240 — never a grant to nobody passed off as done):
--   data_plane_builder   SELECT, INSERT on the object table; SELECT, INSERT, DELETE on the two chart x generation tables (the
--                        delete-then-insert replace of a candidate generation, 1242's reading of the same guards). No UPDATE, no TRUNCATE.
--   gochara_verifier     SELECT on all three (it re-derives the near-miss set independently and compares; it writes NOTHING here —
--                        1240's "verifier holds no write privilege on any ka_gochara_% table" closure keeps holding and is re-checked below).
--   gochara_sealer       SELECT on all three.
-- No sequence grants (UUID keys are caller-minted). No function EXECUTE is added: the trigger functions run as the writing role, which
-- already holds EXECUTE on ka_gochara_lock_chart / ka_gochara_generation_is_sealed (1220) or cannot write here at all.
--
-- NOT IN THIS FILE (FINAL_BUILD_SCOPE FB-21 lists them under 1308; they need 1305 and 1306 on the branch and replace functions in full, so
-- they are not additive and are left to the stacked follow-up): the new tables in the hard-coded list of ka_gochara_brief_state_digest
-- (FB-28), the near-miss UNION arm of the completeness function (FB-28, stacked on 1305 -> 1306 per FB-20), and the `occurrence_kind`
-- column on ka_gochara_relationship_record (FB-26). Until they exist a near-miss row is NOT covered by the seal digest.
--
-- ROUTE / WINDOW: PROTECTED-class (it CREATEs tables and triggers in schema public): listed in PROTECTED_PUBLIC_SCHEMA_MIGRATIONS
-- (platform/scripts/migrate.ts) and applied only through deploy.yml's exact `--only` window, after 1305, 1306 and 1307. Everything sits in
-- the one migration transaction (BEGIN/COMMIT belong to migrate.ts): a refusal leaves NOTHING changed.
-- IDEMPOTENT: CREATE TABLE / INDEX IF NOT EXISTS, DROP TRIGGER IF EXISTS + CREATE TRIGGER, GRANT of a held privilege is a no-op.
-- FAIL-CLOSED: refuses to apply when a prerequisite object of 1153/1155 is missing, and the post-apply block raises unless every table,
-- constraint, trigger and (for each role that exists) privilege is exactly as stated.
-- ROLLBACK (only while no generation holding near-miss rows is sealed): DROP TABLE public.ka_gochara_near_miss_search,
-- public.ka_gochara_near_miss, public.ka_gochara_near_miss_object; nothing else was changed.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL lock_timeout = '5s';

-- ── 0. Prerequisites (fail-closed) ───────────────────────────────────────────
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('public.charts'), ('public.ka_gochara_sky_convention'), ('public.ka_gochara_generation_seal')) AS x(name)
  WHERE to_regclass(x.name) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1308: prerequisite table(s) missing: % — apply 1153 first', missing;
  END IF;
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('public.ka_gochara_chart_statement_lock()'), ('public.ka_gochara_chart_write_guard()'),
               ('public.ka_gochara_refuse_truncate()'), ('public.ka_gochara_substrate_chart_lock()'),
               ('public.ka_gochara_insert_only()'), ('public.ka_gochara_generation_governed(text)'),
               ('public.ka_gochara_horizon_finite_ok(tstzrange)'), ('public.ka_gochara_finite_nonneg_ok(double precision)')) AS x(name)
  WHERE to_regprocedure(x.name) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1308: prerequisite function(s) missing: % — apply 1153 and 1155 first', missing;
  END IF;
END;
$$;

-- ── 1. Near-miss object (global, insert-only; FB-25 natural key) ─────────────
CREATE TABLE IF NOT EXISTS public.ka_gochara_near_miss_object (
  near_miss_object_id UUID PRIMARY KEY,
  body                TEXT NOT NULL,
  relation_kind       TEXT NOT NULL,
  canonical_target    TEXT NOT NULL,
  orb_policy_id       TEXT NOT NULL,
  convention_id       TEXT NOT NULL REFERENCES public.ka_gochara_sky_convention(convention_id),
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  CONSTRAINT kgnmo_body_domain_ck CHECK (body IN
    ('sun','moon','mars','mercury','jupiter','venus','saturn','rahu','ketu')),
  -- a near-miss exists only for a POINT contact relation
  CONSTRAINT kgnmo_relation_kind_ck CHECK (relation_kind IN ('aspect','conjunction')),
  CONSTRAINT kgnmo_target_form_ck CHECK (
    canonical_target ~ '^point:([0-9]|[1-9][0-9]|[12][0-9][0-9]|3[0-5][0-9])(\.[0-9]+)?$'),
  CONSTRAINT kgnmo_orb_policy_ck CHECK (length(orb_policy_id) > 0),
  CONSTRAINT ka_gochara_near_miss_object_natural_uq
    UNIQUE (body, relation_kind, canonical_target, orb_policy_id, convention_id)
);

COMMENT ON TABLE public.ka_gochara_near_miss_object IS
  'Near-miss object (ND-P2-20261005 rule 1; FINAL_BUILD_SCOPE FB-25): the identity a near-miss occurrence is numbered under — one per '
  '(body, relation_kind, canonical_target, orb_policy_id, convention_id). Its own namespace: no reference to a physical object or a contact '
  'identity. An orb change is a new object. Global, insert-only; TRUNCATE refused.';

DROP TRIGGER IF EXISTS ka_gochara_near_miss_object_0_chart_context ON public.ka_gochara_near_miss_object;
CREATE TRIGGER ka_gochara_near_miss_object_0_chart_context
  BEFORE INSERT ON public.ka_gochara_near_miss_object
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_substrate_chart_lock();
DROP TRIGGER IF EXISTS ka_gochara_near_miss_object_immutable ON public.ka_gochara_near_miss_object;
CREATE TRIGGER ka_gochara_near_miss_object_immutable
  BEFORE UPDATE OR DELETE ON public.ka_gochara_near_miss_object
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_insert_only('ND-P2 near-miss object identity');
DROP TRIGGER IF EXISTS ka_gochara_near_miss_object_no_truncate ON public.ka_gochara_near_miss_object;
CREATE TRIGGER ka_gochara_near_miss_object_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_near_miss_object
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 2. Near-miss occurrence = the standalone unscored interval (FB-27) ───────
CREATE TABLE IF NOT EXISTS public.ka_gochara_near_miss (
  chart_id            UUID NOT NULL REFERENCES public.charts(id),
  generation          TEXT NOT NULL,
  near_miss_id        UUID NOT NULL,
  near_miss_object_id UUID NOT NULL REFERENCES public.ka_gochara_near_miss_object(near_miss_object_id),
  ordinal             INTEGER NOT NULL,
  level_deg           DOUBLE PRECISION NOT NULL,
  t_in                TIMESTAMPTZ NOT NULL,
  t_out               TIMESTAMPTZ NOT NULL,
  t_closest           TIMESTAMPTZ,
  closest_state       TEXT NOT NULL,
  clearance_deg       DOUBLE PRECISION NOT NULL,
  orb_deg             DOUBLE PRECISION NOT NULL,
  proximity           DOUBLE PRECISION NOT NULL,
  standing            TEXT NOT NULL DEFAULT 'near_miss',
  score               DOUBLE PRECISION,
  score_reason        TEXT NOT NULL DEFAULT 'near_miss_unscored',
  junction            JSONB NOT NULL,
  junction_complete   BOOLEAN NOT NULL,
  coverage            JSONB NOT NULL,
  solver_method       TEXT NOT NULL,
  delta_t             REAL,
  precision_regime    TEXT NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, near_miss_id),
  CONSTRAINT kgnm_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgnm_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgnm_ordinal_ck CHECK (ordinal >= 1),
  CONSTRAINT kgnm_object_ordinal_uq UNIQUE (chart_id, generation, near_miss_object_id, ordinal),
  CONSTRAINT kgnm_level_range_ck CHECK (level_deg >= 0 AND level_deg < 360),
  CONSTRAINT kgnm_span_order_ck CHECK (t_in < t_out),
  -- FB-25: a closest instant that cannot be placed is NULL with the named state, never a guessed instant
  CONSTRAINT kgnm_closest_state_ck CHECK (closest_state IN ('placed','edge_unplaced')),
  CONSTRAINT kgnm_closest_iff_placed_ck CHECK ((t_closest IS NOT NULL) = (closest_state = 'placed')),
  CONSTRAINT kgnm_closest_inside_ck CHECK (t_closest IS NULL OR (t_in <= t_closest AND t_closest <= t_out)),
  -- POSITIVE clearance, strictly inside the orb: zero clearance is a contact, not a near-miss
  CONSTRAINT kgnm_orb_ck CHECK (orb_deg > 0 AND orb_deg < 'Infinity'::double precision),
  CONSTRAINT kgnm_clearance_positive_ck CHECK (clearance_deg > 0 AND clearance_deg < orb_deg),
  CONSTRAINT kgnm_proximity_ck CHECK (proximity >= 0 AND proximity < 1),
  -- ND-P2 rule 2: categorical lower standing, and NO score — by construction, not by convention
  CONSTRAINT kgnm_standing_ck CHECK (standing = 'near_miss'),
  CONSTRAINT kgnm_unscored_ck CHECK (score IS NULL),
  CONSTRAINT kgnm_score_reason_ck CHECK (score_reason = 'near_miss_unscored'),
  CONSTRAINT kgnm_junction_shape_ck CHECK (jsonb_typeof(junction) = 'object' AND junction ? 'contains_junction'),
  CONSTRAINT kgnm_coverage_shape_ck CHECK (jsonb_typeof(coverage) = 'object'),
  CONSTRAINT kgnm_solver_method_ck CHECK (solver_method IN ('swiss_refined_extremum','arc_index_extremum')),
  CONSTRAINT kgnm_uncertainty_finite_ck CHECK (public.ka_gochara_finite_nonneg_ok(delta_t) IS TRUE)
);

COMMENT ON TABLE public.ka_gochara_near_miss IS
  'Near-miss occurrence (ND-P2-20261005 rules 1-2; FINAL_BUILD_SCOPE FB-27): one certified, complete, rootless point-contact stretch with '
  'positive clearance AND the standalone lower-standing UNSCORED interval [t_in, t_out) it opens. standing = near_miss; score IS NULL '
  '(near_miss_unscored); proximity = 1 - clearance/orb is geometric, not a strength. Never read by the scored path. PK (chart_id, '
  'generation, near_miss_id); near_miss_id = hash(object id, ordinal), the ordinal over the full-domain ordered set of the object. Writer: '
  'per-(chart_id x generation) delete-then-insert of CANDIDATE generations (CLAUDE.md §N.3); UPDATE refused; a sealed generation refuses '
  'INSERT and DELETE; TRUNCATE refused.';

CREATE INDEX IF NOT EXISTS idx_kgnm_chart_gen_time ON public.ka_gochara_near_miss (chart_id, generation, t_in);
CREATE INDEX IF NOT EXISTS idx_kgnm_object ON public.ka_gochara_near_miss (near_miss_object_id, ordinal);

DROP TRIGGER IF EXISTS ka_gochara_nm_0_statement_lock ON public.ka_gochara_near_miss;
CREATE TRIGGER ka_gochara_nm_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_near_miss
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
DROP TRIGGER IF EXISTS ka_gochara_nm_1_write_guard ON public.ka_gochara_near_miss;
CREATE TRIGGER ka_gochara_nm_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_near_miss
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('no_update');
DROP TRIGGER IF EXISTS ka_gochara_nm_no_truncate ON public.ka_gochara_near_miss;
CREATE TRIGGER ka_gochara_nm_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_near_miss
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 3. Near-miss search (verified-empty + layer version; FB-28) ──────────────
CREATE TABLE IF NOT EXISTS public.ka_gochara_near_miss_search (
  chart_id            UUID NOT NULL REFERENCES public.charts(id),
  generation          TEXT NOT NULL,
  near_miss_object_id UUID NOT NULL REFERENCES public.ka_gochara_near_miss_object(near_miss_object_id),
  layer_version       INTEGER NOT NULL,
  searched_complete   BOOLEAN NOT NULL,
  horizon             TSTZRANGE NOT NULL,
  near_miss_count     INTEGER NOT NULL,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, near_miss_object_id),
  CONSTRAINT kgnms_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgnms_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgnms_layer_version_ck CHECK (layer_version = 1),
  CONSTRAINT kgnms_horizon_ck CHECK (public.ka_gochara_horizon_finite_ok(horizon) IS TRUE),
  CONSTRAINT kgnms_count_ck CHECK (near_miss_count >= 0)
);

COMMENT ON TABLE public.ka_gochara_near_miss_search IS
  'Near-miss search coverage (FINAL_BUILD_SCOPE FB-28): one row per (chart_id, generation, near-miss object) the builder searched over '
  'the horizon, with the count it stored — so an object with no near-miss is a VERIFIED-EMPTY result and a generation with no row has the '
  'near-miss layer OFF. layer_version is the layer''s version (1). Same write discipline as ka_gochara_near_miss.';

DROP TRIGGER IF EXISTS ka_gochara_nms_0_statement_lock ON public.ka_gochara_near_miss_search;
CREATE TRIGGER ka_gochara_nms_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_near_miss_search
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
DROP TRIGGER IF EXISTS ka_gochara_nms_1_write_guard ON public.ka_gochara_near_miss_search;
CREATE TRIGGER ka_gochara_nms_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_near_miss_search
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('no_update');
DROP TRIGGER IF EXISTS ka_gochara_nms_no_truncate ON public.ka_gochara_near_miss_search;
CREATE TRIGGER ka_gochara_nms_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_near_miss_search
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 4. Grants (roles that exist; an absent role is NAMED) ────────────────────
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT SELECT, INSERT ON public.ka_gochara_near_miss_object TO data_plane_builder;
    GRANT SELECT, INSERT, DELETE ON public.ka_gochara_near_miss, public.ka_gochara_near_miss_search TO data_plane_builder;
    RAISE NOTICE 'migration 1308: builder grants issued to role data_plane_builder';
  ELSE
    RAISE NOTICE 'migration 1308: role data_plane_builder NOT FOUND — NO builder grant was issued; until it holds them the builder cannot store a near-miss and a full build refuses the first one';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN
    GRANT SELECT ON public.ka_gochara_near_miss_object, public.ka_gochara_near_miss, public.ka_gochara_near_miss_search TO gochara_verifier;
    RAISE NOTICE 'migration 1308: verifier SELECT grants issued to role gochara_verifier';
  ELSE
    RAISE NOTICE 'migration 1308: role gochara_verifier NOT FOUND — NO verifier grant was issued; the near-miss set cannot be independently verified until it is provisioned and granted SELECT';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer') THEN
    GRANT SELECT ON public.ka_gochara_near_miss_object, public.ka_gochara_near_miss, public.ka_gochara_near_miss_search TO gochara_sealer;
    RAISE NOTICE 'migration 1308: sealer SELECT grants issued to role gochara_sealer';
  ELSE
    RAISE NOTICE 'migration 1308: role gochara_sealer NOT FOUND — NO sealer grant was issued';
  END IF;
END;
$$;

-- ── 5. Post-apply presence checks (raise, never a silent skip) ───────────────
DO $$
DECLARE missing text; n integer; t text;
BEGIN
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('public.ka_gochara_near_miss_object'), ('public.ka_gochara_near_miss'), ('public.ka_gochara_near_miss_search')) AS x(name)
  WHERE to_regclass(x.name) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1308 post-apply check failed: missing table(s): %', missing;
  END IF;

  SELECT string_agg(x.tbl || '.' || x.trg, ', ') INTO missing
  FROM (VALUES
    ('ka_gochara_near_miss_object', 'ka_gochara_near_miss_object_0_chart_context'),
    ('ka_gochara_near_miss_object', 'ka_gochara_near_miss_object_immutable'),
    ('ka_gochara_near_miss_object', 'ka_gochara_near_miss_object_no_truncate'),
    ('ka_gochara_near_miss', 'ka_gochara_nm_0_statement_lock'),
    ('ka_gochara_near_miss', 'ka_gochara_nm_1_write_guard'),
    ('ka_gochara_near_miss', 'ka_gochara_nm_no_truncate'),
    ('ka_gochara_near_miss_search', 'ka_gochara_nms_0_statement_lock'),
    ('ka_gochara_near_miss_search', 'ka_gochara_nms_1_write_guard'),
    ('ka_gochara_near_miss_search', 'ka_gochara_nms_no_truncate')) AS x(tbl, trg)
  WHERE NOT EXISTS (SELECT 1 FROM pg_trigger g WHERE g.tgname = x.trg AND NOT g.tgisinternal AND g.tgenabled = 'O'
                    AND g.tgrelid = ('public.' || x.tbl)::regclass);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1308 post-apply check failed: missing or disabled trigger(s): %', missing;
  END IF;

  -- the constraints that MAKE a near-miss unscored, lower-standing and positive-clearance must be present AND validated
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES ('kgnm_unscored_ck'), ('kgnm_score_reason_ck'), ('kgnm_standing_ck'), ('kgnm_clearance_positive_ck'),
               ('kgnm_proximity_ck'), ('kgnm_canonical_chart_ck'), ('kgnm_generation_governed_ck'), ('kgnm_closest_state_ck'),
               ('kgnm_closest_iff_placed_ck'), ('kgnm_span_order_ck'), ('kgnm_object_ordinal_uq'), ('kgnm_junction_shape_ck')) AS x(name)
  WHERE NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = x.name AND c.convalidated
                    AND c.conrelid = 'public.ka_gochara_near_miss'::regclass);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1308 post-apply check failed: ka_gochara_near_miss lacks constraint(s): %', missing;
  END IF;
  SELECT count(*) INTO n FROM pg_constraint c
  WHERE c.conrelid = 'public.ka_gochara_near_miss_search'::regclass AND c.convalidated
    AND c.conname IN ('kgnms_canonical_chart_ck', 'kgnms_generation_governed_ck', 'kgnms_layer_version_ck', 'kgnms_horizon_ck', 'kgnms_count_ck');
  IF n <> 5 THEN
    RAISE EXCEPTION 'migration 1308 post-apply check failed: ka_gochara_near_miss_search carries % of its 5 CHECK constraints', n;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint c WHERE c.conname = 'ka_gochara_near_miss_object_natural_uq'
                 AND c.conrelid = 'public.ka_gochara_near_miss_object'::regclass) THEN
    RAISE EXCEPTION 'migration 1308 post-apply check failed: the near-miss object natural key is missing';
  END IF;

  -- NONINTERFERENCE, structurally: no foreign key leads from any other relation INTO the new tables (nothing on the scored path can
  -- depend on a near-miss), and none leads from them into a publication manifest or a build run (the small-test teardown's catalog scan
  -- of incoming keys finds nothing new)
  SELECT string_agg(c.conname || ' on ' || c.conrelid::regclass::text, ', ') INTO missing
  FROM pg_constraint c
  WHERE c.contype = 'f'
    AND c.confrelid IN ('public.ka_gochara_near_miss_object'::regclass, 'public.ka_gochara_near_miss'::regclass,
                        'public.ka_gochara_near_miss_search'::regclass)
    AND c.conrelid NOT IN ('public.ka_gochara_near_miss'::regclass, 'public.ka_gochara_near_miss_search'::regclass);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1308 post-apply check failed: a relation outside the near-miss layer references it: %', missing;
  END IF;

  IF to_regrole('data_plane_builder') IS NOT NULL THEN
    IF NOT (has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss_object', 'SELECT')
            AND has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss_object', 'INSERT')
            AND has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss', 'SELECT')
            AND has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss', 'INSERT')
            AND has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss', 'DELETE')
            AND has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss_search', 'SELECT')
            AND has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss_search', 'INSERT')
            AND has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss_search', 'DELETE')) THEN
      RAISE EXCEPTION 'migration 1308 post-apply check failed: the builder does not hold the near-miss storage privileges';
    END IF;
    FOREACH t IN ARRAY ARRAY['ka_gochara_near_miss_object', 'ka_gochara_near_miss', 'ka_gochara_near_miss_search'] LOOP
      IF has_table_privilege('data_plane_builder', 'public.' || t, 'UPDATE')
         OR has_table_privilege('data_plane_builder', 'public.' || t, 'TRUNCATE')
         OR has_any_column_privilege('data_plane_builder', 'public.' || t, 'UPDATE') THEN
        RAISE EXCEPTION 'migration 1308 post-apply check failed: the builder holds UPDATE or TRUNCATE on %', t;
      END IF;
    END LOOP;
    IF has_table_privilege('data_plane_builder', 'public.ka_gochara_near_miss_object', 'DELETE') THEN
      RAISE EXCEPTION 'migration 1308 post-apply check failed: the builder holds DELETE on the insert-only near-miss object table';
    END IF;
  END IF;

  FOREACH t IN ARRAY ARRAY['gochara_verifier', 'gochara_sealer'] LOOP
    IF to_regrole(t) IS NOT NULL THEN
      SELECT string_agg(p.priv || ' on ' || x.tbl, ', ') INTO missing
      FROM (VALUES ('ka_gochara_near_miss_object'), ('ka_gochara_near_miss'), ('ka_gochara_near_miss_search')) AS x(tbl)
      CROSS JOIN (VALUES ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE')) AS p(priv)
      WHERE has_table_privilege(t, 'public.' || x.tbl, p.priv)
         OR (p.priv IN ('INSERT', 'UPDATE') AND has_any_column_privilege(t, 'public.' || x.tbl, p.priv));
      IF missing IS NOT NULL THEN
        RAISE EXCEPTION 'migration 1308 post-apply check failed: % holds a WRITE privilege on the near-miss tables: %', t, missing;
      END IF;
      SELECT count(*) INTO n
      FROM (VALUES ('ka_gochara_near_miss_object'), ('ka_gochara_near_miss'), ('ka_gochara_near_miss_search')) AS x(tbl)
      WHERE has_table_privilege(t, 'public.' || x.tbl, 'SELECT');
      IF n <> 3 THEN
        RAISE EXCEPTION 'migration 1308 post-apply check failed: % can read only % of the 3 near-miss tables', t, n;
      END IF;
    END IF;
  END LOOP;

  RAISE NOTICE 'migration 1308: presence checks passed';
END;
$$;
