---
artifact: MADHAV_DATA_PLANE_L3_W0_BENCHMARK_BASELINE
version: "1.0"
status: FINAL_REVIEW_PENDING
observed_at: 2026-09-15T04:45:00+05:30
strategy_decision: DP-SD-017
source_tip: 3f109869d
production_builds: 0
production_mutations: 0
---

# L3 W0 reproducible benchmark baseline

## Boundary and host

These are matched, repeated, source-local measurements. They establish a W0
comparison baseline and falsifying tests; they are not PostgreSQL, deployed,
full-chart, consumer-value or production-duration evidence.

Host: Darwin 25.5.0 arm64, Apple M5 Pro, 64 GiB RAM, Python 3.14.6,
NumPy 2.5.1 and pyswisseph 20230604. Each pytest repeat is a fresh single
Python process. The structured publication harness creates a fresh writer and
strict in-memory connection per repeat in one process; it requests no worker
threads. `/usr/bin/time -lp` supplies process elapsed/CPU/RSS observations.
The harness performs no filesystem writes or benchmark-data reads. Its transit
context performs bounded path-existence probes and, only if a file-backed path
resolves, reads the selected ephemeris file to record its size and SHA-256.

Database SQL execution time, database I/O, WAL bytes, durable storage bytes,
network time and qualified live first-result latency are **not applicable** to
these no-database workloads. They remain unmeasured, not zero. The fake records
SQL statement intent but does not execute SQL or emulate PostgreSQL timing.

## Exact commands

Run from `platform/python-sidecar`:

```text
for i in 1 2 3 4 5; do echo run=$i-transit; /usr/bin/time -lp pytest -q -s tests/l3/test_transit_search_cache.py; done
for i in 1 2 3 4 5; do echo run=$i-null; /usr/bin/time -lp pytest -q tests/l3/ka_kshetra/test_stage5_null.py; done
for i in 1 2 3 4 5; do echo run=$i-preparation; /usr/bin/time -lp pytest -q tests/l3/ka_kshetra/test_planning_safety.py; done
for i in 1 2 3 4 5; do echo run=$i-publication; /usr/bin/time -lp pytest -q tests/l3/ka_kshetra/test_writer.py -k 'Stage6Salience or Stage65Insights or Stage8TimelineSpec or HashCoverage or ContentHashStreams'; done
/usr/bin/time -lp python3 scripts/validate_data_plane_l3_w0_baselines.py --repeats 5
```

The harness is committed at
`platform/python-sidecar/scripts/validate_data_plane_l3_w0_baselines.py` and
prints one canonical JSON record containing workload pins, substeps, statement
counts, rows, serialization bytes and both the output and field-content hashes.

## Transit-search kernel

Workload: deterministic 30-day Saturn search over five aspects, Swiss ephemeris,
one process/thread, with bypassed, cold-cache and warm-cache paths plus the
maintained multi-call fanout. Seven tests passed on each repeat.

The measured host resolved no file-backed ephemeris path:
`SWE_EPHE_PATH` and `SWISSEPH_EPHE_PATH` were unset and neither
`/app/ephe/sepl_18.se1` nor `/tmp/se1/sepl_18.se1` existed. Pyswisseph
2.10.03 at
`/opt/homebrew/lib/python3.14/site-packages/swisseph.cpython-314-darwin.so`
received flags 65,792 (`FLG_SIDEREAL | FLG_SPEED`) and returned flags 65,860,
including `FLG_MOSEPH` and not `FLG_SWIEPH`: these runs used the built-in
Moshier fallback, not Swiss `.se1` files. The mode was Lahiri; Rahu used
`TRUE_NODE` and Ketu was derived as Rahu + 180 degrees. Therefore there is no
ephemeris file set or file digest for this baseline. The committed harness emits
this effective context so a future file-backed run cannot be compared silently.

| run | uncached ms | cold cached ms | warm cached ms | fanout ms | process real s | max RSS bytes |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 4.65 | 2.49 | 1.88 | 40.89 | 0.25 | 48,971,776 |
| 2 | 4.12 | 2.52 | 1.92 | 44.86 | 0.26 | 49,283,072 |
| 3 | 4.56 | 2.42 | 1.79 | 43.07 | 0.26 | 49,299,456 |
| 4 | 4.72 | 2.37 | 2.00 | 45.06 | 0.26 | 49,135,616 |
| 5 | 4.30 | 2.42 | 1.98 | 44.51 | 0.25 | 48,758,784 |
| median (range) | 4.56 (4.12-4.72) | 2.42 (2.37-2.52) | 1.92 (1.79-2.00) | 44.51 (40.89-45.06) | 0.26 (0.25-0.26) | 49,135,616 (48,758,784-49,299,456) |

Every repeat produced 124 hits/31 misses cold, 279 hits/31 misses warm and
2,539 hits/177 misses in fanout (93.5%). Bypassed/cold/warm outputs were
bit-identical. Output rows/serialized bytes are not a meaningful interface for
this pure search test; the 31 misses are unique ephemeris computations, not
database rows. There is no general or production speedup claim.

## Kshetra null kernel

Workload: 45 deterministic pure tests covering 200-day and 400-day
`FieldEvaluator` inputs, replicate counts 8 and 16, and `QuantilePool` workloads
up to 100,000 values. No cache, database, SQL, network, filesystem or worker
thread participates.

| run | pytest s | process real s | user s | sys s | max RSS bytes |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.19 | 0.47 | 0.28 | 0.06 | 64,454,656 |
| 2 | 0.13 | 0.31 | 0.26 | 0.03 | 64,651,264 |
| 3 | 0.14 | 0.30 | 0.26 | 0.03 | 64,471,040 |
| 4 | 0.13 | 0.30 | 0.26 | 0.03 | 64,831,488 |
| 5 | 0.13 | 0.31 | 0.26 | 0.04 | 64,552,960 |
| median (range) | 0.13 (0.13-0.19) | 0.31 (0.30-0.47) | 0.26 (0.26-0.28) | 0.03 (0.03-0.06) | 64,552,960 (64,454,656-64,831,488) |

Rows, bytes, publication, recovery and qualified first-result latency are not
interfaces of this pure numerical suite.

## Kshetra preparation and recovery

Workload: the 27-test strict-fake planning/recovery suite at `3f109869d`. It
checks transaction-scoped chart locking, every writer-owned relation, the
`kala_insights.lel_derived=false` carve-out, zero-DML planning, fail-before-DML
preservation of populated/stale/empty-discovery output, genuinely empty
behavior, resume identity and the real substep driver/savepoint rollback shape.

| run | pytest s | process real s | user s | sys s | max RSS bytes |
|---:|---:|---:|---:|---:|---:|
| 1 | 0.59 | 0.86 | 0.45 | 0.09 | 112,443,392 |
| 2 | 0.29 | 0.48 | 0.40 | 0.06 | 112,607,232 |
| 3 | 0.27 | 0.44 | 0.38 | 0.05 | 112,410,624 |
| 4 | 0.29 | 0.47 | 0.40 | 0.05 | 112,508,928 |
| 5 | 0.28 | 0.45 | 0.39 | 0.05 | 112,312,320 |
| median (range) | 0.29 (0.27-0.59) | 0.47 (0.44-0.86) | 0.40 (0.38-0.45) | 0.05 (0.05-0.09) | 112,443,392 (112,312,320-112,607,232) |

The recovery outcome is categorical and test-asserted: a populated slice raises
`KshetraReplacementHeld` before any `DELETE`, `INSERT`, `UPDATE` or `TRUNCATE`;
the prior rows and progress remain byte-for-byte equal. This is preservation by
refusal, not backup/restore or atomic replacement. Populated replacement remains
held until immutable candidate/publication support exists.

## Kshetra publication and content hashing

The matched pytest subset covers stage 6 salience, stage 6.5 insights, stage 8
timeline publication, hash coverage and streaming content hashing. Each repeat
passed 23 tests with 39 deselected.

| run | pytest s | process real s | user s | sys s | max RSS bytes |
|---:|---:|---:|---:|---:|---:|
| 1 | 6.87 | 7.01 | 6.96 | 0.03 | 71,106,560 |
| 2 | 6.73 | 6.87 | 6.81 | 0.04 | 69,468,160 |
| 3 | 6.85 | 6.99 | 6.93 | 0.04 | 69,599,232 |
| 4 | 6.76 | 6.90 | 6.85 | 0.03 | 69,238,784 |
| 5 | 6.86 | 7.00 | 6.94 | 0.04 | 69,566,464 |
| median (range) | 6.85 (6.73-6.87) | 6.99 (6.87-7.01) | 6.93 (6.81-6.96) | 0.04 (0.03-0.04) | 69,566,464 (69,238,784-71,106,560) |

The structured harness uses the same small-build pins: one fixture chart,
400-day horizon, eight null replicates in blocks of four, 22 planned substeps,
one Python thread and fresh writer/fake state per run. Its five measured build
wall times were 0.316173, 0.315060, 0.311651, 0.310525 and 0.315712 s: median
0.315060 s, range 0.310525-0.316173 s. CPU median was 0.313901 s. Planning-only
wall median was 0.000086 s. The five CPU samples were 0.314605, 0.313901,
0.311499, 0.310422 and 0.314798 s (range 0.310422-0.314798). The five planning
samples were 0.000700, 0.000086, 0.000097, 0.000082 and 0.000080 s (range
0.000080-0.000700). The harness now also emits median/minimum/maximum summaries
for all three timing fields on every run.

Each repeat recorded 66 SELECT intents, nine DELETE intents and 83 INSERT
intents in the strict fake. It produced 61 output rows and 263,206 canonical
JSON bytes:

| relation | rows |
|---|---:|
| `kala_field` | 21 |
| `kala_field_null` | 10 |
| `kala_field_provenance` | 19 |
| `kala_field_salience` | 1 |
| `kala_field_snapshots` | 1 |
| `kala_field_windows` | 1 |
| `kala_insights` | 2 |
| `kala_timeline_spec` | 6 |

All five repeats produced canonical output SHA-256
`5c6b5993e07aa23546df89973a52ed3add3d4386f10bb0574ba3b3cc56b8c7cb`
and field content hash `kfh_8fa468f994b8381135b667e4e97f6dce`.
`/usr/bin/time` over all five harness repeats reported 1.73 s real, 1.67 s user,
0.02 s system and 53,821,440 bytes maximum RSS. Canonical JSON bytes are a
reproducible serialization comparator, not PostgreSQL storage size.

## Interpretation gate

The baseline is accepted only if independent review can rerun the exact commands
and reconcile the raw observations above. Any future comparison must preserve
the workload, cache and thread state or disclose the difference. PostgreSQL
rows/storage/WAL, full-chart duration, crash restoration, deployed consumer
latency and qualified first-result latency remain future packet measurements.
