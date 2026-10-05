-- Migration 1305: G12 route 1 — the search-input snapshot OWNS a COPY of the L1 rows it consumed. ADDITIVE on top of 1206/1232.
-- Pravāha B (Stream B, Śāstra), steward G12-ROUTE1 (2026-10-05), design note
-- 00_ARCHITECTURE/briefs/pravaha/decisions/G12_ROUTE1_SNAPSHOT_DESIGN_v1_0.md. STATUS: HOLD (protected window, with G8's 1306).
--
-- WHY
-- ═══
-- 1206's snapshot POINTS at its L1 inputs (consumed_fact_ids text[], consumed_dasha_row_ids uuid[]) and digests the WHOLE rows (every column
-- but computed_at, including row ids, build ids and parent ids). `chart_dashas.dasha_row_id` is a gen_random_uuid RE-ISSUED by every
-- ga_dashas rebuild; `chart_facts` rows carry `build_id`/`engine_version`. So after ANY later L1 rebuild a sealed generation reads every
-- consumed row as MISSING or changed: the completeness function reports input_snapshot_drift forever, the verification job cannot re-derive
-- (`consumed id resolves to no row`), and a sealed generation cannot be repaired. Citing fact ids does not help (the facts digest hashes
-- `build_id` too). The snapshot must therefore carry what it consumed.
--
-- WHAT THIS DOES (and what it deliberately does NOT do)
-- ════════════════════════════════════════════════════
--   1. Four additive columns on ka_gochara_search_input_snapshot: consumed_fact_rows / consumed_dasha_rows (jsonb arrays of
--      {key, content, metadata}) and l1_facts_metadata_digest / dasha_metadata_digest. consumed_fact_ids / consumed_dasha_row_ids stay as the KEYS
--      the builder submits (and as provenance). A NOT VALID CHECK makes the copies mandatory for every NEW row (0 snapshots exist on production; no
--      backfill; a legacy row without a copy keeps the 1206 behaviour).
--   2. IDENTITY vs METADATA. content = the columns that say what the search was cut from (fact: ayanamsha, category, subject, key, value text / num /
--      jsonb with every number scale-trimmed, unit; daśā: lord, end, parent level and start, lord path and ORDINAL path; key = fact_id, or
--      ayanamsha/system/level/start/kp_sublevel). metadata = ids, build, tier, engine, citation columns. The existing columns l1_facts_digest /
--      dasha_digest now hold the IDENTITY digest (so input_digest and every inventory / ledger digest keep their recipe); the METADATA digest is
--      informational and never enters input_digest.
--   3. THE COPY IS PRODUCED BY THE DATABASE (Codex round 1): a BEFORE INSERT trigger (named 0z, so it fires before 1206's write guard) BUILDS the copy and
--      the metadata digests from the live rows named by the submitted keys, overwriting whatever was submitted in those columns, and refuses unless the
--      submitted identity digests are those of what it built AND the built copy is EXACTLY the REQUIRED live population, a contract FIXED IN THE DATABASE
--      independent of the submitted ids (Vimśottarī MD, AD, PD of the canonical ayanamsha at the consumed tier over the bound manifest horizon; the ten
--      natal longitude facts): a missing level, period or subject, an extra or a conflicting row refuses by name. Fact identity is the NATURAL key
--      (fact_id is metadata), so a rebuild that re-issues fact ids is not drift.
--   4. New functions (nothing dropped, nothing renamed): ka_gochara_search_copy_digest, _normalize_numbers, _facts_copy, _facts_live_population,
--      _dasha_path, _dasha_ordinal_path, _dasha_element, _dasha_copy, _dasha_required_population, _dasha_live_population, and the copy-build trigger function.
--   5. Replaces TWO existing functions: ka_gochara_search_moon_resolved_domain (reads the copy) and ka_gochara_search_completeness_violations (the
--      1232 body, EXACTLY, with one block replaced: the L1 drift check compares the IDENTITY digest of the COMPLETE live population with the stored one,
--      so a changed value, a missing row AND an extra or conflicting row are all hard drift; a metadata-only difference (a tier, a build) is not a violation;
--      a legacy snapshot keeps the 1206 check but is REFUSED at first seal with its own violation, `input_snapshot_without_copy`; replay is unchanged).
--
-- ORDER (read this): 1305 must apply BEFORE G8's 1306. BOTH replace ka_gochara_search_completeness_violations in full, so whichever applies
-- LATER must carry the other's body. The gate below REFUSES when the applied completeness function already carries G8's census block
-- (`expected_class_list_missing`): applying this file after 1306 would silently revert G8. Re-sync 1306 onto 1305 instead.
--
-- GATE PIN: the two functions replaced here must be EXACTLY the 1232 bodies (sha256 of their pg_get_functiondef text, read READ-ONLY from production
-- 2026-10-05: completeness 63d9e7e7…, Moon domain 707bd37c…); the test suite reproduces both on a fresh 1206+1232 chain.
--
-- PRINCIPALS: EXECUTE on the new functions is granted (only to roles that exist) to data_plane_builder (the writer builds the copy and the
-- INSERT trigger recomputes digests as the invoker), gochara_verifier and gochara_sealer (the completeness and Moon-domain functions run as
-- the invoker and call them). In production every function created by amjis_app has PUBLIC EXECUTE revoked by default (1220), so these
-- grants are required, not decoration. No table grant changes: the new columns inherit the table-level privileges.
--
-- WINDOW: protected public-schema window, AFTER 1206/1232, BEFORE 1306. Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns one
-- transaction per migration. ROLLBACK (unused installation only): drop the trigger and the new functions, CREATE OR REPLACE the two replaced
-- functions from their 1232 text, drop the CHECK and the four columns, delete the _migrations_applied row. After any generation has been
-- built under 1305, correct forward instead.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE ──────────────────────────────────────────────────────────────────────
DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'snapshot_table_missing', 'ka_gochara_search_input_snapshot' WHERE to_regclass('public.ka_gochara_search_input_snapshot') IS NULL
    UNION ALL SELECT 'migration_1232_not_applied', 'ka_gochara_search_moon_resolved_domain'
    WHERE to_regprocedure('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)') IS NULL
    UNION ALL SELECT 'completeness_function_missing', 'ka_gochara_search_completeness_violations'
    WHERE to_regprocedure('public.ka_gochara_search_completeness_violations(uuid,text)') IS NULL
    UNION ALL SELECT 'helper_missing', h
    FROM unnest(ARRAY['public.ka_gochara_sha256_hex(text)', 'public.ka_gochara_canonical_json(jsonb)', 'public.ka_gochara_search_input_digest(text,jsonb,text,text,text[])',
                      'public.ka_gochara_search_l1_facts_digest(uuid,text[])', 'public.ka_gochara_search_dasha_digest(uuid,uuid[])']) h
    WHERE to_regprocedure(h) IS NULL
    UNION ALL SELECT 'chart_facts_missing', 'chart_facts' WHERE to_regclass('public.chart_facts') IS NULL
    UNION ALL SELECT 'chart_dashas_missing', 'chart_dashas' WHERE to_regclass('public.chart_dashas') IS NULL
    UNION ALL SELECT 'migration_1305_already_applied', 'consumed_fact_rows'
    WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'
                    AND column_name = 'consumed_fact_rows')
    UNION ALL SELECT 'g8_1306_applied_first', 'the applied completeness function already carries the G8 census block: re-sync 1306 onto 1305, never apply 1305 after it'
    WHERE to_regprocedure('public.ka_gochara_search_completeness_violations(uuid,text)') IS NOT NULL
      AND pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) LIKE '%expected_class_list_missing%'
    -- GATE PIN: the two functions this migration replaces must be EXACTLY what 1232 produced (sha256 of pg_get_functiondef, read READ-ONLY from
    -- production on 2026-10-05 and reproduced by a fresh 1206+1232 chain in the test suite): replacing a function someone has changed would revert it.
    UNION ALL SELECT 'completeness_function_is_not_the_1232_body', 'sha256 of its definition is not the one 1232 produces (63d9e7e737b0...)'
    WHERE to_regprocedure('public.ka_gochara_search_completeness_violations(uuid,text)') IS NOT NULL
      AND encode(sha256(convert_to(pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure), 'UTF8')), 'hex')
          <> '63d9e7e737b020784ca52c4cd06e66e74434c20b60d9b9d65834f4e1c773f1fb'
      AND pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) NOT LIKE '%expected_class_list_missing%'
    UNION ALL SELECT 'moon_domain_function_is_not_the_1232_body', 'sha256 of its definition is not the one 1232 produces (707bd37ce48a...)'
    WHERE to_regprocedure('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)') IS NOT NULL
      AND encode(sha256(convert_to(pg_get_functiondef('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)'::regprocedure), 'UTF8')), 'hex')
          <> '707bd37ce48a3c5fbaf2de881bc7554d97bc81fc1a09a6534d36b4ec5f09cf07'
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1305 BLOCKED: %', failures;
  END IF;
END;
$$;

-- ── 1. the copies (additive columns; NOT VALID so no existing row is scanned) ───
ALTER TABLE public.ka_gochara_search_input_snapshot
  ADD COLUMN consumed_fact_rows        jsonb,
  ADD COLUMN consumed_dasha_rows       jsonb,
  ADD COLUMN l1_facts_metadata_digest  text,
  ADD COLUMN dasha_metadata_digest     text;
ALTER TABLE public.ka_gochara_search_input_snapshot ADD CONSTRAINT kgsis_l1_copy_ck
  CHECK (consumed_fact_rows IS NOT NULL AND jsonb_typeof(consumed_fact_rows) = 'array'
         AND consumed_dasha_rows IS NOT NULL AND jsonb_typeof(consumed_dasha_rows) = 'array'
         AND l1_facts_metadata_digest ~ '^[0-9a-f]{64}$' AND dasha_metadata_digest ~ '^[0-9a-f]{64}$') NOT VALID;

-- ── 2. pure digest over a copy: sha256 of the byte-sorted `key|sha256(block)` lines ──────────────────────────────
-- p_block is 'content' (the IDENTITY digest) or 'metadata'. A null block (a row that was not found) contributes MISSING, so a deletion
-- changes the digest. Key and block are canonical JSON (sorted keys), so the digest does not depend on array or key order.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_copy_digest(p_copy jsonb, p_block text)
RETURNS text LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog, public AS $$
BEGIN
  IF p_block NOT IN ('content', 'metadata') THEN
    RAISE EXCEPTION 'ka_gochara_search_copy_digest: block must be content or metadata, got %', p_block;
  END IF;
  RETURN public.ka_gochara_sha256_hex(COALESCE((
    SELECT string_agg(public.ka_gochara_canonical_json(e.value -> 'key') || '|' ||
                      CASE WHEN jsonb_typeof(e.value -> p_block) = 'object'
                           THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> p_block)) ELSE 'MISSING' END,
                      E'\n' ORDER BY public.ka_gochara_canonical_json(e.value -> 'key') COLLATE "C")
    FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS e(value)), ''));
END;
$$;

-- ── 3. the L1 FACT rows: built from ids (strict: a missing row is an error), keyed by NATURAL KEY ────────────────────────────────────────
-- An element's KEY is the fact's natural key (ayanamsha, category, key, subject): a later ga_positions rebuild that re-issues fact_ids (deterministic row ids)
-- changes none of the identity; the fact_id lives in the METADATA block. Rendering is independent of the caller's session (timezone UTC, extra_float_digits),
-- numerics are scale-trimmed so a rebuild that stores the same value with a different trailing scale is NOT a value change.
-- Numbers nested ANYWHERE in a jsonb get their scale trimmed (12.50 and 12.5 are the same value), so a rebuild that stores the same number with a different
-- scale inside fact_value_jsonb is not a changed value. Pure; recursion over objects and arrays only.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_normalize_numbers(j jsonb)
RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog, public AS $$
BEGIN
  IF j IS NULL THEN RETURN NULL; END IF;
  IF jsonb_typeof(j) = 'number' THEN RETURN to_jsonb(trim_scale((j #>> '{}')::numeric)); END IF;
  IF jsonb_typeof(j) = 'object' THEN
    RETURN COALESCE((SELECT jsonb_object_agg(e.key, public.ka_gochara_search_normalize_numbers(e.value)) FROM jsonb_each(j) e), '{}'::jsonb);
  END IF;
  IF jsonb_typeof(j) = 'array' THEN
    RETURN COALESCE((SELECT jsonb_agg(public.ka_gochara_search_normalize_numbers(e.value) ORDER BY e.ord) FROM jsonb_array_elements(j) WITH ORDINALITY e(value, ord)), '[]'::jsonb);
  END IF;
  RETURN j;
END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_facts_copy(p_chart uuid, p_ids text[])
RETURNS jsonb LANGUAGE plpgsql STABLE
SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
DECLARE missing text; r jsonb;
BEGIN
  SELECT string_agg(i.id, ',' ORDER BY i.id) INTO missing
  FROM unnest(p_ids) AS i(id) WHERE NOT EXISTS (SELECT 1 FROM public.chart_facts f WHERE f.fact_id = i.id AND f.chart_id = p_chart);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'ka_gochara_search_facts_copy: consumed fact id(s) % do not exist for chart % — a snapshot is built from existing rows', missing, p_chart;
  END IF;
  SELECT COALESCE(jsonb_agg(s.el ORDER BY public.ka_gochara_canonical_json(s.el -> 'key') COLLATE "C", s.fid COLLATE "C"), '[]'::jsonb) INTO r
  FROM (
    SELECT f.fact_id AS fid,
           jsonb_build_object(
             'key', jsonb_build_object('ayanamsha_id', f.ayanamsha_id, 'fact_category', f.fact_category, 'fact_key', f.fact_key, 'fact_subject', f.fact_subject),
             'content', jsonb_build_object(
                 'fact_value_text', f.fact_value_text, 'fact_value_num', trim_scale(f.fact_value_num::numeric),
                 'fact_value_jsonb', public.ka_gochara_search_normalize_numbers(f.fact_value_jsonb), 'unit', f.unit),
             'metadata', jsonb_build_object(
                 'fact_id', f.fact_id, 'build_id', f.build_id, 'verification_pass_status', f.verification_pass_status, 'engine_version', f.engine_version,
                 'salience_formula_ver', f.salience_formula_ver, 'tolerance_arcsec', f.tolerance_arcsec, 'citation_ref', f.citation_ref,
                 'citation_human', f.citation_human, 'source_calculation', f.source_calculation, 'formula_provenance_text', f.formula_provenance_text,
                 'formula_id', f.formula_id, 'near_sign_boundary_flag', f.near_sign_boundary_flag,
                 'near_nakshatra_boundary_flag', f.near_nakshatra_boundary_flag, 'vargottama_flag_at_point', f.vargottama_flag_at_point,
                 'cross_ayanamsha_divergence_arcsec', f.cross_ayanamsha_divergence_arcsec)) AS el
    FROM unnest(p_ids) AS i(id)
    JOIN public.chart_facts f ON f.fact_id = i.id AND f.chart_id = p_chart) s;
  RETURN r;
END;
$$;

-- The REQUIRED fact population (Codex round 2, P1): a CONTRACT FIXED IN THE DATABASE, independent of the ids a builder submits and of the copy itself — every
-- natal longitude fact of the canonical ayanamsha for the ten subjects the read contract names (LAGNA, SUN, MOON, MAR, MER, JUP, VEN, SAT, RAH_MEAN,
-- KET_MEAN; fact_category graha_position, fact_key longitude_sidereal; a row without a numeric value is not an operand). A snapshot whose copy is not EXACTLY this
-- population is refused at INSERT, and a drift check compares the same population, so a missing subject, an extra or conflicting row cannot hide behind
-- the subjects the copy happens to contain. The contract values equal the Python read contract (a test pins both).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_facts_live_population(p_chart uuid)
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
  SELECT public.ka_gochara_search_facts_copy(
    p_chart,
    COALESCE((SELECT array_agg(f.fact_id ORDER BY f.fact_id COLLATE "C")
                FROM public.chart_facts f
               WHERE f.chart_id = p_chart
                 AND f.ayanamsha_id = 'lahiri_chitrapaksha' AND f.fact_category = 'graha_position' AND f.fact_key = 'longitude_sidereal'
                 AND f.fact_subject IN ('LAGNA', 'SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN')
                 AND f.fact_value_num IS NOT NULL),
             ARRAY[]::text[]));
$$;

-- ── 4. the DASHA rows: ordinal lord path, one element per row, the live view by NATURAL KEY ────────────────────────────────────────
-- ordinal_path = the 1-based INDEX of the period among its siblings (same parent, same build, ordered by start) at every level from the root MD down
-- ('3.2.7' = the 7th pratyantara of the 2nd antardasha of the 3rd mahadasha); lord_path = the lords on the same path ('venus/mars/sun'). The
-- ORDINAL path is cycle-specific (a repeated lord in the next 120-year cycle has another index), so a moved boundary is named "the 2nd AD of the 3rd
-- MD moved by N seconds", never mislabelled by a lord that recurs. The parent is a natural pointer (level, start), never parent_row_id.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_path(p_chart uuid, p_row uuid)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH RECURSIVE up(id, parent, lord, depth) AS (
    SELECT d.dasha_row_id, d.parent_row_id, lower(d.lord_graha), 1
    FROM public.chart_dashas d WHERE d.chart_id = p_chart AND d.dasha_row_id = p_row
    UNION ALL
    SELECT d.dasha_row_id, d.parent_row_id, lower(d.lord_graha), up.depth + 1
    FROM up JOIN public.chart_dashas d ON d.chart_id = p_chart AND d.dasha_row_id = up.parent
    WHERE up.depth < 8)
  SELECT string_agg(lord, '/' ORDER BY depth DESC) FROM up;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_ordinal_path(p_chart uuid, p_row uuid)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH RECURSIVE up(id, parent, idx, depth) AS (
    SELECT d.dasha_row_id, d.parent_row_id,
           (SELECT count(*) FROM public.chart_dashas s
             WHERE s.chart_id = d.chart_id AND s.ayanamsha_id IS NOT DISTINCT FROM d.ayanamsha_id AND s.system_id IS NOT DISTINCT FROM d.system_id
               AND s.level_n = d.level_n AND s.build_id IS NOT DISTINCT FROM d.build_id AND s.parent_row_id IS NOT DISTINCT FROM d.parent_row_id
               AND COALESCE(s.kp_sublevel, '') = COALESCE(d.kp_sublevel, '') AND s.start_iso <= d.start_iso), 1
    FROM public.chart_dashas d WHERE d.chart_id = p_chart AND d.dasha_row_id = p_row
    UNION ALL
    SELECT d.dasha_row_id, d.parent_row_id,
           (SELECT count(*) FROM public.chart_dashas s
             WHERE s.chart_id = d.chart_id AND s.ayanamsha_id IS NOT DISTINCT FROM d.ayanamsha_id AND s.system_id IS NOT DISTINCT FROM d.system_id
               AND s.level_n = d.level_n AND s.build_id IS NOT DISTINCT FROM d.build_id AND s.parent_row_id IS NOT DISTINCT FROM d.parent_row_id
               AND COALESCE(s.kp_sublevel, '') = COALESCE(d.kp_sublevel, '') AND s.start_iso <= d.start_iso), up.depth + 1
    FROM up JOIN public.chart_dashas d ON d.chart_id = p_chart AND d.dasha_row_id = up.parent
    WHERE up.depth < 8)
  SELECT string_agg(idx::text, '.' ORDER BY depth DESC) FROM up;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_element(p_chart uuid, p_row uuid)
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
  SELECT jsonb_build_object(
    'key', jsonb_build_object('ayanamsha_id', d.ayanamsha_id, 'system_id', d.system_id, 'level_n', d.level_n,
                              'start_iso', d.start_iso, 'kp_sublevel', COALESCE(d.kp_sublevel, '')),
    'content', jsonb_build_object('lord_graha', lower(d.lord_graha), 'end_iso', d.end_iso, 'parent_level_n', p.level_n,
                                  'parent_start_iso', p.start_iso, 'lord_path', public.ka_gochara_search_dasha_path(p_chart, d.dasha_row_id),
                                  'ordinal_path', public.ka_gochara_search_dasha_ordinal_path(p_chart, d.dasha_row_id)),
    'metadata', jsonb_build_object('dasha_row_id', d.dasha_row_id, 'build_id', d.build_id, 'parent_row_id', d.parent_row_id,
                                   'verification_pass_status', d.verification_pass_status, 'engine_version', d.engine_version))
  FROM public.chart_dashas d
  LEFT JOIN public.chart_dashas p ON p.chart_id = d.chart_id AND p.dasha_row_id = d.parent_row_id
  WHERE d.chart_id = p_chart AND d.dasha_row_id = p_row;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_copy(p_chart uuid, p_ids uuid[])
RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
DECLARE missing int; r jsonb;
BEGIN
  SELECT count(*) INTO missing FROM unnest(p_ids) AS i(id)
  WHERE NOT EXISTS (SELECT 1 FROM public.chart_dashas d WHERE d.chart_id = p_chart AND d.dasha_row_id = i.id);
  IF missing > 0 THEN
    RAISE EXCEPTION 'ka_gochara_search_dasha_copy: % consumed daśā row id(s) do not exist for chart % — a snapshot is built from existing rows', missing, p_chart;
  END IF;
  SELECT COALESCE(jsonb_agg(s.el ORDER BY public.ka_gochara_canonical_json(s.el -> 'key') COLLATE "C"), '[]'::jsonb) INTO r
  FROM (SELECT public.ka_gochara_search_dasha_element(p_chart, i.id) AS el FROM unnest(p_ids) AS i(id)) s;
  RETURN r;
END;
$$;

-- The REQUIRED daśā population (Codex round 2, P1): a CONTRACT FIXED IN THE DATABASE, independent of the submitted ids, of the copy and of the writer — every
-- Vimśottarī row of the canonical ayanamsha at the three levels the read contract names (MD, AD, PD), at the consumed tier (two_pass_verified), overlapping the
-- BOUND MANIFEST HORIZON. Omitting a whole level, a period, or adding a foreign row is refused at INSERT. Builds are not filtered: a second build is an extra
-- row, i.e. a conflict. The contract values equal the Python read contract (a test pins both).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_required_population(p_chart uuid, p_horizon tstzrange)
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
  SELECT COALESCE(jsonb_agg(s.el ORDER BY public.ka_gochara_canonical_json(s.el -> 'key') COLLATE "C", s.el #>> '{metadata,dasha_row_id}'), '[]'::jsonb)
  FROM (
    SELECT public.ka_gochara_search_dasha_element(p_chart, d.dasha_row_id) AS el
    FROM public.chart_dashas d
    WHERE d.chart_id = p_chart AND d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.system_id = 'vimshottari' AND d.level_n IN (1, 2, 3)
      AND d.verification_pass_status = 'two_pass_verified'
      AND d.start_iso < upper(p_horizon) AND d.end_iso > lower(p_horizon)) s;
$$;

-- The live view a DRIFT check compares with the copy (Codex round 2, P1 + P2-4): (a) EVERY live row at a copy element's NATURAL KEY, whatever its tier or build
-- (a tier-only change is a soft metadata difference, never a "missing" row), plus (b) every row of the REQUIRED scope (same contract as above, so a whole level
-- the copy lacks is visible) whose natural key the copy does not name, i.e. an EXTRA row. The scope is the contract, never derived from the copy.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_live_population(p_chart uuid, p_copy jsonb, p_horizon tstzrange)
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
  SELECT COALESCE(jsonb_agg(s.el ORDER BY public.ka_gochara_canonical_json(s.el -> 'key') COLLATE "C", s.el #>> '{metadata,dasha_row_id}'), '[]'::jsonb)
  FROM (
    SELECT public.ka_gochara_search_dasha_element(p_chart, d.dasha_row_id) AS el
    FROM public.chart_dashas d
    WHERE d.chart_id = p_chart
      AND EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS c(e)
                   WHERE c.e #>> '{key,ayanamsha_id}' = d.ayanamsha_id AND c.e #>> '{key,system_id}' = d.system_id
                     AND (c.e #>> '{key,level_n}')::int = d.level_n AND (c.e #>> '{key,start_iso}')::timestamptz = d.start_iso
                     AND c.e #>> '{key,kp_sublevel}' = COALESCE(d.kp_sublevel, ''))
    UNION ALL
    SELECT public.ka_gochara_search_dasha_element(p_chart, d.dasha_row_id)
    FROM public.chart_dashas d
    WHERE d.chart_id = p_chart AND d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.system_id = 'vimshottari' AND d.level_n IN (1, 2, 3)
      AND d.verification_pass_status = 'two_pass_verified'
      AND d.start_iso < upper(p_horizon) AND d.end_iso > lower(p_horizon)
      AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS c(e)
                       WHERE c.e #>> '{key,ayanamsha_id}' = d.ayanamsha_id AND c.e #>> '{key,system_id}' = d.system_id
                         AND (c.e #>> '{key,level_n}')::int = d.level_n AND (c.e #>> '{key,start_iso}')::timestamptz = d.start_iso
                         AND c.e #>> '{key,kp_sublevel}' = COALESCE(d.kp_sublevel, ''))) s;
$$;

-- ── 5. the copy is PRODUCED BY THE DATABASE (BEFORE INSERT, before 1206's write guard) ────────────────────────────────────────────────
-- Codex round 1 ruling 2: matching digests prove consistency, not authenticity (the builder holds INSERT and could submit a consistent false copy). So the
-- builder submits only KEYS (consumed_fact_ids, consumed_dasha_row_ids) and the identity digests it computed; this trigger BUILDS consumed_fact_rows /
-- consumed_dasha_rows and the metadata digests itself from the live rows IN THE INSERT TRANSACTION, OVERWRITING whatever was submitted in those columns,
-- and refuses unless (a) the submitted identity digests are the digests of what it built, and (b) the built copy is the COMPLETE live population of what it
-- captures, in both directions (a missing, extra or conflicting row refuses by name). Why build rather than compare: a submitted copy that is compared
-- element by element still leaves JSON rendering differences and the builder in the content path; building removes both, at a cost of one read of at most
-- about a thousand rows. It fires BEFORE 1206's write guard (named 0z: after 0_statement_lock, before 1_write_guard) so that guard checks input_digest
-- against digests that are the database's own.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_input_snapshot_copy_build()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE facts jsonb; dashas jsonb; l1 text; dd text; hz tstzrange;
BEGIN
  IF NEW.consumed_fact_ids IS NULL OR NEW.consumed_dasha_row_ids IS NULL THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): consumed_fact_ids and consumed_dasha_row_ids are the KEYS the database builds the copy from';
  END IF;
  SELECT p.horizon INTO hz FROM public.kala_gochara_publication p WHERE p.chart_id = NEW.chart_id AND p.generation = NEW.generation;
  IF hz IS NULL THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): no bound manifest horizon for this generation — the population a snapshot must cover is the manifest''s, not the copy''s own span';
  END IF;
  facts := public.ka_gochara_search_facts_copy(NEW.chart_id, NEW.consumed_fact_ids);            -- raises by name if a consumed id does not exist
  dashas := public.ka_gochara_search_dasha_copy(NEW.chart_id, NEW.consumed_dasha_row_ids);
  l1 := public.ka_gochara_search_copy_digest(facts, 'content');
  dd := public.ka_gochara_search_copy_digest(dashas, 'content');
  IF NEW.l1_facts_digest IS DISTINCT FROM l1 OR NEW.dasha_digest IS DISTINCT FROM dd THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): l1_facts_digest / dasha_digest are not the identity digests of the live rows the submitted keys name';
  END IF;
  IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_facts_live_population(NEW.chart_id), 'content') IS DISTINCT FROM l1 THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): the consumed fact rows are not the COMPLETE live population (a missing, extra or conflicting row of the same subjects exists)';
  END IF;
  IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_required_population(NEW.chart_id, hz), 'content') IS DISTINCT FROM dd THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): the consumed daśā rows are not the COMPLETE live population (a missing, extra or conflicting period overlapping the consumed span exists)';
  END IF;
  NEW.consumed_fact_rows := facts;
  NEW.consumed_dasha_rows := dashas;
  NEW.l1_facts_metadata_digest := public.ka_gochara_search_copy_digest(facts, 'metadata');
  NEW.dasha_metadata_digest := public.ka_gochara_search_copy_digest(dashas, 'metadata');
  RETURN NEW;
END;
$$;
CREATE TRIGGER ka_gochara_search_input_snapshot_0z_copy_build
  BEFORE INSERT ON public.ka_gochara_search_input_snapshot
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_search_input_snapshot_copy_build();

-- ── 6. the snapshot-bound Moon-resolved domain now reads the snapshot's COPY ──────────────────────────────────────────────────────
-- (the 1232 function with the join to live chart_dashas replaced by the stored daśā rows; a LEGACY snapshot without a copy is built on the fly
-- from its ids, as before)
CREATE OR REPLACE FUNCTION public.ka_gochara_search_moon_resolved_domain(
  p_chart uuid, p_generation text, p_class text, p_ob uuid)
RETURNS tstzmultirange LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT COALESCE(
    (SELECT range_agg(tstzrange((c.e #>> '{key,start_iso}')::timestamptz, (c.e #>> '{content,end_iso}')::timestamptz, '[)'))
       FROM public.ka_gochara_search_input_snapshot s
       JOIN public.ka_gochara_search_obligation o
         ON (o.chart_id, o.generation, o.event_class, o.ob_id) = (p_chart, p_generation, p_class, p_ob)
       CROSS JOIN LATERAL jsonb_array_elements(
         COALESCE(s.consumed_dasha_rows, public.ka_gochara_search_dasha_copy(s.chart_id, s.consumed_dasha_row_ids))) AS c(e)
      WHERE s.chart_id = p_chart AND s.generation = p_generation
        AND o.agent ~ '^period_lord:(md|ad|pd)$'
        AND (c.e #>> '{key,level_n}')::int = CASE substr(o.agent, 13) WHEN 'md' THEN 1 WHEN 'ad' THEN 2 ELSE 3 END
        AND lower(c.e #>> '{content,lord_graha}') = 'moon')
    * (SELECT i.horizon::tstzmultirange FROM public.ka_gochara_search_inventory i
        WHERE (i.chart_id, i.generation, i.event_class) = (p_chart, p_generation, p_class)),
    '{}'::tstzmultirange);
$$;

-- ── 7. the completeness function: the 1232 body with ONE block replaced (the L1 drift check) ─────────────────────────────────────
CREATE OR REPLACE FUNCTION public.ka_gochara_search_completeness_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, violation text, detail text)
LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE pub record; snap record; live_l1 text; live_dasha text; e text;
BEGIN
  SELECT p.horizon, p.input_generation_vector, p.convention_id INTO pub
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
    IF snap.consumed_fact_rows IS NULL OR snap.consumed_dasha_rows IS NULL THEN
      -- a LEGACY snapshot (written before 1305, no copy): the 1206 id-and-whole-row digests, unchanged ... and a FIRST SEAL needs the copy (Codex round 2, P2):
      -- this function runs for the first-seal branch of the seal trigger and for the candidate gate; the REPLAY branch calls ka_gochara_search_replay_violations
      -- instead, so an already sealed legacy generation replays exactly as before.
      RETURN QUERY SELECT '*'::text, 'input_snapshot_without_copy'::text, 'the search-input snapshot is the LEGACY shape (ids only, no copy of the L1 rows it consumed): a first seal needs a self-contained snapshot (apply 1305 and rebuild)'::text;
      live_l1 := public.ka_gochara_search_l1_facts_digest(p_chart, snap.consumed_fact_ids);
      live_dasha := public.ka_gochara_search_dasha_digest(p_chart, snap.consumed_dasha_row_ids);
      IF live_l1 IS DISTINCT FROM snap.l1_facts_digest THEN
        RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed L1 fact rows no longer match the snapshot digest'::text;
      END IF;
      IF live_dasha IS DISTINCT FROM snap.dasha_digest THEN
        RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed dasha rows no longer match the snapshot digest'::text;
      END IF;
    ELSE
      -- 1305 (G12 route 1): the live rows are looked up by their NATURAL KEY and compared on their CONTENT only. A later L1 rebuild
      -- that re-issues row ids, build ids, engine versions or adds columns changes none of this; a changed VALUE or a missing row does.
      -- A metadata-only difference is NOT a violation here (it is reported by the staleness check, never blocking).
      IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_facts_live_population(p_chart), 'content')
           IS DISTINCT FROM snap.l1_facts_digest THEN
        RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed L1 fact rows no longer match the snapshot: a value changed, a row is gone, or an extra/conflicting row exists (identity digest of the complete live population)'::text;
      END IF;
      IF public.ka_gochara_search_copy_digest(public.ka_gochara_search_dasha_live_population(p_chart, snap.consumed_dasha_rows,
           (SELECT q.horizon FROM public.kala_gochara_publication q WHERE q.chart_id = p_chart AND q.generation = p_generation)), 'content')
           IS DISTINCT FROM snap.dasha_digest THEN
        RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, 'consumed dasha rows no longer match the snapshot: a value changed, a row is gone, or an extra/conflicting row exists (identity digest of the complete live population)'::text;
      END IF;
    END IF;
    FOREACH e IN ARRAY snap.av_declarations LOOP
      IF public.ka_gochara_search_av_entry(left(e, GREATEST(length(e) - 65, 0))) IS DISTINCT FROM e THEN
        RETURN QUERY SELECT '*'::text, 'input_snapshot_drift'::text, ('AV declaration entry no longer matches: ' || e)::text;
      END IF;
    END LOOP;
    IF pub.input_generation_vector IS DISTINCT FROM snap.input_generation_vector THEN
      RETURN QUERY SELECT '*'::text, 'input_vector_mismatch'::text, 'snapshot vector differs from the published manifest vector'::text;
    END IF;
    -- R2: the snapshot's sky convention is bound to BOTH the publication's and every claimed
    -- event_class partition's legacy convention through the immutable bridge
    RETURN QUERY
    SELECT '*'::text, 'convention_bridge_missing'::text, ('publication legacy convention ' || COALESCE(pub.convention_id, 'NULL'))::text
    WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_convention_bridge b WHERE b.kala_convention_id = pub.convention_id);
    RETURN QUERY
    SELECT '*'::text, 'convention_mismatch'::text,
           ('publication legacy convention ' || pub.convention_id || ' is bridged to ' || b.sky_convention_id ||
            ' but the snapshot is bound to ' || snap.convention_id)::text
    FROM public.ka_gochara_convention_bridge b
    WHERE b.kala_convention_id = pub.convention_id AND b.sky_convention_id IS DISTINCT FROM snap.convention_id;
    RETURN QUERY
    SELECT c.partition_key, 'convention_bridge_missing'::text, ('partition legacy convention ' || c.convention_id)::text
    FROM public.kala_gochara_coverage c
    WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind = 'event_class'
      AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_convention_bridge b WHERE b.kala_convention_id = c.convention_id);
    RETURN QUERY
    SELECT c.partition_key, 'convention_mismatch'::text,
           ('partition legacy convention ' || c.convention_id || ' is bridged to ' || b.sky_convention_id ||
            ' but the snapshot is bound to ' || snap.convention_id)::text
    FROM public.kala_gochara_coverage c
    JOIN public.ka_gochara_convention_bridge b ON b.kala_convention_id = c.convention_id
    WHERE c.chart_id = p_chart AND c.generation = p_generation AND c.partition_kind = 'event_class'
      AND b.sky_convention_id IS DISTINCT FROM snap.convention_id;
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

  -- version scope (F-3): per class and path AT MOST ONE version is 'included' — nothing may be
  -- searched twice under two versions of the same rule path and silently double-counted.
  RETURN QUERY
  SELECT p.event_class, 'multiple_included_versions'::text,
         (lower(p.path_id) || '@' || string_agg(p.rule_version, ',' ORDER BY p.rule_version))::text
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.disposition = 'included'
  GROUP BY p.event_class, lower(p.path_id)
  HAVING count(DISTINCT p.rule_version) > 1;
  -- 'superseded_by_version' asserts that ANOTHER version of the same path carries the search: a
  -- supersession claim with no included superseder is a coverage hole wearing a non-degrading
  -- reason (no ruling_ref), so it needs its own detector (CLAUDE.md §N.8).
  RETURN QUERY
  SELECT p.event_class, 'superseded_without_included_version'::text,
         (lower(p.path_id) || '@' || p.rule_version)::text
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation
    AND p.disposition = 'excluded' AND p.exclusion_reason = 'superseded_by_version'
    AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_path_pin q
                    WHERE q.chart_id = p.chart_id AND q.generation = p.generation
                      AND q.event_class = p.event_class AND lower(q.path_id) = lower(p.path_id)
                      AND q.rule_version <> p.rule_version AND q.disposition = 'included');

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

  -- committed obligation set == stored obligations, per pin, on the FULL key
  -- (chart, generation, class, path, rule_version): another path's — or another version's —
  -- obligations can never satisfy this pin's commitment (Codex R1). The detail names, for each
  -- committed id that is not stored under THIS pin, whether it is stored under a DIFFERENT pin.
  RETURN QUERY
  SELECT p.event_class, 'committed_set_mismatch'::text,
         (p.path_id || '@' || p.rule_version || ' committed-not-stored=' ||
          COALESCE((SELECT string_agg(c::text || COALESCE('(stored-under-' || fo.path_id || '@' || fo.rule_version || ')', ''), ',' ORDER BY c::text)
                    FROM unnest(p.committed_ob_ids) c
                    LEFT JOIN public.ka_gochara_search_obligation fo
                      ON (fo.chart_id, fo.generation, fo.event_class, fo.ob_id) = (p.chart_id, p.generation, p.event_class, c)
                    WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                                      WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version, o.ob_id)
                                          = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version, c))), '') ||
          ' stored-not-committed=' ||
          COALESCE((SELECT string_agg(o.ob_id::text, ',' ORDER BY o.ob_id::text) FROM public.ka_gochara_search_obligation o
                    WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version)
                        = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                      AND NOT (o.ob_id = ANY (p.committed_ob_ids))), ''))::text
  FROM public.ka_gochara_search_path_pin p
  WHERE p.chart_id = p_chart AND p.generation = p_generation
    AND ( EXISTS (SELECT 1 FROM unnest(p.committed_ob_ids) c
                  WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_obligation o
                                    WHERE (o.chart_id, o.generation, o.event_class, o.path_id, o.rule_version, o.ob_id)
                                        = (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version, c)))
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
                        AND v.state IN ('searched_complete','searched_unqualified','excluded_moon_tier')), '{}'::tstzmultirange))::text)::text
  FROM public.ka_gochara_search_obligation o
  JOIN public.ka_gochara_search_inventory i
    ON (i.chart_id, i.generation, i.event_class) = (o.chart_id, o.generation, o.event_class)
  WHERE o.chart_id = p_chart AND o.generation = p_generation
    AND NOT isempty(i.horizon::tstzmultirange -
          COALESCE((SELECT range_agg(v.search_range) FROM public.ka_gochara_search_interval v
                    WHERE (v.chart_id, v.generation, v.event_class, v.ob_id) = (o.chart_id, o.generation, o.event_class, o.ob_id)
                      AND v.state IN ('searched_complete','searched_unqualified','excluded_moon_tier')), '{}'::tstzmultirange));
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

  -- AM-14 (1232): the Moon-scope accounting — stored exclusion = derived Moon-resolved domain; scope bound to the manifest
  RETURN QUERY SELECT * FROM public.ka_gochara_search_moon_scope_violations(p_chart, p_generation);
END;
$$;

-- ── 8. grants (only to roles that exist; production revokes PUBLIC EXECUTE on functions amjis_app creates, 1220) ──────────────────
DO $$
DECLARE r text; fn text;
BEGIN
  FOREACH r IN ARRAY ARRAY['data_plane_builder', 'gochara_verifier', 'gochara_sealer'] LOOP
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = r) THEN
      FOREACH fn IN ARRAY ARRAY[
        'public.ka_gochara_search_copy_digest(jsonb,text)', 'public.ka_gochara_search_normalize_numbers(jsonb)',
        'public.ka_gochara_search_facts_copy(uuid,text[])', 'public.ka_gochara_search_facts_live_population(uuid)',
        'public.ka_gochara_search_dasha_path(uuid,uuid)', 'public.ka_gochara_search_dasha_ordinal_path(uuid,uuid)',
        'public.ka_gochara_search_dasha_element(uuid,uuid)', 'public.ka_gochara_search_dasha_copy(uuid,uuid[])',
        'public.ka_gochara_search_dasha_required_population(uuid,tstzrange)', 'public.ka_gochara_search_dasha_live_population(uuid,jsonb,tstzrange)'] LOOP
        EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO %I', fn, r);
      END LOOP;
    END IF;
  END LOOP;
END;
$$;

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
BEGIN
  IF (SELECT count(*) FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'ka_gochara_search_input_snapshot'
        AND column_name IN ('consumed_fact_rows', 'consumed_dasha_rows', 'l1_facts_metadata_digest', 'dasha_metadata_digest')) <> 4 THEN
    RAISE EXCEPTION 'migration 1305 post-apply check failed: a snapshot copy column is missing';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'kgsis_l1_copy_ck' AND conrelid = 'public.ka_gochara_search_input_snapshot'::regclass) THEN
    RAISE EXCEPTION 'migration 1305 post-apply check failed: kgsis_l1_copy_ck is missing';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'ka_gochara_search_input_snapshot_0z_copy_build' AND NOT tgisinternal) THEN
    RAISE EXCEPTION 'migration 1305 post-apply check failed: the copy-build trigger is missing';
  END IF;
  IF pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) NOT LIKE '%ka_gochara_search_dasha_live_population%'
     OR pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) NOT LIKE '%ka_gochara_search_moon_scope_violations%' THEN
    RAISE EXCEPTION 'migration 1305 post-apply check failed: the completeness function is not the 1232 body with the 1305 drift block';
  END IF;
  IF pg_get_functiondef('public.ka_gochara_search_moon_resolved_domain(uuid,text,text,uuid)'::regprocedure) NOT LIKE '%consumed_dasha_rows%' THEN
    RAISE EXCEPTION 'migration 1305 post-apply check failed: the Moon-resolved domain does not read the snapshot copy';
  END IF;
  RAISE NOTICE 'migration 1305: presence checks passed';
END;
$$;

COMMENT ON COLUMN public.ka_gochara_search_input_snapshot.consumed_fact_rows IS
  '1305 (G12 route 1): COPY of the consumed chart_facts rows as {key, content, metadata}; l1_facts_digest is the IDENTITY digest of the content blocks; ids are provenance only.';
COMMENT ON COLUMN public.ka_gochara_search_input_snapshot.consumed_dasha_rows IS
  '1305 (G12 route 1): COPY of the consumed chart_dashas rows keyed by natural key; dasha_digest is the IDENTITY digest of the content blocks; row ids and build ids are metadata.';
