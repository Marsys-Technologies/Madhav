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

## Acceptance command

From the repository root:

```sh
PYTHONPATH=platform/scripts/governance python3 -m unittest discover \
  -s platform/scripts/governance/pravaha_tracker/tests -p 'test_*.py' -q
```

The B-1b author run passed 70 tests, including the legacy Pravāha suite and
the KĀLA-YANTRA acceptance cases. This marker requests independent B-1c review;
it is not itself a verdict or permission to queue the bootstrap PR.
