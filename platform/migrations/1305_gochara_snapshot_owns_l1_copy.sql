-- Migration 1305: G12 route 1 — the search-input snapshot OWNS a COPY of the L1 rows it consumed. ADDITIVE on top of 1206/1232.
-- Pravāha B (Stream B, Śāstra), steward G12-ROUTE1 (2026-10-05), design note
-- 00_ARCHITECTURE/briefs/pravaha/decisions/G12_ROUTE1_SNAPSHOT_DESIGN_v1_0.md. STATUS: HOLD (protected window, with G8's 1306).
--
-- WHY
-- ═══
-- 1206's snapshot POINTS at its L1 inputs (consumed_fact_ids text[], consumed_dasha_row_ids uuid[]) and digests the WHOLE rows (every column
-- but computed_at, including row ids, build ids and parent ids). Every ga_dashas / ga_positions rebuild re-issues `build_id` (and may bump
-- `engine_version`) on every row it writes, and those columns are inside the 1206 digests. (`chart_dashas.dasha_row_id` itself is a UUID5 that
-- the L1 writer stabilises across rebuilds of the same natural key, so the row ids usually survive; the premise does not rest on them.) So after
-- ANY later L1 rebuild a sealed generation reads every consumed row as changed: the completeness function reports input_snapshot_drift forever,
-- and a sealed generation cannot be repaired. Citing fact ids does not help (the facts digest hashes `build_id` too). The snapshot must therefore
-- carry what it consumed, and say which part of it is identity and which is metadata.
--
-- WHAT THIS DOES (and what it deliberately does NOT do)
-- ════════════════════════════════════════════════════
--   1. Four additive columns on ka_gochara_search_input_snapshot: consumed_fact_rows / consumed_dasha_rows (jsonb arrays of
--      {key, content, metadata}) and l1_facts_metadata_digest / dasha_metadata_digest. consumed_fact_ids / consumed_dasha_row_ids stay as the KEYS
--      the builder submits (and as provenance). A NOT VALID CHECK makes the copies mandatory for every NEW row (0 snapshots exist on production; no
--      backfill; a legacy row without a copy keeps the 1206 behaviour).
--   2. IDENTITY vs METADATA. The identity (key + content) holds ONLY values of rows the snapshot consumed: fact = natural key (ayanamsha, category,
--      key, subject) + value text / num / jsonb (every number scale-trimmed) and unit; daśā = natural key (ayanamsha, system, level, start,
--      kp_sublevel) + lord, end, the parent's level and start, and the lord path (a function of the row and of its ancestors, which are consumed
--      with it). metadata = row ids, parent row id, build, tier, engine, citation columns AND the ordinal path (it counts every sibling in the
--      table, including periods outside the horizon that were never consumed; it names a moved boundary and decides nothing). The existing columns
--      l1_facts_digest / dasha_digest hold the IDENTITY digest (so input_digest and every inventory / ledger digest keep their recipe); the METADATA
--      digest is informational and never enters input_digest. THE RECIPE FREEZES AT THE FIRST PRODUCTION CAPTURE.
--   3. THE COPY IS PRODUCED BY THE DATABASE AND VALIDATED AS STORED: a BEFORE INSERT trigger (named 0z, so it fires before 1206's write guard) BUILDS
--      the copy and the metadata digests from the live rows named by the submitted keys, in ONE statement (one upstream snapshot), overwriting
--      whatever was submitted in those columns, and then judges THE VALUE IT STORES: (a) the capture CONTRACT over the copy itself
--      (ka_gochara_search_copy_violations, a PURE function of the copy and the bound manifest horizon: the ten natal longitude facts each once;
--      Vimśottarī MD, AD, PD of the canonical ayanamsha, each level unique by start, contiguous and covering the horizon; the hierarchy closed
--      INSIDE the copy by natural pointer AND by row id; and the copy's own recorded tier and one build); (b) the copy is the WHOLE upstream scope
--      and nothing else (every upstream row of the scope WHATEVER its tier or build; a row the copy lacks is refused by its key); (c) the submitted
--      identity digests are the copy's. Every refusal is by name.
--   4. AFTER CAPTURE TIER AND BUILD ARE METADATA. ka_gochara_search_snapshot_copy_violations reports three things and reads no tier for any of them:
--      input_snapshot_copy_inconsistent (the STORED copy no longer recomputes to its STORED digests, or no longer satisfies the contract: a statement
--      about the row, nothing upstream is read), input_snapshot_required_scope (the upstream scope is structurally broken) and input_snapshot_drift
--      (the identity of the upstream scope is not the stored one: a changed value, a missing row, or an extra row of ANY tier).
--   5. New functions (nothing dropped, nothing renamed): ka_gochara_search_copy_digest, _normalize_numbers, _facts_copy, _facts_live_population,
--      _dasha_path, _dasha_ordinal_path, _dasha_element, _dasha_copy, _dasha_live_population, _copy_violations, _copy_difference,
--      _snapshot_copy_violations, and the copy-build trigger function.
--   6. Replaces TWO existing functions: ka_gochara_search_moon_resolved_domain (reads the copy) and ka_gochara_search_completeness_violations (the
--      1232 body, EXACTLY, with one block replaced: a copy-bearing snapshot is judged by ka_gochara_search_snapshot_copy_violations; a legacy
--      snapshot keeps the 1206 check but is REFUSED at first seal with its own violation, `input_snapshot_without_copy`; replay is unchanged).
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
-- grants are required, not decoration. ONE grant is on a 1206 function: ka_gochara_search_input_digest, which the copy-consistency detector
-- recomputes as the invoker (the builder already holds it from 1206; the verifier and the sealer did not). No table grant changes: the new
-- columns inherit the table-level privileges.
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
-- changes the digest. Key and block are canonical JSON (sorted keys), so the digest does not depend on array or key order. The lines are ordered by the
-- FULL line (key AND block hash), so two elements that share a key (a conflicting duplicate) still give ONE digest whatever order they arrive in: the
-- digest is a function of the MULTISET of lines, nothing else (round 6, R10).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_copy_digest(p_copy jsonb, p_block text)
RETURNS text LANGUAGE plpgsql IMMUTABLE SET search_path = pg_catalog, public AS $$
BEGIN
  IF p_block NOT IN ('content', 'metadata') THEN
    RAISE EXCEPTION 'ka_gochara_search_copy_digest: block must be content or metadata, got %', p_block;
  END IF;
  RETURN public.ka_gochara_sha256_hex(COALESCE((
    SELECT string_agg(l.line, E'\n' ORDER BY l.line COLLATE "C")
    FROM (SELECT public.ka_gochara_canonical_json(e.value -> 'key') || '|' ||
                 CASE WHEN jsonb_typeof(e.value -> p_block) = 'object'
                      THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(e.value -> p_block)) ELSE 'MISSING' END AS line
          FROM jsonb_array_elements(COALESCE(p_copy, '[]'::jsonb)) AS e(value)) l), ''));
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

-- The UPSTREAM fact scope: every natal longitude fact of the canonical ayanamsha for the ten subjects the read contract names (LAGNA, SUN, MOON, MAR, MER, JUP,
-- VEN, SAT, RAH_MEAN, KET_MEAN; fact_category graha_position, fact_key longitude_sidereal; a row without a numeric value is not an operand). It is a SCOPE, not a
-- judgement: it filters by what a row IS (its natural key), never by a verification tier or a build. The contract values equal the Python read contract (a test
-- pins both).
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

-- ── 4. the DASHA rows: one element per row ────────────────────────────────────────────────────────────────────────────────────────────
-- lord_path = the lords from the root MD down to the row ('venus/mars/sun'): it is a function of the row and of its ANCESTORS, which a snapshot always
-- consumes with it (a period inside the horizon has its parent over the horizon too), so it belongs to the IDENTITY. ordinal_path = the 1-based INDEX of the
-- period among its siblings at every level ('3.2.7' = the 7th pratyantara of the 2nd antardasha of the 3rd mahadasha): it counts EVERY sibling in the table,
-- including periods wholly outside the horizon that the snapshot never consumed, so it is METADATA (round 6, R3): adding or removing an upstream period the
-- search never read must not change the identity of what it did read. It only serves to NAME a moved boundary. The parent is a natural pointer (level, start).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_path(p_chart uuid, p_row uuid)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH RECURSIVE up(id, parent, lord, depth, ay, sy) AS (
    SELECT d.dasha_row_id, d.parent_row_id, lower(d.lord_graha), 1, d.ayanamsha_id, d.system_id
    FROM public.chart_dashas d WHERE d.chart_id = p_chart AND d.dasha_row_id = p_row
    UNION ALL
    SELECT d.dasha_row_id, d.parent_row_id, lower(d.lord_graha), up.depth + 1, up.ay, up.sy
    FROM up JOIN public.chart_dashas d ON d.chart_id = p_chart AND d.dasha_row_id = up.parent
      AND d.ayanamsha_id IS NOT DISTINCT FROM up.ay AND d.system_id IS NOT DISTINCT FROM up.sy      -- an ancestor of ANOTHER ayanamsha/system is not an ancestor
    WHERE up.depth < 8)
  SELECT string_agg(lord, '/' ORDER BY depth DESC) FROM up;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_ordinal_path(p_chart uuid, p_row uuid)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH RECURSIVE up(id, parent, idx, depth, ay, sy) AS (
    SELECT d.dasha_row_id, d.parent_row_id,
           (SELECT count(*) FROM public.chart_dashas s
             WHERE s.chart_id = d.chart_id AND s.ayanamsha_id = d.ayanamsha_id AND s.system_id = d.system_id        -- plain equality: indexable (both are NOT NULL in L1)
               AND s.level_n = d.level_n AND s.build_id IS NOT DISTINCT FROM d.build_id AND s.parent_row_id IS NOT DISTINCT FROM d.parent_row_id
               AND COALESCE(s.kp_sublevel, '') = COALESCE(d.kp_sublevel, '') AND s.start_iso <= d.start_iso), 1, d.ayanamsha_id, d.system_id
    FROM public.chart_dashas d WHERE d.chart_id = p_chart AND d.dasha_row_id = p_row
    UNION ALL
    SELECT d.dasha_row_id, d.parent_row_id,
           (SELECT count(*) FROM public.chart_dashas s
             WHERE s.chart_id = d.chart_id AND s.ayanamsha_id = d.ayanamsha_id AND s.system_id = d.system_id        -- plain equality: indexable (both are NOT NULL in L1)
               AND s.level_n = d.level_n AND s.build_id IS NOT DISTINCT FROM d.build_id AND s.parent_row_id IS NOT DISTINCT FROM d.parent_row_id
               AND COALESCE(s.kp_sublevel, '') = COALESCE(d.kp_sublevel, '') AND s.start_iso <= d.start_iso), up.depth + 1, up.ay, up.sy
    FROM up JOIN public.chart_dashas d ON d.chart_id = p_chart AND d.dasha_row_id = up.parent
      AND d.ayanamsha_id IS NOT DISTINCT FROM up.ay AND d.system_id IS NOT DISTINCT FROM up.sy
    WHERE up.depth < 8)
  SELECT string_agg(idx::text, '.' ORDER BY depth DESC) FROM up;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_element(p_chart uuid, p_row uuid)
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
  SELECT jsonb_build_object(
    'key', jsonb_build_object('ayanamsha_id', d.ayanamsha_id, 'system_id', d.system_id, 'level_n', d.level_n,
                              'start_iso', d.start_iso, 'kp_sublevel', COALESCE(d.kp_sublevel, '')),
    'content', jsonb_build_object('lord_graha', lower(d.lord_graha), 'end_iso', d.end_iso, 'parent_level_n', p.level_n,
                                  'parent_start_iso', p.start_iso, 'lord_path', public.ka_gochara_search_dasha_path(p_chart, d.dasha_row_id)),
    'metadata', jsonb_build_object('dasha_row_id', d.dasha_row_id, 'build_id', d.build_id, 'parent_row_id', d.parent_row_id,
                                   'verification_pass_status', d.verification_pass_status, 'engine_version', d.engine_version,
                                   'ordinal_path', public.ka_gochara_search_dasha_ordinal_path(p_chart, d.dasha_row_id)))
  FROM public.chart_dashas d
  LEFT JOIN public.chart_dashas p ON p.chart_id = d.chart_id AND p.dasha_row_id = d.parent_row_id
    AND p.ayanamsha_id IS NOT DISTINCT FROM d.ayanamsha_id AND p.system_id IS NOT DISTINCT FROM d.system_id        -- a parent of another ayanamsha/system never enters the copied ancestry
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
  SELECT COALESCE(jsonb_agg(s.el ORDER BY public.ka_gochara_canonical_json(s.el -> 'key') COLLATE "C", s.el #>> '{metadata,dasha_row_id}'), '[]'::jsonb) INTO r
  FROM (SELECT public.ka_gochara_search_dasha_element(p_chart, i.id) AS el FROM unnest(p_ids) AS i(id)) s;
  RETURN r;
END;
$$;

-- The UPSTREAM daśā scope (round 6, R2: TIER IS METADATA): EVERY Vimśottarī row of the canonical ayanamsha at the three levels the read contract names (MD, AD,
-- PD) that overlaps the BOUND MANIFEST HORIZON, WHATEVER its verification tier and WHATEVER its build. It is a SCOPE, not a judgement: nothing here, and nothing
-- that reads it, filters on the tier. Whether a row may be CONSUMED (its tier, one build) is decided once, at capture, on the COPY (copy_violations below, with
-- eligibility on); an upstream row of this scope that the copy does not hold is an EXTRA row, a violation at capture and at every later drift check, whatever
-- tier it carries. The contract values equal the Python read contract (a test pins both).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_dasha_live_population(p_chart uuid, p_horizon tstzrange)
RETURNS jsonb LANGUAGE sql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' SET extra_float_digits = 1 AS $$
  SELECT COALESCE(jsonb_agg(s.el ORDER BY public.ka_gochara_canonical_json(s.el -> 'key') COLLATE "C", s.el #>> '{metadata,dasha_row_id}'), '[]'::jsonb)
  FROM (
    SELECT public.ka_gochara_search_dasha_element(p_chart, d.dasha_row_id) AS el
    FROM public.chart_dashas d
    WHERE d.chart_id = p_chart AND d.ayanamsha_id = 'lahiri_chitrapaksha' AND d.system_id = 'vimshottari' AND d.level_n IN (1, 2, 3)
      AND d.start_iso < upper(p_horizon) AND d.end_iso > lower(p_horizon)) s;
$$;

-- ── 4b. THE CONTRACT, judged over a COPY and nothing else (round 6, R1: what is validated is exactly what is stored) ───────────────────────────────────────
-- PURE: this function reads NO table. It takes a fact copy, a daśā copy and the bound horizon and returns one row per violation (code, detail). It is the ONE
-- statement of the capture contract, and it is applied to three things: (1) the copy a snapshot is about to STORE (the trigger, eligibility on), (2) the copy a
-- snapshot HAS stored (the completeness gate, eligibility on), (3) the upstream scope rendered in the copy's shape (drift, eligibility OFF). Because the judged
-- object is always a jsonb value, no row can be validated in one place and a different row stored in another.
--   FACTS   copy_malformed · fact_out_of_scope (an element that is not a natal longitude of the canonical ayanamsha for one of the ten subjects) ·
--           required_fact_missing · required_fact_duplicate (natural key not unique) · fact_value_missing
--   PERIODS copy_malformed · period_out_of_scope (not lahiri / vimshottari / MD-AD-PD) · period_outside_horizon · period_not_positive (end <= start) ·
--           period_row_id_duplicate · required_level_missing · required_period_duplicate (two periods of a level share a start) · required_period_overlap ·
--           required_period_gap · required_horizon_start_uncovered · required_horizon_end_uncovered
--   HIERARCHY (every AD and PD) required_parent_missing (its natural parent pointer names no period of the copy at the level above, same ayanamsha and
--           system) · required_parent_id_mismatch (the row's parent_row_id is not the row id of that period: the copy holds another row at the parent's
--           natural key than the one this row hangs under, the round-5 substitution) · required_parent_not_containing · lord_path_inconsistent (the lord path
--           is not the parent's lord path plus the row's lord, i.e. the identity would rest on a row the copy does not hold) · root_has_parent (a Mahādaśā
--           whose parent_row_id, parent level or parent start is not NULL)
--   ELIGIBILITY (p_eligibility only; the copy's OWN recorded tier and build, decided once at capture) period_tier_ineligible · period_build_missing ·
--           dasha_builds_mixed
-- With p_eligibility false NOTHING in this function reads a tier or a build: after capture they are metadata.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_copy_violations(p_facts jsonb, p_dashas jsonb, p_horizon tstzrange, p_eligibility boolean)
RETURNS TABLE (code text, detail text) LANGUAGE sql STABLE SET search_path = pg_catalog, public SET timezone = 'UTC' AS $$
  WITH fraw AS (
    SELECT e.value AS el, e.ord,
           (jsonb_typeof(e.value) = 'object' AND jsonb_typeof(e.value -> 'key') = 'object' AND jsonb_typeof(e.value -> 'content') = 'object'
            AND jsonb_typeof(e.value -> 'metadata') = 'object') IS TRUE AS ok
    FROM jsonb_array_elements(CASE WHEN jsonb_typeof(p_facts) = 'array' THEN p_facts ELSE '[]'::jsonb END) WITH ORDINALITY e(value, ord)),
  draw AS (
    SELECT e.value AS el, e.ord,
           (jsonb_typeof(e.value) = 'object' AND jsonb_typeof(e.value -> 'key') = 'object' AND jsonb_typeof(e.value -> 'content') = 'object'
            AND jsonb_typeof(e.value -> 'metadata') = 'object') IS TRUE AS ok
    FROM jsonb_array_elements(CASE WHEN jsonb_typeof(p_dashas) = 'array' THEN p_dashas ELSE '[]'::jsonb END) WITH ORDINALITY e(value, ord)),
  f AS (
    SELECT public.ka_gochara_canonical_json(x.el -> 'key') AS k, x.el #>> '{key,fact_subject}' AS subj,
           (x.el #>> '{key,ayanamsha_id}' = 'lahiri_chitrapaksha' AND x.el #>> '{key,fact_category}' = 'graha_position' AND x.el #>> '{key,fact_key}' = 'longitude_sidereal'
            AND x.el #>> '{key,fact_subject}' IN ('LAGNA', 'SUN', 'MOON', 'MAR', 'MER', 'JUP', 'VEN', 'SAT', 'RAH_MEAN', 'KET_MEAN')) IS TRUE AS in_scope,
           jsonb_typeof(x.el #> '{content,fact_value_num}') = 'number' AS has_num
    FROM fraw x WHERE x.ok),
  subjects(s) AS (VALUES ('LAGNA'), ('SUN'), ('MOON'), ('MAR'), ('MER'), ('JUP'), ('VEN'), ('SAT'), ('RAH_MEAN'), ('KET_MEAN')),
  fcount AS (SELECT s.s, (SELECT count(*) FROM f WHERE f.in_scope AND f.subj = s.s) AS n FROM subjects s),
  dall AS (
    SELECT x.ord, public.ka_gochara_canonical_json(x.el -> 'key') AS k, x.el #>> '{key,ayanamsha_id}' AS ay, x.el #>> '{key,system_id}' AS sy,
           (x.el #>> '{key,level_n}')::int AS lv, (x.el #>> '{key,start_iso}')::timestamptz AS st, (x.el #>> '{content,end_iso}')::timestamptz AS en,
           x.el #>> '{content,lord_graha}' AS lord, (x.el #>> '{content,parent_level_n}')::int AS plv, (x.el #>> '{content,parent_start_iso}')::timestamptz AS pst,
           x.el #>> '{content,lord_path}' AS lpath, x.el #>> '{metadata,dasha_row_id}' AS id, x.el #>> '{metadata,parent_row_id}' AS pid,
           x.el #>> '{metadata,build_id}' AS build, x.el #>> '{metadata,verification_pass_status}' AS tier
    FROM draw x WHERE x.ok),
  dscope AS (
    SELECT a.*, (a.ay = 'lahiri_chitrapaksha' AND a.sy = 'vimshottari' AND a.lv IN (1, 2, 3)) IS TRUE AS in_scope,
           (a.st < upper(p_horizon) AND a.en > lower(p_horizon)) IS TRUE AS in_horizon
    FROM dall a),
  d AS (
    SELECT a.*, lag(a.st) OVER w AS prev_start, lag(a.en) OVER w AS prev_end
    FROM dscope a WHERE a.in_scope AND a.in_horizon
    WINDOW w AS (PARTITION BY a.lv ORDER BY a.st, a.en, a.id)),
  levels(l) AS (VALUES (1), (2), (3)),
  -- the NATURAL parent of every AD and PD: the period of the copy at the level above, same ayanamsha and system, that the row's parent pointer names
  kin AS (
    SELECT c.ord, c.k, c.lv, c.st, c.en, c.id, c.pid, c.lord, c.lpath,
           count(p.k) AS parents,
           count(p.k) FILTER (WHERE p.id IS NOT DISTINCT FROM c.pid AND c.pid IS NOT NULL) AS parents_by_id,
           count(p.k) FILTER (WHERE NOT (c.st >= p.st AND c.en <= p.en)) AS parents_not_containing,
           count(p.k) FILTER (WHERE c.lpath IS NOT DISTINCT FROM (p.lpath || '/' || c.lord)) AS parents_on_path,
           min(p.st) AS p_st, max(p.en) AS p_en
    FROM d c LEFT JOIN d p ON p.ay = c.ay AND p.sy = c.sy AND p.lv = c.lv - 1 AND p.lv = c.plv AND p.st = c.pst
    WHERE c.lv IN (2, 3)
    GROUP BY c.ord, c.k, c.lv, c.st, c.en, c.id, c.pid, c.lord, c.lpath)                 -- one group per ELEMENT of the copy
  SELECT 'copy_malformed'::text, 'the fact copy is not a JSON array'::text WHERE p_facts IS NULL OR jsonb_typeof(p_facts) <> 'array'
  UNION ALL SELECT 'copy_malformed', 'the daśā copy is not a JSON array' WHERE p_dashas IS NULL OR jsonb_typeof(p_dashas) <> 'array'
  UNION ALL SELECT 'copy_malformed', ('fact element ' || x.ord || ' is not {key, content, metadata}') FROM fraw x WHERE NOT x.ok
  UNION ALL SELECT 'copy_malformed', ('daśā element ' || x.ord || ' is not {key, content, metadata}') FROM draw x WHERE NOT x.ok
  UNION ALL SELECT 'fact_out_of_scope', ('fact ' || f.k || ' is not a natal longitude of the canonical ayanamsha for a required subject') FROM f WHERE NOT f.in_scope
  UNION ALL SELECT 'required_fact_missing', ('subject ' || c.s) FROM fcount c WHERE c.n = 0
  UNION ALL SELECT 'required_fact_duplicate', ('subject ' || c.s || ' has ' || c.n || ' rows (natural key not unique)') FROM fcount c WHERE c.n > 1
  UNION ALL SELECT 'fact_value_missing', ('fact ' || f.k || ' has no numeric value') FROM f WHERE f.in_scope AND f.has_num IS NOT TRUE
  UNION ALL SELECT 'period_out_of_scope', ('period ' || a.k || ' is not a Vimśottarī MD/AD/PD of the canonical ayanamsha') FROM dscope a WHERE NOT a.in_scope
  UNION ALL SELECT 'period_outside_horizon', ('period ' || a.k || ' ending ' || COALESCE(a.en::text, 'NULL') || ' does not overlap the horizon ' || COALESCE(p_horizon::text, 'NULL'))
            FROM dscope a WHERE a.in_scope AND NOT a.in_horizon
  UNION ALL SELECT 'period_not_positive', ('level ' || d.lv || ' period starting ' || d.st::text || ' ends ' || d.en::text || ' (not after its start)') FROM d WHERE NOT (d.en > d.st)
  UNION ALL SELECT 'period_row_id_duplicate', ('row id ' || COALESCE(a.id, 'NULL') || ' is carried by ' || count(*) || ' elements') FROM dall a GROUP BY a.id HAVING count(*) > 1 OR a.id IS NULL
  UNION ALL SELECT 'period_tier_ineligible', ('period ' || a.k || ' (row ' || COALESCE(a.id, 'NULL') || ') carries tier ' || COALESCE(a.tier, 'NULL') || ', not two_pass_verified')
            FROM dall a WHERE p_eligibility AND a.tier IS DISTINCT FROM 'two_pass_verified'
  UNION ALL SELECT 'period_build_missing', ('period ' || a.k || ' (row ' || COALESCE(a.id, 'NULL') || ') carries no build id') FROM dall a WHERE p_eligibility AND a.build IS NULL
  UNION ALL SELECT 'dasha_builds_mixed', ('the copy holds rows of ' || count(DISTINCT a.build) || ' builds: ' || string_agg(DISTINCT a.build, ', ' ORDER BY a.build))
            FROM dall a WHERE p_eligibility AND a.build IS NOT NULL HAVING count(DISTINCT a.build) > 1
  UNION ALL SELECT 'required_level_missing', ('level ' || l.l || ' has no period overlapping the horizon') FROM levels l WHERE NOT EXISTS (SELECT 1 FROM d WHERE d.lv = l.l)
  UNION ALL SELECT 'required_period_duplicate', ('level ' || d.lv || ' start ' || d.st::text || ' (another period of the level shares the start)')
            FROM d WHERE d.prev_start IS NOT NULL AND d.st = d.prev_start
  UNION ALL SELECT 'required_period_overlap', ('level ' || d.lv || ' period starting ' || d.st::text || ' begins before the previous ends (' || d.prev_end::text || ')')
            FROM d WHERE d.prev_start IS NOT NULL AND d.st > d.prev_start AND d.st < d.prev_end
  UNION ALL SELECT 'required_period_gap', ('level ' || d.lv || ' period starting ' || d.st::text || ' begins after the previous ends (' || d.prev_end::text || ')')
            FROM d WHERE d.prev_end IS NOT NULL AND d.st > d.prev_end
  UNION ALL SELECT 'required_horizon_start_uncovered', ('level ' || d.lv || ' first period starts ' || min(d.st)::text || ' after the horizon start ' || lower(p_horizon)::text)
            FROM d GROUP BY d.lv HAVING min(d.st) > lower(p_horizon)
  UNION ALL SELECT 'required_horizon_end_uncovered', ('level ' || d.lv || ' last period ends ' || max(d.en)::text || ' before the horizon end ' || upper(p_horizon)::text)
            FROM d GROUP BY d.lv HAVING max(d.en) < upper(p_horizon)
  UNION ALL SELECT 'required_parent_missing', ('level ' || c.lv || ' period starting ' || c.st::text || ' has no parent present at level ' || (c.lv - 1) || ' of the same ayanamsha and system')
            FROM kin c WHERE c.parents = 0
  UNION ALL SELECT 'required_parent_id_mismatch', ('level ' || c.lv || ' period starting ' || c.st::text || ' hangs under row ' || COALESCE(c.pid, 'NULL') || ', which is not the row the copy holds at its parent''s natural key')
            FROM kin c WHERE c.parents > 0 AND c.parents_by_id = 0
  UNION ALL SELECT 'required_parent_not_containing', ('level ' || c.lv || ' period ' || c.st::text || ' .. ' || c.en::text || ' is not inside its parent ' || c.p_st::text || ' .. ' || c.p_en::text)
            FROM kin c WHERE c.parents > 0 AND c.parents_not_containing > 0
  UNION ALL SELECT 'lord_path_inconsistent', ('level ' || c.lv || ' period starting ' || c.st::text || ' carries lord path ' || COALESCE(c.lpath, 'NULL') || ', which is not its parent''s path plus its own lord')
            FROM kin c WHERE c.parents > 0 AND c.parents_on_path = 0
  UNION ALL SELECT 'lord_path_inconsistent', ('level 1 period starting ' || d.st::text || ' carries lord path ' || COALESCE(d.lpath, 'NULL') || ', which is not its own lord')
            FROM d WHERE d.lv = 1 AND d.lpath IS DISTINCT FROM d.lord
  -- a ROOT has no parent (round 6 follow-up): the ancestry joins drop a parent of another chart, ayanamsha or system, so a Mahādaśā hanging under such a row
  -- would carry NULL natural parent fields and still hold the foreign row id in its metadata. The L1 writer never gives a Mahādaśā a parent.
  UNION ALL SELECT 'root_has_parent', ('level 1 period starting ' || d.st::text || ' carries a parent (row ' || COALESCE(d.pid, 'NULL') || ', level ' || COALESCE(d.plv::text, 'NULL') || '): a Mahādaśā is a root')
            FROM d WHERE d.lv = 1 AND (d.pid IS NOT NULL OR d.plv IS NOT NULL OR d.pst IS NOT NULL);
$$;

-- What differs between two copies, BY NAME (round 6, R8): one row per natural key whose `key|sha256(content)` lines are not the same MULTISET on both sides —
-- exactly the condition under which the two identity digests differ (the digest is a function of that multiset). A key only one side holds is a missing or an
-- extra row; a key both hold with other content is a changed value; a key one side holds twice is a conflicting duplicate. The detail names the key, how many
-- rows each side has there, and the row ids, tiers and builds of both (as NAMES only: nothing is decided by them).
CREATE OR REPLACE FUNCTION public.ka_gochara_search_copy_difference(p_copy jsonb, p_upstream jsonb)
RETURNS TABLE (code text, detail text) LANGUAGE sql IMMUTABLE SET search_path = pg_catalog, public AS $$
  WITH side AS (
    SELECT 'copy'::text AS side, e.value AS el FROM jsonb_array_elements(CASE WHEN jsonb_typeof(p_copy) = 'array' THEN p_copy ELSE '[]'::jsonb END) AS e(value)
    UNION ALL
    SELECT 'upstream', e.value FROM jsonb_array_elements(CASE WHEN jsonb_typeof(p_upstream) = 'array' THEN p_upstream ELSE '[]'::jsonb END) AS e(value)),
  line AS (
    SELECT s.side, public.ka_gochara_canonical_json(s.el -> 'key') AS k,
           CASE WHEN jsonb_typeof(s.el -> 'content') = 'object' THEN public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(s.el -> 'content')) ELSE 'MISSING' END AS h,
           COALESCE(s.el #>> '{metadata,dasha_row_id}', s.el #>> '{metadata,fact_id}', '?') || ' tier ' || COALESCE(s.el #>> '{metadata,verification_pass_status}', 'NULL')
             || ' build ' || COALESCE(s.el #>> '{metadata,build_id}', 'NULL') AS who
    FROM side s),
  per AS (
    SELECT l.k, l.h, count(*) FILTER (WHERE l.side = 'copy') AS n_copy, count(*) FILTER (WHERE l.side = 'upstream') AS n_up FROM line l GROUP BY l.k, l.h),
  bad AS (SELECT DISTINCT p.k FROM per p WHERE p.n_copy <> p.n_up),
  named AS (
    SELECT b.k,
           (SELECT count(*) FROM line l WHERE l.k = b.k AND l.side = 'copy') AS n_copy,
           (SELECT count(*) FROM line l WHERE l.k = b.k AND l.side = 'upstream') AS n_up,
           (SELECT string_agg(l.who, '; ' ORDER BY l.who) FROM line l WHERE l.k = b.k AND l.side = 'copy') AS who_copy,
           (SELECT string_agg(l.who, '; ' ORDER BY l.who) FROM line l WHERE l.k = b.k AND l.side = 'upstream') AS who_up
    FROM bad b)
  SELECT CASE WHEN n.n_copy = 0 THEN 'upstream_row_not_in_copy' WHEN n.n_up = 0 THEN 'copy_row_not_in_upstream_scope'
              WHEN n.n_copy = n.n_up THEN 'row_content_differs' ELSE 'row_count_differs' END::text,
         (n.k || ': the copy has ' || n.n_copy || ' row(s)' || COALESCE(' [' || n.who_copy || ']', '') || ', upstream has ' || n.n_up || ' row(s)' || COALESCE(' [' || n.who_up || ']', ''))::text
  FROM named n;
$$;

-- ── 5. the copy is PRODUCED BY THE DATABASE and VALIDATED AS STORED (BEFORE INSERT, before 1206's write guard) ───────────────────────────────────────────────
-- Codex round 1 ruling 2: matching digests prove consistency, not authenticity (the builder holds INSERT and could submit a consistent false copy). So the
-- builder submits only KEYS (consumed_fact_ids, consumed_dasha_row_ids) and the identity digests it computed; this trigger BUILDS consumed_fact_rows /
-- consumed_dasha_rows and the metadata digests itself from the live rows IN THE INSERT TRANSACTION, OVERWRITING whatever was submitted in those columns.
-- Round 6 (R1): the copy is assigned to NEW first, and EVERY check below reads NEW.consumed_fact_rows / NEW.consumed_dasha_rows, i.e. the value that is
-- stored. Rounds 1 to 5 validated the upstream population and then compared content digests, which let a copy of other ROWS with equal content through.
--   (a) the copy satisfies the contract by itself, eligibility included (copy_violations);
--   (b) the copy is the WHOLE upstream scope and nothing else (copy_difference against the upstream scope of every tier and build);
--   (c) the submitted identity digests are those of the copy.
-- ONE SNAPSHOT (R9): the single SELECT ... INTO below is the ONLY statement of this function that reads live L1. Its four function calls are STABLE, so they run
-- on the snapshot of that one statement (READ COMMITTED gives a VOLATILE trigger function a new snapshot per statement, so two statements could see two L1
-- states; one statement cannot). Everything after it is arithmetic on jsonb values. Assumption stated: the writer runs under the per-chart lock
-- (ka_gochara_lock_chart) at READ COMMITTED or stricter; nothing here depends on a stricter level.
-- It fires BEFORE 1206's write guard (named 0z: after 0_statement_lock, before 1_write_guard) so that guard checks input_digest against digests that are the
-- database's own.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_input_snapshot_copy_build()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE upstream_facts jsonb; upstream_dashas jsonb; hz tstzrange; problems text; n_problems int;
BEGIN
  IF NEW.consumed_fact_ids IS NULL OR NEW.consumed_dasha_row_ids IS NULL THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): consumed_fact_ids and consumed_dasha_row_ids are the KEYS the database builds the copy from';
  END IF;
  SELECT p.horizon INTO hz FROM public.kala_gochara_publication p WHERE p.chart_id = NEW.chart_id AND p.generation = NEW.generation;
  IF hz IS NULL OR isempty(hz) OR lower_inf(hz) OR upper_inf(hz) THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): no bound, finite manifest horizon for this generation — the population a snapshot must cover is the manifest''s, not the copy''s own span';
  END IF;
  SELECT public.ka_gochara_search_facts_copy(NEW.chart_id, NEW.consumed_fact_ids), public.ka_gochara_search_dasha_copy(NEW.chart_id, NEW.consumed_dasha_row_ids),
         public.ka_gochara_search_facts_live_population(NEW.chart_id), public.ka_gochara_search_dasha_live_population(NEW.chart_id, hz)
    INTO NEW.consumed_fact_rows, NEW.consumed_dasha_rows, upstream_facts, upstream_dashas;       -- the ONE live read; raises by name if a consumed id does not exist
  NEW.l1_facts_metadata_digest := public.ka_gochara_search_copy_digest(NEW.consumed_fact_rows, 'metadata');
  NEW.dasha_metadata_digest := public.ka_gochara_search_copy_digest(NEW.consumed_dasha_rows, 'metadata');
  SELECT count(*), string_agg(v.code || ' (' || v.detail || ')', '; ' ORDER BY v.code, v.detail) FILTER (WHERE v.rn <= 25) INTO n_problems, problems
  FROM (SELECT u.code, u.detail, row_number() OVER (ORDER BY u.code, u.detail) AS rn
        FROM (SELECT c.code, c.detail FROM public.ka_gochara_search_copy_violations(NEW.consumed_fact_rows, NEW.consumed_dasha_rows, hz, true) c
              UNION ALL SELECT 'fact_' || c.code, c.detail FROM public.ka_gochara_search_copy_difference(NEW.consumed_fact_rows, upstream_facts) c
              UNION ALL SELECT 'period_' || c.code, c.detail FROM public.ka_gochara_search_copy_difference(NEW.consumed_dasha_rows, upstream_dashas) c) u) v;
  IF n_problems > 0 THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): the copy this snapshot would store violates the capture contract (% violation(s)): %', n_problems, problems;
  END IF;
  IF NEW.l1_facts_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_fact_rows, 'content')
     OR NEW.dasha_digest IS DISTINCT FROM public.ka_gochara_search_copy_digest(NEW.consumed_dasha_rows, 'content') THEN
    RAISE EXCEPTION 'ka_gochara_search_input_snapshot refused (1305): l1_facts_digest / dasha_digest are not the identity digests of the copy the database built from the submitted keys';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER ka_gochara_search_input_snapshot_0z_copy_build
  BEFORE INSERT ON public.ka_gochara_search_input_snapshot
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_search_input_snapshot_copy_build();

-- ── 5b. the snapshot's copy AFTER capture: is it still what it says it is, and does upstream still agree? ───────────────────────────────────────────────────
-- Called by the completeness function for a copy-bearing snapshot (its ONE 1305 block). STABLE: every statement runs on the caller's snapshot, so the upstream
-- facts and periods are read as ONE L1 state. Three detectors, each of which can really fire (CLAUDE.md §N.8):
--   input_snapshot_copy_inconsistent  the STORED copy does not recompute to the STORED digests (identity, metadata, input), or the stored copy itself violates
--                                     the capture contract. Nothing upstream is read for this: it is a statement about the row (round 6, R7).
--   input_snapshot_required_scope     the upstream scope, as it is now, violates the structural contract (a member, coverage, uniqueness, hierarchy). No tier
--                                     and no build is read (eligibility off).
--   input_snapshot_drift              the identity digest of the upstream scope is not the stored one: a value changed, a row is gone, or an extra or
--                                     conflicting row exists, WHATEVER tier that row carries (R2). The detail names the keys.
-- A metadata-only difference (ids, build, tier, engine, ordinal path) is no violation here: the staleness report shows it as soft.
CREATE OR REPLACE FUNCTION public.ka_gochara_search_snapshot_copy_violations(p_chart uuid, p_generation text)
RETURNS TABLE (violation text, detail text) LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE snap record; hz tstzrange; up_f jsonb; up_d jsonb; names text; n int;
BEGIN
  SELECT s.* INTO snap FROM public.ka_gochara_search_input_snapshot s WHERE s.chart_id = p_chart AND s.generation = p_generation;
  IF NOT FOUND OR snap.consumed_fact_rows IS NULL OR snap.consumed_dasha_rows IS NULL THEN
    RETURN;                                                                  -- no snapshot, or a legacy one: the caller's legacy branch judges it
  END IF;
  SELECT q.horizon INTO hz FROM public.kala_gochara_publication q WHERE q.chart_id = p_chart AND q.generation = p_generation;
  -- (1) the stored copy recomputes to the stored digests
  RETURN QUERY
  SELECT 'input_snapshot_copy_inconsistent'::text, x.d::text
  FROM (VALUES
    (public.ka_gochara_search_copy_digest(snap.consumed_fact_rows, 'content') IS DISTINCT FROM snap.l1_facts_digest, 'l1_facts_digest is not the identity digest of the stored fact copy'),
    (public.ka_gochara_search_copy_digest(snap.consumed_dasha_rows, 'content') IS DISTINCT FROM snap.dasha_digest, 'dasha_digest is not the identity digest of the stored daśā copy'),
    (public.ka_gochara_search_copy_digest(snap.consumed_fact_rows, 'metadata') IS DISTINCT FROM snap.l1_facts_metadata_digest, 'l1_facts_metadata_digest is not the metadata digest of the stored fact copy'),
    (public.ka_gochara_search_copy_digest(snap.consumed_dasha_rows, 'metadata') IS DISTINCT FROM snap.dasha_metadata_digest, 'dasha_metadata_digest is not the metadata digest of the stored daśā copy'),
    (public.ka_gochara_search_input_digest(snap.convention_id, snap.input_generation_vector, snap.l1_facts_digest, snap.dasha_digest, snap.av_declarations)
       IS DISTINCT FROM snap.input_digest, 'input_digest is not the digest of the stored convention, vector, identity digests and AV declarations')
  ) AS x(bad, d) WHERE x.bad;
  IF hz IS NULL OR isempty(hz) OR lower_inf(hz) OR upper_inf(hz) THEN
    RETURN QUERY SELECT 'input_snapshot_required_scope'::text, 'no bound, finite manifest horizon: the scope the copy must cover cannot be stated'::text;
    RETURN;
  END IF;
  -- (2) the stored copy still satisfies the capture contract, eligibility included (its OWN recorded tier and build)
  RETURN QUERY
  SELECT 'input_snapshot_copy_inconsistent'::text, ('the stored copy violates the capture contract: ' || v.code || ' (' || v.detail || ')')::text
  FROM public.ka_gochara_search_copy_violations(snap.consumed_fact_rows, snap.consumed_dasha_rows, hz, true) v;
  -- (3) upstream, as it is now (structure only; then identity)
  up_f := public.ka_gochara_search_facts_live_population(p_chart);
  up_d := public.ka_gochara_search_dasha_live_population(p_chart, hz);
  RETURN QUERY
  SELECT 'input_snapshot_required_scope'::text, (v.code || ' (' || v.detail || ')')::text
  FROM public.ka_gochara_search_copy_violations(up_f, up_d, hz, false) v;
  IF public.ka_gochara_search_copy_digest(up_f, 'content') IS DISTINCT FROM snap.l1_facts_digest THEN
    SELECT count(*), string_agg(c.code || ' ' || c.detail, '; ' ORDER BY c.detail) FILTER (WHERE c.rn <= 5) INTO n, names
    FROM (SELECT x.code, x.detail, row_number() OVER (ORDER BY x.detail) AS rn FROM public.ka_gochara_search_copy_difference(snap.consumed_fact_rows, up_f) x) c;
    RETURN QUERY SELECT 'input_snapshot_drift'::text, ('consumed L1 fact rows no longer match the snapshot: a value changed, a row is gone, or an extra/conflicting row exists (identity digest of the complete upstream scope); '
                                                       || n || ' key(s) differ: ' || COALESCE(names, 'none named (the stored copy itself does not recompute)'))::text;
  END IF;
  IF public.ka_gochara_search_copy_digest(up_d, 'content') IS DISTINCT FROM snap.dasha_digest THEN
    SELECT count(*), string_agg(c.code || ' ' || c.detail, '; ' ORDER BY c.detail) FILTER (WHERE c.rn <= 5) INTO n, names
    FROM (SELECT x.code, x.detail, row_number() OVER (ORDER BY x.detail) AS rn FROM public.ka_gochara_search_copy_difference(snap.consumed_dasha_rows, up_d) x) c;
    RETURN QUERY SELECT 'input_snapshot_drift'::text, ('consumed dasha rows no longer match the snapshot: a value changed, a row is gone, or an extra/conflicting row exists (identity digest of the complete upstream scope); '
                                                       || n || ' key(s) differ: ' || COALESCE(names, 'none named (the stored copy itself does not recompute)'))::text;
  END IF;
END;
$$;

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
      -- 1305 (G12 route 1): a snapshot that OWNS a copy is judged by ka_gochara_search_snapshot_copy_violations — the stored copy recomputes to its stored
      -- digests and still satisfies the capture contract (input_snapshot_copy_inconsistent), the upstream scope is structurally whole
      -- (input_snapshot_required_scope) and has the stored identity (input_snapshot_drift). A later L1 rebuild that re-issues row ids, build ids, tiers or
      -- engine versions changes none of this; a changed VALUE, a missing row or an extra row of ANY tier does.
      RETURN QUERY SELECT '*'::text, v.violation, v.detail FROM public.ka_gochara_search_snapshot_copy_violations(p_chart, p_generation) v;
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
        'public.ka_gochara_search_dasha_live_population(uuid,tstzrange)', 'public.ka_gochara_search_copy_violations(jsonb,jsonb,tstzrange,boolean)',
        'public.ka_gochara_search_copy_difference(jsonb,jsonb)', 'public.ka_gochara_search_snapshot_copy_violations(uuid,text)',
        -- a 1206 helper, not a 1305 function: the copy-consistency detector recomputes input_digest as the INVOKER (verifier, sealer); the builder
        -- already holds it from 1206 (a GRANT of a held privilege is a no-op). Found by the faithful-role suite, which is its detector.
        'public.ka_gochara_search_input_digest(text,jsonb,text,text,text[])'] LOOP
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
  IF pg_get_functiondef('public.ka_gochara_search_completeness_violations(uuid,text)'::regprocedure) NOT LIKE '%ka_gochara_search_snapshot_copy_violations%'
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
