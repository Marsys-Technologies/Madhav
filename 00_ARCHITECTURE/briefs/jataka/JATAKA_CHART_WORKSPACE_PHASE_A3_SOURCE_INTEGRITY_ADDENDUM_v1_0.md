---
artifact: JATAKA_CHART_WORKSPACE_PHASE_A3_SOURCE_INTEGRITY_ADDENDUM
version: 1.0
status: ACTIVE
authorized_by: native
authorized_on: 2026-09-27
decision: CCD-016
coordination_request: JATAKA-REQ-04
migration_reservation: 1123_jataka_context_staleness_deferred_surfaces.sql
parent: 00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PARALLEL_EXECUTION_AMENDMENT_v1_0.md
predecessor: 00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A2_INTEGRITY_ADDENDUM_v1_0.md
changelog:
  - v1.0 (2026-09-27): Records the native-authorized Phase-A3 source-integrity pass and the two
      separately governed source-evidence refreshes that follow it. Additive: the parent amendment
      and the Phase-A/Phase-A2 addenda and handshakes are not edited or retrospectively broadened.
governs:
  worktree: /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
  branch: codex/jataka-chart-workspace
  session: JATAKA-PHASE-A3-SOURCE-INTEGRITY-20260927
---

# Jātaka Chart Workspace — Phase-A3 Source-Integrity Addendum

## 1. Decision

The native accepted the Phase-A2 report at local commit `7673c96b8` as source-local, mock-tested
evidence with four explicitly understood governance-artifact failures, and authorized a Phase-A3
source-integrity pass followed by two separately governed source-evidence refreshes at one exact
reviewed technical head.

## 2. Authorized work, in required order

1. Finish chart-context staleness for the three deferred surfaces: `brahma_mimamsa_prediction_ledger`,
   `brahma_prospective_ledger`, `mimamsa_calibration_snapshot`. Same invariant as items already
   closed: former-chart data remains historical evidence, never current chart truth. Preserve every
   immutable prediction text, lifecycle history, outcome, review decision, provenance and timestamp;
   never delete a historical row or rewrite a lifecycle/outcome value; add only orthogonal
   context-validity metadata (stale marker, reason, superseding run, prior chart-input revision
   where necessary), marked inside the atomic correction transaction with rollback undoing it. For
   `mimamsa_calibration_snapshot`: establish its exact chart-scope first; if a row aggregates
   multiple charts, never stale the whole row for one chart's correction — add dependency membership
   or invalidate only the affected partition; if safe attribution is impossible under the existing
   schema, stop and report the exact missing provenance contract.
2. Enforce every current-serving, planning, lifecycle, calibration, availability, MCP and sidecar
   consumer of the three surfaces to exclude context-stale rows by default; historical/audit paths
   may include them only with explicit historical-context metadata. No UI-only treatment and no
   write-only marker qualifies as enforcement while any current reader ignores it.
3. Establish one reviewed technical head: complete source implementation, regenerate ordinary
   generated files through their canonical generators, run the full verification set, commit, and
   obtain an independent fresh-context review of every Phase-A3 change, the complete five-table
   staleness invariant, rollback/historical-audit behaviour, migration safety, and the absence of
   broadened Pūrṇa/Nirmāṇa claims. Fix High/Important findings with RED→GREEN tests. No source
   mutation after the reviewed head is recorded; a further source change invalidates both
   refreshes below and repeats review.
4. A narrow, separately recorded native-decision authorizes only a Nirmāṇa L5 successor re-pin
   (source-provenance only — no chart data, rebuild, dispatch, freeze, layer elevation, deployment
   or production acceptance), run through the canonical generator's successor path at the exact
   reviewed technical head, predecessor generations preserved immutable.
5. A Pūrṇa Beyond-Ācārya v7 successor is created alongside the immutable v6 predecessor (never
   overwritten), evaluated against the final generated capability snapshot from the reviewed
   technical head, gated on the denominators/coverage/fingerprint conditions the native specified,
   and independently reviewed for metric relaxation before acceptance. Source-local only; does not
   reopen or close the Pūrṇa campaign.
6. Final verification and close.

## 3. Exact file scope (in addition to the parent amendment and the Phase-A/Phase-A2 addenda)

Deferred-surface staleness:
- `platform/supabase/migrations/1123_jataka_context_staleness_deferred_surfaces.sql` and its test
- `platform/src/lib/charts/chartContextStaleness.ts` and its test; `platform/src/lib/charts/recomputeChart.ts` and its test

Current-query consumers of the three deferred surfaces (exact files):
- `platform/src/lib/lel/prospective_ledger.ts` and its tests
- `platform/src/lib/retrieval/registry/layers/L4_phala/query_prospective_ledger.ts` and its test
- `platform/src/lib/pariprashna/samiksha/{reader,badge,review,reviewConfirm,capture,writer}.ts`,
  `platform/src/lib/pariprashna/observability/queries.ts`, `platform/src/lib/pariprashna/samiksha/daily_job.ts`,
  `platform/src/lib/pariprashna/samiksha/outcome_recorder.ts`, `platform/src/app/clients/[id]/samiksha/actions.ts`
  and their tests
- `platform/src/app/api/clients/[id]/learning/route.ts` and its `__tests__/`
- `platform/python-sidecar/services/mi_bhara/db.py` and its tests
- `platform/python-sidecar/pipeline/orchestrator/writers/mi_gunanaka.py` (the `mimamsa_calibration_snapshot`
  publish path only) and its tests
- `platform-mcp/src/tools/register_p1_aliases.ts`, `platform-mcp/src/lib/ahead_autofile.ts` (refusal/read
  shaping only) and their tests

Reviewed-head and evidence-refresh surfaces:
- `platform/src/generated/nirmana-analysis-layer-pins.json` (canonical successor generator only, L5 only)
- `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v7.json` (new file; v6 untouched)
- the narrow Nirmāṇa L5 re-pin decision record and the Pūrṇa v7 decision record (new governance files)
- `platform/src/lib/vidhi/inquiry/beyond_acarya_acceptance.test.ts` (v6 as immutable predecessor, v7 as
  current successor)
- `platform/src/generated/__tests__/nirmana-analysis-receipts.test.ts`

Governance: this addendum; CCD-016 and its `CAPABILITY_MANIFEST.json` fingerprint rotation;
`CURRENT_STATE_v1_0.md` / `SESSION_LOG.md` close records; own lease/request rows on
`origin/campaign-coordination`.

## 4. Exclusions

Task 9; browser acceptance; migration application; any database or external-service access;
credentials; push, PR, merge, deploy; production data; real-user mutation; chart rebuild;
empirical/production acceptance. No blanket sidecar, MCP, retrieval, Pūrṇa or Nirmāṇa authority —
only the exact files above. Frozen `WriterBase`, runner/`asset_runner` transaction contracts, governed
`asset_registry` definitions, unrelated writers, L3 Kāla implementation, and every Nirmāṇa/Pūrṇa
surface not named above stay excluded. The Nirmāṇa re-pin is source-provenance only, never a data or
value acceptance claim; the Pūrṇa v7 successor never reopens or closes that campaign.

## 5. Close condition

Closes with a report stating: all five context-stale table contracts; every current consumer
updated; historical/audit behaviour retained; the independent-review result; Nirmāṇa predecessor and
successor generation IDs; Beyond-Ācārya v6 and v7 hashes; exact verification results with inherited
failures separated from new ones; Task 9 status; final branch and commit; and confirmation that
nothing was pushed, applied, deployed, merged or production-verified.
