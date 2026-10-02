# GATE_V2: binding pre-run gate for every executor / dispatch

Version string: `GATE_VERSION = "GATE_V2"` (constant in `prerun_gate.py`). Replaces the v1 gate that lives in the orphan-receipts executor folder.
Stdlib only, read-only, fails closed. Used BYTE-IDENTICALLY by the orphan-receipt executor, the D6 index executor, F-A2, the step-2 D6 plan
and the level-wave wrapper. **The three files below are what SS binds; the sha256 column is checked by a test (`test_readme_documents_the_current_sha256_of_every_bound_file`).**

| file | role | sha256 |
|---|---|---|
| `prerun_gate.py` | the gate | `01ab1d70d0cffea015a64af5430f355dd8d419307aceeaeacf3a0cc4d715773e` |
| `run_gated.sh` | the launcher (gate, then exec target) | `305b4406bba57f85944bbb57cb269368287aaa6d6f782e986afa7f857606f076` |
| `executor_standards.py` | launch-marker verification + outcome file (import or copy byte-identically) | `bbea69552a6a92e7aed3a75758b533868e3e3d2c5b47385ccc1bf6c0660dc135` |

## What the gate guarantees

In ONE invocation it reads and prints (to **stderr**; stdout is always empty):

1. `deploy_runs_not_completed`: runs of workflow `deploy.yml` on ANY ref (deploy.yml accepts `workflow_dispatch` from any ref, so a dispatched deploy on a
   feature ref must be seen) with status != `completed`, EXCEPT runs whose `event` is exactly `pull_request` (build-only runs). An unknown, missing or any other event is counted
   (fail closed). Over the union by `databaseId` of
   `gh run list -R Marsys-Technologies/Madhav --workflow deploy.yml --limit 1000 --json databaseId,status,event` and one query per non-completed status
   (`--status queued|in_progress|waiting|pending|requested`, each `--limit 1000`; gh pages internally and a page that fails midway gives a non-zero exit, which fails closed; GitHub caps a filtered query at 1000). A stuck run older than the newest 10000 is still found by its status query.
   A per-status query that returns a FULL `--limit` page (1000) containing `pull_request` runs fails closed (exit 2, `full page`): a non-PR run could be hidden behind them (see "Operator remedy for the full-page backstop" below).
   The repository is pinned (`-R Marsys-Technologies/Madhav`, a named constant `REPO`) and `GH_REPO`, `GH_HOST`, `GH_ENTERPRISE_TOKEN`, `GITHUB_ENTERPRISE_TOKEN`,
   `GITHUB_REPOSITORY`, `GH_CONFIG_DIR`, `GH_PATH` are removed from gh's environment (the token variables gh needs are kept).
2. `build_runs_in_flight`: `build_runs` in state `planned/running/paused` on ANY chart, via `psql -X -A -t -F '|'` as `suvarna_reader`, reading
   `SELECT current_user, current_database(), count(*) FROM public.build_runs WHERE state IN ('planned','running','paused')` in the SAME psql call.
   The subshell must `source ~/.config/suvarna/pgenv.sh` successfully; every ambient `PG*` variable (and `BASH_ENV`/`ENV`/exported functions) is removed
   from the subshell first, so nothing but the sourced file can supply the connection. The role must be exactly `suvarna_reader` and the database exactly `amjis`.

It exits 0 only when both counts are 0 and the role is right, and prints one final line a log reader can grep:

```
GATE_V2 deploy_runs_not_completed=0 build_runs_in_flight=0 role=suvarna_reader OK
GATE_V2 FAIL <reason>                                    (any other outcome)
```

Fail closed on: empty output, non-JSON, JSON that is not a list, entries without an integer `databaseId` / non-empty `status`, an EMPTY `--limit 1000`
history list (a repo with history never returns zero runs; an empty per-status list is fine and means zero), a 60 s timeout per command (process group killed),
a missing binary (gh, psql, bash), a non-zero exit, output that is not valid UTF-8, JSON nested so deep that parsing recurses out, a malformed/empty/multi-line psql answer
(the count must be 1 to 12 ASCII decimal digits), a missing or failing `pgenv.sh`, and a wrong role or database. An unexpected internal error is also a classified failure:
`GATE_V2 FAIL internal_error <ExceptionClassName>` (exit 2, class name only). **Every exit path prints exactly one final `GATE_V2` line.**
It never prints a credential, a child process's output, or row content (the role name is printed only when it is the wrong one, and only the name).

### Exit codes

| code | meaning |
|---|---|
| 0 | both counts read and both 0, role `suvarna_reader` |
| 1 | at least one count is > 0 |
| 2 | a read failed or its output was malformed / empty / not UTF-8 / timed out / non-zero exit, or an internal error |
| 64 | `run_gated.sh` usage error (no target) |
| 93 | `require_gate_launch` refusal (executor not launched by `run_gated.sh`) |
| 94 | a required binary (gh, psql, bash, python3) is missing (final line label `missing_binary`) |
| 95 | a test-only variable is set outside the harness (`ORPH_TEST_EVIDENCE_ROOT`, `PYTEST_CURRENT_TEST`) |
| 96 | the psql session is not `suvarna_reader`, or not connected to database `amjis` (label `wrong_role_or_database`; message names the unexpected value only) |
| 97 | `source ~/.config/suvarna/pgenv.sh` failed (missing file or non-zero status; label `pgenv_failed`) |
| 128+n | the gate was terminated by signal n (SIGTERM 143, SIGHUP 129, SIGQUIT 131): `GATE_V2 FAIL signal <n>`; the gh / psql child is killed, a second signal is ignored while cleaning up, and a signal already ignored at start (nohup's SIGHUP) stays ignored |
| 98 | `run_gated.sh`: the target is missing / not an executable file / not found in PATH (checked before the gate runs), or the final exec failed: `GATE_V2 FAIL target_not_executable` |

When several reads fail the most specific code is returned (97, 96, 94, then 2). `run_gated.sh` returns the gate's own exit code.

## How executors must call it

Never start the executor directly. Always:

```bash
./run_gated.sh <executor> <executor args...>            # e.g. ./run_gated.sh python3 orphan_receipts_exec.py --asset ... --dry-run
```

`run_gated.sh`: `set -euo pipefail`; refuses the test env (exit 95); resolves python3, gh, psql, bash ONCE by absolute path (`command -v`) and prints them
(`run_gated: python3=... gh=... psql=... bash=...`); runs the gate with those paths (its stdout is forced to stderr, so the executor's stdout JSON stays clean);
before the gate it checks that the target is an executable file (or a name found in PATH) and refuses with exit 98 otherwise (no OK / launch line is printed for a doomed launch);
only on gate exit 0 sets `GATE_V2_LAUNCH` and does `exec -- "$@"` (arguments pass through intact, no word splitting; `--` so a dash-named target is never read as an exec option; tested on macOS bash 3.2). On any failure the target is NOT started and
`run_gated: gate exit=<n>; target NOT started` is printed.

### Test-only switches (`GATE_V2_UNDER_TEST=1`)

The gate is run by operators, not by pytest. It refuses (exit 95) when `ORPH_TEST_EVIDENCE_ROOT` is set (even empty) or `PYTEST_CURRENT_TEST` is set.
Tests set `GATE_V2_UNDER_TEST=1`, which bypasses ONLY that refusal and enables `GATE_V2_PGENV` (a fake pgenv file) and `GATE_V2_TIMEOUT_S` (shorter timeout, never longer than 60).
Without it neither override is read: the production pgenv path is always the real `~/.config/suvarna/pgenv.sh`. When the flag is set the gate logs
`GATE_V2 WARNING under_test=1` so a log reader can see that a run was not a production run. The role check, the counts and everything else are never bypassed.
`GATE_V2_GH` / `GATE_V2_PSQL` / `GATE_V2_BASH` carry the absolute binary paths run_gated.sh resolved (a nonexistent override fails closed, no fallback).

## Operator remedy for the full-page backstop

`GATE_V2 FAIL read_failed (fail closed): gh --status <s> returned a full page of 1000 runs including pull_request runs: a non-PR run may be hidden` (exit 2) means a single
status (normally `queued`) has at least 1000 deploy.yml runs, some of them build-only `pull_request` runs, so the gate cannot prove that no deploy run is hidden among them.
It is a refusal, never a bypass:
1. check how many runs are in that status: `gh run list -R Marsys-Technologies/Madhav --workflow deploy.yml --status queued --limit 1000 --json databaseId,status,event,headBranch | jq 'group_by(.event) | map({event: .[0].event, n: length})'`;
2. cancel the stuck `pull_request` runs (`gh run cancel <id>`) or wait for them to drain, then run the gate again;
3. if it persists, ask Strategic Suvarna / the repository owner. **Bypassing the gate (editing it, setting `GATE_V2_UNDER_TEST`, running the executor directly) is never acceptable.**

## Executor standards (inherited by every executor)

Implemented once in `executor_standards.py` (stdlib; import it, or copy it byte-identically next to the executor; tests in `tests/test_gate_v2_standards.py`).

1. **Gate shas are part of the plan hash, and the executor refuses unless launched by `run_gated.sh`.**
   - `fp = fingerprint()` returns the sha256 of the live `prerun_gate.py` and `run_gated.sh`; `bind_gate_into_plan_hash(plan_hash, fp)` folds both into the plan hash, so editing either gate file changes the plan the operator approved.
   - After a passing gate `run_gated.sh` sets the environment variable **`GATE_V2_LAUNCH`** (and only it, only then):
     `v2.<gate_sha256>.<run_gated_sha256>.<epoch_seconds>.<nonce_hex32>.<under_test 0|1>.<check>` with
     `check = sha256("GATE_V2_LAUNCH|v2|<gate_sha256>|<run_gated_sha256>|<epoch_seconds>|<nonce>|<under_test>")`; `epoch_seconds` is at most 12 ASCII digits.
     `under_test` is `1` only when `run_gated.sh` ran with `GATE_V2_UNDER_TEST=1`; it is part of the check input (a production marker cannot be replayed as an under-test one or the reverse) and a
     verifier refuses an under-test marker (`under_test_marker_refused_outside_tests`, exit 93) unless it is itself under test (`GATE_V2_UNDER_TEST=1` or `PYTEST_CURRENT_TEST` in its environment).
   - The executor calls `require_gate_launch(expected_gate_sha=..., expected_launcher_sha=...)` FIRST. It exits **93** unless the marker exists and parses, its `check` recomputes,
     its two shas equal the sha256 of the live files next to `executor_standards.py` (and the shas pinned in the plan), it is not more than 120 s in the future and not older than 6 hours.
     The refusal message names a class (`no_marker`, `marker_check_mismatch`, `gate_sha_differs_from_live_gate_file`, `marker_stale`, ...) and never echoes the marker.
   - **Limit: this is a convention-grade guard against accidents in a single-operator setting (running the executor directly, running a stale or edited gate). It is not a security boundary:** anyone who can run python can forge a marker.
2. **Every executor writes an outcome file in every mode, also on failure.** `outcome_guard(evidence_dir, executor_path, plan_hash, gate_fp)` is a context manager; inside it call
   `o.dry_run(evidence_digest)` / `o.applied(evidence_digest)` / `o.fail([check names])`. Whatever else happens (a refusal, an exception, a `SystemExit`, a block that returns without declaring an outcome)
   `<evidence_dir>/outcome.json` is written with status `failed` and the reason as check name. The file (atomic write, `0600`; evidence directory forced `0700`) holds exactly:
   `schema` (`executor_outcome_v1`), `status` (`dry_run` | `applied` | `failed` | `commit_state_unknown`), `utc`, `executor_sha256`, `plan_hash`, `gate_sha256`, `run_gated_sha256`, `evidence_digest` (hex or null), `failed_checks` (names; non-empty only for `failed`),
   `under_test` (bool, from the launch marker: pass the dict `require_gate_launch` returns as `gate_fp`) and `warnings` (list of `<warning>:<ExceptionClassName>` strings; empty normally).
   A lost stdout therefore never hides what happened. `commit_state_unknown` is for an executor whose COMMIT call itself raised (e.g. the connection dropped at the acknowledgement): the server may have committed, so check the database before anything else. **A MISSING `outcome.json` means "nothing was recorded, check the database"** (SIGKILL, power loss, a crash right after COMMIT can leave none); it never means "nothing happened".

Minimal executor skeleton:

```python
import executor_standards as es
fp = es.require_gate_launch(expected_gate_sha=PLAN["gate_sha256"], expected_launcher_sha=PLAN["run_gated_sha256"])   # exit 93 if not launched by run_gated.sh
with es.outcome_guard(evidence_dir, __file__, plan_hash, fp) as o:
    ...                                     # raise / sys.exit(n) / o.fail(["P5_no_build_in_flight"]) -> outcome.json status failed
    o.dry_run(evidence_digest)              # or o.applied(evidence_digest)
```

## What it does NOT guarantee

- It is a point-in-time read: a deploy or build can start one second after the gate passes. It narrows the race, it does not close it (the executors keep their own in-transaction checks).
- `gh` and the database are trusted to report truthfully; a `--limit 1000` history is checked for emptiness, not for completeness (the per-status queries are what cover old stuck runs; a status outside the five listed and not `completed` would be seen only if it is in the newest 1000).
- It cannot stop an operator from skipping `run_gated.sh`; the launch marker is an accident guard, not authentication. An operator with a shell can set `GATE_V2_UNDER_TEST=1` (it is logged, never silent).
- `build_runs_in_flight` is exactly the three states `planned/running/paused`; a new state added to the schema is not seen until the gate is versioned.
- Sourcing `pgenv.sh` executes it as shell: it is trusted operator-owned configuration (never printed, never committed).

## Tests

The pytest files live in `platform/scripts/governance/__tests__/` (`gate_v2_helpers.py`, `test_gate_v2_prerun_gate.py`, `test_gate_v2_run_gated.py`, `test_gate_v2_executor_standards.py`),
so the existing CI step "Governance Tool Tests (pytest)" (`python -m pytest platform/scripts/governance/__tests__`) runs them with no workflow change. They execute the gate files
from this folder by repo-relative path (single source of truth). They use no network, no database, no credential and no macOS-only command or homebrew path: PATH shims for gh and psql
and python3/bash symlinks are written to a temp dir at test time; `/bin/bash` and python3 only.

```bash
python3 -m pytest platform/scripts/governance/__tests__/test_gate_v2_*.py -q
python3 00_ARCHITECTURE/briefs/suvarna/exec/gate_v2/tests/mutation_proof.py   # script (not collected by CI): neuters each rule in a copy and shows its tests go red (51 mutations: the 19 original, one per revision-2 fix and one per revision-3 fix)
```
