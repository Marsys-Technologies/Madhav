---
artifact: MIGRATION_1226_EDGES_INTENT
version: "1.4"
status: "MIGRATION 1226 APPLIED in production (four pre-S-L1 L1 edges); the file is on main. This revision lands the matching seed edit and seed-parity test. Two L2 edges are migration 1253 (separate)."
produced_by: Exec Suvarṇa
produced_on: 2026-10-02
ruling: "SS 2026-10-02: the ga_vargas -> ga_sensitive edge rides this migration with the two Q-L1-02 edges and the N-69 ga_dashas edge; ONE guarded, append-only, acyclic-checked migration; applied before S-L1. SS follow-up 2026-10-02: split from the chart_grants migration (1224, PR #2896); held for the S-L1 window. SS decision GO option B: the two Q-L2-07 L2 edges move to migration 1253, applied immediately before S-L2 is dispatched."
shape: "same kind as migration 1210 (surgical, append-only, guarded, verified by production structure afterwards)"
renumbering: "v1.1 called this migration 1220 (six edges); 1220 is Pravaha's #2884 (merged); the migration is 1226 (four edges) and the older held five-edge set formerly called 1220 is 1228."
changelog: "1.4: migration 1226 is applied and on main; seed carries the four edges (tests-only PR, no migration); apply-timing and freshness sections kept as the historical record of the apply. 1.3: four edges; L2 edges split to 1253; stale-set narrowed to three assets; serving effect added. 1.2: file written, apply timing + freshness staleness + apply order. 1.1: six edges (intent only)."
---

# Migration 1226 (four pre-S-L1 L1 edges): intent (v1.4)

Notation: `A.depends_on += B` means A reads B's output and must be built after B.

| # | edge (live `asset_registry.depends_on`) | source of the edge | evidence (read 2026-10-02) |
|---|---|---|---|
| 1 | `ga_dashas.depends_on += ga_vargas` | Q-L1-02 (a) | `ga_dashas_writer.py:575-587` reads `chart_divisionals` |
| 2 | `ga_yoga.depends_on += ga_vargas` | Q-L1-02 (a) | `ga_yoga_writer.py:2435-2445` reads D9 through `ga_structural_writer._load_varga_positions` |
| 3 | `ga_vargas.depends_on += ga_sensitive` | N-69 karaka lane | `ga_vargas` will READ `ga_sensitive`'s `kn_rao_rahu_included` karaka assignments instead of re-deriving them (`ga_vargas_writer.py:649-675` today); live `ga_vargas {ga_positions}`, `ga_sensitive {ga_positions, bg_reference}` |
| 4 | `ga_dashas.depends_on += ga_sensitive` | N-69 dashas karaka roles (S-L1 mandatory) | `ga_dashas_writer` will READ ga_sensitive's `kn_rao_rahu_included` assignments instead of the hard-coded `_JAIMINI_KARAKAS` (`ga_dashas_writer.py:645-657`; feeds `karaka_role_at_period` and `karakas_active_during_period`, ~169,000 non-null rows per chart); live `ga_dashas {ga_positions}` (+ `ga_vargas` by edge 1) |

Live before: `ga_dashas {ga_positions}`, `ga_yoga {ga_structural, ga_dashas}`, `ga_vargas {ga_positions}`; producer `ga_sensitive {ga_positions, bg_reference}` unchanged.

## Moved to migration 1253 (own branch and held PR #2904)

`bo_laksana += ga_yoga` (`bo_laksana.py:2713,2769` read `ga_yoga_firings`) and `bo_upaya += bo_bimba` (`bo_upaya.py:578` joins `bodha_cgm_nodes`), both Q-L2-07. Applied IMMEDIATELY BEFORE S-L2 is dispatched (applying after would re-stale `bo_laksana`/`bo_upaya`; applying early stales their freshness and gates their lit `bo_*` dependents). The two migrations are independent: either order is valid, the union is acyclic, and their seed edits touch disjoint asset entries.

## Acyclic check (by hand, re-proved by the migration's own guard)

After the four edges: `ga_dashas -> {ga_positions, ga_vargas, ga_sensitive}`, `ga_vargas -> {ga_positions, ga_sensitive}`, `ga_sensitive -> {ga_positions, bg_reference}`, `ga_yoga -> {ga_structural, ga_dashas, ga_vargas}`. `ga_sensitive` depends on neither `ga_vargas` nor `ga_dashas`; `ga_vargas` gains only `ga_sensitive`; no path leads back from `ga_sensitive`, `ga_vargas` or `ga_dashas` to `ga_yoga`, `ga_structural` or `ga_dashas`. The live 129-asset registry graph plus the four edges (and plus 1253's two) was checked acyclic offline, read-only.

## Migration shape (same kind as 1210)

- Guarded on the four involved assets existing (all-or-nothing; empty registry is a no-op; partial or inactive producer RAISES); each edge appended only if absent (idempotent, never edits an applied file); an in-migration recursive-CTE cycle check over the post-edit graph that RAISES on any cycle through an edited consumer; `SET LOCAL lock_timeout = '5s'` first (a blocked migrate job must fail fast, not hang a shared deploy); no BEGIN/COMMIT.
- No other column changes. The registry seed (`platform/scripts/seed/asset_registry_seed.ts`) carries the same four edges (and only these; 1253's seed edits are on its own branch) so seed parity holds on each PR independently.
- Consequences stated plainly: `compute_upstream_hash` changes once for `ga_dashas`, `ga_yoga`, `ga_vargas` (a one-time rebuild signal; with S-L1 executing everything it costs nothing extra); each edited asset's frozen manifest goes to `plan_adaptation_required` (`assertManifestMatchesRegistryIdentity`); no data table row changes.
- Order: applied BEFORE S-L1 (the writer change that makes `ga_vargas` read `ga_sensitive` ships with, and requires, edge 3 and the S-L1 build order `ga_sensitive` then `ga_vargas`).

## Apply timing and apply order (historical record; 1226 is now applied)

**Merge = apply.** `platform/scripts/migrate.ts` runs on every deploy, so the moment PR #2898 merges, the next deploy applies 1226. It therefore merges ONLY in the S-L1 window, immediately before the L1 dispatches. Order:

1. S-L1 writer PRs deployed.
2. 1219 applied (argala migration).
3. **1226 applied** (this migration; deploy of the merge commit).
4. F-A2 D6 plan.
5. Dispatches: `ga_positions`, `ga_sensitive`, `ga_vargas`, ...

Precondition at apply (operator check, not enforced in the file): no other run is dispatching or running these assets. Read 2026-10-02: `SELECT count(*) FROM build_runs WHERE state IN ('planned','running','paused')` = 0, and 0 active runs include any of the four involved assets (the status column of `build_runs` is `state`).

## Freshness staleness (all charts, three assets)

`asset_registry` carries the trigger `nirmana_registry_receipt_invalidation` (migration 596; `AFTER UPDATE OF depends_on, ... FOR EACH ROW WHEN OLD IS DISTINCT FROM NEW`). Its function runs `UPDATE asset_freshness SET freshness_state = 'stale', reasons += 'registry_changed', observed_at = now() WHERE asset_id = NEW.asset_id` with no chart filter. So at apply, every `asset_freshness` row of `ga_vargas`, `ga_dashas` and `ga_yoga` goes **stale on EVERY chart**. `ga_sensitive` is the producer and is not staled; `bo_laksana` and `bo_upaya` are no longer staled by 1226 (their edges are 1253's). The last receipt is kept; only the projection flips, and it stays stale until each chart's rebuild re-establishes a fresh receipt. Serving effect on the canonical chart (SS): exactly those three flip from resolved to unresolved until rebuilt, about 37 min typical compute. Through the hard gate (`asset_runner.deps_unsatisfied`) a stale `ga_vargas` gates `ga_dashas`, `ga_yoga` and every other declared dependent of the three until rebuilt; this is the intended S-L1 order (`ga_sensitive` -> `ga_vargas` -> `ga_dashas`/`ga_yoga` -> ...). A second run does not re-fire the trigger. Production 2026-10-02: one chart carries these rows (one fresh row each for the three). This is why 1226 is held and was split from 1224.

## Post-apply verification (by production structure, not the deploy log; Trap 103)

```sql
SELECT asset_id, depends_on FROM asset_registry
 WHERE asset_id IN ('ga_dashas','ga_yoga','ga_vargas') ORDER BY 1;                    -- the four edges present
SELECT asset_id, chart_id, freshness_state, reasons FROM asset_freshness
 WHERE asset_id IN ('ga_dashas','ga_yoga','ga_vargas') ORDER BY 1, 2;                 -- stale + registry_changed
-- plus the full-registry recursive-CTE closure (query in the migration header): 0 rows
```

## Landing record

- Migration `platform/migrations/1226_asset_registry_four_pre_s_l1_edges.sql`, seed edit, seed-parity test, regenerated census (seed hash only moves) and `platform/python-sidecar/tests/test_migration_1226_four_l1_edges.py` (live tier against a disposable PostgreSQL; cycle guard mutation-checked) were carried by closed PR #2898. Migration 1226 is already applied in production and its file is on main; this tests-only PR lands the seed edit, the seed-parity test, the regenerated census (seed hash only) and the test file (a later commit), so the seed now matches the applied migration.
- Seed arrays: `ga_vargas ['ga_positions','ga_sensitive']`; `ga_dashas ['ga_positions','ga_sensitive','ga_vargas']`; `ga_yoga ['ga_structural','ga_dashas','ga_vargas']` (same order the migration appends them).
- The chart_grants migration (1224) is a separate PR, #2896, safe to merge at any time. The two L2 edges are migration 1253 (separate held PR).
- If both 1226 and 1253 merge, the only textual overlap is the generated census JSON (`content_sha256` and the seed file hash): the second to merge regenerates it (`npm run codegen:capability-estate-census` with the committed provenance), never hand-merges it. The seed and parity-test hunks are disjoint.
