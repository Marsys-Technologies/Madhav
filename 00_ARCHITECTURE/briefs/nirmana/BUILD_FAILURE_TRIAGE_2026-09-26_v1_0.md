---
artifact: BUILD_FAILURE_TRIAGE_2026-09-26
canonical_id: BUILD_FAILURE_TRIAGE_2026_09_26
version: "1.0"
status: MEASURED
date: 2026-09-26
authority: "Native context, 2026-09-26: the orchestrator skips L0 on a global build and walks L1-L5; assets fail and the autonomous build breaks, or an asset is dropped in a layer-scope build. This artefact measures that rather than describing it."
measured_against: "build_runs (776 runs) · build_run_assets (6,962 asset-run records) · asset_throughput · asset_registry — production, read-only, 2026-09-26"
role: "Triage of every recorded build failure by cause, so the work is aimed at causes rather than at consequences."
---

# Why the autonomous build breaks — measured

**2,283 of 6,962 asset-run records failed or aborted: one attempt in three.** That is the number behind
"many of the assets fail and the autonomous build breaks." But it is not 2,283 problems.

## The triage

| family | records | distinct assets | what it is |
|---|---|---|---|
| **cascade — BLOCKED by upstream** | **1,281 (56%)** | 66 | not failures. An upstream asset did not light, so everything downstream was refused. These are *consequences* of the causal rows below |
| **infra — crash, orphan, guardian reap, stall** | **543 (24%)** | 71 | the worker died, the run was orphaned, a guardian reaped it. Not an asset defect |
| **no error text at all** | **307 (13%)** | 82 | failed or aborted with nothing recorded. **A diagnosability gap** — a third of non-cascade failures cannot be attributed to anything |
| **causal: writer code error** | 33 | 17 | `TypeError`, `KeyError`, `ValueError`, `AttributeError`, UUID/Decimal not JSON serializable |
| **causal: post-write integrity check** | 27 | 16 | the asset's own `integrity_check_sql` returned false after its write |
| **causal: dependency not lit at run time** | 19 | 15 | `DEP-ASSERT` / `UpstreamStageIncomplete` — declared correctly, not satisfied in that run |
| **causal: frozen manifest invalidated mid-run** | 18 | 18 | `asset_registry changed after the manifest was frozen` — the run aborts **wholesale** |
| **causal: constraint violation** | 15 | 10 | check, foreign-key, not-null, unique |
| **causal: schema mismatch** | 8 | 8 | `UndefinedColumn` — the writer and the table disagree |
| **causal: no writer registered** | 7 | 5 | `no writer registered for bo_cdlm_summary / bo_cgm_motifs / bo_cgm_paths / bo_chart_gestalt / ka_gochara_sweep` |
| other · timeout | 25 | 19 | |

**About 127 causal records, across roughly 60 assets, produce 1,281 blocked ones.** That ratio is the
whole finding: the autonomous build does not break because a third of the estate is broken. It breaks
because a small number of causal failures cascade, and because a quarter of the record is infrastructure
and an eighth is undiagnosable.

## Where the causes are

| layer | causal records | causal assets | cascade | infra | no text |
|---|---|---|---|---|---|
| **L3 Kāla** | **51** | 16 | 295 | 198 | 102 |
| L1 Gaṇita | 30 | 10 | 103 | 91 | 66 |
| L2 Bodha | 26 | 13 | 331 | 127 | 72 |
| **L0 Brahmagyan** | 24 | 13 | **0** | **0** | **0** |
| L5 Mīmāṃsā | 12 | 6 | 282 | 66 | 40 |
| L4 Phala | 7 | 4 | 270 | 63 | 27 |

**L0's column is the shape of a layer that is never in the global chain.** Zero cascade and zero infra
records, because a global build skips it — confirmed independently: of **68 global runs, zero** included
a `bg_*` asset. L0 fails only in its own asset-scope runs, where nothing is downstream of it.

**L3 carries the most causes**, and L2 the most cascade — consistent with L2 sitting upstream of L3, L4
and L5 in the DAG.

## The correction this triage makes to its own prompt

I recommended investigating the seven L0 assets whose post-write integrity checks failed, calling it the
most interesting finding and putting it ahead of the layer packets. **Measured, that recommendation was
wrong.** All seven checks **pass today**; every cross-asset table they assert **is** a declared dependency;
and the run history shows what actually happened — `bg_yogas` was rebuilt on 09-04, 09-05 and 09-06,
failing its check each time, and completed on the fourth attempt the same day. That is a **repair loop
converging**, not a standing defect. The same shape holds for the other six.

What the evidence says to fix instead, in order:

1. **The 307 no-error-text failures.** You cannot fix what you cannot attribute, and this is an eighth of
   the record across 82 assets. Whatever swallows the error is worth more than any single asset fix.
2. **The 543 infra crashes and reaps.** A quarter of the record is the build system failing, not the
   assets. Until that falls, asset-level work is measured against noise.
3. **The 5 assets with no writer registered** — `bo_cdlm_summary`, `bo_cgm_motifs`, `bo_cgm_paths`,
   `bo_chart_gestalt`, `ka_gochara_sweep`. This is `Build.registered` failing in L2 and L3 exactly as the
   gate predicts, and it is the cheapest causal class to close.
4. **The frozen-manifest invalidation**, 18 assets across 8 runs: one registry change mid-flight aborts
   every asset in the run. On 2026-09-04 it aborted a 10-asset L0 run in full — the "assets get dropped"
   mechanism, precisely.
5. Then the per-asset causal classes (writer code errors, constraint and schema mismatches), which the
   `Build` gate's checks 2, 8 and 9 now surface per asset without waiting for a run to fail.

## What this says about the gate

Every causal family maps onto a check the `Build` gate already runs: no-writer → check 1 · writer code
error → checks 2 and 8 · dependency not lit → check 9 · post-write integrity → checks 5 and 6 ·
manifest invalidation → check 8's history. The gate was designed from the contract; the record confirms
it is aimed at the right things. What the record adds is **priority**: the blocking radius of a causal
failure, which is why one asset's error becomes 1,281 blocked runs.
