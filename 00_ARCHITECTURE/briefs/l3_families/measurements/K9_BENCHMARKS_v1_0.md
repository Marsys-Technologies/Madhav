---
artifact: K9_BENCHMARKS
version: "1.0"
status: PREBUILD — measurement protocol, no full-layer speed claim
produced_on: 2026-10-16
item: K9-23
source_plan: KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md §6.1–§6.3, §10 Build
changelog: "1.0: code-only SR-A4-01 preparation; identify unmeasured quantities and retain activation gates."
---

# Kāla rebuild measurement contract

This is preparation under SR-A4-01. Full-candidate rebuild, prospective consumer
qualification, invalidation and killed-substep measurements have **not** been
performed here. Their values are null, not zero. No speedup or minutes-per-chart
claim follows from the fixture tests.

## Reproducible environment

The pre-build starts at `ef14167bcc35a321b11d4d189a6b752bf3c658b8`.
Inherited tooling was read at `origin/kalayantra/k9-23` commit
`8021067f74e7e020d9bee7b0b4617d697cb2c6e5`; no fetch or Git mutation was
performed. The local ref was already available. Before a real benchmark, record the landed source SHA, dirty patch
SHA if applicable, dependency lock hashes, model digest, rule-registry version,
candidate generation, build id and complete candidate conventions. The current
machine is Apple M5 Max, arm64, 18 logical CPUs, 137438953472 bytes RAM,
macOS 27.0.1. Local test tools: Python 3.14.6, pytest 9.1.1, psycopg 3.3.4,
pyswisseph 2.10.3.2, PyYAML 6.0.3. The local server reports PostgreSQL
15.17 (Homebrew), read through the suite's guarded throwaway fixture; CI uses
PostgreSQL 16, so this is not qualification on an identical server version. CI's Python version is separately pinned in
`.github/workflows/ci.yml`; do not merge results from different environments.

Pinned local corpus (`SE_EPHE_PATH=/Users/Dev/kalayantra/ephe`):

| File | SHA-256 |
|---|---|
| sepl_18.se1 | ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66 |
| semo_18.se1 | 1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7 |
| seas_18.se1 | a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2 |

The publication tests use guarded, uniquely named fixture databases on
`127.0.0.1:55433`, 19 frozen-roster writer/service identities, one grain each, explicit input grains, and actual
PostgreSQL manifest/head rows. They exercise no astronomical workload and do not
substitute for the layer benchmark. Tests do not read production or fetch corpus
files. Ephemeris cache use: none in these publication fixtures; OS/PostgreSQL
caches: uncontrolled. These test runtimes cannot be labelled cold or warm builds.

## Each benchmark record

Store the following alongside raw measurements; nulls require a named reason.

| Dimension | Required observation | Pre-build value |
|---|---|---|
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
never share a “faster and equivalent” claim.

## Execution boundary

`services.kala_core.publication.inspect_rebuild` checks the frozen build plan;
its `PLAN_ONLY`, `executed_assets=[]`, `dry_run_passed=null` result is a read-only
inspection. The real orchestrator parser has only `--run-id`
(`platform/python-sidecar/pipeline/orchestrator/main.py:52`).

**(I) INTERPRETATION:** because no orchestrator dry-run flag exists, the prepared
`orchestrator_rebuild_dryrun` binding means plan inspection. Alternative: invent a
runner dry-run flag or label an inspection a successful execution rehearsal.
Neither earns `dry_run_passed`. Before activating rebuild, obtain a real
rehearsal/transaction rollback proof and J-1a's qualified backup/restore evidence.


The environment and ephemeris hashes were measured anew for K923B and retained
in the job's `environment.json`. Each test oracle compares fixture candidate
outputs with independently recomputed `source × 3` values. No production
Jyotish oracle is claimed: the production checker registry is empty and refuses.
The local manifest test duration is test overhead, not build performance.

Source anchors: PLAN §6.1 at
`00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:265`,
benchmark dimensions at `:289`, and the actual-run/restart requirement at `:469`.
