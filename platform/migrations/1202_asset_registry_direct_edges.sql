-- 1202_asset_registry_direct_edges.sql
--
-- Suvarna Track I (ruling 2026-10-01): declare the DIRECT `depends_on` edges for reads that are
-- today ordered only TRANSITIVELY. 27 edges across 15 assets (14 of which the E6 `Build.dag`
-- reads-match detector turns from FAIL to PASS; bo_laksana_rerank keeps one residual finding,
-- see "NOT in this migration" below).
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
-- WHAT EACH EDGE IS. Every edge below is a producer asset -> table read verified as a real SQL
-- read in the consumer's own writer code path. Where the table is multi-producer the producer is
-- the writer of the specific fact_category / signal read: graha_position + bhava_cusps ->
-- ga_positions; lord_in_house_per_varga -> ga_structural; bodha_msr_signals -> bo_laksana (the
-- registry's target_table owner, the same ruling bo_grounding already records). Several reads are
-- SAVEPOINT- or try/except-guarded (soft: degrade to empty when the producer has not run); a hard
-- edge is the correct declaration for them, and no extra wait is introduced because the producer
-- is already upstream through the existing path.
--
-- ACYCLIC. The full 127-asset registry graph (seed + migrations 913/1084/730/676, md5 of sorted
-- depends_on = live as of the E6 review) plus these 27 edges was topologically sorted: 127/127
-- ordered, no cycle. Every producer is an active asset with a writer. This migration re-checks
-- both properties inside the transaction and RAISEs rather than leave a dependency trap.
--
-- NOT in this migration (reported separately to the owner):
--   * 3 BACK-READS whose edge would create a cycle: ka_bhavishya_lekha -> ph_nimitta,
--     ga_structural -> ga_vichara, ga_structural -> ga_yoga.
--   * bo_pramana_mapa and bo_laksana_rerank chart_facts reads: polymorphic (a join over whatever
--     facts the signals cite, written by many ga_* assets); no single producer to name.
--   * 14 assets with direct missing edges NOT covered by any path (different class).
--
-- BEHAVIOUR. Appends only, existing array order preserved, other columns untouched. Idempotent: an
-- edge already present is skipped; a fully-covered row is not rewritten; a NULL depends_on is treated
-- as empty. On a database where a consumer row does not exist yet (fresh bootstrap) it is a no-op;
-- the TypeScript seed (asset_registry_seed.ts) carries the same edges for NEW rows (its re-seed never
-- rewrites depends_on of an existing row).
--
-- APPLY ONLY WHEN no build_runs row is in state planned/running/paused. runner.py
-- `_verify_registry_still_matches_manifest` compares each planned asset's live depends_on against the
-- run's frozen manifest; any run planned/running across the deploy has its diverged assets (the 15
-- consumers) terminalized by `_terminalize_diverged_assets`, and their dependents blocked.
--
-- CONSEQUENCES (verified in code; read-only checks are in the evidence verify SQL):
--  1. Nirmana frozen-definition contract. `registryContractFingerprintInput`
--     (src/lib/nirmana-elevation/definitions.ts) includes depends_on, and
--     `assertManifestMatchesRegistryIdentity` throws on ANY depends_on change vs the frozen manifest.
--     6 of the 15 consumers are Nirmana-frozen (NIRMANA_SUPERSESSION_RECORD s2.3): bo_bimba (t3),
--     bo_karanajala (t3), bo_laksana_rerank (t3), bo_pratijna (t1), bo_yantra_mechanism (t1),
--     ka_yojaka (t2) = 11 of the 27 edges. Effects: (a) their `asset_analysis_accepted` evidence is
--     bound to a registry fingerprint that no longer matches (snapshot.ts stale-accepted logic);
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
--     directly. Verify SQL Q4 lists state + freshness + receipt per new producer.
--  3. Upstream hash. `compute_upstream_hash` hashes DECLARED deps: each consumer's next dispatch sees
--     a changed upstream set (one-time rebuild signal). A producer whose latest receipt is missing or
--     not 'proven' makes that consumer's upstream_digest NULL for that build.
--  4. Cockpit direct blocking radius of the producers rises by their new direct consumers.
--
-- Transaction ownership belongs to platform/scripts/migrate.ts (BEGIN/COMMIT around this file).
-- No DDL on a shared table other than row updates; asset_registry is owned by amjis_app.

SET LOCAL lock_timeout = '5s';

CREATE TEMP TABLE _m1202_edges (
    asset_id text NOT NULL,
    dep      text NOT NULL
) ON COMMIT DROP;

INSERT INTO _m1202_edges (asset_id, dep) VALUES
  ('bo_bimba', 'ga_positions'),
  ('bo_grounding', 'bg_rules'),
  ('bo_karanajala', 'ga_vichara'),
  ('bo_laksana_rerank', 'bo_bimba'),
  ('bo_laksana_rerank', 'ga_vichara'),
  ('bo_pratijna', 'bg_reference'),
  ('bo_pratijna', 'ga_positions'),
  ('bo_pratijna', 'ga_vargas'),
  ('bo_yantra_mechanism', 'bo_bimba'),
  ('bo_yantra_mechanism', 'ga_positions'),
  ('ka_avadhi', 'ga_positions'),
  ('ka_kalasutra', 'ga_dashas'),
  ('ka_vighnakara', 'ga_dashas'),
  ('ka_yojaka', 'ga_structural'),
  ('ka_yojaka', 'ga_yoga'),
  ('mi_darshana', 'bg_ghatana'),
  ('mi_darshana', 'bo_laksana'),
  ('mi_darshana', 'bo_sangati'),
  ('mi_gunanaka', 'mi_bhavisya'),
  ('mi_pariksha', 'bo_laksana'),
  ('mi_pariksha', 'mi_bhavisya'),
  ('mi_pariksha', 'mi_jivanaghatana'),
  ('mi_pariksha', 'ph_nimitta'),
  ('ph_muhurta', 'bg_ghatana'),
  ('ph_nimitta', 'bg_ghatana'),
  ('ph_nimitta', 'bo_pratijna'),
  ('ph_nimitta', 'ka_yojaka');

-- Guard 1: every producer of an edge whose consumer row exists must be an ACTIVE asset.
DO $$
DECLARE
    bad text;
BEGIN
    SELECT string_agg(e.asset_id || ' -> ' || e.dep, ', ' ORDER BY e.asset_id, e.dep)
      INTO bad
      FROM _m1202_edges e
      JOIN asset_registry c ON c.asset_id = e.asset_id
      LEFT JOIN asset_registry p ON p.asset_id = e.dep AND p.is_active
     WHERE p.asset_id IS NULL;
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1202: edge target missing or inactive in asset_registry (dependency trap): %', bad;
    END IF;
END $$;

-- Append only the missing deps, preserving existing order. Rows already covered are not touched.
UPDATE asset_registry r
   SET depends_on = COALESCE(r.depends_on, '{}'::text[]) || n.deps
  FROM (
        SELECT e.asset_id, array_agg(e.dep ORDER BY e.dep) AS deps
          FROM _m1202_edges e
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
      FROM _m1202_edges e
      JOIN asset_registry c ON c.asset_id = e.asset_id
     WHERE e.dep <> ALL (COALESCE(c.depends_on, '{}'::text[]));
    IF bad IS NOT NULL THEN
        RAISE EXCEPTION '1202: edge not present after update: %', bad;
    END IF;
    -- scoped to the consumers this migration touches: a pre-existing self-edge elsewhere must not
    -- fail the deploy for everyone (it is reported by verify Q3 instead)
    IF EXISTS (SELECT 1 FROM asset_registry r
                WHERE r.asset_id IN (SELECT asset_id FROM _m1202_edges)
                  AND r.asset_id = ANY (r.depends_on)) THEN
        RAISE EXCEPTION '1202: self-dependency present in asset_registry.depends_on of an edited asset';
    END IF;
END $$;

-- DOWN (ops reference, not executed by migrate.ts): remove exactly these edges.
--   UPDATE asset_registry r SET depends_on = ARRAY(
--       SELECT x FROM unnest(r.depends_on) x
--        WHERE x NOT IN (SELECT e.dep FROM (VALUES <the 27 (asset_id, dep) pairs above>) e(asset_id, dep)
--                         WHERE e.asset_id = r.asset_id))
--    WHERE r.asset_id IN (<the 15 consumer asset_ids above>);
