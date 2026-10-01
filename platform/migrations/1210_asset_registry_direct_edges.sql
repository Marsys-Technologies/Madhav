-- 1210_asset_registry_direct_edges.sql
--
-- Suvarna Track I (ruling 2026-10-01): declare the DIRECT `depends_on` edges for reads that are
-- today ordered only TRANSITIVELY. 12 edges across 9 consumers, 8 distinct producers. On the ALIGNED E6
-- `Build.dag` reads-match detector (E6 commit 1048ec743) 8 consumers go FAIL -> PASS (bo_karanajala,
-- bo_laksana_rerank, bo_pratijna, bo_yantra_mechanism, ka_kalasutra, ka_vighnakara, ka_yojaka,
-- mi_darshana); mi_pariksha shrinks but keeps findings that need the 1211 edges.
--
-- SCOPE (SS rulings Q2/Q3, 2026-10-01). Only edges the aligned detector STILL requires: for each edge, with
-- every other edge present and this one absent, the detector reports a missing-edge FAIL for that read.
-- Deliberately NOT here: (a) edges to L0 bedrock tables (bg_*/brahma_*/reference_*/sutravali_*/classical_*):
-- reads of bedrock tables are satisfied without a direct edge (dag_edge_guard never gates them) and a global
-- L0 edge risks blocking per-chart builds; (b) edges justified only by a chart_facts read (shared SOFT table,
-- satisfied by any producer in the transitive closure). Dropped from the post-split 22-edge cut (the first
-- review had 27 edges) for these two reasons: bo_grounding -> bg_rules, bo_pratijna -> bg_reference, mi_darshana -> bg_ghatana,
-- ph_muhurta -> bg_ghatana, ph_nimitta -> bg_ghatana (bedrock); bo_bimba, bo_pratijna,
-- bo_yantra_mechanism, ka_avadhi -> ga_positions and ka_yojaka -> ga_structural (chart_facts).
--
-- SPLIT (SS ruling 2026-10-01). A read-only gate preview on the canonical chart showed four producers NOT
-- lit+fresh (bo_pratijna stale, ka_yojaka stale, ph_nimitta stale, mi_bhavisya throughput 'error' = a
-- cascade skip); a direct edge to a producer that is not gate-ready would BLOCK its consumer (see
-- CONSEQUENCES 2). This file keeps only edges whose producer is lit, fresh and proven. The 5 edges to those
-- four producers (all five still required by the aligned detector) are in a separate, BLOCKED migration
-- 1211_asset_registry_direct_edges_held.sql (branch suvarna/land/TI-edges-002): ph_nimitta -> bo_pratijna,
-- ph_nimitta -> ka_yojaka, mi_gunanaka -> mi_bhavisya, mi_pariksha -> mi_bhavisya, mi_pariksha ->
-- ph_nimitta. 1211 must not be applied until those four producers are each lit and fresh (gate_ok true)
-- and 1210 is applied.
--
-- PR-body line: makes 5 Nirmana-frozen manifests stale against the registry fingerprint; Nirmana is
-- superseded (NIRMANA-SUPERSESSION).
--
-- WHY. E6 (T4: declared edges must match what a writer actually reads) found writers that read
-- another asset's table where the producer is reachable through an intermediate asset but the
-- direct edge is undeclared. Ordering is not at risk today (a transitive path exists), but the
-- declaration is wrong in three ways that matter: (1) `compute_upstream_hash` hashes DECLARED deps
-- only, so a rebuild of the producer is invisible to a consumer that reads it directly; (2) the
-- cockpit's direct blocking radius under-counts the producer; (3) the edge set cannot be audited
-- against the code. Evidence, per edge, with file:line of the SQL read:
-- /Users/Dev/suvarna-evidence/TrackI/edges_evidence.md (consumer, producer, table, read site,
-- transitive path that today carries the ordering).
--
-- WHAT EACH EDGE IS. Every edge below is a producer asset -> table read verified as a real SQL read in the
-- consumer's own writer code path, of a non-bedrock, non-chart_facts table owned by the producer
-- (chart_vichara -> ga_vichara; chart_dashas -> ga_dashas; chart_divisionals -> ga_vargas;
-- ga_yoga_firings -> ga_yoga; bodha_cgm_nodes -> bo_bimba; bodha_triangulation -> bo_sangati;
-- mimamsa_event_provenance -> mi_jivanaghatana; bodha_msr_signals -> bo_laksana, the registry's
-- target_table owner, the same ruling bo_grounding already records). Several reads are SAVEPOINT- or
-- try/except-guarded (soft: degrade to empty when the producer has not run); a hard edge is the correct
-- declaration for them, and no extra wait is introduced because the producer is already upstream through
-- the existing path.
--
-- ACYCLIC. The full 127-asset registry graph (seed + migrations 913/1084/730/676, md5 of sorted
-- depends_on = live as of the E6 review) plus these 12 edges was topologically sorted: 127/127
-- ordered, no cycle. Every producer is an active asset with a writer. This migration re-checks
-- both properties inside the transaction and RAISEs rather than leave a dependency trap.
--
-- NOT in this migration (reported separately to the owner):
--   * the 5 edges held for 1211 (producer not gate-ready; see SPLIT above).
--   * the 10 edges dropped as bedrock / chart_facts-soft (see SCOPE above).
--   * 3 BACK-READS whose edge would create a cycle: ka_bhavishya_lekha -> ph_nimitta,
--     ga_structural -> ga_vichara, ga_structural -> ga_yoga.
--   * the remaining FAIL assets on the aligned detector whose missing edges have no covering path (different
--     class; listed in the evidence file).
--
-- BEHAVIOUR. Appends only, existing array order preserved, other columns untouched. Idempotent: an
-- edge already present is skipped; a fully-covered row is not rewritten; a NULL depends_on is treated
-- as empty. On a database where a consumer row does not exist yet (fresh bootstrap) it is a no-op;
-- the TypeScript seed (asset_registry_seed.ts) carries the same edges for NEW rows (its re-seed never
-- rewrites depends_on of an existing row).
--
-- APPLY ONLY WHEN no build_runs row is in state planned/running/paused. runner.py
-- `_verify_registry_still_matches_manifest` compares each planned asset's live depends_on against the
-- run's frozen manifest; any run planned/running across the deploy has its diverged assets (the 9
-- consumers) terminalized by `_terminalize_diverged_assets`, and their dependents blocked.
--
-- CONSEQUENCES (verified in code; read-only checks are in the evidence verify SQL):
--  1. Nirmana frozen-definition contract. `registryContractFingerprintInput`
--     (src/lib/nirmana-elevation/definitions.ts) includes depends_on, and
--     `assertManifestMatchesRegistryIdentity` throws on ANY depends_on change vs the frozen manifest.
--     5 of the 9 consumers are Nirmana-frozen (NIRMANA_SUPERSESSION_RECORD s2.3): bo_karanajala (t3),
--     bo_laksana_rerank (t3), bo_pratijna (t1), bo_yantra_mechanism (t1), ka_yojaka (t2)
--     = 6 of the 12 edges (bo_bimba is no longer a consumer; the 1211 consumers ph_nimitta, mi_gunanaka, mi_pariksha
--     are not frozen). Effects: (a) their `asset_analysis_accepted` evidence is bound to a registry
--     fingerprint that no longer matches (snapshot.ts stale-accepted logic);
--     (b) snapshot.ts `validManifest` returns null (the assert is caught), and the monitor
--     (monitor.ts) reports `plan_adaptation_required`; (c) scripts/dispatch_nirmana_campaign_wave.py
--     raises "live registry contract changed for <asset>: depends_on" and refuses the whole wave.
--     Mitigating: the Nirmana campaign is OFF (native 2026-09-28; the DB definition row still reads
--     frozen), and migrations 1084 (ka_kshetra, ka_sangam) and 1091 (ka_gochara) already changed
--     depends_on after the t3 freeze, so the monitor is probably already red. Confirm with the latest
--     nirmana_elevation_monitor_observations row BEFORE deploy (verify SQL Q5).
--  2. Hard dependency gate. asset_runner.deps_unsatisfied (enforce mode) requires every declared dep to
--     be asset_throughput.state 'lit' (or 'service_ok') AND its latest asset_freshness 'fresh'. A new
--     direct producer whose state is not lit, or whose freshness is stale/unknown/absent, now BLOCKS
--     its consumer even though the old transitive path did not check that producer's freshness
--     directly. Read-only gate preview on the canonical chart: all 8 producers of THIS migration are
--     lit, fresh and proven; the four that were not are the producers of the 5 edges held in 1211.
--     Verify SQL Q4 (limited to the 8 producers) re-checks this right before apply.
--  3. Upstream hash. `compute_upstream_hash` hashes DECLARED deps: each consumer's next dispatch sees
--     a changed upstream set (one-time rebuild signal). A producer whose latest receipt is missing or
--     not 'proven' makes that consumer's upstream_digest NULL for that build.
--  4. Cockpit direct blocking radius of the producers rises by their new direct consumers.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).
-- No DDL on a shared table other than row updates; asset_registry is owned by amjis_app.

SET LOCAL lock_timeout = '5s';

CREATE TEMP TABLE _m1210_edges (
    asset_id text NOT NULL,
    dep      text NOT NULL
) ON COMMIT DROP;

INSERT INTO _m1210_edges (asset_id, dep) VALUES
  ('bo_karanajala', 'ga_vichara'),
  ('bo_laksana_rerank', 'bo_bimba'),
  ('bo_laksana_rerank', 'ga_vichara'),
  ('bo_pratijna', 'ga_vargas'),
  ('bo_yantra_mechanism', 'bo_bimba'),
  ('ka_kalasutra', 'ga_dashas'),
  ('ka_vighnakara', 'ga_dashas'),
  ('ka_yojaka', 'ga_yoga'),
  ('mi_darshana', 'bo_laksana'),
  ('mi_darshana', 'bo_sangati'),
  ('mi_pariksha', 'bo_laksana'),
  ('mi_pariksha', 'mi_jivanaghatana');

-- Guard 1: every producer of an edge whose consumer row exists must be an ACTIVE asset.
DO $$
DECLARE
    bad text;
BEGIN
    SELECT string_agg(e.asset_id || ' -> ' || e.dep, ', ' ORDER BY e.asset_id, e.dep)
      INTO bad
      FROM _m1210_edges e
      JOIN asset_registry c ON c.asset_id = e.asset_id
      LEFT JOIN asset_registry p ON p.asset_id = e.dep AND p.is_active
     WHERE p.asset_id IS NULL;
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1210: edge target missing or inactive in asset_registry (dependency trap): %', bad;
    END IF;
END $$;

-- Append only the missing deps, preserving existing order. Rows already covered are not touched.
UPDATE asset_registry r
   SET depends_on = COALESCE(r.depends_on, '{}'::text[]) || n.deps
  FROM (
        SELECT e.asset_id, array_agg(e.dep ORDER BY e.dep) AS deps
          FROM _m1210_edges e
          JOIN asset_registry c ON c.asset_id = e.asset_id
         WHERE e.dep <> ALL (COALESCE(c.depends_on, '{}'::text[]))
         GROUP BY e.asset_id
       ) n
 WHERE r.asset_id = n.asset_id;

-- Guard 2: verify it actually applied (never trust a silent no-op) and that no self-edge slipped in.
DO $$
DECLARE
    bad text;
BEGIN
    SELECT string_agg(e.asset_id || ' -> ' || e.dep, ', ' ORDER BY e.asset_id, e.dep)
      INTO bad
      FROM _m1210_edges e
      JOIN asset_registry c ON c.asset_id = e.asset_id
     WHERE e.dep <> ALL (COALESCE(c.depends_on, '{}'::text[]));
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1210: edge not present after update: %', bad;
    END IF;
    -- scoped to the consumers this migration touches: a pre-existing self-edge elsewhere must not
    -- fail the deploy for everyone (it is reported by verify Q3 instead)
    IF EXISTS (SELECT 1 FROM asset_registry r
                WHERE r.asset_id IN (SELECT asset_id FROM _m1210_edges)
                  AND r.asset_id = ANY (r.depends_on)) THEN
        RAISE EXCEPTION '1210: self-dependency present in asset_registry.depends_on of an edited asset';
    END IF;
END $$;

-- DOWN (ops reference, not executed by migrate.ts): remove exactly these edges.
--   UPDATE asset_registry r SET depends_on = ARRAY(
--       SELECT x FROM unnest(r.depends_on) x
--        WHERE x NOT IN (SELECT e.dep FROM (VALUES <the 12 (asset_id, dep) pairs above>) e(asset_id, dep)
--                         WHERE e.asset_id = r.asset_id))
--    WHERE r.asset_id IN (<the 9 consumer asset_ids above>);
