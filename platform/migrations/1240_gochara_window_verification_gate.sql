-- Migration 1240: the generation-bound WINDOW VERIFICATION result, the window provenance it verifies, and the seal-time
-- candidate gate that consumes it — ADDITIVE.
-- Pravāha A5.3, Codex round 8 R8-4 (steward M20261002T032818-3cf4, M20261002T034837-d6de, M20261002T035035-0c4b;
-- Stream B's constraints note design/MIGRATION_1240_CONTRACT_CONSTRAINTS_v1_0.md), 2026-10-02. Author: pravaha stream A.
-- STATUS: authored and tested on disposable databases (as restricted roles) only; NOT applied anywhere. HOLD.
--
-- WHY
-- ═══
-- The window writer's independent semantic verifier produced a report that only reached the build's notes: nothing in
-- the database recorded that a window grain WAS verified, against which stored windows, under which qualification policy
-- and input identity — so a candidate could be sealed with a missing, stale or unverified window result and no gate
-- could tell. 1206 solved this for the search inventory; this is its sibling for windows — with one deliberate
-- difference: the VERIFIER is a separate principal (`gochara_verifier`); the builder gets NOTHING on the new table
-- (the writer cannot verify itself; 1206 §7 lets the builder write the inventory verification — not repeated here).
--
-- WHAT THIS DOES
-- ══════════════
--   1. ka_gochara_eval_window gains three NULLABLE columns (the 1233 pattern): `objective` (the NAME of the function
--      the peak maximises), `objective_value` (its value at the peak) and `qualification` (structured provenance: the
--      unqualified reason, the unresolved reasons per record count, the affected channels, member counts — a closed
--      key set). The builder writes them with the window; a SEALED generation stays frozen automatically (the chart
--      write guard compares to_jsonb(NEW) with to_jsonb(OLD)). A named CHECK ties them: an unqualified window carries
--      no peak, score or evidence.
--   2. ka_gochara_eval_window_verification: ONE row per (chart, generation, class, path, rule_version) — status,
--      policy_version, expected / stored / reproduced / unverified window counts, the digests of the INDEPENDENTLY
--      derived expected window set and of the stored one, the digest of the stored window CONTENT (staleness), the
--      governed fields reproduced, the generation's search-snapshot input_digest, the verifier identity. Composite FKs
--      to the finalised inventory header and the pin; CHECKs make VERIFIED total.
--   3. ka_gochara_window_verification_write_guard (the 1206 trio: statement lock → chart key first, sealed generation
--      refuses INSERT/UPDATE/DELETE, rows immutable → no TRUNCATE) — NOT 1155's table-keyed guard.
--   4. Digest functions over the STORED rows: REAL columns are hashed as IEEE-754 bits (float4send, hex) with NULL
--      distinct from JSON null (`ka_gochara_f4_token`); a frozen literal vector is asserted in the static test.
--   5. ka_gochara_window_verification_violations (first seal): for every INCLUDED P1–P4 pin, refuse no row, any row
--      status <> 'VERIFIED', unknown policy, short field coverage, a count differing from the stored windows, a stale
--      content digest, an expected-set / stored-set digest differing from the DATABASE's recomputation (the expected
--      set is derived from the admitted scored records' supports and the 1206 pins — never from a writer-supplied
--      count), a wrong input identity, or a stored window lacking its provenance.
--      ka_gochara_window_verification_replay_violations (replay): integrity only — a generation sealed BEFORE 1240 has
--      no rows and must still replay; rows that exist must still equal the frozen windows.
--      ka_gochara_candidate_gate_violations = 1206/1232 completeness UNION the window violations.
--   6. ONE additive BEFORE INSERT trigger on ka_gochara_generation_seal, named to fire AFTER 1206's
--      (…_z_search_complete): `ka_gochara_generation_seal_zz_window_verified`, with a mandatory REPLAY branch. No 1153 /
--      1206 function is replaced; lock order chart EXCLUSIVE then global SHARED; no new family key.
--   7. Privileges (role-existence-guarded, table-level, explicit, no SECURITY DEFINER): the VERIFIER gets SELECT/INSERT
--      (and pre-seal DELETE, enforced by the guard) on the new table, SELECT on the tables it reads and EXECUTE on the
--      functions the write path calls as the invoking role; the SEALER gets SELECT on the new table and EXECUTE on the
--      gate functions (the seal trigger fires as the sealing role). The builder gets NOTHING on the new table.
--
-- CONSEQUENCE, STATED PLAINLY: neither `gochara_verifier` nor `gochara_sealer` exists in production today (native decision
-- pending). Until they are provisioned NO verification row can be written there and the candidate gate stays CLOSED
-- (a first seal is refused by the trigger above). That is the honest state — and it makes the roles decision a named
-- blocker of the first candidate build. The grants are written so the builder is never needed on this table and the
-- verifier role can later be narrowed or renamed without a schema change.
--
-- WINDOW: protected public-schema window, AFTER 1233 (and 1234): 1204 → 1206 → 1232 → 1233 → 1240. Reads 1153–1156 and
-- 1206 objects. Transaction ownership: NO BEGIN/COMMIT — migrate.ts owns one transaction per file.
-- ROLLBACK (unused installation only): DROP the trigger and the functions and the table, DROP the three window columns,
-- delete the _migrations_applied row.
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
    UNION ALL SELECT 'migration_1206_not_applied', 'ka_gochara_generation_seal_z_search_complete'
      WHERE NOT EXISTS (SELECT 1 FROM pg_trigger t WHERE t.tgname = 'ka_gochara_generation_seal_z_search_complete'
                        AND t.tgrelid = 'public.ka_gochara_generation_seal'::regclass)
    UNION ALL SELECT 'helper_missing', s.sig
      FROM (VALUES ('public.ka_gochara_canonical_json(jsonb)'), ('public.ka_gochara_sha256_hex(text)'),
                   ('public.ka_gochara_lock_chart(uuid)'), ('public.ka_gochara_lock_global_shared()'),
                   ('public.ka_gochara_generation_is_sealed(uuid,text)'), ('public.ka_gochara_generation_governed(text)'),
                   ('public.ka_gochara_chart_statement_lock()'), ('public.ka_gochara_refuse_truncate()'),
                   ('public.ka_gochara_require_sealed_rule_path()'),
                   ('public.ka_gochara_search_completeness_violations(uuid,text)'),
                   ('public.ka_gochara_finite_nonneg_ok(double precision)')) AS s(sig)
      WHERE to_regprocedure(s.sig) IS NULL
    UNION ALL SELECT 'migration_1240_already_applied', 'ka_gochara_eval_window_verification'
      WHERE to_regclass('public.ka_gochara_eval_window_verification') IS NOT NULL
    UNION ALL SELECT 'migration_1240_already_applied', 'ka_gochara_eval_window.objective'
      WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public'
                    AND table_name = 'ka_gochara_eval_window' AND column_name IN ('objective', 'objective_value', 'qualification'))
  )
  SELECT string_agg(failure || ' (' || detail || ')', ', ') INTO failures FROM f;
  IF failures IS NOT NULL THEN
    RAISE EXCEPTION 'preflight 1240 BLOCKED: %', failures;
  END IF;
END;
$$;

-- ── 1. the window's own provenance (nullable; the 1233 pattern) ───────────────
CREATE OR REPLACE FUNCTION public.ka_gochara_window_qualification_ok(q jsonb)
RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path = pg_catalog, public AS $$
  SELECT q IS NULL OR (
    jsonb_typeof(q) = 'object'
    AND q ?& ARRAY['unqualified_reason', 'unresolved', 'affected_channels', 'members', 'qualified_members']
    AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys(q) k
                    WHERE k NOT IN ('unqualified_reason', 'unresolved', 'affected_channels', 'members', 'qualified_members'))
    AND (jsonb_typeof(q -> 'unqualified_reason') IN ('string', 'null'))
    AND jsonb_typeof(q -> 'unresolved') = 'object'
    AND jsonb_typeof(q -> 'affected_channels') = 'array'
    AND jsonb_typeof(q -> 'members') = 'number' AND jsonb_typeof(q -> 'qualified_members') = 'number'
    AND NOT EXISTS (SELECT 1 FROM jsonb_array_elements(q -> 'affected_channels') c
                    WHERE c NOT IN ('"evidence_for_occurrence"'::jsonb, '"evidence_against_occurrence"'::jsonb))
    AND NOT EXISTS (SELECT 1 FROM jsonb_each(q -> 'unresolved') u WHERE jsonb_typeof(u.value) <> 'number'));
$$;

ALTER TABLE public.ka_gochara_eval_window
  ADD COLUMN objective       TEXT,
  ADD COLUMN objective_value REAL,
  ADD COLUMN qualification   JSONB;

ALTER TABLE public.ka_gochara_eval_window
  ADD CONSTRAINT kgew_objective_token_ck CHECK (objective IS NULL OR objective ~ '^[a-z][a-z0-9_]*$'),
  ADD CONSTRAINT kgew_objective_value_ck CHECK (public.ka_gochara_finite_nonneg_ok(objective_value) IS TRUE),
  ADD CONSTRAINT kgew_qualification_shape_ck CHECK (public.ka_gochara_window_qualification_ok(qualification) IS TRUE),
  ADD CONSTRAINT kgew_provenance_pair_ck CHECK ((objective IS NULL) = (qualification IS NULL)),
  -- an UNQUALIFIED window carries no numeric result (the frozen qualification policy: peak, score and evidence NULL)
  ADD CONSTRAINT kgew_unqualified_no_result_ck CHECK (
    qualification IS NULL OR (qualification -> 'unqualified_reason') = 'null'::jsonb
    OR (peak_instant IS NULL AND score IS NULL AND evidence_for IS NULL AND evidence_against IS NULL
        AND objective_value IS NULL));

COMMENT ON COLUMN public.ka_gochara_eval_window.objective IS
  'A5.3 R8-4: the NAME of the function the peak maximises (max_min_agent_activity | evidence_for_per_root_sum).';
COMMENT ON COLUMN public.ka_gochara_eval_window.objective_value IS
  'A5.3 R8-4: that function''s value at the peak — distinct from `score` (the max live record product). NULL when unqualified.';
COMMENT ON COLUMN public.ka_gochara_eval_window.qualification IS
  'A5.3 R8-4: structured qualification provenance {unqualified_reason, unresolved{reason:records}, affected_channels[], members, qualified_members} — closed keys.';

-- ── 2. the verification result ────────────────────────────────────────────────
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
  verified_at             timestamptz NOT NULL DEFAULT now(),

  PRIMARY KEY (chart_id, generation, event_class, path_id, rule_version),
  CONSTRAINT kgewv_header_fk FOREIGN KEY (chart_id, generation, event_class)
    REFERENCES public.ka_gochara_search_inventory (chart_id, generation, event_class) ON DELETE CASCADE,
  CONSTRAINT kgewv_pin_fk FOREIGN KEY (chart_id, generation, event_class, path_id, rule_version)
    REFERENCES public.ka_gochara_search_path_pin (chart_id, generation, event_class, path_id, rule_version)
    ON DELETE CASCADE,
  CONSTRAINT kgewv_rule_fk FOREIGN KEY (path_id, rule_version)
    REFERENCES public.ka_gochara_rule_path (path_id, rule_version),
  CONSTRAINT kgewv_canonical_chart_ck CHECK (chart_id = '482012f1-710e-4a25-994a-93821f5871aa'::uuid),
  CONSTRAINT kgewv_generation_governed_ck CHECK (public.ka_gochara_generation_governed(generation) IS TRUE),
  CONSTRAINT kgewv_event_class_ck CHECK (event_class IN (
    'achievement_recognition','bereavement','birth_anchor',
    'business_launch','career_advancement','career_change',
    'career_entry','career_setback','childbirth',
    'chronic_onset','education_milestone','exam_outcome',
    'financial_deception','foreign_settlement','illness_acute',
    'major_gain','major_loss','marriage','parental_event',
    'property_acquisition','psychological_arc','relocation',
    'romantic_start','separation','spiritual_turn','surgery',
    'travel_event')),
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
  -- VERIFIED is a claim about EVERY expected window and EVERY governed field
  CONSTRAINT kgewv_verified_total_ck CHECK (status <> 'VERIFIED' OR (
      windows_unverified = 0 AND windows_reproduced = windows_stored AND windows_stored = windows_expected
      AND expected_windows_digest = stored_windows_digest)),
  CONSTRAINT kgewv_unverified_dynamic_ck CHECK (status <> 'UNVERIFIED_DYNAMIC' OR windows_unverified > 0),
  CONSTRAINT kgewv_fields_ck CHECK (cardinality(fields_verified) > 0)
);

COMMENT ON TABLE public.ka_gochara_eval_window_verification IS
  'A5.3 R8-4: the INDEPENDENT window verifier''s generation-bound result per window grain. Written by the VERIFIER role '
  'only (the builder holds no privilege on it); the seal trigger ka_gochara_generation_seal_zz_window_verified consumes '
  'it. Independence of the verifier is a process property.';

-- ── 3. digests over the STORED rows (IEEE bits for REAL; NULL distinct from JSON null) ─────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_f4_token(r real)
RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path = pg_catalog, public AS $$
  SELECT CASE WHEN r IS NULL THEN jsonb_build_object('null', true)
              ELSE jsonb_build_object('f4', encode(float4send(r), 'hex')) END;
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_eval_window_content_digest(
  p_chart uuid, p_generation text, p_class text, p_path text, p_version text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(COALESCE((
    SELECT jsonb_agg(jsonb_build_object(
             'interval', jsonb_build_array(to_char(lower(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
                                           to_char(upper(w.interval) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')),
             'peak', CASE WHEN w.peak_instant IS NULL THEN jsonb_build_object('null', true)
                          ELSE jsonb_build_object('t', to_char(w.peak_instant AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')) END,
             'score', public.ka_gochara_f4_token(w.score),
             'evidence_for', public.ka_gochara_f4_token(w.evidence_for),
             'evidence_against', public.ka_gochara_f4_token(w.evidence_against),
             'severity', public.ka_gochara_f4_token(w.severity),
             'objective_value', public.ka_gochara_f4_token(w.objective_value),
             'valence', w.outcome_valence_for_native,
             'objective', CASE WHEN w.objective IS NULL THEN jsonb_build_object('null', true)
                               ELSE jsonb_build_object('s', w.objective) END,
             'qualification', CASE WHEN w.qualification IS NULL THEN jsonb_build_object('null', true)
                                   ELSE jsonb_build_object('q', w.qualification) END,
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

-- the EXPECTED window set, recomputed from the admitted scored records' supports (Codex round 6 R3: one window per maximal
-- connected component of the prerequisite-satisfied support; P4 — the intersection of the Jupiter and Saturn unions).
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

-- ── 4. the gates ──────────────────────────────────────────────────────────────

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
    WHERE s.chart_id = p_chart AND s.generation = p_generation),
  required_fields AS (
    SELECT ARRAY['evidence_against','evidence_for','interval','membership','null_states_used','objective',
                 'objective_value','outcome_valence_for_native','peak_instant','qualification','score',
                 'severity']::text[] AS f)
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
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_field_coverage_short'::text,
         array_to_string(ARRAY(SELECT f FROM unnest((SELECT f FROM required_fields)) f
                               WHERE NOT (f = ANY (v.fields_verified))), ',')::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND NOT ((SELECT f FROM required_fields) <@ v.fields_verified)
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
    AND v.input_digest IS DISTINCT FROM (SELECT input_digest FROM snap)
  UNION ALL
  SELECT e.event_class, e.path_id, e.rule_version, 'window_provenance_missing'::text,
         (count(*) || ' stored window(s) carry no objective/qualification provenance')::text
  FROM expected e
  JOIN public.ka_gochara_eval_window w
    ON (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
     = (p_chart, p_generation, e.event_class, e.path_id, e.rule_version)
  WHERE w.objective IS NULL OR w.qualification IS NULL
  GROUP BY e.event_class, e.path_id, e.rule_version;
$$;

COMMENT ON FUNCTION public.ka_gochara_window_verification_violations(uuid, text) IS
  'A5.3 R8-4: the window half of the first-seal gate — empty iff every included P1–P4 grain has a VERIFIED, current, '
  'input-bound, full-field-coverage verification matching the database recomputation, and its windows carry provenance. '
  'UNVERIFIED_DYNAMIC, FAILED and missing results fail it.';

-- REPLAY of an already-sealed generation: integrity only. A generation sealed before 1240 has no rows and must still
-- replay; rows that exist must still equal the frozen windows. Never reads today's catalogue.
CREATE OR REPLACE FUNCTION public.ka_gochara_window_verification_replay_violations(p_chart uuid, p_generation text)
RETURNS TABLE (event_class text, path_id text, rule_version text, violation text, detail text)
LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_stale'::text,
         'a verification row no longer equals the sealed windows'::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.windows_content_digest IS DISTINCT FROM public.ka_gochara_eval_window_content_digest(
          v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version);
$$;

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
  'verification violations. No 1206/1232 function is redefined.';

-- ── 5. the write guard (the 1206 trio) ────────────────────────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_window_verification_write_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE ch uuid; gen text; cls text;
BEGIN
  IF TG_OP = 'UPDATE' THEN
    RAISE EXCEPTION 'ka_gochara_eval_window_verification is insert-only: UPDATE refused — a changed result is DELETE + INSERT in the candidate generation';
  END IF;
  IF TG_OP = 'DELETE' THEN ch := OLD.chart_id; gen := OLD.generation; cls := OLD.event_class;
  ELSE ch := NEW.chart_id; gen := NEW.generation; cls := NEW.event_class; END IF;
  PERFORM public.ka_gochara_lock_chart(ch);                       -- chart EXCLUSIVE first (N13)
  IF public.ka_gochara_generation_is_sealed(ch, gen) THEN
    RAISE EXCEPTION 'ka_gochara_eval_window_verification is publication-immutable: (chart %, generation %) is SEALED — % refused',
      ch, gen, TG_OP;
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  PERFORM public.ka_gochara_lock_global_shared();                 -- … then global SHARED (before any registry read)
  -- the header precondition (mirrors 1206): a FINALISED inventory and an INCLUDED pin for the grain
  IF NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_inventory i
                 WHERE (i.chart_id, i.generation, i.event_class) = (NEW.chart_id, NEW.generation, NEW.event_class)
                   AND i.inventory_digest IS NOT NULL) THEN
    RAISE EXCEPTION 'ka_gochara_eval_window_verification refused: the inventory (%, %, %) is absent or not FINALISED',
      NEW.chart_id, NEW.generation, NEW.event_class;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.ka_gochara_search_path_pin p
                 WHERE (p.chart_id, p.generation, p.event_class, p.path_id, p.rule_version)
                     = (NEW.chart_id, NEW.generation, NEW.event_class, NEW.path_id, NEW.rule_version)
                   AND p.disposition = 'included') THEN
    RAISE EXCEPTION 'ka_gochara_eval_window_verification refused: no INCLUDED pin for (%, %, %, %, %)',
      NEW.chart_id, NEW.generation, NEW.event_class, NEW.path_id, NEW.rule_version;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER ka_gochara_ewv_0_statement_lock
  BEFORE UPDATE OR DELETE ON public.ka_gochara_eval_window_verification
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_chart_statement_lock();
CREATE TRIGGER ka_gochara_ewv_1_write_guard
  BEFORE INSERT OR UPDATE OR DELETE ON public.ka_gochara_eval_window_verification
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_window_verification_write_guard();
CREATE TRIGGER ka_gochara_ewv_2_sealed_path_check
  BEFORE INSERT ON public.ka_gochara_eval_window_verification
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_require_sealed_rule_path();
CREATE TRIGGER ka_gochara_ewv_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_eval_window_verification
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_refuse_truncate();

-- ── 6. the seal trigger (ONE additive BEFORE INSERT trigger, firing AFTER 1206's) ─────────────────────

CREATE OR REPLACE FUNCTION public.ka_gochara_generation_seal_window_guard()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
DECLARE existing uuid; n integer; msg text;
BEGIN
  PERFORM public.ka_gochara_lock_chart(NEW.chart_id);          -- chart EXCLUSIVE first …
  PERFORM public.ka_gochara_lock_global_shared();               -- … then global SHARED (no new family key)
  SELECT s.manifest_id INTO existing FROM public.ka_gochara_generation_seal s
  WHERE s.chart_id = NEW.chart_id AND s.generation = NEW.generation;
  IF FOUND THEN
    -- REPLAY (ka_gochara_seal_generation inserts ON CONFLICT DO NOTHING; the BEFORE triggers fire first). A generation
    -- sealed before 1240 has no verification rows and replays cleanly; existing rows must still agree.
    SELECT count(*), string_agg(v.event_class || '/' || v.path_id || ':' || v.violation, '; ') INTO n, msg
    FROM public.ka_gochara_window_verification_replay_violations(NEW.chart_id, NEW.generation) v;
    IF n > 0 THEN
      RAISE EXCEPTION 'ka_gochara_generation_seal replay refused (window verification integrity): %', msg;
    END IF;
    RETURN NEW;
  END IF;
  SELECT count(*), string_agg(v.event_class || '/' || v.path_id || '@' || v.rule_version || ':' || v.violation || ':' || v.detail,
                              E'\n  ' ORDER BY v.event_class, v.path_id, v.violation)
    INTO n, msg
  FROM public.ka_gochara_window_verification_violations(NEW.chart_id, NEW.generation) v;
  IF n > 0 THEN
    RAISE EXCEPTION 'ka_gochara_generation_seal refused (window verification): % violation(s) for (chart %, generation %):%  %',
      n, NEW.chart_id, NEW.generation, E'\n', msg;
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER ka_gochara_generation_seal_zz_window_verified
  BEFORE INSERT ON public.ka_gochara_generation_seal
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_generation_seal_window_guard();

-- ── 7. privileges (role-existence-guarded; explicit; table-level; no SECURITY DEFINER) ─────────────────
-- The builder gets NOTHING on the verification table. The VERIFIER writes it (INSERT; pre-seal DELETE — enforced by the
-- write guard) and reads what it verifies; the SEALER reads it and runs the gate (the seal trigger fires as the sealing
-- role). EXECUTE lists were derived by running the real flows as these roles under a PUBLIC-EXECUTE-revoked schema and
-- adding one grant per `permission denied` until the suite converged (the live tests are the detector).
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN
    GRANT SELECT, INSERT, DELETE ON public.ka_gochara_eval_window_verification TO gochara_verifier;
    GRANT SELECT ON
      public.ka_gochara_eval_window, public.ka_gochara_eval_window_record,
      public.ka_gochara_relationship_record, public.ka_gochara_contact, public.ka_gochara_physical_object,
      public.kala_gochara_coverage, public.ka_gochara_search_inventory, public.ka_gochara_search_path_pin,
      public.ka_gochara_search_input_snapshot, public.ka_gochara_generation_seal,
      public.ka_gochara_rule_path, public.ka_gochara_rule_path_seal,
      public.ka_gochara_rule_path_soft_factor, public.ka_gochara_factor
      TO gochara_verifier;
    GRANT EXECUTE ON FUNCTION
      public.ka_gochara_lock_chart(uuid), public.ka_gochara_lock_global_shared(),
      public.ka_gochara_generation_is_sealed(uuid, text), public.ka_gochara_generation_governed(text),
      public.ka_gochara_eval_window_content_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_stored_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_expected_digest(uuid, text, text, text, text),
      public.ka_gochara_canonical_json(jsonb), public.ka_gochara_sha256_hex(text),
      public.ka_gochara_f4_token(real)
      TO gochara_verifier;
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer') THEN
    GRANT SELECT ON public.ka_gochara_eval_window_verification TO gochara_sealer;
    GRANT SELECT ON
      public.ka_gochara_eval_window, public.ka_gochara_eval_window_record,
      public.ka_gochara_relationship_record, public.ka_gochara_search_path_pin,
      public.ka_gochara_search_input_snapshot, public.ka_gochara_generation_seal
      TO gochara_sealer;
    GRANT EXECUTE ON FUNCTION
      public.ka_gochara_window_verification_violations(uuid, text),
      public.ka_gochara_window_verification_replay_violations(uuid, text),
      public.ka_gochara_candidate_gate_violations(uuid, text),
      public.ka_gochara_eval_window_content_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_stored_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_expected_digest(uuid, text, text, text, text),
      public.ka_gochara_f4_token(real),
      public.ka_gochara_canonical_json(jsonb), public.ka_gochara_sha256_hex(text),
      public.ka_gochara_lock_chart(uuid), public.ka_gochara_lock_global_shared()
      TO gochara_sealer;
  END IF;
END;
$$;

-- ── Presence checks ────────────────────────────────────────────────────────────
DO $$
DECLARE missing text; n integer;
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
  SELECT count(*) INTO n FROM pg_trigger t
  WHERE t.tgrelid = 'public.ka_gochara_generation_seal'::regclass AND NOT t.tgisinternal
    AND t.tgname = 'ka_gochara_generation_seal_zz_window_verified';
  IF n <> 1 THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: the seal trigger is not present exactly once';
  END IF;
  SELECT string_agg(x.sig, ', ') INTO missing
  FROM (VALUES
    ('public.ka_gochara_f4_token(real)'),
    ('public.ka_gochara_eval_window_content_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_eval_window_stored_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_eval_window_expected_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_window_verification_violations(uuid,text)'),
    ('public.ka_gochara_window_verification_replay_violations(uuid,text)'),
    ('public.ka_gochara_candidate_gate_violations(uuid,text)'),
    ('public.ka_gochara_window_verification_write_guard()'),
    ('public.ka_gochara_generation_seal_window_guard()'),
    ('public.ka_gochara_window_qualification_ok(jsonb)')) AS x(sig)
  WHERE to_regprocedure(x.sig) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: missing functions: %', missing;
  END IF;
  SELECT count(*) INTO n FROM pg_constraint c
  WHERE c.conrelid = 'public.ka_gochara_eval_window'::regclass
    AND c.conname IN ('kgew_objective_token_ck', 'kgew_objective_value_ck', 'kgew_qualification_shape_ck',
                      'kgew_provenance_pair_ck', 'kgew_unqualified_no_result_ck');
  IF n <> 5 THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: expected 5 window provenance constraints, found %', n;
  END IF;
  RAISE NOTICE 'migration 1240: presence checks passed';
END;
$$;
