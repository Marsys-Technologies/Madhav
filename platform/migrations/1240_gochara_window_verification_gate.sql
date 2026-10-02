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
    UNION ALL SELECT 'migration_1233_not_applied', 'ka_gochara_relationship_record.period_anchor_lord'
      WHERE NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public'
                        AND table_name = 'ka_gochara_relationship_record' AND column_name = 'period_anchor_lord')
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
    AND q ?& ARRAY['policy', 'unqualified_reason', 'unresolved', 'affected_channels', 'members', 'qualified_members']
    AND NOT EXISTS (SELECT 1 FROM jsonb_object_keys(q) k
                    WHERE k NOT IN ('policy', 'unqualified_reason', 'unresolved', 'affected_channels', 'members', 'qualified_members'))
    -- R9-1: the result policy this window was drafted under — one of the two NAMED policies
    AND (q -> 'policy') IN ('"all_null_candidate/1"'::jsonb, '"window_qualification/1"'::jsonb)
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
        AND objective_value IS NULL)),
  -- R9-1: under `all_null_candidate/1` EVERY numerical result field is NULL, the peak absent, the valence unqualified,
  -- for every path and channel composition (constant objectives and empty sums included)
  ADD CONSTRAINT kgew_all_null_policy_ck CHECK (
    qualification IS NULL OR (qualification ->> 'policy') IS DISTINCT FROM 'all_null_candidate/1'
    OR (peak_instant IS NULL AND score IS NULL AND evidence_for IS NULL AND evidence_against IS NULL
        AND severity IS NULL AND objective_value IS NULL
        AND outcome_valence_for_native = 'unqualified'
        AND (qualification ->> 'unqualified_reason') = 'all_null_candidate_policy'));

COMMENT ON COLUMN public.ka_gochara_eval_window.objective IS
  'A5.3 R8-4: the NAME of the function the peak maximises (max_min_agent_activity | evidence_for_per_root_sum).';
COMMENT ON COLUMN public.ka_gochara_eval_window.objective_value IS
  'A5.3 R8-4: that function''s value at the peak — distinct from `score` (the max live record product). NULL when unqualified.';
COMMENT ON COLUMN public.ka_gochara_eval_window.qualification IS
  'A5.3 R8-4/R9-1: structured qualification provenance {policy, unqualified_reason, unresolved{reason:records}, affected_channels[], members, qualified_members} — closed keys.';

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
  -- R9-2: the digest of EVERY derivation input of the grain (records, their prerequisites, contacts, the snapshot's
  -- input identity, the manifest vector and policy) as the verifier saw it; the gate recomputes it, so a record
  -- inserted (or a prerequisite/contact/manifest changed) after verification invalidates the stored verification
  derivation_inputs_digest text       NOT NULL,
  -- R10-4 / AM-24 item 4: the identity of the RUNNER that executed the verification — its code commit, the digest of the
  -- implementation modules it ran (which must be the ones the manifest vector pinned: the gate compares it to the vector's
  -- `implementation`), its runtime and login. The database cannot prove the runner computed independently; it records WHAT ran
  -- and refuses a row that does not name a commit or whose code is not the pinned code.
  runner_identity         jsonb       NOT NULL,
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
  CONSTRAINT kgewv_runner_identity_ck CHECK (jsonb_typeof(runner_identity) = 'object'
    AND btrim(COALESCE(runner_identity ->> 'commit', '')) <> ''
    AND COALESCE(runner_identity ->> 'implementation_digest', '') ~ '^[0-9a-f]{64}$'),
  CONSTRAINT kgewv_status_ck CHECK (status IN ('VERIFIED', 'UNVERIFIED_DYNAMIC', 'FAILED')),
  CONSTRAINT kgewv_counts_ck CHECK (windows_expected >= 0 AND windows_stored >= 0
                                    AND windows_reproduced >= 0 AND windows_unverified >= 0
                                    AND windows_reproduced + windows_unverified <= windows_stored),
  CONSTRAINT kgewv_digests_ck CHECK (expected_windows_digest ~ '^[0-9a-f]{64}$'
                                     AND stored_windows_digest ~ '^[0-9a-f]{64}$'
                                     AND windows_content_digest ~ '^[0-9a-f]{64}$'
                                     AND input_digest ~ '^[0-9a-f]{64}$'
                                     AND derivation_inputs_digest ~ '^[0-9a-f]{64}$'),
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

-- R9-2 / R10-2: the digest of the COMPLETE SEMANTIC DEPENDENCY SET of the window derivation — preimage version 'inputs/2'.
--   records   every record of the grain: identity, agent, relation, kind, object role, operator role, PROVENANCE, RULING,
--             admission, house, frame (kind, arg), affected person, anchor, target, contact, support state and supports, and
--             EVERY result field (evidence for/against, severity — as the text the database prints for the REAL — and the
--             valence): a post-verification delete+reinsert of a record with a number in it changes this digest;
--   prerequisites   each record's declared-prerequisite results;
--   contacts  EVERY contact of the generation (not only those a surviving record references — a contact whose records were
--             all removed is still a dependency) with the fields the geometry certification reads: identity, body,
--             relation, target, t_in, t_out, t_exact, solver, delta_lambda, delta_t, precision regime;
--   input / manifest / policy  the snapshot's input identity, the manifest vector (digest) and the result policy.
-- The independent verifier builds the SAME canonical preimage in Python from its own reads (`window_gate`); the gate
-- recomputes this one, so any later change to any of it makes the stored verification stale at the seal.
CREATE OR REPLACE FUNCTION public.ka_gochara_eval_window_inputs_digest(
  p_chart uuid, p_generation text, p_class text, p_path text, p_version text)
RETURNS text LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  WITH recs AS (
    SELECT r.record_id, r.agent, r.relation, r.object_kind, r.object_role, r.operator_role, r.provenance, r.ruling_ref,
           r.admission_state, r.house_from_frame, r.frame_kind, r.frame_arg, r.affected_person, r.temporal_support_state,
           r.period_anchor_lord, r.period_anchor_level, r.contact_id, r.temporal_support_intervals, o.canonical_target,
           r.evidence_for_occurrence, r.evidence_against_occurrence, r.severity, r.outcome_valence_for_native
    FROM public.ka_gochara_relationship_record r
    JOIN public.ka_gochara_physical_object o ON o.physical_object_id = r.object_id
    WHERE (r.chart_id, r.generation, r.event_class, r.path_id, r.rule_version)
        = (p_chart, p_generation, p_class, p_path, p_version))
  SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(jsonb_build_object(
    'version', 'inputs/2',
    'records', COALESCE((SELECT jsonb_agg(jsonb_build_object(
        'id', r.record_id::text, 'agent', r.agent, 'relation', r.relation, 'kind', r.object_kind,
        'object_role', r.object_role, 'role', r.operator_role, 'provenance', r.provenance, 'ruling', r.ruling_ref,
        'admission', r.admission_state, 'house', r.house_from_frame,
        'frame_kind', r.frame_kind, 'frame_arg', r.frame_arg, 'person', r.affected_person,
        'support_state', r.temporal_support_state,
        'anchor', jsonb_build_array(r.period_anchor_lord, r.period_anchor_level),
        'target', r.canonical_target, 'contact', r.contact_id::text,
        'evidence_for', r.evidence_for_occurrence::text, 'evidence_against', r.evidence_against_occurrence::text,
        'severity', r.severity::text, 'valence', r.outcome_valence_for_native,
        'supports', COALESCE((SELECT jsonb_agg(jsonb_build_array(
                       to_char(lower(x) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
                       to_char(upper(x) AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"')) ORDER BY lower(x))
                     FROM unnest(r.temporal_support_intervals) x), '[]'::jsonb))
        ORDER BY r.record_id::text) FROM recs r), '[]'::jsonb),
    'prerequisites', COALESCE((SELECT jsonb_agg(jsonb_build_array(
        pr.record_id::text, pr.ordinal, pr.predicate_id, pr.predicate_rule_version, pr.result)
        ORDER BY pr.record_id::text, pr.ordinal)
      FROM public.ka_gochara_record_prerequisite pr WHERE pr.record_id IN (SELECT record_id FROM recs)), '[]'::jsonb),
    'contacts', COALESCE((SELECT jsonb_agg(jsonb_build_array(
        c.contact_id::text, c.body, c.relation_kind, o.canonical_target,
        to_char(c.t_in AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        to_char(c.t_out AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        to_char(c.t_exact AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
        c.solver_method, c.delta_lambda::text, c.delta_t::text, c.precision_regime) ORDER BY c.contact_id::text)
      FROM public.ka_gochara_contact c
      JOIN public.ka_gochara_physical_object o ON o.physical_object_id = c.physical_object_id
      WHERE c.chart_id = p_chart AND c.generation = p_generation), '[]'::jsonb),
    'input', (SELECT s.input_digest FROM public.ka_gochara_search_input_snapshot s
              WHERE s.chart_id = p_chart AND s.generation = p_generation),
    'manifest', (SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(p.input_generation_vector))
                 FROM public.kala_gochara_publication p WHERE p.chart_id = p_chart AND p.generation = p_generation),
    'policy', (SELECT p.input_generation_vector ->> 'result_policy'
               FROM public.kala_gochara_publication p WHERE p.chart_id = p_chart AND p.generation = p_generation)
  )));
$$;

-- ── 4. the gates ──────────────────────────────────────────────────────────────

-- R12-1: the LEGACY projection relations (`kala_gochara_contacts`, `kala_gochara_windows`) are not part of the '5.0' candidate: its writer
-- writes none, publication consumes the first's content and the second's count, and a numeric legacy row would falsify the all-NULL
-- disclosure. For a governed generation NONE may exist. Dynamic and table-existence-guarded (a relation that does not exist holds no
-- rows); invoker rights (the caller needs SELECT on the columns it reads — chart_id, generation).
CREATE OR REPLACE FUNCTION public.ka_gochara_legacy_projection_rows(p_chart uuid, p_generation text)
RETURNS TABLE (relation text, n bigint) LANGUAGE plpgsql STABLE SET search_path = pg_catalog, public AS $$
DECLARE t text; c bigint;
BEGIN
  FOREACH t IN ARRAY ARRAY['kala_gochara_contacts', 'kala_gochara_windows'] LOOP
    IF to_regclass('public.' || t) IS NOT NULL THEN
      EXECUTE format('SELECT count(*) FROM public.%I WHERE chart_id = $1 AND generation = $2', t) INTO c USING p_chart, p_generation;
      IF c > 0 THEN relation := t; n := c; RETURN NEXT; END IF;
    END IF;
  END LOOP;
END;
$$;

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
                 'severity']::text[] AS f),
  -- R9-1: the policy the generation's MANIFEST selected (the vector's `result_policy`), the only source of truth
  mp AS (
    SELECT p.input_generation_vector ->> 'result_policy' AS pol
    FROM public.kala_gochara_publication p WHERE p.chart_id = p_chart AND p.generation = p_generation)
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
  SELECT e.event_class, e.path_id, e.rule_version, 'result_policy_not_selected'::text,
         'the manifest vector selects no known result policy'::text
  FROM expected e
  WHERE NOT EXISTS (SELECT 1 FROM mp WHERE mp.pol IN ('all_null_candidate/1', 'window_qualification/1'))
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_policy_unknown'::text, v.policy_version
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.policy_version NOT IN ('all_null_candidate/1', 'window_qualification/1')
  UNION ALL
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_policy_differs_from_manifest'::text,
         (v.policy_version || ' vs ' || COALESCE((SELECT pol FROM mp), 'none'))::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.policy_version IS DISTINCT FROM (SELECT pol FROM mp)
  UNION ALL
  -- R11-1: GENERATION-WIDE — every window of the generation, whatever grain it sits in (an excluded / superseded / held
  -- version's window is not exempt because no verification covers it)
  SELECT w.event_class, w.path_id, w.rule_version, 'window_policy_differs_from_manifest'::text,
         (count(*) || ' window(s) were drafted under a policy other than the manifest''s')::text
  FROM public.ka_gochara_eval_window w
  WHERE w.chart_id = p_chart AND w.generation = p_generation
    AND w.qualification IS NOT NULL AND (w.qualification ->> 'policy') IS DISTINCT FROM (SELECT pol FROM mp)
  GROUP BY w.event_class, w.path_id, w.rule_version
  UNION ALL
  -- the all-NULL policy: a window that carries ANY number (or a peak, or a valence other than unqualified) is refused —
  -- in EVERY grain of the generation
  SELECT w.event_class, w.path_id, w.rule_version, 'window_carries_a_number_under_all_null_policy'::text,
         (count(*) || ' window(s) carry a numerical result or peak while all_null_candidate/1 is in force')::text
  FROM public.ka_gochara_eval_window w
  WHERE w.chart_id = p_chart AND w.generation = p_generation
    AND (SELECT pol FROM mp) = 'all_null_candidate/1'
    AND (w.peak_instant IS NOT NULL OR w.score IS NOT NULL OR w.evidence_for IS NOT NULL
         OR w.evidence_against IS NOT NULL OR w.severity IS NOT NULL OR w.objective_value IS NOT NULL
         OR w.outcome_valence_for_native IS DISTINCT FROM 'unqualified')
  GROUP BY w.event_class, w.path_id, w.rule_version
  UNION ALL
  SELECT '*'::text, NULL::text, NULL::text, 'legacy_projection_rows_present'::text,
         (l.n || ' row(s) in ' || l.relation || ' for this generation — none may exist (the all-NULL candidate''s writer writes none; a numeric legacy row would falsify the all-NULL disclosure)')::text
  FROM public.ka_gochara_legacy_projection_rows(p_chart, p_generation) l
  UNION ALL
  -- R11-1: the generation's PERMITTED OUTPUT GRAINS are exactly the grains its inventory INCLUDES on a windowed path (P1–P4,
  -- the `expected` CTE). A relationship record, a window or a membership link in ANY other (class, path, version) — a
  -- sealed-but-superseded version, a held path (P5), a class with no pin — is output nothing verified and nothing digests
  -- (it may reuse an existing contact, so no contact/inventory digest moves): refused outright.
  SELECT r.event_class, r.path_id, r.rule_version, 'output_grain_not_permitted'::text,
         (count(*) || ' relationship record(s) sit in a grain this generation''s inventory does not include')::text
  FROM public.ka_gochara_relationship_record r
  WHERE r.chart_id = p_chart AND r.generation = p_generation
    AND NOT EXISTS (SELECT 1 FROM expected e WHERE (e.event_class, e.path_id, e.rule_version)
                                                  = (r.event_class, r.path_id, r.rule_version))
  GROUP BY r.event_class, r.path_id, r.rule_version
  UNION ALL
  SELECT w.event_class, w.path_id, w.rule_version, 'output_grain_not_permitted'::text,
         (count(*) || ' window(s) sit in a grain this generation''s inventory does not include')::text
  FROM public.ka_gochara_eval_window w
  WHERE w.chart_id = p_chart AND w.generation = p_generation
    AND NOT EXISTS (SELECT 1 FROM expected e WHERE (e.event_class, e.path_id, e.rule_version)
                                                  = (w.event_class, w.path_id, w.rule_version))
  GROUP BY w.event_class, w.path_id, w.rule_version
  UNION ALL
  SELECT l.event_class, l.path_id, l.rule_version, 'output_grain_not_permitted'::text,
         (count(*) || ' window-membership link(s) sit in a grain this generation''s inventory does not include')::text
  FROM public.ka_gochara_eval_window_record l
  WHERE l.chart_id = p_chart AND l.generation = p_generation
    AND NOT EXISTS (SELECT 1 FROM expected e WHERE (e.event_class, e.path_id, e.rule_version)
                                                  = (l.event_class, l.path_id, l.rule_version))
  GROUP BY l.event_class, l.path_id, l.rule_version
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
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_inputs_changed'::text,
         'a record, prerequisite, contact, manifest or input revision changed after the windows were verified'::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.derivation_inputs_digest IS DISTINCT FROM public.ka_gochara_eval_window_inputs_digest(
          v.chart_id, v.generation, v.event_class, v.path_id, v.rule_version)
  UNION ALL
  -- COMPLETE expected membership, both directions (the builder's own post-write check is not a seal-time invariant):
  -- every admitted scored record whose support overlaps a window is a member, no other record is, and no admitted record
  -- with a support sits in no window
  SELECT e.event_class, e.path_id, e.rule_version, 'window_membership_not_expected'::text,
         (m.missing || ' overlapping admitted record(s) not members, ' || m.extra || ' unexpected member link(s), '
          || m.orphans || ' admitted record(s) in no window')::text
  FROM expected e
  CROSS JOIN LATERAL (
    SELECT
      (SELECT count(*) FROM (
         SELECT w.window_id, r.record_id FROM public.ka_gochara_eval_window w
         JOIN public.ka_gochara_relationship_record r
           ON (r.chart_id, r.generation, r.event_class, r.path_id, r.rule_version)
            = (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
          AND r.admission_state = 'admitted' AND r.operator_role = 'scored'
         WHERE (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
             = (p_chart, p_generation, e.event_class, e.path_id, e.rule_version)
           AND EXISTS (SELECT 1 FROM unnest(r.temporal_support_intervals) x WHERE x && w.interval)
         EXCEPT
         SELECT l.window_id, l.record_id FROM public.ka_gochara_eval_window_record l
         WHERE (l.chart_id, l.generation, l.event_class, l.path_id, l.rule_version)
             = (p_chart, p_generation, e.event_class, e.path_id, e.rule_version)) z) AS missing,
      (SELECT count(*) FROM (
         SELECT l.window_id, l.record_id FROM public.ka_gochara_eval_window_record l
         WHERE (l.chart_id, l.generation, l.event_class, l.path_id, l.rule_version)
             = (p_chart, p_generation, e.event_class, e.path_id, e.rule_version)
         EXCEPT
         SELECT w.window_id, r.record_id FROM public.ka_gochara_eval_window w
         JOIN public.ka_gochara_relationship_record r
           ON (r.chart_id, r.generation, r.event_class, r.path_id, r.rule_version)
            = (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
          AND r.admission_state = 'admitted' AND r.operator_role = 'scored'
         WHERE (w.chart_id, w.generation, w.event_class, w.path_id, w.rule_version)
             = (p_chart, p_generation, e.event_class, e.path_id, e.rule_version)
           AND EXISTS (SELECT 1 FROM unnest(r.temporal_support_intervals) x WHERE x && w.interval)) z) AS extra,
      (SELECT count(*) FROM public.ka_gochara_relationship_record r
        WHERE (r.chart_id, r.generation, r.event_class, r.path_id, r.rule_version)
            = (p_chart, p_generation, e.event_class, e.path_id, e.rule_version)
          AND r.admission_state = 'admitted' AND r.operator_role = 'scored'
          AND cardinality(r.temporal_support_intervals) > 0
          AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_eval_window_record l WHERE l.record_id = r.record_id)) AS orphans
  ) m
  WHERE m.missing + m.extra + m.orphans > 0
  UNION ALL
  -- R10-4 / AM-24 item 4: the verification must name the code that ran, and that code must be the code the manifest PINNED
  -- (the vector's `implementation` digests — the verification-job modules are in the governed implementation identity)
  SELECT v.event_class, v.path_id, v.rule_version, 'window_verification_runner_not_pinned'::text,
         ('runner ' || COALESCE(v.runner_identity ->> 'commit', '?') || ' ran implementation '
          || COALESCE(v.runner_identity ->> 'implementation_digest', '?') || ', the manifest pins '
          || COALESCE((SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(p.input_generation_vector -> 'implementation'))
                       FROM public.kala_gochara_publication p WHERE p.chart_id = p_chart AND p.generation = p_generation), 'none'))::text
  FROM public.ka_gochara_eval_window_verification v
  WHERE v.chart_id = p_chart AND v.generation = p_generation
    AND v.runner_identity ->> 'implementation_digest' IS DISTINCT FROM (
          SELECT public.ka_gochara_sha256_hex(public.ka_gochara_canonical_json(p.input_generation_vector -> 'implementation'))
          FROM public.kala_gochara_publication p WHERE p.chart_id = p_chart AND p.generation = p_generation)
  UNION ALL
  -- R10-2 / R11-1: the manifest's result policy governs EVERY record result field of the GENERATION — every record in every
  -- grain, included or not, independently of the expected-verification CTE. No independent derivation of a record number
  -- exists under either known policy, so a record carries NULL evidence and severity and the `unqualified` valence
  SELECT r.event_class, r.path_id, r.rule_version, 'record_result_not_policy'::text,
         (count(*) || ' relationship record(s) carry a numeric evidence/severity or a qualified valence under the manifest policy')::text
  FROM public.ka_gochara_relationship_record r
  WHERE r.chart_id = p_chart AND r.generation = p_generation
    AND (r.evidence_for_occurrence IS NOT NULL OR r.evidence_against_occurrence IS NOT NULL
         OR r.severity IS NOT NULL OR r.outcome_valence_for_native <> 'unqualified')
  GROUP BY r.event_class, r.path_id, r.rule_version
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

-- ── 4b. the seal APPROVAL RECEIPT (R11-3) ──────────────────────────────────────────────────────────────────
-- A durable record, linked to the seal row, of WHAT was approved and by whom: the brief digest (the sha256 of the canonical
-- complete approval payload the sealing transaction recomputed under the seal locks and found equal), the approver login and the
-- workflow run the approval was given in. Append-only (UPDATE/DELETE/TRUNCATE refused). The database cannot make the sealing
-- workflow use the brief — the approval-gated workflow running as the sealer is part of the trusted system — but the receipt
-- exists only with a seal (FK), is immutable, and names the digest that was approved.
CREATE TABLE public.ka_gochara_seal_approval (
  chart_id        uuid        NOT NULL,
  generation      text        NOT NULL,
  manifest_id     uuid        NOT NULL,
  brief_digest    text        NOT NULL,
  approver_login  text        NOT NULL,
  approved_by_note text       NOT NULL,
  run_id          bigint      NOT NULL,
  run_attempt     integer     NOT NULL,
  workflow_commit text        NOT NULL,
  sealed_by       text        NOT NULL DEFAULT session_user,
  approved_at     timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (chart_id, generation),
  -- DEFERRED: the receipt and the seal row are written in ONE transaction (either order); a seal with no receipt is detectable
  -- (`ka_gochara_seal_receipt_missing`), and the sealer step calls it before COMMIT
  CONSTRAINT kgsa_seal_fk FOREIGN KEY (chart_id, generation)
    REFERENCES public.ka_gochara_generation_seal (chart_id, generation) DEFERRABLE INITIALLY DEFERRED,
  CONSTRAINT kgsa_digest_ck CHECK (brief_digest ~ '^[0-9a-f]{64}$'),
  CONSTRAINT kgsa_approver_ck CHECK (btrim(approver_login) <> ''),
  CONSTRAINT kgsa_commit_ck CHECK (btrim(workflow_commit) <> ''),
  CONSTRAINT kgsa_attempt_ck CHECK (run_attempt >= 1)
);
-- (a new table carries no PUBLIC privilege: PostgreSQL grants none by default, so no REVOKE is needed — and 1240 revokes nothing)
COMMENT ON TABLE public.ka_gochara_seal_approval IS
  'A5.3 R11-3: the approval receipt of a seal — brief digest (sha256 of the canonical approval payload recomputed under the seal '
  'locks), approver login + note, workflow run id/attempt, workflow commit. Append-only; FK to the seal row (deferred); inserted by '
  'the sealer in the sealing transaction. The grants on it are 1241''s.';

-- the sealer step calls this before COMMIT: TRUE iff the generation is sealed and no receipt exists for it
CREATE OR REPLACE FUNCTION public.ka_gochara_seal_receipt_missing(p_chart uuid, p_generation text)
RETURNS boolean LANGUAGE sql STABLE SET search_path = pg_catalog, public AS $$
  SELECT EXISTS (SELECT 1 FROM public.ka_gochara_generation_seal s WHERE s.chart_id = p_chart AND s.generation = p_generation)
     AND NOT EXISTS (SELECT 1 FROM public.ka_gochara_seal_approval a WHERE a.chart_id = p_chart AND a.generation = p_generation);
$$;

CREATE OR REPLACE FUNCTION public.ka_gochara_seal_approval_immutable()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  RAISE EXCEPTION 'ka_gochara_seal_approval is append-only: % refused', TG_OP;
END;
$$;
-- RECEIPT ATTRIBUTION (Codex round 12): `sealed_by` and `approved_at` are not caller-supplied facts. A BEFORE INSERT trigger SETS them —
-- whatever the sealer's INSERT carried — to the SESSION login (`session_user`, not a role switched to inside the session) and the
-- transaction's timestamp, so they are database-attested.
CREATE OR REPLACE FUNCTION public.ka_gochara_seal_approval_attest()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  NEW.sealed_by := session_user;
  NEW.approved_at := now();
  RETURN NEW;
END;
$$;
CREATE TRIGGER ka_gochara_seal_approval_attest
  BEFORE INSERT ON public.ka_gochara_seal_approval
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_seal_approval_attest();

-- …and a receipt is valid only for the FIRST SEAL OF THIS TRANSACTION with the SAME manifest: at COMMIT the seal row for (chart, generation)
-- must exist, name the receipt's manifest, and have been written in this very transaction (`sealed_at` is the transaction timestamp).
-- So a receipt cannot be attached to a generation sealed before 1240 (or before this transaction), nor to another manifest.
CREATE OR REPLACE FUNCTION public.ka_gochara_seal_approval_requires_first_seal()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.ka_gochara_generation_seal s
                 WHERE s.chart_id = NEW.chart_id AND s.generation = NEW.generation AND s.manifest_id = NEW.manifest_id
                   AND s.sealed_at = transaction_timestamp()) THEN
    RAISE EXCEPTION 'ka_gochara_seal_approval refused at commit (receipt_without_first_seal): the receipt for (chart %, generation %, manifest %) has no seal row of the same manifest written in this transaction — a receipt exists only for the first seal it is written with',
      NEW.chart_id, NEW.generation, NEW.manifest_id USING ERRCODE = 'check_violation';
  END IF;
  RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER ka_gochara_seal_approval_zz_first_seal
  AFTER INSERT ON public.ka_gochara_seal_approval
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_seal_approval_requires_first_seal();

CREATE TRIGGER ka_gochara_seal_approval_no_change
  BEFORE UPDATE OR DELETE ON public.ka_gochara_seal_approval
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_seal_approval_immutable();
CREATE TRIGGER ka_gochara_seal_approval_no_truncate
  BEFORE TRUNCATE ON public.ka_gochara_seal_approval
  FOR EACH STATEMENT EXECUTE FUNCTION public.ka_gochara_seal_approval_immutable();

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

-- ── 6b. the approval receipt is ENFORCED at the first seal (R11-3; steward M…145007) ───────────────────────────────────
-- A seal must not be able to exist without its approval receipt. A DEFERRED constraint trigger on the seal INSERT requires, at
-- COMMIT, a `ka_gochara_seal_approval` row for the same (chart, generation) naming THIS manifest and carrying a brief digest;
-- otherwise the whole transaction (the publication flip, the seal row) is refused by name and nothing remains. It is an AFTER
-- INSERT trigger, so it fires only for a row actually inserted: a REPLAY (`ka_gochara_seal_generation` inserts ON CONFLICT DO
-- NOTHING) and every generation sealed before 1240 are untouched. A receipt cannot pre-exist its seal (its FK to the seal row is
-- deferred to the same commit), so "a receipt exists" means "written in this transaction". The receipt table's `sealed_by` is the
-- SESSION login (`session_user`), not a role switched to inside the session.
CREATE OR REPLACE FUNCTION public.ka_gochara_seal_requires_approval_receipt()
RETURNS trigger LANGUAGE plpgsql SET search_path = pg_catalog, public AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.ka_gochara_seal_approval a
                 WHERE a.chart_id = NEW.chart_id AND a.generation = NEW.generation AND a.manifest_id = NEW.manifest_id
                   AND a.brief_digest ~ '^[0-9a-f]{64}$') THEN
    RAISE EXCEPTION 'ka_gochara_generation_seal refused at commit (approval_receipt_missing): no ka_gochara_seal_approval row with a brief digest was written for (chart %, generation %, manifest %) in this transaction — a seal exists only with its approval receipt',
      NEW.chart_id, NEW.generation, NEW.manifest_id USING ERRCODE = 'check_violation';
  END IF;
  RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER ka_gochara_generation_seal_zz_receipt_required
  AFTER INSERT ON public.ka_gochara_generation_seal
  DEFERRABLE INITIALLY DEFERRED
  FOR EACH ROW EXECUTE FUNCTION public.ka_gochara_seal_requires_approval_receipt();

-- ── 7. privileges (role-existence-guarded; explicit; table-level; no SECURITY DEFINER) ─────────────────
-- The builder gets NOTHING on the verification table, and exactly ONE function: EXECUTE on the window CHECK helper
-- `ka_gochara_window_qualification_ok(jsonb)`, which this migration's own `kgew_qualification_shape_ck` CALLS on every
-- window INSERT — production revokes PUBLIC EXECUTE, and a table INSERT grant does not carry the function privilege, so
-- without it the restricted builder cannot insert a window at all (Codex round 9, R9-4). The VERIFIER writes it (INSERT; pre-seal DELETE — enforced by the
-- write guard) and reads what it verifies; the SEALER reads it and runs the gate (the seal trigger fires as the sealing
-- role). EXECUTE lists were derived by running the real flows as these roles under a PUBLIC-EXECUTE-revoked schema and
-- adding one grant per `permission denied` until the suite converged (the live tests are the detector).
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
    GRANT EXECUTE ON FUNCTION public.ka_gochara_window_qualification_ok(jsonb) TO data_plane_builder;
    RAISE NOTICE 'migration 1240: builder EXECUTE on ka_gochara_window_qualification_ok issued to role data_plane_builder (and nothing on the verification table)';
  ELSE
    RAISE NOTICE 'migration 1240: role data_plane_builder NOT FOUND — NO builder grant was issued; once it exists it needs EXECUTE on ka_gochara_window_qualification_ok(jsonb) or it cannot insert a window';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN
    GRANT SELECT, INSERT, DELETE ON public.ka_gochara_eval_window_verification TO gochara_verifier;
    GRANT SELECT ON
      public.ka_gochara_eval_window, public.ka_gochara_eval_window_record,
      public.ka_gochara_relationship_record, public.ka_gochara_record_prerequisite, public.ka_gochara_contact,
      public.ka_gochara_physical_object, public.kala_gochara_coverage, public.ka_gochara_search_inventory, public.ka_gochara_search_path_pin,
      public.ka_gochara_search_input_snapshot, public.ka_gochara_generation_seal,
      public.ka_gochara_rule_path, public.ka_gochara_rule_path_seal,
      public.ka_gochara_rule_path_soft_factor, public.ka_gochara_factor, public.kala_gochara_publication
      TO gochara_verifier;
    GRANT EXECUTE ON FUNCTION
      public.ka_gochara_lock_chart(uuid), public.ka_gochara_lock_global_shared(),
      public.ka_gochara_generation_is_sealed(uuid, text), public.ka_gochara_generation_governed(text),
      public.ka_gochara_eval_window_content_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_stored_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_expected_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_inputs_digest(uuid, text, text, text, text),
      public.ka_gochara_canonical_json(jsonb), public.ka_gochara_sha256_hex(text),
      public.ka_gochara_f4_token(real),
      -- R10-4 (iii): the job ENDS in the same combined candidate gate the seal uses (1240's own function; the 1206/1232
      -- completeness function it calls, and what that reads, are Stream B's grants — see 1241)
      public.ka_gochara_candidate_gate_violations(uuid, text)
      TO gochara_verifier;
    RAISE NOTICE 'migration 1240: verifier grants issued to role gochara_verifier';
  ELSE
    -- a grants block that granted to nobody must be VISIBLE (steward M20261002T042833-a966)
    RAISE NOTICE 'migration 1240: role gochara_verifier NOT FOUND — NO verifier grants were issued; no verification row can be written until it is provisioned and its grants applied (the candidate gate stays CLOSED)';
  END IF;
  IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer') THEN
    GRANT SELECT ON public.ka_gochara_eval_window_verification TO gochara_sealer;
    GRANT SELECT ON
      public.ka_gochara_eval_window, public.ka_gochara_eval_window_record,
      public.ka_gochara_relationship_record, public.ka_gochara_search_path_pin,
      public.ka_gochara_search_input_snapshot, public.ka_gochara_generation_seal, public.kala_gochara_publication,
      public.ka_gochara_record_prerequisite, public.ka_gochara_contact, public.ka_gochara_physical_object
      TO gochara_sealer;
    GRANT EXECUTE ON FUNCTION
      public.ka_gochara_window_verification_violations(uuid, text),
      public.ka_gochara_window_verification_replay_violations(uuid, text),
      public.ka_gochara_candidate_gate_violations(uuid, text),
      public.ka_gochara_eval_window_content_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_stored_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_expected_digest(uuid, text, text, text, text),
      public.ka_gochara_eval_window_inputs_digest(uuid, text, text, text, text),
      public.ka_gochara_f4_token(real),
      public.ka_gochara_canonical_json(jsonb), public.ka_gochara_sha256_hex(text),
      public.ka_gochara_lock_chart(uuid), public.ka_gochara_lock_global_shared()
      TO gochara_sealer;
    RAISE NOTICE 'migration 1240: sealer grants issued to role gochara_sealer';
  ELSE
    RAISE NOTICE 'migration 1240: role gochara_sealer NOT FOUND — NO sealer grants were issued; the seal trigger runs as whichever role seals and refuses a first seal until verification rows exist';
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
  WHERE t.tgrelid = 'public.ka_gochara_seal_approval'::regclass AND NOT t.tgisinternal
    AND t.tgname IN ('ka_gochara_seal_approval_no_change', 'ka_gochara_seal_approval_no_truncate',
                     'ka_gochara_seal_approval_attest', 'ka_gochara_seal_approval_zz_first_seal');
  IF n <> 4 THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: the seal-approval receipt table lacks its append-only / attestation / first-seal triggers';
  END IF;
  SELECT count(*) INTO n FROM pg_trigger t
  WHERE t.tgrelid = 'public.ka_gochara_generation_seal'::regclass AND NOT t.tgisinternal
    AND t.tgname IN ('ka_gochara_generation_seal_zz_window_verified', 'ka_gochara_generation_seal_zz_receipt_required');
  IF n <> 2 THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: the window-verification seal trigger and the receipt-required seal trigger must each be present exactly once';
  END IF;
  SELECT string_agg(x.sig, ', ') INTO missing
  FROM (VALUES
    ('public.ka_gochara_f4_token(real)'),
    ('public.ka_gochara_eval_window_content_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_eval_window_stored_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_eval_window_expected_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_eval_window_inputs_digest(uuid,text,text,text,text)'),
    ('public.ka_gochara_window_verification_violations(uuid,text)'),
    ('public.ka_gochara_window_verification_replay_violations(uuid,text)'),
    ('public.ka_gochara_candidate_gate_violations(uuid,text)'),
    ('public.ka_gochara_window_verification_write_guard()'),
    ('public.ka_gochara_generation_seal_window_guard()'),
    ('public.ka_gochara_window_qualification_ok(jsonb)'),
    ('public.ka_gochara_seal_receipt_missing(uuid,text)'),
    ('public.ka_gochara_legacy_projection_rows(uuid,text)')) AS x(sig)
  WHERE to_regprocedure(x.sig) IS NULL;
  IF missing IS NOT NULL THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: missing functions: %', missing;
  END IF;
  SELECT count(*) INTO n FROM pg_constraint c
  WHERE c.conrelid = 'public.ka_gochara_eval_window'::regclass
    AND c.conname IN ('kgew_objective_token_ck', 'kgew_objective_value_ck', 'kgew_qualification_shape_ck',
                      'kgew_provenance_pair_ck', 'kgew_unqualified_no_result_ck', 'kgew_all_null_policy_ck');
  IF n <> 6 THEN
    RAISE EXCEPTION 'migration 1240 post-apply check failed: expected 6 window provenance constraints, found %', n;
  END IF;
  -- R10-5: the verifier must hold NO write privilege — table OR column level — anywhere on the builder write surface (every
  -- Gochara table except the two verification tables it writes). `has_table_privilege` alone cannot see a column grant
  -- (1242 grants the builder columns), so the column predicate is checked as well — the same predicate the job's identity
  -- self-check applies at run time.
  IF to_regrole('gochara_verifier') IS NOT NULL THEN
    SELECT string_agg(h.what, ', ') INTO missing
    FROM (
      SELECT p.priv || ' on ' || c.relname AS what
      FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
      CROSS JOIN (VALUES ('INSERT'), ('UPDATE'), ('DELETE'), ('TRUNCATE')) AS p(priv)
      WHERE ns.nspname = 'public' AND c.relkind IN ('r', 'p')
        AND (c.relname LIKE 'ka\_gochara\_%' OR c.relname LIKE 'kala\_gochara\_%')
        AND c.relname NOT IN ('ka_gochara_search_inventory_verification', 'ka_gochara_eval_window_verification')
        AND has_table_privilege('gochara_verifier', c.oid, p.priv)
      UNION ALL
      SELECT p.priv || '(' || a.attname || ') on ' || c.relname
      FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
      JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum > 0 AND NOT a.attisdropped
      CROSS JOIN (VALUES ('INSERT'), ('UPDATE')) AS p(priv)
      WHERE ns.nspname = 'public' AND c.relkind IN ('r', 'p')
        AND (c.relname LIKE 'ka\_gochara\_%' OR c.relname LIKE 'kala\_gochara\_%')
        AND c.relname NOT IN ('ka_gochara_search_inventory_verification', 'ka_gochara_eval_window_verification')
        AND has_column_privilege('gochara_verifier', c.oid, a.attnum, p.priv)
        AND NOT has_table_privilege('gochara_verifier', c.oid, p.priv)
    ) h;
    IF missing IS NOT NULL THEN
      RAISE EXCEPTION 'migration 1240 post-apply check failed: gochara_verifier holds write privileges on the builder write surface (table or column level): %', missing;
    END IF;
  END IF;
  RAISE NOTICE 'migration 1240: presence checks passed';
END;
$$;
