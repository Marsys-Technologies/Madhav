# A4 D-31 — DB check sharding

The existing job IDs remain the execution jobs. Their matrices contain shard indices;
`required-<job-id>` jobs retain the exact original check names and accept only a
`success` matrix result. Worker names start with the shard index so GitHub
shortening long names keeps every shard distinct. Umbrellas run when main's D-29 selection requires their job (full events, or a PR that selects it), so once an
umbrella runs, failed, cancelled and skipped matrices produce a failing umbrella; an unselected PR job and its umbrella are
skipped together. The regression test executes each umbrella's
actual shell with all four outcomes.

Each worker retains its original PostgreSQL service, provisioning, test environments,
command flags and immediate source-bound generated-output restore. The 1206 mutation
harness runs once, on SAMĪKṢĀ shard 4. File execution remains serial wherever the old
job required it. Existing required-DB and required-ephemeris flags are retained.

Most jobs use the full job's discovered file list and timing weights, placing
the heaviest file on the lightest shard, with path/index tie-breaks. New files join
automatically. Empty whole-job shards fail; a profile with no files on one shard
returns without launching an unfiltered test runner. See `ci_db_shard.py:37` and
`ci_discovery.py:140`. Vitest also excludes files assigned elsewhere because its
positional filename filters use substring matching (`ci_discovery.py:152`).

- **(I) INTERPRETATION:** a deterministic file-list matrix is represented by an index
  matrix plus runtime discovery, rather than a literal file allowlist rejected by
  #3588's guard. `ci_db_shard_coverage.json` records the resulting file lists.
- **(I) INTERPRETATION:** the shard jobs and their `required-*` umbrellas use main's D-29 selection
  (`ci_gate.select_db` -> `needs.changes.outputs.db_jobs`) instead of running on every PR. Whenever a job is selected
  (or on a full event) every shard must run and succeed: a skipped shard fails its umbrella, with no docs-only exception.
  An unselected PR job is skipped whole, as it was on main, and its umbrella is skipped with it. Alternative: always run
  the shards on PRs (rejected: it reverses D-29's CI demand halving). The `full-suite` aggregate lists the umbrellas
  and `replace-chain-substrate`, whose selection comes from `ci_gate.select_db`'s needs closure.
- **(I) INTERPRETATION:** unmeasured/new files receive a one-second scheduling weight
  until measured. That estimate affects assignment only (`ci_db_shard.py:25`).

The single-file jobs `gochara-a55-slice-transitions` and
`gochara-a55-teardown-round2` retain their commands and names. File sharding cannot
reduce their individual runtime. C37 dispatch and measuring-build also remain
unchanged because they are outside the slow C38/A5.5f selection.

The Kāla DB step now uses its existing `kala-db-tests-5-0` discovery profile. The
parent branch had an inline glob command while its pinned #3588 test required the
profile invocation. The node-ID comparison also covers this selector correction.

Reproduce collection equality against main at the #3588 merge (install the
sidecar CI Python dependencies and platform npm dependencies first):

```sh
PYTHONDONTWRITEBYTECODE=1 python -B platform/scripts/governance/compare_ci_db_shards.py \
  --baseline cc9f509b480461880be80b225ff44b084995b3d7 \
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

The #3588 refresh preserves every incoming discovery profile and the required
readback case-count/skip checks. The named `db-integration-tests-smalltest` profile
declares `shard_job: db-integration-tests`, so its two fleet suites join the same
whole-job partition as the numeric profiles. The numeric boundary still prevents
teardown from claiming teardown-round2/round3. The regression compares every
worker's actual workflow selectors with its partition owners and checks that each
small-test file runs exactly once across the four workers.

The current-main merge retains all 96 incoming profiles, including the narrowed
`37-2` builder-role family, the narrowed readback profile, both named readback
profiles and the tracker step-receipt selection. `unit-tests` still depends on
both `changes` and `generated-artifacts`; the AM-5 static test still asserts the
`8-0` discovery invocation. All 33 pinned check names, including the required
contexts, retain their names and remain unique.

- **(I) INTERPRETATION:** the supplied three-way resolver's union restored the
  superseded broad `ga_writers/__tests__/test_l1*.py` glob in `37-2`. Main's explicit
  narrowing takes precedence for this one family; all other resolver output is
  retained. The alternative union would select the unrelated data-plane suite
  and break current-main node parity. The discovery regression tests both that
  exclusion and automatic inclusion of a future `test_l1_min_fixes*.py` case.

- **(I) INTERPRETATION:** named profiles use explicit `shard_job` ownership; the
  alternative of accepting every nonnumeric suffix by prefix could also claim
  the distinct teardown-round2/round3 jobs.

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

Replace-chain uses four **node** workers instead of an indivisible file split.
`ci_discovery.py` still discovers every file in the profile; it explicitly loads
`ci_db_node_shard.py`, which partitions the actual collected pytest node IDs before
fixtures run. Timing keys only select placement: new files, functions and parameter
cases join automatically. Pytest's original ordering, scopes, `-k` and `--deselect`
policy are retained. An empty worker is a collection error. Every worker remains
an independent pytest process with its own guarded fixture databases.

The slow module fixture used to build the complete 1998–2085 sky-event substrate
serially before its first scenario. Eight `replace-chain-substrate` workers now
run the original writer's convention/body substeps, one real body each, over that
same full domain and checksum-pinned Swiss corpus. They export the physical-object
and sky-event tables through PostgreSQL COPY. The test fixture registers its own
convention, then restores all eight parts before cloning per-test worlds. It still
runs the original production manifest/snapshot/inventory/coverage/record substeps.
No computation, body, domain, node ID, or assertion is removed.

Artifacts bind the source digest (sidecar Python, migrations and the preparation
helper), ephemeris checksums, body set, table row counts and COPY file checksums.
Verification precedes the restore transaction; missing, duplicate, stale or corrupt
parts fail. There is no artifact-path fallback to a long serial rebuild. The exact
original umbrella requires **both** preparation and test matrices to succeed;
its shell is tested against every pair of success/failure/skip/cancel/empty results.
Restore runs inside the writer convention substep's chart-locked transaction, so
COPY observes the same chart-before-substrate lock discipline as ordinary inserts.

Within the heavy module's node workers, the pytest plugin also memoizes the actual
`production_arc_index(body, ephe_path)` result. The corpus is checksum-pinned and
read-only for the fixture lifetime; each caller receives a deep copy, and fixture
teardown restores the original function. The index is still computed over the
complete 1998–2085 domain by the original sampler/solver. All direct Swiss probes
and their backend checks remain active. Cache hit/miss counts are printed at the
end of each worker; the regression checks factory reuse and mutation isolation.

- **(I) INTERPRETATION:** use collected node IDs as the independent test units rather
  than physically moving functions, preserving the exact pre-sharding IDs.
- **(I) INTERPRETATION:** preparing each body's real immutable substrate separately
  is part of sharding the original fixture, rather than exempting fixture work from
  the runtime target. Ordinary local runs keep their original serial fixture.
- **(I) INTERPRETATION:** memoize real full-domain indexes within each module worker,
  rather than resampling the same immutable pinned corpus in every record phase.
  Deep copies retain independent caller state; no numerical value is substituted.
- **(I) INTERPRETATION:** initial node weights apportion the original observed file
  work across its collected cases. These remain estimates, not invented per-case
  observations. The old expensive substrate cost stays in those estimates
  conservatively; measured preparation and node-worker durations are recorded too.

The original 26.171-minute file observation remains in `file_seconds` as historical
evidence. It must not be counted as a single scheduling unit for this job. Node
weights and repeated fixture work are recorded separately; full hosted elapsed
time remains a CI follow-up, including provisioning and dependency installation.

Recheck only the changed job while preserving the existing same-baseline rows:

```sh
PYTHONDONTWRITEBYTECODE=1 python -B platform/scripts/governance/compare_ci_db_shards.py \
  --baseline cc9f509b480461880be80b225ff44b084995b3d7 --job gochara-a55-replace-chain \
  --scratch "$JOB_SCRATCH/coverage-recheck" --ephe-path /Users/Dev/kalayantra/ephe
```

This invokes the production collection plugin, rather than treating its input file
list as proof of which nodes a worker runs. The job retains all 59 original IDs,
including parametrized cases and historical expected failures.

The unregenerated local A5.3 baseline produced 2,053 passed, 67 failed, 16 skipped
and 1 deselected; the failures trace to its stale implementation-digest lock. The
existing CI compiler regenerates and verifies that lock (`ci_generated.py:100`).
The canonical generated output was left untouched; independently generating the
lock under the job scratch directory verified the current source digest.

R1 verification on the corrected tree: all eight real preparation units completed
in 0.27–7.80 minutes. The four full node-worker invocations took
6.09, 7.71, 10.27, 7.38 minutes (51 passed, 8 historical xfailed; all 59 IDs executed once).
All four restored fixtures matched the original serial fixture's 2,146 physical
objects and 50,124 sky events, comparing every field except `created_at`.
The timing JSON binds the manifests, raw worker reports and executing source files
by SHA-256. Updated scheduling estimates, including the measured repeated template
setup reserve, are 7.35, 6.49, 6.47, 6.47 minutes. These are local test-work results;
N1's full hosted elapsed-time follow-up remains outstanding.

(I) INTERPRETATION: the approximately ten-minute criterion uses strict 600-second
estimate/preparation budgets and a 5% (630-second) allowance for instrumented
parallel worker wall time on the shared local host. One worker measured 616.20
seconds, so a strict 600-second wall limit was NOT met. Hosted elapsed time is
unmeasured; this tolerance does not claim a hosted CI result.
