-- Migration 1206: AM-5 search-completeness storage + seal checks —
--                 GOCHARA_SPECS_V1_5_AMENDMENTS_DRAFT §AM-5 (accepted at pre-gate,
--                 ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS_v1_4; follow-up F-1, steward
--                 M20261001T201843-f8e5 item 3). Six NEW chart-scoped tables, the
--                 digest/identity helpers, the completeness-violation functions and
--                 ONE additive BEFORE-INSERT trigger on ka_gochara_generation_seal.
-- Created: 2026-10-02. Author: pravaha/b6-am5-inventory-migration (Stream B, B6.0).
--
-- NEVER EDITS 1153–1157 (applied, immutable — CLAUDE.md §N.4). Every object here is
-- new; the only touch on an existing relation is CREATE TRIGGER on
-- ka_gochara_generation_seal, which replaces nothing: the applied
-- ka_gochara_generation_seal_guard (1153) keeps firing, this trigger fires AFTER it
-- (name order) and takes the chart key itself, so ordering cannot matter.
--
-- WHY A DATABASE LAYER (the review's finding, restated)
-- ═════════════════════════════════════════════════════
-- 1155/1156 validate EXISTING consumers (records, windows). Nothing in them can see a
-- required path that was never searched or whose obligations were never inserted —
-- such a path contributes no consumer row (1156:509–518 enumerates records/windows
-- only; 1153:939–954 checks that drift and existing memberships). Completeness
-- therefore needs its own storage:
--   search_input_snapshot  one immutable L1/declaration/manifest input identity per
--                          (chart, generation); every inventory and interval FKs it
--   search_inventory       one header per (chart, generation, event_class) — horizon,
--                          input binding, and (after finalisation) the two digests
--   search_path_pin        a TOTAL partition of the registry's sealed rule versions:
--                          included (committed obligation-id set) | computed_empty |
--                          excluded (closed reason, structured basis, ruling_ref)
--   search_obligation      the qualified 9-tuples, ob_id = UUIDv8 recomputed here
--   search_interval        per-obligation searched ranges, disjoint, input-bound
--   search_inventory_verification  the independent re-derivation's digest
-- Seal: refuses a first publication unless every obligation of every claimed class is
-- covered over the class horizon, every pin's committed set equals its stored
-- obligations (never-inserted obligations ⇒ refusal), inputs are unchanged, and an
-- independent verification digest equals the stored inventory digest. A REPLAY of an
-- already-sealed generation takes a separate integrity-only branch (the function
-- inserts ON CONFLICT DO NOTHING, and a BEFORE-INSERT trigger fires before conflict
-- handling), so historical inventories never have to adopt later registry versions.
--
-- WHAT SQL ENFORCES vs WHAT IT CANNOT (draft §AM-5, restated)
-- ───────────────────────────────────────────────────────────
-- Enforced: committed-set equality, ledger coverage, input binding/drift, digest
-- recomputation, immutability, partition over-claim, presence + equality of the
-- verification row. NOT enforced (cannot be): that the inventory is the RIGHT one for
-- the class — that is the independent verifier's derivation (O-RP-9); if writer and
-- verifier share a misreading of the doctrine this migration cannot detect it. The
-- verifier's independence is a process property, not a database property.
--
-- DEVIATIONS FROM THE DRAFT, DISCLOSED (each is folded back into the draft text):
--   * the inventory header carries inventory_digest / ledger_digest as NULL until a
--     one-shot FINALISATION UPDATE (digests recomputed and equal, else refused);
--     after it, new pins/obligations/intervals for that class are refused;
--   * timestamps in every digest preimage are whole-second UTC; sub-second bounds are
--     refused by CHECK (the preimage would otherwise collide);
--   * canonical JSON = sorted keys (codepoint order), no spaces, UTF-8 not escaped;
--   * pin/obligation path_id and rule_version appear LOWERCASED in preimages and
--     obligation bytes (the registry's own ids are stored with their case for the FK);
--   * the migration grants data_plane_builder SELECT on ka_gochara_generation_seal and
--     ka_gochara_av_polarity_declaration (1216 deferred them: no write path then) —
--     the new guards read seal state and declaration rows as the invoking role;
--   * F-3 (open): every sealed registry (path_id, rule_version) must be accounted for
--     per class; historical/superseded version selection is not yet specified.
--
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns ONE transaction. Gate →
-- DDL → presence checks. Deploy route: the protected public-schema window (deploy.yml
-- gochara_contracts_schema_migration), the SAME window as 1204, in order after it.
-- ROLLBACK (dependents first): DROP TRIGGER ka_gochara_generation_seal_z_search_complete
-- ON ka_gochara_generation_seal; DROP the six tables in reverse dependency order
-- (verification, interval, obligation, path_pin, inventory, input_snapshot); DROP the
-- functions named below.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;   -- pinned schema resolution (F9)
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE (byte-identical to preflight_1206_search_inventory_completeness.sql) ──
DO $$
DECLARE
  failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'schema_missing', 'public'
    WHERE to_regnamespace('public') IS NULL
    UNION ALL
    SELECT 'no_usage_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'USAGE')
    UNION ALL
    SELECT 'no_create_privilege_on_public', current_user
    WHERE NOT has_schema_privilege('public', 'CREATE')
    UNION ALL
    SELECT 'table_missing', t.rel
    FROM (VALUES ('public.charts'), ('public.ka_gochara_generation_seal'),
                 ('public.ka_gochara_rule_path_seal'), ('public.ka_gochara_sky_convention'),
                 ('public.ka_gochara_av_polarity_declaration'),
                 ('public.kala_gochara_coverage'), ('public.kala_gochara_publication'),
                 ('public.chart_facts'), ('public.chart_dashas')) AS t(rel)
    WHERE to_regclass(t.rel) IS NULL
    UNION ALL
    SELECT 'function_missing', p.sig
    FROM (VALUES ('public.ka_gochara_lock_chart(uuid)'),
                 ('public.ka_gochara_lock_global_shared()'),
                 ('public.ka_gochara_generation_is_sealed(uuid,text)'),
                 ('public.ka_gochara_generation_governed(text)'),
                 ('public.ka_gochara_horizon_finite_ok(tstzrange)'),
                 ('public.ka_gochara_chart_statement_lock()'),
                 ('public.ka_gochara_refuse_truncate()'),
                 ('public.ka_gochara_require_sealed_rule_path()')) AS p(sig)
    WHERE to_regprocedure(p.sig) IS NULL
    UNION ALL
    SELECT 'object_already_exists', o.rel
    FROM (VALUES ('public.ka_gochara_search_input_snapshot'), ('public.ka_gochara_search_inventory'),
                 ('public.ka_gochara_search_path_pin'), ('public.ka_gochara_search_obligation'),
                 ('public.ka_gochara_search_interval'),
                 ('public.ka_gochara_search_inventory_verification')) AS o(rel)
    WHERE to_regclass(o.rel) IS NOT NULL
    UNION ALL
    -- ordered execution gate: 1157 recorded, 1206 not
    SELECT 'prerequisite_migration_not_applied', p.prefix
    FROM (VALUES ('1157_')) AS p(prefix)
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND NOT EXISTS (SELECT 1 FROM _migrations_applied m WHERE starts_with(m.filename, p.prefix))
    UNION ALL
    SELECT 'migration_already_applied', m.filename
    FROM _migrations_applied m
    WHERE to_regclass('public._migrations_applied') IS NOT NULL
      AND starts_with(m.filename, '1206_')
  )
  SELECT string_agg(f.failure || ' :: ' || f.detail, E'\n' ORDER BY f.failure, f.detail)
  INTO failures
  FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1206 BLOCKED — migration 1206 must NOT be applied:% %', E'\n', failures;
  END IF;
  RAISE NOTICE 'preflight 1206: all checks passed';
END;
$$;

-- ── 1. Pure helpers (identity + digest bytes — AM-2 / AM-5) ────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_sha256_hex(t text)
RETURNS text LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT encode(sha256(convert_to(t, 'UTF8')), 'hex');
$$;

-- UUIDv8 from SHA-256 (RFC 9562 §5.8): first 16 digest bytes, version nibble 8,
-- variant bits 10 — exactly the AM-2 construction (122 digest bits remain).
CREATE OR REPLACE FUNCTION public.ka_gochara_uuidv8(t text)
RETURNS uuid LANGUAGE sql IMMUTABLE STRICT AS $$
  SELECT encode(set_byte(set_byte(s.b, 6, (get_byte(s.b, 6) & 15) | 128),
                         8, (get_byte(s.b, 8) & 63) | 128), 'hex')::uuid
  FROM (SELECT substring(sha256(convert_to(t, 'UTF8')) from 1 for 16) AS b) s;
$$;

-- Canonical JSON: sorted keys (codepoint order), no spaces, UTF-8 not escaped.
CREATE OR REPLACE FUNCTION public.ka_gochara_canonical_json(j jsonb)
RETURNS text LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog, public AS $$
BEGIN
  IF j IS NULL THEN RETURN 'null'; END IF;
  IF jsonb_typeof(j) = 'object' THEN
    RETURN '{' || COALESCE((SELECT string_agg(to_jsonb(e.key)::text || ':' || public.ka_gochara_canonical_json(e.value),
                                              ',' ORDER BY e.key COLLATE "C")
                            FROM jsonb_each(j) e), '') || '}';
  ELSIF jsonb_typeof(j) = 'array' THEN
    RETURN '[' || COALESCE((SELECT string_agg(public.ka_gochara_canonical_json(e.value), ',' ORDER BY e.ord)
                            FROM jsonb_array_elements(j) WITH ORDINALITY AS e(value, ord)), '') || ']';
  END IF;
  RETURN j::text;
END;
$$;

-- Whole-second UTC rendering used in every digest preimage.
CREATE OR REPLACE FUNCTION public.ka_gochara_utc_ts(t timestamptz)
RETURNS text LANGUAGE sql IMMUTABLE STRICT SET timezone = 'UTC' AS $$
  SELECT to_char(t AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"');
$$;

-- A uuid[] that is non-NULL-element, sorted ascending and duplicate-free.
CREATE OR REPLACE FUNCTION public.ka_gochara_uuid_set_ok(a uuid[])
RETURNS boolean LANGUAGE sql IMMUTABLE AS $$
  SELECT a IS NOT NULL
     AND array_position(a, NULL) IS NULL
     AND a = COALESCE((SELECT array_agg(DISTINCT x ORDER BY x) FROM unnest(a) x), ARRAY[]::uuid[]);
$$;

-- input_digest: sha256 over the five sorted key=value lines (draft §AM-5 item 0).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_input_digest(
  conv text, vec jsonb, l1_digest text, dasha_digest text, av text[])
RETURNS text LANGUAGE sql IMMUTABLE AS $$
  SELECT public.ka_gochara_sha256_hex(
    'av_declarations=' || COALESCE((SELECT string_agg(x, ',' ORDER BY x COLLATE "C") FROM unnest(av) x), '') || E'\n' ||
    'convention_id=' || conv || E'\n' ||
    'dasha_digest=' || dasha_digest || E'\n' ||
    'input_generation_vector=' || public.ka_gochara_canonical_json(vec) || E'\n' ||
    'l1_facts_digest=' || l1_digest);
$$;

-- Live recomputation of the consumed L1 rows (row content = every column except
-- audit timestamps; a missing id contributes MISSING so a deletion changes the digest).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_l1_facts_digest(ids text[])
RETURNS text LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE d text;
BEGIN
  SELECT public.ka_gochara_sha256_hex(COALESCE(string_agg(
           i.id || '|' || COALESCE(public.ka_gochara_sha256_hex(
             public.ka_gochara_canonical_json(to_jsonb(f) - 'created_at')), 'MISSING'),
           E'\n' ORDER BY i.id COLLATE "C"), ''))
    INTO d
  FROM unnest(ids) AS i(id)
  LEFT JOIN public.chart_facts f ON f.fact_id = i.id;
  RETURN d;
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_digest(ids text[])
RETURNS text LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE d text;
BEGIN
  SELECT public.ka_gochara_sha256_hex(COALESCE(string_agg(
           i.id || '|' || COALESCE(public.ka_gochara_sha256_hex(
             public.ka_gochara_canonical_json(to_jsonb(r) - 'computed_at')), 'MISSING'),
           E'\n' ORDER BY i.id COLLATE "C"), ''))
    INTO d
  FROM unnest(ids) AS i(id)
  LEFT JOIN public.chart_dashas r ON r.dasha_row_id::text = i.id;
  RETURN d;
END;
$$;

-- One AV-declaration entry '<key>:<sha256 of the row>' (key may itself contain ':').
CREATE OR REPLACE FUNCTION public.ka_gochara_search_av_entry(key text)
RETURNS text LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE h text;
BEGIN
  SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(to_jsonb(a) - 'created_at'))
    INTO h FROM public.ka_gochara_av_polarity_declaration a WHERE a.convention = key;
  RETURN key || ':' || COALESCE(h, 'MISSING');
END;
$$;

-- ── 2. Tables ──────────────────────────────────────────────────────────────────

CREATE TABLE public.ka_gochara_search_input_snapshot (
  chart_id                uuid NOT NULL REFERENCES public.charts(id),
  generation              text NOT NULL,
  convention_id           text NOT NULL REFERENCES public.ka_gochara_sky_convention(convention_id),
  input_generation_vector jsonb NOT NULL,
  consumed_fact_ids       text[] NOT NULL,
  consumed_dasha_row_ids  text[] NOT NULL,
  av_declarations         text[] NOT NULL,
  l1_facts_digest         text NOT NULL,
  dasha_digest            text NOT NULL,
  input_digest            text NOT NULL,
  created_at              timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation),
  CONSTRAINT kgsis_input_uq UNIQUE (chart_id, generation, input_digest),
  CONSTRAINT kgsis_canonical_chart_ck
    CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgsis_generation_governed_ck
    CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgsis_digests_ck
    CHECK (l1_facts_digest ~ '^[0-9a-f]{64}$' AND dasha_digest ~ '^[0-9a-f]{64}$'
           AND input_digest ~ '^[0-9a-f]{64}$'),
  CONSTRAINT kgsis_vector_object_ck CHECK (jsonb_typeof(input_generation_vector) = 'object')
);

CREATE TABLE public.ka_gochara_search_inventory (
  chart_id         uuid NOT NULL,
  generation       text NOT NULL,
  event_class      text NOT NULL,
  horizon          tstzrange NOT NULL,
  input_digest     text NOT NULL,
  inventory_digest text,
  ledger_digest    text,
  finalized_at     timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, event_class),
  CONSTRAINT kgsi_input_uq UNIQUE (chart_id, generation, event_class, input_digest),
  CONSTRAINT kgsi_snapshot_fk FOREIGN KEY (chart_id, generation, input_digest)
    REFERENCES public.ka_gochara_search_input_snapshot (chart_id, generation, input_digest),
  CONSTRAINT kgsi_event_class_ck CHECK (event_class IN (
    'achievement_recognition','bereavement','birth_anchor',
    'business_launch','career_advancement','career_change',
    'career_entry','career_setback','childbirth',
    'chronic_onset','education_milestone','exam_outcome',
    'financial_deception','foreign_settlement','illness_acute',
    'major_gain','major_loss','marriage','parental_event',
    'property_acquisition','psychological_arc','relocation',
    'romantic_start','separation','spiritual_turn','surgery',
    'travel_event')),
  CONSTRAINT kgsi_horizon_ck
    CHECK (public.ka_gochara_horizon_finite_ok(horizon) IS TRUE
           AND lower_inc(horizon) AND NOT upper_inc(horizon)
           AND date_trunc('second', lower(horizon)) = lower(horizon)
           AND date_trunc('second', upper(horizon)) = upper(horizon)),
  CONSTRAINT kgsi_final_pair_ck
    CHECK ((inventory_digest IS NULL) = (ledger_digest IS NULL)
           AND (inventory_digest IS NULL) = (finalized_at IS NULL)),
  CONSTRAINT kgsi_digests_ck
    CHECK ((inventory_digest IS NULL OR inventory_digest ~ '^[0-9a-f]{64}$')
           AND (ledger_digest IS NULL OR ledger_digest ~ '^[0-9a-f]{64}$'))
);

CREATE TABLE public.ka_gochara_search_path_pin (
  chart_id         uuid NOT NULL,
  generation       text NOT NULL,
  event_class      text NOT NULL,
  path_id          text NOT NULL,
  rule_version     text NOT NULL,
  disposition      text NOT NULL,
  exclusion_reason text,
  ruling_ref       text,
  basis            text,
  note             text,            -- non-authoritative; in NO digest, never read by serving
  committed_ob_ids uuid[] NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, event_class, path_id, rule_version),
  CONSTRAINT kgspp_header_fk FOREIGN KEY (chart_id, generation, event_class)
    REFERENCES public.ka_gochara_search_inventory (chart_id, generation, event_class),
  CONSTRAINT kgspp_rule_seal_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path_seal (path_id, rule_version),
  CONSTRAINT kgspp_disposition_ck CHECK (disposition IN ('included','computed_empty','excluded')),
  CONSTRAINT kgspp_committed_set_ck CHECK (public.ka_gochara_uuid_set_ok(committed_ob_ids) IS TRUE),
  -- included ⇔ a non-empty committed set; computed_empty / excluded commit nothing
  CONSTRAINT kgspp_included_nonempty_ck
    CHECK ((disposition = 'included') = (cardinality(committed_ob_ids) >= 1)),
  CONSTRAINT kgspp_included_bare_ck
    CHECK (disposition <> 'included'
           OR (exclusion_reason IS NULL AND ruling_ref IS NULL AND basis IS NULL)),
  CONSTRAINT kgspp_basis_required_ck
    CHECK (disposition = 'included' OR basis IS NOT NULL),
  CONSTRAINT kgspp_computed_empty_bare_ck
    CHECK (disposition <> 'computed_empty' OR (exclusion_reason IS NULL AND ruling_ref IS NULL)),
  CONSTRAINT kgspp_reason_closed_ck
    CHECK (disposition <> 'excluded'
           OR exclusion_reason IN ('not_applicable_to_class','on_demand_tier','disabled_form',
                                   'inputs_unavailable','tier_withheld_by_ruling')),
  -- ruling_ref is present IFF the exclusion reason is one of the three degrading reasons
  CONSTRAINT kgspp_ruling_iff_degrading_ck
    CHECK ((disposition = 'excluded'
            AND exclusion_reason IN ('disabled_form','inputs_unavailable','tier_withheld_by_ruling'))
           = (ruling_ref IS NOT NULL)),
  CONSTRAINT kgspp_basis_grammar_ck
    CHECK (basis IS NULL OR basis ~ '^(spec:[A-Za-z0-9_.-]+@[0-9][0-9A-Za-z.]*#[^|\n\r%]+|ruling:[A-Za-z0-9._-]+|oracle:[A-Za-z0-9._-]+)$'),
  CONSTRAINT kgspp_ruling_format_ck CHECK (ruling_ref IS NULL OR ruling_ref ~ '^[A-Za-z0-9._-]+$'),
  CONSTRAINT kgspp_ids_nonblank_ck CHECK (btrim(path_id) <> '' AND btrim(rule_version) <> '')
);

CREATE TABLE public.ka_gochara_search_obligation (
  chart_id        uuid NOT NULL,
  generation      text NOT NULL,
  event_class     text NOT NULL,
  ob_id           uuid NOT NULL,
  path_id         text NOT NULL,
  rule_version    text NOT NULL,
  agent           text NOT NULL,
  relation        text NOT NULL,
  object_role     text NOT NULL,
  target          text NOT NULL,
  frame           text NOT NULL,
  person          text NOT NULL,
  canonical_bytes text NOT NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, event_class, ob_id),
  CONSTRAINT kgso_pin_fk FOREIGN KEY (chart_id, generation, event_class, path_id, rule_version)
    REFERENCES public.ka_gochara_search_path_pin (chart_id, generation, event_class, path_id, rule_version),
  CONSTRAINT kgso_bytes_ck CHECK (
    canonical_bytes = event_class || '|' || lower(path_id) || '|' || lower(rule_version) || '|' ||
                      agent || '|' || relation || '|' || object_role || '|' || target || '|' ||
                      frame || '|' || person),
  -- arity 9, lowercase stored form, no newline: the preimage needs no escaping
  CONSTRAINT kgso_bytes_shape_ck CHECK (
    canonical_bytes = lower(canonical_bytes)
    AND canonical_bytes !~ E'[\\n\\r]'
    AND cardinality(string_to_array(canonical_bytes, '|')) = 9),
  CONSTRAINT kgso_core_nonblank_ck CHECK (agent <> '' AND relation <> '' AND object_role <> ''),
  CONSTRAINT kgso_relation_ck CHECK (relation IN
    ('residence','aspect','conjunction','dispositorship',
     'association','ownership','occupancy','period_running'))
);

CREATE TABLE public.ka_gochara_search_interval (
  chart_id     uuid NOT NULL,
  generation   text NOT NULL,
  event_class  text NOT NULL,
  ob_id        uuid NOT NULL,
  search_range tstzrange NOT NULL,
  state        text NOT NULL,
  detail       jsonb,
  input_digest text NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, event_class, ob_id, search_range),
  CONSTRAINT kgsiv_obligation_fk FOREIGN KEY (chart_id, generation, event_class, ob_id)
    REFERENCES public.ka_gochara_search_obligation (chart_id, generation, event_class, ob_id),
  -- every interval carries the SAME input identity as its inventory (mixed snapshots impossible)
  CONSTRAINT kgsiv_input_fk FOREIGN KEY (chart_id, generation, event_class, input_digest)
    REFERENCES public.ka_gochara_search_inventory (chart_id, generation, event_class, input_digest),
  CONSTRAINT kgsiv_state_ck CHECK (state IN ('searched_complete','searched_unqualified','missing_inputs')),
  CONSTRAINT kgsiv_range_ck CHECK (
    NOT isempty(search_range) AND NOT lower_inf(search_range) AND NOT upper_inf(search_range)
    AND lower_inc(search_range) AND NOT upper_inc(search_range)
    AND date_trunc('second', lower(search_range)) = lower(search_range)
    AND date_trunc('second', upper(search_range)) = upper(search_range))
);

CREATE TABLE public.ka_gochara_search_inventory_verification (
  chart_id                  uuid NOT NULL,
  generation                text NOT NULL,
  event_class               text NOT NULL,
  verifier_id               text NOT NULL,
  verifier_version          text NOT NULL,
  rederived_inventory_digest text NOT NULL,
  verified_at               timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, event_class, verifier_id, verifier_version),
  CONSTRAINT kgsv_header_fk FOREIGN KEY (chart_id, generation, event_class)
    REFERENCES public.ka_gochara_search_inventory (chart_id, generation, event_class),
  CONSTRAINT kgsv_ids_nonblank_ck CHECK (btrim(verifier_id) <> '' AND btrim(verifier_version) <> ''),
  CONSTRAINT kgsv_digest_ck CHECK (rederived_inventory_digest ~ '^[0-9a-f]{64}$')
);

CREATE INDEX idx_kgso_pin ON public.ka_gochara_search_obligation
  (chart_id, generation, event_class, path_id, rule_version);
CREATE INDEX idx_kgsiv_ob ON public.ka_gochara_search_interval
  (chart_id, generation, event_class, ob_id);

-- ── 3. Digests (read the stored rows; preimage per draft §AM-5 item 3) ─────────

CREATE OR REPLACE FUNCTION public.ka_gochara_search_inventory_preimage(
  p_chart uuid, p_generation text, p_class text)
RETURNS text LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE h record; conv text; pins text; obs text;
BEGIN
  SELECT i.horizon, i.input_digest, s.convention_id INTO h
  FROM public.ka_gochara_search_inventory i
  JOIN public.ka_gochara_search_input_snapshot s
    ON (s.chart_id, s.generation, s.input_digest) = (i.chart_id, i.generation, i.input_digest)
  WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.event_class = p_class;
  IF NOT FOUND THEN RETURN NULL; END IF;
  SELECT string_agg('pin=' || lower(p.path_id) || '|' || lower(p.rule_version) || '|' || p.disposition || '|' ||
                    COALESCE(p.exclusion_reason, '') || '|' || COALESCE(p.ruling_ref, '') || '|' ||
                    COALESCE(p.basis, '') || '|' ||
                    COALESCE((SELECT string_agg(x::text, ',' ORDER BY x::text COLLATE "C") FROM unnest(p.committed_ob_ids) x), ''),
                    E'\n' ORDER BY lower(p.path_id) COLLATE "C", lower(p.rule_version) COLLATE "C")
    INTO pins
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.event_class = p_class;
  SELECT string_agg('ob=' || o.canonical_bytes, E'\n' ORDER BY o.canonical_bytes COLLATE "C")
    INTO obs
  FROM public.ka_gochara_search_obligation o
  WHERE o.chart_id = p_chart AND o.generation = p_generation AND o.event_class = p_class;
  RETURN 'convention=' || h.convention_id || E'\n' ||
         'horizon=[' || public.ka_gochara_utc_ts(lower(h.horizon)) || ',' ||
                        public.ka_gochara_utc_ts(upper(h.horizon)) || ')' || E'\n' ||
         'input=' || h.input_digest ||
         COALESCE(E'\n' || pins, '') || COALESCE(E'\n' || obs, '');
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_inventory_digest(
  p_chart uuid, p_generation text, p_class text)
RETURNS text LANGUAGE sql STABLE AS $$
  SELECT public.ka_gochara_sha256_hex(public.ka_gochara_search_inventory_preimage(p_chart, p_generation, p_class));
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_ledger_digest(
  p_chart uuid, p_generation text, p_class text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT public.ka_gochara_sha256_hex(COALESCE(string_agg(r.row, E'\n' ORDER BY r.row COLLATE "C"), ''))
  FROM (SELECT v.ob_id::text || '|' || public.ka_gochara_utc_ts(lower(v.search_range)) || '|' ||
               public.ka_gochara_utc_ts(upper(v.search_range)) || '|' || v.state || '|' || v.input_digest AS row
        FROM public.ka_gochara_search_interval v
        WHERE v.chart_id = p_chart AND v.generation = p_generation AND v.event_class = p_class) r;
$$;

-- sha256 over the sorted 'event_class|inventory_digest|ledger_digest' lines of the
-- generation's FINALISED headers; NULL while any header is unfinalised.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_inventories_digest(p_chart uuid, p_generation text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT CASE WHEN count(*) = 0 OR bool_or(i.inventory_digest IS NULL) THEN NULL
              ELSE public.ka_gochara_sha256_hex(string_agg(
                     i.event_class || '|' || i.inventory_digest || '|' || i.ledger_digest,
                     E'\n' ORDER BY i.event_class COLLATE "C")) END
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation;
$$;

-- ── 4. Write guards ────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_search_write_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE
  r jsonb; ch uuid; gen text; cls text; tbl text := TG_TABLE_NAME;
  hdr record; snap record; pin record; pub record; want text;
BEGIN
  IF TG_OP = 'UPDATE' AND tbl <> 'ka_gochara_search_inventory' THEN
    RAISE EXCEPTION '% is insert-only (AM-5): UPDATE refused — a changed search is a new candidate generation', tbl;
  END IF;

  r := to_jsonb(CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END);
  ch := (r ->> 'chart_id')::uuid; gen := r ->> 'generation'; cls := r ->> 'event_class';
  PERFORM public.ka_gochara_lock_chart(ch);                       -- chart EXCLUSIVE first (N13)
  IF public.ka_gochara_generation_is_sealed(ch, gen) THEN
    RAISE EXCEPTION '% is publication-immutable (AM-5): (chart %, generation %) is SEALED — % refused; a changed search is a new generation',
      tbl, ch, gen, TG_OP;
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;   -- candidate replacement, dependency order (FKs enforce it)

  IF tbl = 'ka_gochara_search_input_snapshot' THEN
    IF NEW.input_digest IS DISTINCT FROM public.ka_gochara_search_input_digest(
         NEW.convention_id, NEW.input_generation_vector, NEW.l1_facts_digest, NEW.dasha_digest, NEW.av_declarations) THEN
      RAISE EXCEPTION 'ka_gochara_search_input_snapshot.input_digest does not recompute from its components (AM-5 item 0)';
    END IF;
    SELECT p.input_generation_vector INTO pub
    FROM public.kala_gochara_publication p WHERE p.chart_id = NEW.chart_id AND p.generation = NEW.generation;
    IF NOT FOUND THEN
      RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused: no kala_gochara_publication manifest row for (chart %, generation %) — the snapshot''s vector is bound to the manifest', NEW.chart_id, NEW.generation;
    END IF;
    IF pub.input_generation_vector IS DISTINCT FROM NEW.input_generation_vector THEN
      RAISE EXCEPTION 'ka_gochara_search_input_snapshot.input_generation_vector % differs from the manifest''s % (AM-5 item 0b)',
        NEW.input_generation_vector, pub.input_generation_vector;
    END IF;
    RETURN NEW;
  END IF;

  IF tbl = 'ka_gochara_search_inventory' THEN
    IF TG_OP = 'INSERT' THEN
      IF NEW.inventory_digest IS NOT NULL OR NEW.ledger_digest IS NOT NULL OR NEW.finalized_at IS NOT NULL THEN
        RAISE EXCEPTION 'ka_gochara_search_inventory is declared UNFINALISED; digests are set by the one-shot finalisation UPDATE';
      END IF;
      RETURN NEW;
    END IF;
    -- UPDATE = one-shot finalisation
    IF OLD.inventory_digest IS NOT NULL THEN
      RAISE EXCEPTION 'ka_gochara_search_inventory (%, %, %) is already FINALISED and immutable', OLD.chart_id, OLD.generation, OLD.event_class;
    END IF;
    IF (NEW.chart_id, NEW.generation, NEW.event_class, NEW.horizon, NEW.input_digest, NEW.created_at)
       IS DISTINCT FROM (OLD.chart_id, OLD.generation, OLD.event_class, OLD.horizon, OLD.input_digest, OLD.created_at) THEN
      RAISE EXCEPTION 'ka_gochara_search_inventory: finalisation may set only inventory_digest / ledger_digest / finalized_at';
    END IF;
    IF NEW.inventory_digest IS DISTINCT FROM public.ka_gochara_search_inventory_digest(OLD.chart_id, OLD.generation, OLD.event_class)
       OR NEW.ledger_digest IS DISTINCT FROM public.ka_gochara_search_ledger_digest(OLD.chart_id, OLD.generation, OLD.event_class) THEN
      RAISE EXCEPTION 'ka_gochara_search_inventory finalisation refused: the supplied digests do not equal the recomputation from the stored pins/obligations/intervals';
    END IF;
    NEW.finalized_at := now();
    RETURN NEW;
  END IF;

  -- everything below is a child row of an existing, UNFINALISED header
  SELECT i.* INTO hdr FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = ch AND i.generation = gen AND i.event_class = cls;
  IF NOT FOUND THEN
    RAISE EXCEPTION '% refused: no inventory header for (chart %, generation %, class %)', tbl, ch, gen, cls;
  END IF;

  IF tbl = 'ka_gochara_search_inventory_verification' THEN
    IF hdr.inventory_digest IS NULL THEN
      RAISE EXCEPTION 'ka_gochara_search_inventory_verification refused: the inventory (%, %, %) is not FINALISED — verify the finalised inventory', ch, gen, cls;
    END IF;
    RETURN NEW;
  END IF;

  IF hdr.inventory_digest IS NOT NULL THEN
    RAISE EXCEPTION '% refused: the inventory (%, %, %) is FINALISED — a changed search replaces the candidate chain (intervals → obligations → pins → verification → header)', tbl, ch, gen, cls;
  END IF;

  IF tbl = 'ka_gochara_search_path_pin' THEN
    PERFORM public.ka_gochara_lock_global_shared();   -- chart EXCLUSIVE → global SHARED (draft §AM-5 item 7)
    RETURN NEW;
  END IF;

  IF tbl = 'ka_gochara_search_obligation' THEN
    IF NEW.ob_id IS DISTINCT FROM public.ka_gochara_uuidv8(NEW.canonical_bytes) THEN
      RAISE EXCEPTION 'ka_gochara_search_obligation.ob_id % is not the UUIDv8 of its canonical bytes % (AM-2)', NEW.ob_id, NEW.canonical_bytes;
    END IF;
    SELECT p.disposition, p.committed_ob_ids INTO pin
    FROM public.ka_gochara_search_path_pin p
    WHERE (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
        = (NEW.chart_id, NEW.generation, NEW.event_class, NEW.path_id, NEW.rule_version);
    IF NOT FOUND OR pin.disposition <> 'included' THEN
      RAISE EXCEPTION 'ka_gochara_search_obligation refused: its pin (%, %) is absent or not ''included''', NEW.path_id, NEW.rule_version;
    END IF;
    IF NOT (NEW.ob_id = ANY (pin.committed_ob_ids)) THEN
      RAISE EXCEPTION 'ka_gochara_search_obligation refused: ob_id % is not in the pin''s committed obligation set (AM-5 item 2)', NEW.ob_id;
    END IF;
    RETURN NEW;
  END IF;

  IF tbl = 'ka_gochara_search_interval' THEN
    IF NOT (hdr.horizon @> NEW.search_range) THEN
      RAISE EXCEPTION 'ka_gochara_search_interval % lies outside the inventory horizon %', NEW.search_range, hdr.horizon;
    END IF;
    IF EXISTS (SELECT 1 FROM public.ka_gochara_search_interval v
               WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (NEW.chart_id, NEW.generation, NEW.event_class, NEW.ob_id)
                 AND v.search_range && NEW.search_range) THEN
      RAISE EXCEPTION 'ka_gochara_search_interval % overlaps an existing interval of obligation % — ranges are disjoint per obligation', NEW.search_range, NEW.ob_id;
    END IF;
    RETURN NEW;
  END IF;
  RETURN NEW;
END;
$$;

-- ── 5. Triggers ────────────────────────────────────────────────────────────────

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['ka_gochara_search_input_snapshot','ka_gochara_search_inventory',
                           'ka_gochara_search_path_pin','ka_gochara_search_obligation',
                           'ka_gochara_search_interval','ka_gochara_search_inventory_verification'] LOOP
    EXECUTE format('CREATE TRIGGER %I BEFORE UPDATE OR DELETE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock()', t || '_0_statement_lock', t);
    EXECUTE format('CREATE TRIGGER %I BEFORE INSERT OR UPDATE OR DELETE ON public.%I FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_search_write_guard()', t || '_1_write_guard', t);
    EXECUTE format('CREATE TRIGGER %I BEFORE TRUNCATE ON public.%I FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate()', t || '_no_truncate', t);
  END LOOP;
END;
$$;

-- an obligation / pin may only name a SEALED rule version; the helper takes
-- ka_gochara_lock_global_shared() first (chart EXCLUSIVE → global SHARED, 1154:479–490)
CREATE TRIGGER ka_gochara_search_path_pin_2_sealed_rule_check
  BEFORE INSERT ON public.ka_gochara_search_path_pin
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();
CREATE TRIGGER ka_gochara_search_obligation_2_sealed_rule_check
  BEFORE INSERT ON public.ka_gochara_search_obligation
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();

-- ── 6. Seal-time checks ────────────────────────────────────────────────────────

-- First-publication completeness violations. Callers hold chart EXCLUSIVE → global SHARED
-- (the seal trigger does). One row per violation: (event_class, violation, detail).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_completeness_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, violation text, detail text)
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE pub record; snap record; live_l1 text; live_dasha text; e text;
BEGIN
  SELECT p.horizon, p.input_generation_vector INTO pub
  FROM public.kala_gochara_publication p
  WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.status = 'published';

  -- the class census a generation CLAIMS = its event_class partitions
  RETURN QUERY
  SELECT c.partition_key, 'partition_without_inventory'::text, 'event_class partition has no search inventory'::text
  FROM public.kala_gochara_coverage c
  WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind = 'event_class'
    AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory i
                    WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.event_class = c.partition_key);
  RETURN QUERY
  SELECT i.event_class, 'inventory_without_partition'::text, 'search inventory has no event_class coverage partition'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND NOT EXISTS (SELECT 1 FROM public.kala_gochara_coverage c
                    WHERE c.chart_id = p_chart AND c.generation = p_generation
                      AND c.partition_kind = 'event_class' AND c.partition_key = i.event_class);

  -- snapshot (one per generation)
  SELECT s.* INTO snap FROM public.ka_gochara_search_input_snapshot s
  WHERE s.chart_id = p_chart AND s.generation = p_generation;
  IF FOUND THEN
    live_l1 := public.ka_gochara_search_l1_facts_digest(snap.consumed_fact_ids);
    live_dasha := public.ka_gochara_search_dasha_digest(snap.consumed_dasha_row_ids);
    IF live_l1 IS DISTINCT FROM snap.l1_facts_digest THEN
      RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed L1 fact rows no longer match the snapshot digest'::text;
    END IF;
    IF live_dasha IS DISTINCT FROM snap.dasha_digest THEN
      RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed dasha rows no longer match the snapshot digest'::text;
    END IF;
    FOREACH e IN ARRAY snap.av_declarations LOOP
      IF public.ka_gochara_search_av_entry(left(e, GREATEST(length(e) - 65, 0))) IS DISTINCT FROM e THEN
        RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, ('AV declaration entry no longer matches: ' || e)::text;
      END IF;
    END LOOP;
    IF pub.input_generation_vector IS DISTINCT FROM snap.input_generation_vector THEN
      RETURN QUERY SELECT '*'::text, 'input_vector_mismatch'::text, 'snapshot vector differs from the published manifest vector'::text;
    END IF;
  END IF;

  -- registry accounting: every sealed (path, version) pinned or excluded, per class
  RETURN QUERY
  SELECT i.event_class, 'registry_unaccounted_path'::text, (rs.path_id || '@' || rs.rule_version)::text
  FROM public.ka_gochara_search_inventory i
  CROSS JOIN public.ka_gochara_rule_path_seal rs
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_path_pin p
                    WHERE (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                        = (i.chart_id, i.generation, i.event_class, rs.path_id, rs.rule_version));

  -- finalisation, digests, horizon, snapshot binding
  RETURN QUERY
  SELECT i.event_class, 'inventory_not_finalised'::text, 'inventory header is not FINALISED'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.inventory_digest IS NULL;
  RETURN QUERY
  SELECT i.event_class, 'inventory_digest_mismatch'::text, 'stored digests differ from recomputation'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.inventory_digest IS NOT NULL
    AND (i.inventory_digest IS DISTINCT FROM public.ka_gochara_search_inventory_digest(i.chart_id, i.generation, i.event_class)
         OR i.ledger_digest IS DISTINCT FROM public.ka_gochara_search_ledger_digest(i.chart_id, i.generation, i.event_class));
  RETURN QUERY
  SELECT i.event_class, 'horizon_manifest_mismatch'::text, (i.horizon::text || ' vs manifest ' || COALESCE(pub.horizon::text, 'NULL'))::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation AND i.horizon IS DISTINCT FROM pub.horizon;
  RETURN QUERY
  SELECT i.event_class, 'input_snapshot_mismatch'::text, 'inventory is not bound to the generation snapshot'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND (snap.input_digest IS NULL OR i.input_digest IS DISTINCT FROM snap.input_digest);

  -- committed obligation set == stored obligations, per pin (never-inserted ⇒ refusal)
  RETURN QUERY
  SELECT p.event_class, 'committed_set_mismatch'::text,
         (p.path_id || '@' || p.rule_version || ' committed-not-stored=' ||
          COALESCE((SELECT string_agg(c::text, ',' ORDER BY c::text) FROM unnest(p.committed_ob_ids) c
                    WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                                      WHERE (o.chart_id, o.generation, o.event_class, o.ob_id)
                                          = (p.chart_id, p.generation, p.event_class, c))), '') ||
          ' stored-not-committed=' ||
          COALESCE((SELECT string_agg(o.ob_id::text, ',' ORDER BY o.ob_id::text) FROM public.ka_gochara_search_obligation o
                    WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version)
                        = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                      AND NOT (o.ob_id = ANY (p.committed_ob_ids))), ''))::text
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation
    AND ( EXISTS (SELECT 1 FROM unnest(p.committed_ob_ids) c
                  WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                                    WHERE (o.chart_id, o.generation, o.event_class, o.ob_id)
                                        = (p.chart_id, p.generation, p.event_class, c)))
       OR EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                  WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version)
                      = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                    AND NOT (o.ob_id = ANY (p.committed_ob_ids))) );

  -- ledger coverage: horizon ⊆ ⋃ (searched_complete ∪ searched_unqualified), per obligation
  RETURN QUERY
  SELECT o.event_class, 'obligation_uncovered'::text,
         (o.ob_id::text || ' uncovered ' || (i.horizon::tstzmultirange -
            COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                      WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                        AND v.state IN ('searched_complete','searched_unqualified')), '{}'::tstzmultirange))::text)::text
  FROM public.ka_gochara_search_obligation o
  JOIN public.ka_gochara_search_inventory i
    ON (i.chart_id, i.generation, i.event_class) = (o.chart_id, o.generation, o.event_class)
  WHERE o.chart_id = p_chart AND o.generation = p_generation
    AND NOT isempty(i.horizon::tstzmultirange -
          COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                    WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                      AND v.state IN ('searched_complete','searched_unqualified')), '{}'::tstzmultirange));
  RETURN QUERY
  SELECT v.event_class, 'missing_inputs_present'::text, v.ob_id::text
  FROM public.ka_gochara_search_interval v
  WHERE v.chart_id = p_chart AND v.generation = p_generation AND v.state = 'missing_inputs';

  -- partition over-claim: horizon equality; relations_searched == the included obligations' relations
  RETURN QUERY
  SELECT i.event_class, 'partition_overclaims'::text,
         ('partition ' || c.completed_horizon::text || ' / ' || c.relations_searched::text)::text
  FROM public.ka_gochara_search_inventory i
  JOIN public.kala_gochara_coverage c
    ON (c.chart_id, c.generation, c.partition_kind, c.partition_key) = (i.chart_id, i.generation, 'event_class', i.event_class)
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND ( c.completed_horizon IS DISTINCT FROM i.horizon
          OR ARRAY(SELECT DISTINCT x FROM unnest(c.relations_searched) x ORDER BY x)
             IS DISTINCT FROM
             ARRAY(SELECT DISTINCT o.relation FROM public.ka_gochara_search_obligation o
                   WHERE (o.chart_id, o.generation, o.event_class) = (i.chart_id, i.generation, i.event_class)
                   ORDER BY o.relation) );

  -- independent verification: a row must exist and EVERY row must equal the stored digest
  RETURN QUERY
  SELECT i.event_class, 'verification_missing_or_mismatch'::text, 'no independent verification row, or a row differs from the stored inventory digest'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND ( NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory_verification v
                      WHERE (v.chart_id, v.generation, v.event_class) = (i.chart_id, i.generation, i.event_class))
          OR EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory_verification v
                     WHERE (v.chart_id, v.generation, v.event_class) = (i.chart_id, i.generation, i.event_class)
                       AND v.rederived_inventory_digest IS DISTINCT FROM i.inventory_digest) );
END;
$$;

-- Replay of an already-sealed generation: integrity only (no registry accounting, no
-- live-input drift, no partition checks — those are first-publication predicates).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_replay_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, violation text, detail text)
LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT i.event_class, 'inventory_digest_mismatch'::text, 'sealed inventory no longer recomputes to its stored digests'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND ( i.inventory_digest IS NULL
          OR i.inventory_digest IS DISTINCT FROM public.ka_gochara_search_inventory_digest(i.chart_id, i.generation, i.event_class)
          OR i.ledger_digest IS DISTINCT FROM public.ka_gochara_search_ledger_digest(i.chart_id, i.generation, i.event_class) )
  UNION ALL
  SELECT i.event_class, 'verification_missing_or_mismatch'::text, 'verification row missing or differs from the stored digest'::text
  FROM public.ka_gochara_search_inventory i
  WHERE i.chart_id = p_chart AND i.generation = p_generation
    AND ( NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory_verification v
                      WHERE (v.chart_id, v.generation, v.event_class) = (i.chart_id, i.generation, i.event_class))
          OR EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory_verification v
                     WHERE (v.chart_id, v.generation, v.event_class) = (i.chart_id, i.generation, i.event_class)
                       AND v.rederived_inventory_digest IS DISTINCT FROM i.inventory_digest) );
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_generation_seal_search_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE existing uuid; n integer; msg text;
BEGIN
  PERFORM public.ka_gochara_lock_chart(NEW.chart_id);          -- chart EXCLUSIVE first …
  PERFORM public.ka_gochara_lock_global_shared();               -- … then global SHARED (before any registry read)
  SELECT s.manifest_id INTO existing FROM public.ka_gochara_generation_seal s
  WHERE s.chart_id = NEW.chart_id AND s.generation = NEW.generation;
  IF FOUND THEN
    -- REPLAY (ka_gochara_seal_generation inserts ON CONFLICT DO NOTHING; this BEFORE trigger fires first)
    IF existing IS DISTINCT FROM NEW.manifest_id THEN
      RAISE EXCEPTION 'ka_gochara_generation_seal replay refused (AM-5): manifest % differs from the existing seal''s manifest %', NEW.manifest_id, existing;
    END IF;
    SELECT count(*), string_agg(v.event_class || ':' || v.violation, '; ') INTO n, msg
    FROM public.ka_gochara_search_replay_violations(NEW.chart_id, NEW.generation) v;
    IF n > 0 THEN
      RAISE EXCEPTION 'ka_gochara_generation_seal replay refused (AM-5 integrity): %', msg;
    END IF;
    RETURN NEW;
  END IF;
  SELECT count(*), string_agg(v.event_class || ':' || v.violation || ':' || v.detail, E'\n  ' ORDER BY v.event_class, v.violation, v.detail)
    INTO n, msg
  FROM public.ka_gochara_search_completeness_violations(NEW.chart_id, NEW.generation) v;
  IF n > 0 THEN
    RAISE EXCEPTION 'ka_gochara_generation_seal refused (AM-5 search completeness): % violation(s) for (chart %, generation %):%  %',
      n, NEW.chart_id, NEW.generation, E'\n', msg;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER ka_gochara_generation_seal_z_search_complete
  BEFORE INSERT ON public.ka_gochara_generation_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_generation_seal_search_guard();

-- ── 7. Builder privileges (the 1216 grant model, extended for the new tables) ──
-- Guarded by role existence so a disposable database without the role still applies.
-- SELECT on the seal table and the AV declaration table is new: 1216 deferred them (no
-- write path then), but the new guards read seal state and declaration rows as the
-- INVOKING role. No TRUNCATE/TRIGGER/REFERENCES, no CREATE on schema public.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT SELECT, INSERT, DELETE ON
      public.ka_gochara_search_input_snapshot, public.ka_gochara_search_inventory,
      public.ka_gochara_search_path_pin, public.ka_gochara_search_obligation,
      public.ka_gochara_search_interval, public.ka_gochara_search_inventory_verification
      TO data_plane_builder;
    GRANT UPDATE (inventory_digest, ledger_digest, finalized_at)
      ON public.ka_gochara_search_inventory TO data_plane_builder;
    GRANT SELECT ON public.ka_gochara_generation_seal, public.ka_gochara_av_polarity_declaration
      TO data_plane_builder;
  END IF;
END;
$$;

COMMENT ON TABLE public.ka_gochara_search_input_snapshot IS
  'AM-5 item 0: ONE immutable search-input identity per (chart, generation) — L1 facts digest, dasha digest, AV declaration entries, sky convention and the manifest input_generation_vector. Every inventory and interval FKs input_digest, so intervals computed under different snapshots can never coexist in one generation.';
COMMENT ON TABLE public.ka_gochara_search_inventory IS
  'AM-5: one header per (chart, generation, event_class). Digests are NULL until the one-shot finalisation UPDATE (recomputed and equal, else refused); after it the class is immutable. Completeness authority — the partition in kala_gochara_coverage is only a guard-facing summary.';
COMMENT ON TABLE public.ka_gochara_search_path_pin IS
  'AM-5 item 2: a TOTAL partition of the registry''s sealed rule versions per class — included (committed obligation-id set) | computed_empty (a proven-empty disposition) | excluded (closed reason, structured basis, ruling_ref iff degrading). reason/ruling_ref/basis are inside the verified inventory preimage; note is not.';
COMMENT ON TABLE public.ka_gochara_search_obligation IS
  'AM-5 item 1: the qualified (event_class, path, version, agent, relation, object_role, target, frame, person) 9-tuples; ob_id = UUIDv8 of canonical_bytes, recomputed by the insert guard; insertable only if the pin''s committed set names it.';
COMMENT ON TABLE public.ka_gochara_search_interval IS
  'AM-5: per-obligation searched ranges — half-open whole-second, finite, inside the horizon, disjoint per obligation, bound to the snapshot input_digest.';
COMMENT ON TABLE public.ka_gochara_search_inventory_verification IS
  'AM-5 item 4: the INDEPENDENT re-derivation''s inventory digest; the seal requires a row and every row equal to the stored inventory_digest. Independence of the verifier is a process property.';

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES
    ('ka_gochara_search_input_snapshot_1_write_guard'), ('ka_gochara_search_inventory_1_write_guard'),
    ('ka_gochara_search_path_pin_1_write_guard'), ('ka_gochara_search_path_pin_2_sealed_rule_check'),
    ('ka_gochara_search_obligation_1_write_guard'), ('ka_gochara_search_obligation_2_sealed_rule_check'),
    ('ka_gochara_search_interval_1_write_guard'), ('ka_gochara_search_inventory_verification_1_write_guard'),
    ('ka_gochara_generation_seal_z_search_complete')) AS x(name)
  WHERE NOT EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgname = x.name AND NOT t.tgisinternal);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1206 post-apply check failed: missing triggers: %', missing;
  END IF;
  -- the applied seal guard must STILL be there (this migration adds, never replaces)
  IF NOT EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgname = 'ka_gochara_generation_seal_write_guard' AND NOT t.tgisinternal) THEN
    RAISE EXCEPTION 'migration 1206 post-apply check failed: the applied 1153 seal guard is missing';
  END IF;
  -- identity/digest helpers reproduce the AM-2 / AM-5 vectors
  IF public.ka_gochara_uuidv8('mars|conjunction|point:198.52|c0|1') <> '23276d7c-c127-8f4c-9ad5-6b7c8da8020f'::uuid THEN
    RAISE EXCEPTION 'migration 1206 post-apply check failed: UUIDv8 helper does not reproduce the AM-2 vector';
  END IF;
  IF public.ka_gochara_canonical_json('{"bg_transit_rules":"d1","bg_transit_av_gates":"d2"}'::jsonb)
     <> '{"bg_transit_av_gates":"d2","bg_transit_rules":"d1"}' THEN
    RAISE EXCEPTION 'migration 1206 post-apply check failed: canonical JSON helper';
  END IF;
  IF public.ka_gochara_utc_ts('2025-01-01T00:00:00+00'::timestamptz) <> '2025-01-01T00:00:00Z' THEN
    RAISE EXCEPTION 'migration 1206 post-apply check failed: UTC rendering helper';
  END IF;
  RAISE NOTICE 'migration 1206: presence checks passed';
END;
$$;
