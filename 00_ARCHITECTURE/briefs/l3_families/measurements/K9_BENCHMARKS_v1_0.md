---
artifact: K9_BENCHMARKS
version: "1.1"
status: PREBUILD — measurement protocol, no full-layer speed claim
produced_on: 2026-10-20
item: K9-23
source_plan: KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §6.1–§6.3, §10 Build
changelog: "1.1: environment stated as labelled items (hardware, OS, tool versions, ephemeris path) with the corpus hashed; a claim-kind field makes a semantic correction and an optimisation separate records; the execution boundary now describes the enabled rebuild kinds (SR-PREBUILD-ALL, #3746) and keeps every full-layer measurement null. 1.0: code-only SR-A4-01 preparation; identify unmeasured quantities and retain activation gates."
---

# Kāla rebuild measurement contract

This is preparation under SR-A4-01 and SR-PREBUILD-ALL. Full-candidate rebuild,
prospective consumer qualification, invalidation and killed-substep measurements
have **not** been performed here. Their values are null, not zero. No speedup or
minutes-per-chart claim follows from the fixture tests.

## Reproducible environment

The pre-build starts at `9f7be28a03dd35c1b359d5db01a7ba91269630e6`.
Before a real benchmark, additionally record the landed source SHA, dirty patch
SHA if applicable, dependency lock hashes, model digest, rule-registry version,
candidate generation, build id and complete candidate conventions. CI's Python
version is separately pinned in `.github/workflows/ci.yml`; do not merge results
from different environments. The local machine that ran the K9-23 fixture tests
(measured 2026-10-20):

- **Hardware:** Apple M5 Max, arm64, 18 logical CPUs, 137438953472 bytes RAM
- **Operating system:** macOS 27.0.1
- **Python:** 3.14.6
- **pytest:** 9.1.1
- **psycopg:** 3.3.4
- **pyswisseph:** 2.10.3.2
- **PyYAML:** 6.0.3
- **Ephemeris path:** `SE_EPHE_PATH=/Users/Dev/kalayantra/ephe` (pinned local corpus, never a stand-in or a network fetch)

Corpus files, hashed (`test_k9_publication_docs.py` re-hashes them wherever the corpus is present):

| File | SHA-256 |
|---|---|
| sepl_18.se1 | ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66 |
| semo_18.se1 | 1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7 |
| seas_18.se1 | a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2 |

The publication tests use guarded, uniquely named fixture databases on
`127.0.0.1:55433`, two writer identities, explicit input grains, and actual
PostgreSQL manifest/head rows. They exercise no astronomical workload and do not
substitute for the layer benchmark. Tests do not read production or fetch corpus
files. Ephemeris cache use: none in these publication fixtures; OS/PostgreSQL
caches: uncontrolled. These test runtimes cannot be labelled cold or warm builds.

## Each benchmark record

Store the following alongside raw measurements; nulls require a named reason.

| Dimension | Required observation | Pre-build value |
|---|---|---|
| Claim kind | exactly one of `semantic-correction` or `optimisation`; an optimisation record cites the corrected-model record it is measured against and its numerical-equivalence oracle | null — no record exists yet |
| Workload | chart, horizon, classes, targets, knots, grains, shifts, selected writers, row counts, model/convention pins | null — full K9-1 candidate not operated |
| Cache | cold/warm definition, process reuse, database buffers, prepared context reuse and ephemeris cache | null — full workload not run |
| Whole run | wall seconds, CPU seconds, peak RSS bytes | null — full workload not run |
| Components | context preparation, astronomy, field evaluation, null maxima, pooled quantile separately | null — no component benchmark |
| Storage | SQL round trips, bytes transferred, rows and WAL bytes | null — no production-like measurement |
| First qualified consumer | wall seconds to complete verification and qualified consumer result | null — no full candidate qualification |
| Resume | kill point, durable completed grains, abandoned work seconds, actual repeated grains, resume time | null — killed-substep rehearsal pending |
| Scenarios | no-window, dense-window, station/retrograde, boundary, cold, warm, resume | null — full scenario matrix pending |

Record the old costs from PLAN §6.1 as historical observations with their
original workload, not comparable baselines: Kṣetra 22685 s, century materializer
3480 s, Saṅgam/spine approximately 2251 s, Kalasutra p50 487 s. The replacement
changes semantics. First benchmark the corrected model; only then benchmark an
optimisation against that same corrected model with identical inputs and a
numerical-equivalence oracle. A semantic correction and an optimisation must
never share a “faster and equivalent” claim: every record carries exactly one claim
kind, and a change that is both is stored as two records that never combine.

## Execution boundary

All eight layer and rebuild kinds are enabled in `fleet/executor_ops.json`
(`orchestrator_rebuild(_dryrun)`, `layer_verify(_dryrun)`, `layer_publish(_dryrun)`,
`layer_rollback(_dryrun)`; see K9_DRILLS_v1_0.md). Enablement is a declaration, not a
measurement: it carries no benchmark value.

`orchestrator_rebuild_dryrun` runs `services.kala_core.publication_admission
rebuild-dryrun`, which checks the SR-BOLD-04 phase split and then
`services.kala_core.publication.inspect_rebuild` against the frozen build plan. Its
`PLAN_ONLY`, `executed_assets=[]`, `dry_run_passed=false` result is a read-only
inspection. The real orchestrator parser has only `--run-id`
(`platform/python-sidecar/pipeline/orchestrator/main.py:52`).

**(I) INTERPRETATION:** because no orchestrator dry-run flag exists, the rebuild dry
run means plan inspection. Alternative: invent a runner dry-run flag or label an
inspection a successful execution rehearsal. Neither earns `dry_run_passed` for a
rebuild; only the three layer dry runs, which run the real operation in a
rolled-back transaction, can. A real rebuild is measured only through the
orchestrator in probe (delta-skip) mode, never with `NIRMANA_FORCE_EXECUTE`, and only
after J-1a's qualified backup/restore evidence exists.
