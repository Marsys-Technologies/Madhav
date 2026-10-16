---
artifact: K9_23_N2_CUSTODY_v1_0.md
version: "1.0"
status: PREPARATION
date: 2026-10-16
finding: K9-23-N2
finding_status: open
implementation_fixed: false
parent_accepted_head: d1c027d63f765638c9adca49bd580d6509a19a1c
review_source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261015T231013Z-review2-k9-23/result.json
original_review_source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261015T221120Z-review-k9-23/result.json
owed_regression:
  initial_state: planned
  delegation: execute_run(str(args.run_id)) exactly once
  success: completed readback; exit 0; BUILD_COMPLETED
  incomplete: non-completed or absent readback; exit 2; REFUSED
  mutation: remove execute_run call; successful-delegation test must fail
  location: CI-collected publication regression on the landed parent
activation_prerequisites:
  - K9-1 exact publication_grains and complete run/writer/grain bindings
  - independent semantic checks for every candidate writer
  - frozen ordered canonical-chart rebuild plan and issued-forecast exclusion
  - least-privilege verifier and protected migration qualification
  - absent candidate, failed verification and stale expected-head refusals
  - generation namespace excludes NONE and absent/existing-head CAS cases
  - PLAN_ONLY never earns execution dry-run qualification
  - D-R9 hold until coverage/refinement and backup capability qualification
  - full rehearsal, lineage invalidation and measured restart loss
  - retained previous-head and byte-exact full served-projection rollback
  - J-1a qualified backup and restore capability
  - independent exact-head acceptance, CI, merge and deploy containment
  - live admission and parent completion gates
changelog:
  - "1.0: retain the open finding, reproduce its coverage gap and bind the owed regression without changing runtime or admission."
---

# K9-23-N2 — custody of the open delegation regression

This is D-17 carry-forward preparation only: **no implementation finding is
claimed fixed**. The accepted K9-23 parent remains accepted independently of
this child. Amendment A2 §2.3–2.4 requires tracking non-severe findings and
per-finding fail-on-revert evidence for subsequent implementation fixes.
Amendment A6 §2 permits this preparation to land as **built, waiting on gate**;
that describes the preparation artifact, not resolution of the finding.

The second review's `review_source:19–23` carries K9-23-N2 from round one.
The original review's `original_review_source:29–35` identifies the gap:
removing `execute_run` leaves 21 publication tests and 8 binding tests passing.
At the accepted head above, the actual call is
`platform/python-sidecar/services/kala_core/publication.py:137`; lines 134–141
delegate a validated rebuild, read back `build_runs.state`, and refuse an
absent or non-completed result. The finding's `:134` identifies that branch.

## Independent reproduction and distinguishing negative

The preparation job retained evidence at
`/Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/fast/jobs/X-20261016T091430Z-pb-k9-23-n2/`:

- `parent_evidence.json` binds the accepted head, original publication SHA-256,
  mutation SHA-256, commands and observed exits. The copied parent's 21
  publication tests and 8 binding tests pass both before and after removal of
  the call. This independently reproduces the coverage gap.
- `parent-proof-tree/platform/python-sidecar/tests/l3/kala_db/manifest/test_delegation_probe.py`
  is a **job-only probe**, using the suite's guarded local database fixture and
  a delegation double. It begins with a committed planned run, requires exactly
  one call with that run ID, and checks completed, still-planned, failed and
  absent readbacks. The completed-case probe fails with the call removed
  (exit 1, missing delegation assertion); all four cases pass after restoring
  the accepted source (exit 0). Logs are `logs/probe-no-call.log` and
  `logs/probe-restored.log`; original and mutated bytes are retained separately.

The probe establishes the distinguishing negative without running the real
frozen orchestrator. It is not a committed publication regression, an independent
acceptance verdict, a full rebuild rehearsal or an activation qualification.
The source copy is restored. Only the suite fixture creates and drops isolated
databases on `127.0.0.1:55433`; no production operation is performed.

## Owed implementation and gates

Port the planned-to-completed test and incomplete-outcome negatives into the
parent's CI-collected publication suite when implementing this finding. Retain
the fail-on-revert evidence on a job-local copy as required by A2 §2.4. The
existing manifest, input, publication, rollback and disabled-admission behavior
must continue to pass. The original review's `original_review_source:38–46`
lists the upstream and activation obligations retained in the frontmatter above;
none is discharged by this note. Complete grain bindings include zero results,
service stages and reused/skipped grains. The dispatcher must retain
`action=rebuild`, `clear_before=false`, its frozen asset order and canonical
chart, and exclude issued forecasts. Independent input digests do not establish
semantic verification: each writer still needs non-circular golden-value checks.
Preserve generation-sentinel and both empty/existing-head CAS checks, actual
attachment-versus-interpretation invalidation, killed-substep restart-loss
measurement, single-credential execution and least-privilege grant readback.
Reconcile migration allocation and protected
registration with K9-23-N1 separately; this preparation creates no migration.

The existing declaration at
`00_ARCHITECTURE/control/kalayantra/plan_model.json:27272` already registers
K9-23-N2 as a mandatory code child of K9-23, with detector
`origin/kalayantra/k9-23-n2` and reviewer rule
`v_exact_head_then_deploy_containment`. Preserve that declaration, its dependency
direction and its independent exact-head review. The cockpit owns mapping this
pre-build branch to the registered landing ref and recording guarded completion.
Preparation does not add a stored status, new steps, a parent dependency on the
child, or live-operation authority. All five K9 executor operations stay disabled.

**(I) INTERPRETATION — preparation scope:** the explicit model contract and notes
(`plan_model.json:27291–27305`) require custody only, despite the finding's title
describing a missing test. Preserve the finding as open and retain the diagnostic
probe in job evidence. The alternative is to port parent runtime/tests now and
claim the implementation fixed, contrary to that explicit contract.

**(I) INTERPRETATION — destination and absent parent:** add this note beside the
existing `P06_N1_MIGRATION_COMMENT_RECONCILIATION_v1_0.md` and its acceptance
checks under `platform/scripts/governance/__tests__/` (Amendment A3 D-23).
The advertised K9 measurement files and publication entrypoint are absent on
this pre-build base. Read the available immutable accepted parent head for
diagnosis; do not import it or create competing measurement files. The
alternative is to overwrite parent-owned preparation or wait for its merge.
The existing governance shards discover the new custody checks automatically
(`.github/workflows/ci.yml:2186–2231`); no workflow or digest-lock change is needed.
