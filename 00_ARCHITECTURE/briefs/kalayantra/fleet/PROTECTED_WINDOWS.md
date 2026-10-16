---
artifact: PROTECTED_WINDOWS
version: "1.0"
status: CURRENT
produced_on: 2026-10-16
changelog:
  - "1.0: SR-A6-GCW generalized watcher and prospective required merge admission."
---

# Protected migration windows (SR-A6-GCW)

The 1235 incident exposed two gaps: the old external watcher watched only Kāla and treated its own last successful run as proof of applied SQL; admission did not require a protected migration to carry a scheduling commitment. The replacement sources are `protected_window_dispatch.py` and `protected_windows.py` in this directory. Installing or enabling them remains a cockpit operation; this job does not modify the external watcher or launch a service.

## Sources and boundary

The catalog reads the immutable `origin/main` commit's `.github/workflows/deploy.yml`: inputs at lines 49–78, their environment bindings at lines 1064–1069, and the actual selection blocks at lines 1073–1147. It derives all six schema windows, including Kāla's referenced list, without a second membership table. A future static schema window is discovered automatically; an unknown selection form, duplicate membership or missing SQL file fails closed. Historical filenames with a numeric suffix (for example `346a_…`) retain leading-number ordering.

(I) INTERPRETATION: “every protected set” here means every explicit `*_schema_migration` window. `data_plane_cutover` (deploy.yml line 44) authorizes a broader bootstrap/cutover operation, including ownership and data-plane effects; it remains under its existing executor authority. Alternative: treat that broad cutover as another automatic schema window. This watcher never sets it.

The unchanged predecessor check is `platform/scripts/migrate.ts:841–856`. The watcher checks the same numeric ceiling against a fresh applied-filename readback and reports `waiting_predecessors` with the missing routine files. It does not waive prerequisites or try an unscheduled routine migration. If an earlier protected prerequisite and a later routine prerequisite form a deployment deadlock, the cockpit must arrange the existing protected/ordinary windows; this watcher does not manufacture a new execution path.

## Scheduling in a PR

Append one record per added protected migration to `protected_window_schedule.json`, in the same PR as the SQL and classification. The form is exactly:

```json
{"migration":"1235_ka_gochara_staged_candidate_evidence_function.sql","window_input":"gochara_contracts_schema_migration","lease":"SR-A6-GCW-WINDOW"}
```

This is an illustrative historical filename, not a new authority or a record added by this change. Use the actual migration, its actual catalog input, and the actual planned coordination lease. New SQL classified only in the runner but absent from deploy's windows is refused. Newly classifying existing SQL also needs a new record. Wrong inputs, duplicate records, placeholder leases, pre-existing records reused for new additions, and removal or alteration of commitments fail admission. Records are prospective; historical main migrations are not fabricated into a backfill.

The required existing Governance Gates static job calls `protected_windows.py guard` (`.github/workflows/ci.yml:2523`). PRs use `pull_request.base.sha`, queue runs use `merge_group.base_sha`, and main pushes use `before`; unavailable or invalid event evidence fails closed. Local review supports `guard --base <commit>`. Existing governance pytest discovery and `ci_shard.py` discover `test_protected_windows.py`; this source tree has neither `ci_test_suites.json` nor `ci_discovery.py`, so no new test allowlist or explicit test filename was added to CI.

## Invoking a tick

Requires Python 3.11+, PyYAML, GitHub CLI and a psql-compatible readback executable. The readback executable receives `--command` with this read-only SQL:

```sql
SELECT COALESCE(json_agg(filename ORDER BY filename), '[]'::json)
FROM public._migrations_applied;
```

It must return a JSON array of the database's actual applied filenames. The default executable is `psql`, with `--no-psqlrc`, `ON_ERROR_STOP=1`, and no connection string printed or persisted. Connection configuration and authorization belong to the invoking operator; never substitute the old `KALA_WINDOW_STATE.json`, a workflow conclusion, or a hand-curated applied list. Tests use a separate fake executable and never connect to a remote database.

For the cockpit's reviewed deployment, invoke one foreground tick using its approved repo, persistent state path and active lease:

```sh
python3 -B 00_ARCHITECTURE/briefs/kalayantra/fleet/protected_window_dispatch.py \
  --repo "$WINDOW_REPO" --state "$WINDOW_STATE" --lease-id "$WINDOW_LEASE" --dry-run
```

The same command without `--dry-run` enables dispatch. Dry run performs source/SQL/CI/lease checks and prints the plan; it writes neither dispatch state nor a lock and calls no workflow mutation. The caller must refresh both origin/main and origin/campaign-coordination before each tick. The watcher itself performs only read-only Git operations. State must be shared by all invocations for this repository/database target and retained across restarts. The old watcher must be retired before this source is enabled; running both cannot provide one-dispatch admission.

(I) INTERPRETATION: “under a lease row” requires the specified lease to be the sole unexpired ACTIVE row of section 1 in `CAMPAIGN_COORDINATION.md` on origin/campaign-coordination, using the same IST expiry semantics as `executor.py:220–239`. Alternative: have the watcher claim or edit coordination authority. It does neither. Scheduled pending files must name that same lease. Admission checks the planned lease's form; execution checks its current authority. Expired authority must be renewed by the existing coordination process.

## Selection, durable intent and recovery

(I) INTERPRETATION: “one dispatch per head” means one batch containing all pending schema-window inputs, ordered by each set's lowest pending migration. Alternative: one separate dispatch per set/head. Batching handles overlapping protected ranges in the existing `--only` rule while preserving one external dispatch per green head. All selected sets' routine predecessors still have to be applied.

Only the latest CI push run for the exact origin/main SHA and main branch, completed successfully, authorizes a dispatch. The remote main ref is rechecked before mutation. GitHub workflow dispatch requires a branch/tag, so the command uses `--ref main`; the observed workflow run must match the reserved SHA. Main movement during the remaining API race can prevent run correlation; it is never accepted as the intended run.

A sibling `flock` serializes foreground ticks. The watcher fsyncs a per-head intent containing the lease, ordered inputs, pending filenames, before readback and prior run IDs before calling `gh workflow run`. It identifies a unique new dispatch run for that head, records the run ID, resumes it on later ticks (including after main advances), and reads `_migrations_applied` again after completion. A success conclusion with missing SQL fails verification. A failed workflow with missing SQL retains its readback and never automatically redispatches the head. A later green head may make a new attempt using a fresh SQL readback; the failed head's receipt stays intact. (I) INTERPRETATION: if all intended SQL is present, migration verification succeeds even when a later workflow step failed; the receipt/output preserves that failed workflow conclusion and does not claim a successful deployment. Alternative: require overall workflow success and stall later heads despite complete migration readback.

`awaiting_run_identity` means zero or multiple new matching runs were observed. This can follow API visibility delay, an interrupted client, a crash before the call, a competing manual dispatch, or a head race. A later tick retries observation only. The existing workflow supplies no caller correlation token, so ambiguous identity cannot safely be resolved automatically. The cockpit must inspect the reserved head, intended inputs, run(s), lease and SQL truth before repairing that record; never delete state merely to force a retry. Protected-environment approval remains GitHub's existing gate.

## Verification

The governance tests execute the real catalog and required CI command with fake read-only Git, fake gh and fake SQL readback. They cover all existing sets, future static sets, all-applied/red-head cases, numeric batch ordering, dry run, leases, head races, routine predecessors, API-response loss, restart recovery, false workflow success, prospective schedules, and queue base evidence. Job-local affected-tree copies retain the fail-on-revert evidence. No migration, generated output, frozen orchestrator code, deploy window body, production connection or real dispatch is part of this change.
