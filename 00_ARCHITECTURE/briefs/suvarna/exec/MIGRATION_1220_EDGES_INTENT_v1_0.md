---
artifact: MIGRATION_1220_EDGES_INTENT
version: "1.1"
status: "INTENT ONLY; the migration file is NOT written (owner hold on migrations 1219-1227)"
produced_by: Exec Suvarṇa
produced_on: 2026-10-02
ruling: "SS 2026-10-02: the ga_vargas -> ga_sensitive edge rides migration 1220 (the held edges migration) together with the two Q-L2-07 edges and the two Q-L1-02 edges; ONE guarded, append-only, acyclic-checked migration; must be applied before S-L1"
shape: "same kind as migration 1210 (surgical, append-only, guarded, verified by production structure afterwards)"
---

# Migration 1220 (edges): intent (six edges as of v1.1)

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

- Guarded on the five assets existing; each edge appended only if absent (idempotent, never edits an applied file); an in-migration recursive-CTE cycle check over the post-edit graph that RAISES on any cycle.
- No other column changes. Registry seed (`platform/scripts/seed/asset_registry_seed.ts`) must carry the same five edges so seed parity holds (a seed edit is code, not migration, and travels with the migration PR).
- Consequences stated plainly: `compute_upstream_hash` changes once for `bo_laksana`, `bo_upaya`, `ga_dashas`, `ga_yoga`, `ga_vargas` (a one-time rebuild signal at next dispatch; with S-L1 executing everything it costs nothing extra); each edited asset's frozen manifest goes to `plan_adaptation_required` (`assertManifestMatchesRegistryIdentity`); no data row changes. Verification after apply is by production structure (read the five `depends_on` arrays and the recursive-CTE acyclicity), not by the deploy log (Trap 103).
- Order: applied BEFORE S-L1 (the writer change that makes `ga_vargas` read `ga_sensitive` ships with, and requires, edge 5 and the S-L1 build order `ga_sensitive` then `ga_vargas`).

## Not in this migration

`bo_pratijna` re-point (waits on tracing `chart_fact_identity` and `brahma_reference_planets`), the held `ph_nimitta -> bo_pratijna` edge, argala migrations 1219/1221 (see `MIGRATION_1219_1221_INTENT_v1_0.md`), 1225-1227 (node series).

## Numbering note (SS 2026-10-02)

`1220` was first allocated to the older HELD five-edge set (branch `suvarna/land/TI-edges-002`, local only, head `ee5643a56`, backup bundle `/Users/Dev/suvarna-evidence/TI-edges-002_ee5643a56.bundle`): `ph_nimitta += bo_pratijna`, `ph_nimitta += ka_yojaka`, `mi_gunanaka += mi_bhavisya`, `mi_pariksha += mi_bhavisya`, `mi_pariksha += ph_nimitta`, blocked until their producers are lit and fresh. That older set is RE-ALLOCATED to **1228** (rename the file, its `_m1220_edges` temp table, its test and its seed comments at the owner's line, in one commit) and stays held until after the rebuild stages. The 1228 intent also gains the `bo_pratijna` re-point: remove `bo_laksana` and `bo_sangati`, add `ga_positions`, `ga_structural`, `ga_sensitive` (`ga_vargas` is present; `bg_reference` is bedrock-exempt; `chart_fact_identity` stays an undeclared dependency until the Track I asset `ga_fact_identity` exists).
