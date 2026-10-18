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
  head, its squash merge commit and a successful main deploy that contains it (the post-deploy
  verdict is retired, A8 §4). Artifact, operation
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

## SR-BOLD-07: code items are done when merged and deployed

The server derives each tick, from `gh` and local git it already reads (`merged_deployed.py`; no credential, off the
tick path, cached), that a declared `completion_kind: code` item with a `pr_merged`/`branch_merged` detector is `done`
when its PR is MERGED and the merge commit is contained in a successful `workflow_run` deploy of main. The PR's merged
review is the acceptance: no verdict event is written or needed. Item -> PR: `detector.pr` / `packet_pr` / the PR that
squash-merged `detector.ref`; else the merged PR of the `ref` head branch; else the merged PR whose diff holds every
owned path. A bundle child counts only when at least one of its owned paths is in the bundle's diff and every owned
path is in its merged tree. The row reads `source: derived:merged+deployed` with `merged_pr` and `deploy_run_id`; an
earlier guarded completion event still wins. Operation items close from executor receipts, decisions from the ledger.

## A7 D-46: implemented vs. activated

A code or artifact item (declared `completion_kind`, else the proof's type) is *implemented* — `done` — once merged,
independently accepted and contained in a successful main deploy (artifact: digest + independent verdict). Its open
dependencies no longer block `done`; they are written to the completion event as `activation_pending`, together with
`merged_pr`, `acceptance_ref` and `deploy_run_id`. Code items need no separate step receipts. Operation, packet,
decision, join and verdict items keep strict ordered completion (SR-A4-01). The snapshot reports per row
`activation_pending` (recomputed, so it empties when the last gate closes) and in `overall`: `implemented`,
`activated`, `activation_pending` and `close_ready` (every applicable item implemented AND activated).
`audit` reports `activation_pending_unrecorded` for a deferred gate the completion does not name.

`python3 -m pravaha_tracker.d46_sweep --evidence <file>` (run with `PYTHONPATH=platform/scripts/governance`) lists
what would close and what is missing, reading git read-only; `--apply` writes the completions through the same guard.
The evidence file (schema `ky.d46_evidence/1`) is documented in the module docstring.

## Tracker responsiveness

State, health, item, next and SSE reads serve the last completed tick from memory
with `tick_age_s`. State and health reads take no collector or detector lock;
SSE's condition only coordinates in-memory publication. Health requests never run
power, socket, filesystem or detector probes. Snapshot persistence runs outside
the publication lock. Every subprocess has a hard five-second ceiling, even if a
caller asks for longer, and its process group is killed on timeout.

Timed-out measurements retain their last value. Detector results carry `stale`,
`age_s` and `error`; health groups external call outcomes under `sources` (for
example `power`, `git`, `gh`, `db`) with a stale flag and the age of the last
successful measurement. An unmeasured source has a null age. `degraded` flags a
stale source independently of `ok`, which reports tick liveness. The browser
shows stale sources and preserves the supplied tick age when accepting snapshots.
Power-value changes advance the snapshot version so existing SSE clients receive them.

`PRAVAHA_TICK_BUDGET_S` defaults to 8 seconds. A tick that exceeds it records an
abandonment in `tick_errors`, retains the last complete model/event cursor/snapshot,
and makes health return 503. One collector may remain blocked until its I/O unwinds;
its late result is discarded and replacement collectors do not accumulate. The
next successful tick restores health. Stream git activity remains independent of
the tick and uses the same subprocess timeout cleanup.

Guarded `done` calls `/api/verify` with `KY_VERIFY_TIMEOUT_S` (positive finite
seconds, default 300). A timeout reports “tracker timed out”; a connection failure
reports “tracker unreachable”. Verification never accepts a persisted snapshot or
a completed fetch's TTL. A shared same-ref fetch must have started at or after
the HTTP request; an older flight is followed by a fresh fetch, with bounded waits.
Unrelated refs fetch independently. Verification runs on its own worker, outside
the four dashboard workers, and new dashboard polls defer until active
verifications finish. Failed fetches refuse completion rather than measuring stale
refs. Verification does not update the dashboard result cache.

(I) INTERPRETATION: the unspecified live-verification budget is 20 seconds per
request, with at most four concurrent verification workers and immediate refusal
when those slots are full. Each subprocess also obeys the remaining request
budget. A late worker result is refused, and a slot stays occupied until its
worker exits; timed-out requests cannot accumulate unlimited workers. This server
budget is independent of the CLI's longer transport timeout.

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
