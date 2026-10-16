# A4 D-31 — DB check sharding

The existing job IDs remain the execution jobs. Their matrices contain shard indices;
`required-<job-id>` jobs retain the exact original check names and accept only a
`success` matrix result. Worker names start with the shard index so GitHub
shortening long names keeps every shard distinct. Umbrellas run with `always()`, so failed, cancelled and skipped
matrices produce a failing umbrella. The regression test executes each umbrella's
actual shell with all four outcomes.

Each worker retains its original PostgreSQL service, provisioning, test environments,
command flags and immediate source-bound generated-output restore. The 1206 mutation
harness runs once, on SAMĪKṢĀ shard 4. File execution remains serial wherever the old
job required it. Existing required-DB and required-ephemeris flags are retained.

Assignment uses the full job's discovered file list and timing weights, placing
the heaviest file on the lightest shard, with path/index tie-breaks. New files join
automatically. Empty whole-job shards fail; a profile with no files on one shard
returns without launching an unfiltered test runner. See `ci_db_shard.py:37` and
`ci_discovery.py:140`. Vitest also excludes files assigned elsewhere because its
positional filename filters use substring matching (`ci_discovery.py:152`).

- **(I) INTERPRETATION:** a deterministic file-list matrix is represented by an index
  matrix plus runtime discovery, rather than a literal file allowlist rejected by
  #3588's guard. `ci_db_shard_coverage.json` records the resulting file lists.
- **(I) INTERPRETATION:** these workers also run on docs-only changes. This makes the
  requested rule that *any skipped shard fails* unconditional; a docs-only exception
  would weaken that rule (`.github/workflows/ci.yml:473`, `:1355`).
- **(I) INTERPRETATION:** unmeasured/new files receive a one-second scheduling weight
  until measured. That estimate affects assignment only (`ci_db_shard.py:25`).

The single-file jobs `gochara-a55-slice-transitions` and
`gochara-a55-teardown-round2` retain their commands and names. File sharding cannot
reduce their individual runtime. C37 dispatch and measuring-build also remain
unchanged because they are outside the slow C38/A5.5f selection.

The Kāla DB step now uses its existing `kala-db-tests-5-0` discovery profile. The
parent branch had an inline glob command while its pinned #3588 test required the
profile invocation. The node-ID comparison also covers this selector correction.

Reproduce collection equality against the pre-sharding source revision (install the
sidecar CI Python dependencies and platform npm dependencies first):

```sh
PYTHONDONTWRITEBYTECODE=1 python -B platform/scripts/governance/compare_ci_db_shards.py \
  --baseline e45f1ef5b \
  --scratch "$JOB_SCRATCH/coverage-recheck" \
  --ephe-path /Users/Dev/kalayantra/ephe
```

The tool uses `pytest --collect-only` and `vitest list --json --no-cache`, retains
selection flags and fixture environments, and maps DSNs to the guarded local
cluster at `127.0.0.1:55433`. It compares **multisets**, so duplicate execution is
also a failure. The committed comparison contains the original node IDs, before/
after counts and SHA-256 digests, per-shard files/counts/digests, and missing/extra
nodes. Raw collection output stays under its scratch directory. Collection is
coverage evidence; it does not claim that DB test execution passed.

Timing data and collection evidence are deliberately outside machine-owned output
paths. No generated-output guard or required-name baseline is rewritten.

The timing table binds the recent green main run
[38885741560](https://github.com/Marsys-Technologies/Madhav/actions/runs/38885741560)
and local per-file measurements. **(I) INTERPRETATION:** where the CI `-q` log
records only a whole pytest batch duration, its remaining duration is divided
equally among original files without local measurements. Each such weight is
labelled as an estimate in `file_seconds_basis`; it is not a per-file observation.
New files outside recorded batches retain the one-second fallback.

SAMĪKṢĀ shard 4 alone runs the mutation harness. The balancer reserves the entire
recorded 214-second F-1 step on that shard before assigning files, conservatively
including that step's ordinary Vitest invocation. Reported test-work estimates
exclude service provisioning, dependency installation and generated-output restore.
The full elapsed-time target must be checked on the resulting CI run.

The local replace-chain measurement completed with 51 passed and 8 xfailed.
`test_a55_replace_chain.py` dominates its runtime (about 26 minutes on the loaded
local machine); the other four files took seconds. The job's whole-file split
cannot shorten that dominant file. This is an additional remaining file bottleneck,
alongside the two explicitly single-file jobs above.

The unregenerated local A5.3 baseline produced 2,053 passed, 67 failed, 16 skipped
and 1 deselected; the failures trace to its stale implementation-digest lock. The
existing CI compiler regenerates and verifies that lock (`ci_generated.py:100`).
The canonical generated output was left untouched; independently generating the
lock under the job scratch directory verified the current source digest.
