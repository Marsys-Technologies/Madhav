-- 966_bo_karanajala_edge_contradiction_identity.sql
--
-- NIRMĀṆA L2-W3 — deterministic bo_karanajala edge_id / contradiction_id / node_id.
-- Same defect class as migration 714 (bo_bimba node_id, adjudication #1888/D-CND-29),
-- migration 660/661 (bodha_signal_identity, #1804/D-CND-11), and L4's phala_anchor_identity
-- (migration 680): a writer's own primary identity column is str(uuid.uuid4()), so every
-- rebuild mints fresh identities for the same logical row, and any downstream consumer that
-- stored a reference to an OLDER id (bo_cgm_paths' path_edge_ids_array, bo_cgm_motifs'
-- involved_edge_ids_array/edge_ids_array) silently orphans the moment bo_karanajala rebuilds
-- without them in the same pass.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts.
--
-- WHY THIS EXISTS. bo_karanajala.py mints bodha_cgm_edges.edge_id and
-- bodha_contradictions.contradiction_id via uuid.uuid4() at every emit site (aspect,
-- conjunction, dispositor, yoga_domain/dosha_domain, sade_sati, argala, bhava-structural,
-- yoga_member, arudha/special_lagna edges; yoga_vs_dosha contradictions). bo_karanajala also
-- inserts its own bodha_cgm_nodes rows (arudha A1-A12 + special-lagna nodes, D-2 Lane V-4) via
-- uuid.uuid4() rather than reusing the bodha_cgm_node_identity() function migration 714 already
-- established for exactly this table.
--
-- ─────────────────────────────────────────────────────────────────────────────
-- PART 1 — edge identity
--
-- The natural key is (chart_id, ayanamsha_id, snapshot_type, edge_type, from_node_id,
-- to_node_id) -- this is bodha_cgm_edges' own existing UNIQUE constraint (migration 325)
-- MINUS build_id: `UNIQUE (chart_id, ayanamsha_id, build_id, snapshot_type, edge_type,
-- from_node_id, to_node_id)`. bo_karanajala.py's own `_EDGE_INSERT` ON CONFLICT target
-- (writers/bo_karanajala.py:95) is the FULL tuple INCLUDING build_id -- since build_id is
-- always fresh per rebuild, that ON CONFLICT never fires across rebuilds today and dedup
-- within one build only ever guards against two emit sites producing the exact same edge in
-- the same pass. Dropping build_id from the IDENTITY function (not the writer's dedup target)
-- is the whole point: it is what lets a downstream reference (bo_cgm_paths, bo_cgm_motifs)
-- survive across a delete-then-insert rebuild that mints a new build_id for the same logical
-- edge. Excluded from the key (mirrors migration 714's reasoning): computed_strength,
-- edge_properties_jsonb, and every other value/grading column -- a change in any of these
-- means the edge was RE-COMPUTED or RE-GRADED, not that it became a different edge.
--
-- PART 2 — contradiction identity
--
-- The natural key is (chart_id, ayanamsha_id, signal_a_id, signal_b_id) -- again
-- bodha_contradictions' own existing UNIQUE constraint (migration 325) MINUS build_id, for
-- the identical reason (the writer's own `_CONTRADICTION_INSERT` ON CONFLICT at
-- writers/bo_karanajala.py:111 still includes build_id). Both signal_a_id/signal_b_id are
-- themselves stable bodha_msr_signals.signal_id values (FK'd, migration 325), so this tuple is
-- stable across a bo_karanajala rebuild by construction.
--
-- PART 3 — node identity (arudha / special_lagna)
--
-- bo_karanajala's own bodha_cgm_nodes inserts (node_type in ('arudha', 'special_lagna'),
-- node_subject = the pada label / special-lagna subject) use the SAME natural key shape
-- bodha_cgm_node_identity() (migration 714) already generalizes over: (chart_id,
-- ayanamsha_id, node_type, node_subject). No new function needed for this part -- the writer
-- change (separate PR) wires these emit sites to the existing function directly.

CREATE OR REPLACE FUNCTION bodha_cgm_edge_identity_namespace()
RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT 'f2b5e1c7-4d9e-56b2-af30-7c1e95b4da28'::uuid $$;

COMMENT ON FUNCTION bodha_cgm_edge_identity_namespace() IS
  'Fixed v5 namespace for bodha_cgm_edges identities (Nirmana W3, bo_karanajala identity '
  'fix). Distinct from bodha_cgm_node_identity_namespace, bodha_signal_identity_namespace, '
  'and phala_anchor_identity_namespace so the four id spaces can never collide.';

CREATE OR REPLACE FUNCTION bodha_cgm_edge_identity(
  p_chart_id      uuid,
  p_ayanamsha_id  text,
  p_snapshot_type text,
  p_edge_type     text,
  p_from_node_id  uuid,
  p_to_node_id    uuid
) RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$
  SELECT uuid_generate_v5(
    bodha_cgm_edge_identity_namespace(),
    jsonb_build_array(
      p_chart_id::text, p_ayanamsha_id, p_snapshot_type, p_edge_type,
      p_from_node_id::text, p_to_node_id::text
    )::text
  )
$$;

COMMENT ON FUNCTION bodha_cgm_edge_identity(uuid, text, text, text, uuid, uuid) IS
  'Deterministic bodha_cgm_edges.edge_id (Nirmana W3, bo_karanajala identity fix). Stable '
  'across a bo_karanajala rebuild for an UNCHANGED edge (same chart, ayanamsha, snapshot_type, '
  'edge_type, from_node_id, to_node_id); a downstream reference (bo_cgm_paths'' '
  'path_edge_ids_array, bo_cgm_motifs'' involved_edge_ids_array/edge_ids_array) built on it '
  'continues to resolve after a bo_karanajala rebuild without requiring the orchestrator to '
  'force lockstep rebuilds. Does NOT by itself repair any already-orphaned bo_cgm_paths/'
  'bo_cgm_motifs data -- that needs bo_karanajala to rebuild with this function wired in '
  '(writer change, separate PR), then bo_cgm_paths/bo_cgm_motifs to rebuild fresh against it.';

CREATE OR REPLACE FUNCTION bodha_contradiction_identity_namespace()
RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$ SELECT 'a83c6f95-2e17-5d84-9b46-1f0a7e2c5db3'::uuid $$;

COMMENT ON FUNCTION bodha_contradiction_identity_namespace() IS
  'Fixed v5 namespace for bodha_contradictions identities (Nirmana W3, bo_karanajala identity '
  'fix). Distinct from the edge/node/signal/anchor namespaces so the id spaces can never '
  'collide.';

CREATE OR REPLACE FUNCTION bodha_contradiction_identity(
  p_chart_id     uuid,
  p_ayanamsha_id text,
  p_signal_a_id  uuid,
  p_signal_b_id  uuid
) RETURNS uuid LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
$$
  SELECT uuid_generate_v5(
    bodha_contradiction_identity_namespace(),
    jsonb_build_array(
      p_chart_id::text, p_ayanamsha_id, p_signal_a_id::text, p_signal_b_id::text
    )::text
  )
$$;

COMMENT ON FUNCTION bodha_contradiction_identity(uuid, text, uuid, uuid) IS
  'Deterministic bodha_contradictions.contradiction_id (Nirmana W3, bo_karanajala identity '
  'fix). Stable across a bo_karanajala rebuild for an UNCHANGED contradiction pair (same '
  'chart, ayanamsha, signal_a_id, signal_b_id).';

-- ─────────────────────────────────────────────────────────────────────────────
-- PART 4 — what this migration deliberately does NOT do
--
-- It does not set bo_karanajala.integrity_check_sql. The strong check -- every stored
-- edge_id/contradiction_id equals its identity function recomputed from its own columns --
-- would be RED on all live data today (every row still carries a uuid4()), for the same C12
-- reason migration 714 gave for bo_bimba: "a check that has never been green is a PROPOSAL,
-- not a gate." It becomes adoptable once bo_karanajala rebuilds with these functions wired in
-- (writer change, separate PR). It also does not touch bo_cgm_paths or bo_cgm_motifs'
-- registry rows for the same reason -- their current data referencing today's random edge_ids
-- is genuinely orphaned the instant bo_karanajala next rebuilds regardless, not merely
-- unchecked, and a migration adding SQL functions is not the resync itself. It also does not
-- alter bodha_cgm_edges/bodha_contradictions' existing UNIQUE constraints (migration 325,
-- both still include build_id) -- unnecessary, since the L1+ idempotency standard (delete-
-- then-insert scoped to chart x ayanamsha) means only one build_id's rows exist for a given
-- natural key at any time; making the identity value itself deterministic is what gives a
-- downstream reference continuity across that delete-then-insert, independent of the
-- constraint shape.
