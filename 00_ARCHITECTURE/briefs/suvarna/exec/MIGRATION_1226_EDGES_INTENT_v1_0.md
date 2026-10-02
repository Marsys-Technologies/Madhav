---
artifact: MIGRATION_1226_EDGES_INTENT
version: "1.2"
status: "MIGRATION FILE WRITTEN on PR #2898; HELD for the S-L1 window (merge = apply at next deploy)"
produced_by: Exec Suvarṇa
produced_on: 2026-10-02
ruling: "SS 2026-10-02: the ga_vargas -> ga_sensitive edge rides the six-edge migration together with the two Q-L2-07 edges and the two Q-L1-02 edges; ONE guarded, append-only, acyclic-checked migration; must be applied before S-L1. SS follow-up 2026-10-02: split from the chart_grants migration (1224, PR #2896); 1226 is held and merges only in the S-L1 window."
shape: "same kind as migration 1210 (surgical, append-only, guarded, verified by production structure afterwards)"
renumbering: "v1.1 called this migration 1220; 1220 is now Pravaha's #2884 (merged). The six-edge set is migration 1226. The older held five-edge set formerly called 1220 is 1228."
---

# Migration 1226 (six pre-S-L1 edges): intent (v1.2)

Notation: `A.depends_on += B` means A reads B's output and must be built after B.

| # | edge (live `asset_registry.depends_on`) | source of the edge | evidence (read 2026-10-02) |
|---|---|---|---|
| 1 | `bo_laksana.depends_on += ga_yoga` | Q-L2-07 (1) | `bo_laksana.py:2713,2769` read `ga_yoga_firings`; live `bo_laksana {bg_rules, ga_positions, ga_strength, ga_sensitive, ga_panchanga, ga_sade_sati, ga_structural, ga_nakshatra, ga_condition, ga_vargas, ga_vichara}` has no `ga_yoga` |
| 2 | `bo_upaya.depends_on += bo_bimba` | Q-L2-07 (1) | `bo_upaya.py:578` joins `bodha_cgm_nodes`; live `bo_upaya {bo_laksana, bo_sangati, ga_structural, ga_dashas, bo_cgm_motifs}` |
| 3 | `ga_dashas.depends_on += ga_vargas` | Q-L1-02 (a) | `ga_dashas_writer.py:575-587` reads `chart_divisionals` |
| 4 | `ga_yoga.depends_on += ga_vargas` | Q-L1-02 (a) | `ga_yoga_writer.py:2435-2445` reads D9 through `ga_structural_writer._load_varga_positions` |
| 5 | `ga_vargas.depends_on += ga_sensitive` | N-69 karaka lane (this document) | `ga_vargas` will READ `ga_sensitive`'s `kn_rao_rahu_included` karaka assignments instead of re-deriving them (`ga_vargas_writer.py:649-675` today); live `ga_vargas {ga_positions}`, `ga_sensitive {ga_positions, bg_reference}` |
| 6 | `ga_dashas.depends_on += ga_sensitive` | N-69 dashas karaka roles (S-L1 mandatory) | `ga_dashas_writer` will READ ga_sensitive's `karaka_school` value `kn_rao_rahu_included` assignments instead of the hard-coded `_JAIMINI_KARAKAS` (`ga_dashas_writer.py:645-657`; feeds `karaka_role_at_period` and `karakas_active_during_period`, ~169,000 non-null rows per chart); live `ga_dashas {ga_positions}` (+ `ga_vargas` by edge 3) |

## Acyclic check (by hand, to be re-proved by the migration's own guard)

Live edges involved: `ga_dashas {ga_positions}`, `ga_yoga {ga_structural, ga_dashas}`, `ga_vargas {ga_positions}`, `ga_sensitive {ga_positions, bg_reference}`,
`ga_structural {ga_dashas, ga_nakshatra, ga_panchanga, ga_positions, ga_sensitive, ga_strength, ga_vargas}`, `ga_yoga` `lit`, `bo_bimba {bo_laksana, five satellites}`.
After the six edges: `ga_dashas -> {ga_vargas, ga_sensitive}`, `ga_vargas -> ga_sensitive -> {ga_positions, bg_reference}` and `ga_yoga -> {ga_structural, ga_dashas, ga_vargas}`: no path leads back from `ga_sensitive`, `ga_vargas` or `ga_dashas` to `ga_yoga`, `ga_structural` or `ga_dashas`
(`ga_sensitive` depends on neither `ga_vargas` nor `ga_dashas` and reads no `chart_divisionals`; `ga_vargas` gains only `ga_sensitive`). Edges 1-2: `ga_yoga` depends on no `bo_*`; `bo_bimba` does not depend on `bo_upaya`. Result: acyclic.
`ga_dashas` has 16 dependents, so edge 3 reorders many assets only in the sense that `ga_dashas` now waits for `ga_vargas`; since `ga_vargas` is `lit` on all three charts and S-L1 builds everything in DAG order, it costs nothing extra.

## Migration shape (same kind as 1210)

- Guarded on the involved assets existing (all-or-nothing; empty registry is a no-op); each edge appended only if absent (idempotent, never edits an applied file); an in-migration recursive-CTE cycle check over the post-edit graph that RAISES on any cycle.
- No other column changes. Registry seed (`platform/scripts/seed/asset_registry_seed.ts`) must carry the same six edges so seed parity holds (a seed edit is code, not migration, and travels with the migration PR).
- Consequences stated plainly: `compute_upstream_hash` changes once for `bo_laksana`, `bo_upaya`, `ga_dashas`, `ga_yoga`, `ga_vargas` (a one-time rebuild signal at next dispatch; with S-L1 executing everything it costs nothing extra); each edited asset's frozen manifest goes to `plan_adaptation_required` (`assertManifestMatchesRegistryIdentity`); no data row changes. Verification after apply is by production structure (read the five `depends_on` arrays and the recursive-CTE acyclicity), not by the deploy log (Trap 103).
- Order: applied BEFORE S-L1 (the writer change that makes `ga_vargas` read `ga_sensitive` ships with, and requires, edge 5 and the S-L1 build order `ga_sensitive` then `ga_vargas`).

## Not in this migration

`bo_pratijna` re-point (waits on tracing `chart_fact_identity` and `brahma_reference_planets`), the held `ph_nimitta -> bo_pratijna` edge, argala migrations 1219/1221 (see `MIGRATION_1219_1221_INTENT_v1_0.md`), 1225-1227 (node series).

## Numbering note (SS 2026-10-02)

`1220` was first allocated to the older HELD five-edge set (branch `suvarna/land/TI-edges-002`, local only, head `ee5643a56`, backup bundle `/Users/Dev/suvarna-evidence/TI-edges-002_ee5643a56.bundle`): `ph_nimitta += bo_pratijna`, `ph_nimitta += ka_yojaka`, `mi_gunanaka += mi_bhavisya`, `mi_pariksha += mi_bhavisya`, `mi_pariksha += ph_nimitta`, blocked until their producers are lit and fresh. That older set is RE-ALLOCATED to **1228** (rename the file, its `_m1220_edges` temp table, its test and its seed comments at the owner's line, in one commit) and stays held until after the rebuild stages. The 1228 intent also gains the `bo_pratijna` re-point: remove `bo_laksana` and `bo_sangati`, add `ga_positions`, `ga_structural`, `ga_sensitive` (`ga_vargas` is present; `bg_reference` is bedrock-exempt; `chart_fact_identity` stays an undeclared dependency until the Track I asset `ga_fact_identity` exists).

## Apply timing and apply order (v1.2)

**Merge = apply.** `platform/scripts/migrate.ts` runs on every deploy, so the moment PR #2898 merges, the next deploy applies 1226. It therefore merges ONLY in the S-L1 window, immediately before the L1 dispatches. Order:

1. S-L1 writer PRs deployed.
2. 1219 applied (argala migration).
3. **1226 applied** (this migration; deploy of the merge commit).
4. F-A2 D6 plan.
5. Dispatches: `ga_positions`, `ga_sensitive`, `ga_vargas`, ...

Precondition at apply (operator check, not enforced in the file): no other run is dispatching or running these assets. Read 2026-10-02: `SELECT count(*) FROM build_runs WHERE state IN ('planned','running','paused')` = 0, and 0 active runs include any of the seven involved assets (the status column of `build_runs` is `state`).

## Freshness staleness (found by the migration-guard review; v1.2)

`asset_registry` carries the trigger `nirmana_registry_receipt_invalidation` (migration 596; `AFTER UPDATE OF depends_on, ... FOR EACH ROW WHEN OLD IS DISTINCT FROM NEW`). Its function runs `UPDATE asset_freshness SET freshness_state = 'stale', reasons += 'registry_changed', observed_at = now() WHERE asset_id = NEW.asset_id` with no chart filter. So at apply, every `asset_freshness` row of `bo_laksana`, `bo_upaya`, `ga_dashas`, `ga_yoga`, `ga_vargas` goes **stale on EVERY chart**. The last receipt is kept; only the projection flips, and it stays stale until each chart's rebuild re-establishes a fresh receipt. Through the hard gate (`asset_runner.deps_unsatisfied`), a stale `ga_vargas` gates `ga_dashas` and `ga_yoga`, and a stale `ga_yoga` gates `bo_laksana`, until rebuilt; this is the intended S-L1 order (`ga_sensitive` -> `ga_vargas` -> `ga_dashas`/`ga_yoga` -> ...). Anything reading `asset_freshness = 'fresh'` for these five assets (and the dependents of `ga_dashas`, `ga_yoga`, `ga_vargas`) sees stale until then. A second run does not re-fire the trigger. Production 2026-10-02: one chart carries these rows (`ga_dashas`, `ga_yoga`, `ga_vargas` fresh; `bo_laksana` and `bo_upaya` one fresh and one stale row each). This is why 1226 is held and why it was split from 1224.

## Post-apply verification (by production structure, not the deploy log; Trap 103)

```sql
SELECT asset_id, depends_on FROM asset_registry
 WHERE asset_id IN ('bo_laksana','bo_upaya','ga_dashas','ga_yoga','ga_vargas') ORDER BY 1;   -- the six edges present
SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness
 WHERE asset_id IN ('bo_laksana','bo_upaya','ga_dashas','ga_yoga','ga_vargas') ORDER BY 1, 2;  -- stale + registry_changed
-- plus the recursive-CTE closure used by the migration's Guard 3: no row with src = node over the full registry
```

## Landing record (v1.2)

- Migration file `platform/migrations/1226_asset_registry_six_pre_s_l1_edges.sql`, seed edit, seed-parity test, regenerated census (seed hash only moves), and `platform/python-sidecar/tests/test_migration_1226_six_pre_s_l1_edges.py` (live tier against a disposable PostgreSQL; cycle guard mutation-checked) are on PR #2898 (draft, HELD).
- Seed arrays: `ga_vargas ['ga_positions','ga_sensitive']`; `ga_dashas ['ga_positions','ga_sensitive','ga_vargas']`; `ga_yoga ['ga_structural','ga_dashas','ga_vargas']`; `bo_laksana` + `'ga_yoga'`; `bo_upaya` + `'bo_bimba'` (same order the migration appends).
- The live 129-asset registry graph plus the six edges was checked acyclic offline (read-only) on 2026-10-02.
- The chart_grants migration (1224) is a separate PR, #2896, safe to merge at any time.
