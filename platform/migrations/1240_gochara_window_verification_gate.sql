-- Migration 1240: the generation-bound WINDOW VERIFICATION result and the candidate gate that consumes it — ADDITIVE.
-- Pravāha A5.3, Codex round 8 R8-4 (steward M20261002T032818-3cf4), 2026-10-02. Author: pravaha stream A.
-- STATUS: authored and tested on disposable databases only; NOT applied anywhere.
--
-- WHY
-- ═══
-- The window writer's independent semantic verifier produced a report (`VERIFIED` / `UNVERIFIED_DYNAMIC`) that only
-- reached the build's notes: nothing in the database recorded that a window grain WAS verified, against which
-- stored windows, under which qualification policy and which input identity — so a candidate could be sealed with a
-- missing, stale or unverified window result and no gate could tell. 1206 solved exactly this for the search
-- inventory (`ka_gochara_search_inventory_verification` + the seal's completeness check); this is its sibling for
-- windows.
--
-- WHAT THIS DOES
-- ══════════════
--   1. `ka_gochara_eval_window_verification`: ONE row per (chart, generation, event_class, path, rule_version,
--      verifier) — status (VERIFIED | UNVERIFIED_DYNAMIC | FAILED), the qualification policy version, the expected /
--      stored / reproduced / unverified window counts, the digest of the INDEPENDENTLY derived expected window set
--      and of the stored one (VERIFIED requires them equal: no expected window omitted, none invented), the digest
--      of the stored window CONTENT at verification time (so a later change makes the row stale), the governed fields
--      reproduced, the generation's search-snapshot `input_digest` (the verification is bound to the inputs the
--      generation consumed) and `windows_detail` — the lossless, verifier-derived qualification provenance per window
--      (objective name/value, structured reasons, affected channels) that 1156's window table has no column for.
--      Write guard: the Gochara-5 chart family key first, sealed generations frozen, rows immutable (a changed result
--      is DELETE + INSERT in the candidate), a sealed rule version only, TRUNCATE refused.
--   2. `ka_gochara_eval_window_content_digest` / `ka_gochara_eval_window_expected_digest`: the two digests, computed
--      by the database over the stored windows and over the admitted scored records' supports (non-P4: the connected
--      union; P4: the intersection of the Jupiter and Saturn unions) — the SECOND, SQL implementation of the expected
--      set (the verifier derives it separately, in Python).
--   3. `ka_gochara_window_verification_violations(chart, generation)`: for every INCLUDED P1–P4 pin of the generation's
--      inventory, a violation unless a verification row exists, EVERY row is `VERIFIED`, its policy is known, its
--      counts equal the stored windows, its content digest equals the CURRENT windows' digest, its expected/stored
--      digests equal the database's recomputation, and its input digest equals the snapshot's.
--   4. `ka_gochara_candidate_gate_violations(chart, generation)`: 1206/1232's completeness violations UNION the window
--      violations — the one check a candidate must pass. (Seal wiring — calling it from the sealing path — is the
--      sealer's/steward's; this migration does not redefine any 1206/1232 function.)
--   5. Builder privileges for the new table and the two digest functions (role-guarded, like 1206 §7).
--   NOT changed: 1156's window tables, 1206/1232's functions, any trigger on an existing table.
--
-- WINDOW: protected public-schema window, AFTER 1156 + 1206 (it reads their tables) and after 1232/1233/1234.
-- Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns one transaction per migration.
-- ROLLBACK (unused installation only): DROP FUNCTIONs and the table, delete the _migrations_applied row.
-- ─────────────────────────────────────────────────────────────────────────────

SET LOCAL search_path = public, pg_catalog;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '120s';

-- ── GATE ──────────────────────────────────────────────────────────────────────
DO $$
DECLARE failures text;
BEGIN
  WITH f(failure, detail) AS (
    SELECT 'migration_1156_not_applied', 'ka_gochara_eval_window'
      WHERE to_regclass('public.ka_gochara_eval_window') IS NULL
    UNION ALL SELECT 'migration_1206_not_applied', 'ka_gochara_search_path_pin'
      WHERE to_regclass('public.ka_gochara_search_path_pin') IS NULL
    UNION ALL SELECT 'helper_missing', 'ka_gochara_chart_write_guard'
      WHERE NOT EXISTS (SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
                        WHERE n.nspname = 'public' AND p.proname = 'ka_gochara_chart_write_guard')
    UNION ALL SELECT 'helper_missing', 'ka_gochara_canonical_json'
      WHERE to_regprocedure('public.ka_gochara_canonical_json(jsonb)') IS NULL
    UNION ALL SELECT 'migration_1240_already_applied', 'ka_gochara_eval_window_verification'
      WHERE to_regclass('public.ka_gochara_eval_window_verification') IS NOT NULL
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1240 BLOCKED: %', failures;
  END IF;
END;
$$;

-- ── 1. the verification result ────────────────────────────────────────────────
CREATE TABLE public.ka_gochara_eval_window_verification (
  chart_id                uuid        NOT NULL REFERENCES public.charts(id),
  generation              text        NOT NULL,
  event_class             text        NOT NULL,
  path_id                 text        NOT NULL,
  rule_version            text        NOT NULL,
  verifier_id             text        NOT NULL,
  verifier_version        text        NOT NULL,
  status                  text        NOT NULL,
  policy_version          text        NOT NULL,
  windows_expected        integer     NOT NULL,
  windows_stored          integer     NOT NULL,
  windows_reproduced      integer     NOT NULL,
  windows_unverified      integer     NOT NULL,
  expected_windows_digest text        NOT NULL,
  stored_windows_digest   text        NOT NULL,
  windows_content_digest  text        NOT NULL,
  fields_verified         text[]      NOT NULL,
  input_digest            text        NOT NULL,
  windows_detail          jsonb       NOT NULL,
  verified_at             timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, event_class, path_id, rule_version, verifier_id, verifier_version),
  CONSTRAINT kgewv_canonical_chart_ck CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgewv_generation_governed_ck CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgewv_path_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgewv_ids_nonblank_ck CHECK (btrim(verifier_id) <> '' AND btrim(verifier_version) <> ''
                                          AND btrim(policy_version) <> ''),
  CONSTRAINT kgewv_status_ck CHECK (status IN ('VERIFIED', 'UNVERIFIED_DYNAMIC', 'FAILED')),
  CONSTRAINT kgewv_counts_ck CHECK (windows_expected >= 0 AND windows_stored >= 0
                                    AND windows_reproduced >= 0 AND windows_unverified >= 0
                                    AND windows_reproduced + windows_unverified <= windows_stored),
  CONSTRAINT kgewv_digests_ck CHECK (expected_windows_digest ~ '^[0-9a-f]{64}$'
                                     AND stored_windows_digest ~ '^[0-9a-f]{64}$'
                                     AND windows_content_digest ~ '^[0-9a-f]{64}$'
                                     AND input_digest ~ '^[0-9a-f]{64}$'),
  -- VERIFIED is a claim about EVERY expected window and EVERY governed field: nothing unverified, every stored
  -- window reproduced, and the expected set (derived independently) equals the stored one — no window omitted
  CONSTRAINT kgewv_verified_total_ck CHECK (status <> 'VERIFIED' OR (
      windows_unverified = 0 AND windows_reproduced = windows_stored AND windows_stored = windows_expected
      AND expected_windows_digest = stored_windows_digest)),
  CONSTRAINT kgewv_unverified_dynamic_ck CHECK (status <> 'UNVERIFIED_DYNAMIC' OR windows_unverified > 0),
  CONSTRAINT kgewv_fields_ck CHECK (cardinality(fields_verified) > 0),
  -- the provenance is MANDATORY and lossless: one structured entry per stored window
  CONSTRAINT kgewv_detail_ck CHECK (jsonb_typeof(windows_detail) = 'array'
                                    AND jsonb_array_length(windows_detail) = windows_stored)
);

COMMENT ON TABLE public.ka_gochara_eval_window_verification IS
  'A5.3 R8-4: the INDEPENDENT window verifier''s generation-bound result per window grain. The candidate gate '
  '(ka_gochara_window_verification_violations) requires a row, every row VERIFIED, a known policy, counts and '
  'digests equal to the CURRENT stored windows / the recomputed expected set, and the generation''s input digest. '
  'windows_detail carries the verifier-derived qualification provenance (1156 has no column for it). '
  'Independence of the verifier is a process property.';

CREATE INDEX idx_kgewv_grain ON public.ka_gochara_eval_window_verification
  (chart_id, generation, event_class, path_id, rule_version);

-- ── 2. the digests (database-computed over the stored rows) ───────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_eval_window_content_digest(
  p_chart uuid, p_generation text, p_class text, p_path text, p_version text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(COALESCE((
    SELECT jsonb_agg(jsonb_build_object(
             'interval', jsonb_build_array(to_char(lower(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
                                           to_char(upper(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')),
             'peak', CASE WHEN w.peak_instant IS NULL THEN NULL
                          ELSE to_char(w.peak_instant AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"') END,
             'score', w.score, 'evidence_for', w.evidence_for, 'evidence_against', w.evidence_against,
             'valence', w.outcome_valence_for_native, 'severity', w.severity,
             'null_states', to_jsonb(w.null_states_used),
             'members', COALESCE((SELECT jsonb_agg(m.record_id::text ORDER BY m.record_id::text)
                                  FROM public.ka_gochara_eval_window_record m WHERE m.window_id = w.window_id),
                                 '[]'::jsonb))
           ORDER BY lower(w.interval))
    FROM public.ka_gochara_eval_window w
    WHERE (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
        = (p_chart, p_generation, p_class, p_path, p_version)), '[]'::jsonb)));
$$;

-- the stored interval set alone (what the expected set must equal)
CREATE OR REPLACE FUNCTION public.ka_gochara_eval_window_stored_digest(
  p_chart uuid, p_generation text, p_class text, p_path text, p_version text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(COALESCE((
    SELECT jsonb_agg(jsonb_build_array(to_char(lower(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
                                       to_char(upper(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))
                     ORDER BY lower(w.interval))
    FROM public.ka_gochara_eval_window w
    WHERE (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
        = (p_chart, p_generation, p_class, p_path, p_version)), '[]'::jsonb)));
$$;

-- the EXPECTED window set, recomputed from the admitted scored records' supports (Codex round 6 R3: one window per
-- maximal connected component of the prerequisite-satisfied support; P4 — the intersection of the Jupiter and
-- Saturn unions). The verifier derives the same set separately; the gate compares both with the stored row.
CREATE OR REPLACE FUNCTION public.ka_gochara_eval_window_expected_digest(
  p_chart uuid, p_generation text, p_class text, p_path text, p_version text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH sup AS (
    SELECT r.agent, x AS rng
    FROM public.ka_gochara_relationship_record r
    CROSS JOIN LATERAL unnest(r.temporal_support_intervals) AS x
    WHERE (r.chart_id, r.generation, r.event_class, r.path_id, r.rule_version)
        = (p_chart, p_generation, p_class, p_path, p_version)
      AND r.admission_state = 'admitted' AND r.operator_role = 'scored'),
  allm AS (SELECT range_agg(rng) AS m FROM sup),
  jup AS (SELECT range_agg(rng) AS m FROM sup WHERE agent = 'jupiter'),
  sat AS (SELECT range_agg(rng) AS m FROM sup WHERE agent = 'saturn'),
  expected AS (
    SELECT CASE WHEN p_path = 'P4'
                THEN COALESCE(jup.m, '{}'::tstzmultirange) * COALESCE(sat.m, '{}'::tstzmultirange)
                ELSE COALESCE(allm.m, '{}'::tstzmultirange) END AS m
    FROM allm, jup, sat)
  SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(COALESCE((
    SELECT jsonb_agg(jsonb_build_array(to_char(lower(c) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
                                       to_char(upper(c) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'))
                     ORDER BY lower(c))
    FROM expected, unnest(expected.m) AS c), '[]'::jsonb)));
$$;

-- ── 3. the gate ───────────────────────────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_window_verification_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, path_id text, rule_version text, violation text, detail text)
LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH expected AS (
    -- every grain the generation's inventory INCLUDES on a windowed path (P1–P4; P5 is held)
    SELECT p.event_class, p.path_id, p.rule_version
    FROM public.ka_gochara_search_path_pin p
    WHERE p.chart_id = p_chart AND p.generation = p_generation AND p.disposition = 'included'
      AND p.path_id IN ('P1', 'P2', 'P3', 'P4')),
  snap AS (
    SELECT s.input_digest FROM public.ka_gochara_search_input_snapshot s
    WHERE s.chart_id = p_chart AND s.generation = p_generation)
  SELECT e.event_class, e.path_id, e.rule_version, 'window_verification_missing'::text,
         'no window verification result for this grain'::text
  FROM expected e
  WHERE NOT EXISTS (SELECT 1 FROM public.ka_gochara_eval_window_verification v
                    WHERE (v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version)
                        = (p_chart, p_generation, e.event_class, e.path_id, e.rule_version))
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_not_verified'::text,
         (v.status || ' by ' || v.verifier_id || '@' || v.verifier_version)::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation AND v.status <> 'VERIFIED'
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_policy_unknown'::text, v.policy_version
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation AND v.policy_version <> 'window_qualification/1'
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_count_mismatch'::text,
         (v.windows_stored || ' verified vs ' || (SELECT count(*) FROM public.ka_gochara_eval_window w
            WHERE (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
                = (v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version)) || ' stored now')::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.windows_stored IS DISTINCT FROM (SELECT count(*) FROM public.ka_gochara_eval_window w
            WHERE (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
                = (v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version))
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_stale'::text,
         'the stored windows changed after they were verified'::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.windows_content_digest IS DISTINCT FROM public.ka_gochara_eval_window_content_digest(
          v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version)
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_expected_set_mismatch'::text,
         'the verifier''s expected windows or the stored windows differ from the database recomputation'::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND (v.expected_windows_digest IS DISTINCT FROM public.ka_gochara_eval_window_expected_digest(
           v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version)
         OR v.stored_windows_digest IS DISTINCT FROM public.ka_gochara_eval_window_stored_digest(
           v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version))
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_input_mismatch'::text,
         'verified under a different search-input identity than the generation''s snapshot'::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.input_digest IS DISTINCT FROM (SELECT input_digest FROM snap);
$$;

COMMENT ON FUNCTION public.ka_gochara_window_verification_violations(uuid, text) IS
  'A5.3 R8-4: the window half of the candidate gate — empty iff every included P1–P4 grain has a VERIFIED, current, '
  'input-bound verification that matches the database recomputation. UNVERIFIED_DYNAMIC and missing results fail it.';

CREATE OR REPLACE FUNCTION public.ka_gochara_candidate_gate_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, path_id text, rule_version text, violation text, detail text)
LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT c.event_class, NULL::text, NULL::text, c.violation, c.detail
  FROM public.ka_gochara_search_completeness_violations(p_chart, p_generation) c
  UNION ALL
  SELECT w.event_class, w.path_id, w.rule_version, w.violation, w.detail
  FROM public.ka_gochara_window_verification_violations(p_chart, p_generation) w;
$$;

COMMENT ON FUNCTION public.ka_gochara_candidate_gate_violations(uuid, text) IS
  'A5.3 R8-4: the ONE check a candidate must pass — the search-completeness violations (1206/1232) plus the window '
  'verification violations. Wiring it into the sealing path is the sealer''s; no 1206/1232 function is redefined.';

-- ── 4. triggers (statement lock → chart key / sealed freeze → sealed rule) ─────
CREATE TRIGGER ka_gochara_ewv_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_eval_window_verification
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
CREATE TRIGGER ka_gochara_ewv_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_eval_window_verification
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_chart_write_guard('no_update');
CREATE TRIGGER ka_gochara_ewv_2_sealed_path_check
  BEFORE INSERT ON public.ka_gochara_eval_window_verification
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();
CREATE TRIGGER ka_gochara_ewv_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_eval_window_verification
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 5. builder privileges (guarded by role existence, like 1206 §7) ────────────
-- The builder's verify step writes the result after the independent derivation (the 1206 inventory model).
-- The two gate functions are for the SEALING principal (EXECUTE granted by whoever authorises it); the builder
-- reaches only the digest helpers its INSERT-time check and the writer's persistence call.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT SELECT, INSERT, DELETE ON public.ka_gochara_eval_window_verification TO data_plane_builder;
    GRANT EXECUTE ON FUNCTION
      public.ka_gochara_eval_window_content_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_stored_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_expected_digest(uuid, text, text, text, text),
      public.ka_gochara_window_verification_violations(uuid, text)
      TO data_plane_builder;
  END IF;
END;
$$;

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
DECLARE missing text;
BEGIN
  SELECT string_agg(x.name, ', ') INTO missing
  FROM (VALUES
    ('ka_gochara_ewv_0_statement_lock'), ('ka_gochara_ewv_1_write_guard'),
    ('ka_gochara_ewv_2_sealed_path_check'), ('ka_gochara_ewv_no_truncate')) AS x(name)
  WHERE NOT EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgname = x.name
                    AND t.tgrelid = 'public.ka_gochara_eval_window_verification'::regclass);
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: missing triggers: %', missing;
  END IF;
  SELECT string_agg(x.sig, ', ') INTO missing
  FROM (VALUES
    ('public.ka_gochara_eval_window_content_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_eval_window_stored_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_eval_window_expected_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_window_verification_violations(uuid,text)'),
    ('public.ka_gochara_candidate_gate_violations(uuid,text)')) AS x(sig)
  WHERE to_regprocedure(x.sig) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: missing functions: %', missing;
  END IF;
  RAISE NOTICE 'migration 1240: presence checks passed';
END;
$$;
