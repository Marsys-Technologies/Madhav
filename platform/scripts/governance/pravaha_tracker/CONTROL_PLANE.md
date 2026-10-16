status: READY_FOR_ACCEPTANCE

# KĀLA-YANTRA control plane

This package keeps the existing Pravāha behavior when a plan model has no
`control_plane` declaration. The KĀLA-YANTRA model enables the additions below;
the running tracker uses a separate installed snapshot and changes only at B-2.

## State and commands

- `claim <ID> --worker <lane> --lease <seconds>` locks and rereads the event log,
  grants one eligible worker a claim id, and writes `run/claims/<lane>.json`.
  `renew` and `release` use that identity. An expired claim hands its recorded
  branch, head and step to the next worker.
- `verdict <ID> --head <sha> --result ACCEPTED|REJECTED --detail ...` records an
  independent review. Artifact verdicts use `--artifact-digest` and
  `--phase artifact`; a changed head or later rejection invalidates acceptance.
- `done <ID>` checks eligible dependencies, every declared step, the live
  detector and typed evidence. Code needs the registered PR at the reviewed
  head, its squash merge commit and a post-deploy verdict. Artifact, operation
  and packet completions bind their digests, receipts and independent verdicts.
  A completed event remains durable when a detector later flaps; audit reports
  the discrepancy. S completes independently accepted N- and V-owned items.
- `step <ID> <step> --evidence <path>` still requires the step's own live
  detector to pass. For `file_contains` step receipts, the resolved evidence
  path must equal the detector path. The receipt must be a JSON object encoded
  with sorted keys and compact separators (one optional trailing newline),
  with `item` and `step` matching the command. A named `review_job` must resolve
  inside `PRAVAHA_REVIEW_JOBS` (default
  `/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs`)
  to an existing `result.json` for that item, with exactly one matching step
  whose verdict is `MET`. Alternatively, a receipt's `artifact_sha256` may
  prove the named `artifact_path`; relative artifact paths resolve beside the
  receipt. A supplied artifact digest must always match, and a named review
  result must still exist. Other step detector types keep their prior behavior.
- `decide --outcome approved|refused|deferred|insufficient_evidence` records a
  structured outcome. Approved and refused are final. Deferred and insufficient
  evidence remain open. A final incompatible outcome makes dependent executable
  work `not_applicable`; that state propagates through executable consumers.
  Only items declaring `accepts_not_applicable_dependencies` may proceed from a
  skipped dependency, and the originating gaps remain visible at joins.
- `send` follows the model's `message_policy`. `PRAVAHA_HOLD` selects the HOLD
  path. `preflight` accepts an unclaimed detached lane. `note` cannot unblock;
  owner-authorized `unblock` and `reopen` are explicit transitions.
- `audit --since kickoff` checks duplicate or expired claims, bad completion
  evidence, unmet dependencies, unbound operations or fences, and intervals
  with no earned progress. It lists skipped mandatory items separately.

## Tracker responsiveness

Health and state requests read the last complete snapshot. Health requests never
run power, socket, filesystem or detector probes; only freshness and recent errors
are updated in memory. Snapshot persistence runs outside the publication lock.
Subprocesses have their own sessions and their process groups are killed on timeout.

`PRAVAHA_TICK_BUDGET_S` defaults to 8 seconds. A tick that exceeds it records an
abandonment in `tick_errors`, retains the last complete model/event cursor/snapshot,
and makes health return 503. One collector may remain blocked until its I/O unwinds;
its late result is discarded and replacement collectors do not accumulate. The
next successful tick restores health. Stream git activity remains independent of
the tick and uses the same subprocess timeout cleanup.

## Acceptance command

From the repository root:

```sh
TMPDIR="$JOB_SCRATCH" PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=platform/scripts/governance python3 -m pytest -p no:cacheprovider \
  --basetemp="$JOB_SCRATCH/pytest-tracker" platform/scripts/governance/pravaha_tracker/tests -q
```

The B-1b author run passed 71 tests, including the legacy Pravāha suite and
the KĀLA-YANTRA acceptance cases. This marker requests independent B-1c review;
it is not itself a verdict or permission to queue the bootstrap PR.
