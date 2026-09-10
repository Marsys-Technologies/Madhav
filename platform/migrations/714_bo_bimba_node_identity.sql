-- 714_bo_bimba_node_identity.sql
--
-- NIRMĀṆA L2-W3 — deterministic bo_bimba node identity. Ruling: adjudication
-- #1888, D-CND-29. Pattern mirrors migration 660/661's bodha_signal_identity
-- (#1804/D-CND-11) and L4's phala_anchor_identity (migration 680) -- the
-- third confirmed instance of "a writer's own node_id is uuid.uuid4(),
-- rebuild-unstable, and any downstream consumer desyncs the instant the
-- writer rebuilds without them."
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- WHY THIS EXISTS. bodha_cgm_nodes.node_id is str(uuid.uuid4()) at four emit
-- sites in bo_bimba.py (graha, bhava, domain, yoga/dosha nodes). Every
-- bo_bimba rebuild mints fresh node_ids for the same logical nodes, so any
-- writer that stored a reference to an OLDER node_id (bo_karanajala's edges,
-- bo_cgm_paths' dispositor chains, bo_cgm_motifs' sub-graphs) silently
-- orphans the moment bo_bimba rebuilds without them in the same pass.
-- Confirmed live in #1888: bodha_cgm_paths/bodha_cgm_sub_graphs are 100%/33%
-- orphaned today, two days out of sync with the current bodha_cgm_nodes
-- generation, on all three production charts.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- PART 1 — the identity function (single source of truth, in SQL)
--
-- The natural key is (chart_id, ayanamsha_id, node_type, node_subject),
-- ruled correct by inspection of all four of bo_bimba.py's emit sites
-- (writers/bo_bimba.py:287-495):
--   - graha nodes:  `for graha in KNOWN_GRAHAS:` -- node_subject = the graha
--     name, one row per name, unconditional.
--   - bhava nodes:  `for h in range(1, 13):` -- node_subject = str(h),
--     one row per house number, unconditional.
--   - domain nodes: `for domain in CANONICAL_DOMAINS_SORTED:` -- node_subject
--     = the domain name, one row per canonical domain.
--   - yoga/dosha nodes: deduplicated into a `yoga_best` dict keyed by
--     `(sig_class, subject)` BEFORE the emit loop -- node_subject is already
--     guaranteed unique per node_type within one _build_nodes_for_aya() call.
-- In every case node_subject is set from the SAME loop/dict key that
-- determines node_type, so (chart_id, ayanamsha_id, node_type, node_subject)
-- is exactly unique per node -- verified live: no duplicate tuple exists in
-- bodha_cgm_nodes today across any of the three production charts.
--
-- Excluded from the key (mirrors D-CND-11's "how good, not what it is"
-- line): strength_score, dignity_state, position_in_chart_jsonb, hub_flag,
-- centrality columns (bo_karanajala backfills these on the SAME row after
-- bo_bimba inserts it -- including them would make the identity move the
-- instant bo_karanajala runs, which is exactly the instability this
-- function exists to remove), build_id. A change in any of these means we
-- RE-COMPUTED or RE-GRADED the node; identity must not move.

CREATE OR REPLACE FUNCTION bodha_cgm_node_identity_namespace()
RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT 'e1a4f0b6-3c8d-5a71-9e2f-6b0d84a3c917'::uuid $$;

COMMENT ON FUNCTION bodha_cgm_node_identity_namespace() IS
  'Fixed v5 namespace for bodha_cgm_nodes identities (Nirmana #1888, D-CND-29). '
  'Distinct from bodha_signal_identity_namespace and phala_anchor_identity_namespace '
  'so the three id spaces can never collide.';

CREATE OR REPLACE FUNCTION bodha_cgm_node_identity(
  p_chart_id     uuid,
  p_ayanamsha_id text,
  p_node_type    text,
  p_node_subject text
) RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$
  SELECT uuid_generate_v5(
    bodha_cgm_node_identity_namespace(),
    jsonb_build_array(
      p_chart_id::text, p_ayanamsha_id, p_node_type, p_node_subject
    )::text
  )
$$;

COMMENT ON FUNCTION bodha_cgm_node_identity(uuid, text, text, text) IS
  'Deterministic bodha_cgm_nodes.node_id (Nirmana #1888, D-CND-29). Stable '
  'across a bo_bimba rebuild for an UNCHANGED node (same chart, ayanamsha, '
  'node_type, node_subject); a downstream reference (bo_karanajala edges, '
  'bo_cgm_paths chains, bo_cgm_motifs sub-graphs) built on it continues to '
  'resolve after a bo_bimba rebuild without requiring the orchestrator to '
  'force lockstep rebuilds. Does NOT by itself repair the 100%-orphaned '
  'state measured in #1888 -- that needs bo_bimba to rebuild with these '
  'deterministic ids, then bo_cgm_paths/bo_cgm_motifs to rebuild fresh '
  'against them (ruled sequence, #1888).';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 2 — what this migration deliberately does NOT do
--
-- It does not set bo_bimba.integrity_check_sql. The strong check -- every
-- stored node_id equals bodha_cgm_node_identity(...) recomputed from its own
-- columns -- would be RED on all live data today (every node still carries a
-- uuid4()), for the same C12 reason migration 661 gave for bo_laksana: "a
-- check that has never been green is a PROPOSAL, not a gate." It becomes
-- adoptable once bo_bimba rebuilds with this function wired in (bo_bimba.py
-- change, separate PR) and the resync the #1888 ruling calls for actually
-- runs. It also does not touch bo_cgm_paths or bo_cgm_motifs' registry rows
-- for the same reason -- their current data is genuinely orphaned, not
-- merely unchecked, and a migration adding a SQL function is not the resync
-- itself.
