---
artifact: JATAKA_CHART_WORKSPACE_PHASE_A2_INTEGRITY_ADDENDUM
version: 1.0
status: ACTIVE
authorized_by: native
authorized_on: 2026-09-27
decision: CCD-015
coordination_request: JATAKA-REQ-03
migration_reservation: 1122_jataka_chart_context_staleness.sql
parent: 00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PARALLEL_EXECUTION_AMENDMENT_v1_0.md
predecessor: 00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A_HARDENING_ADDENDUM_v1_0.md
changelog:
  - v1.0 (2026-09-27): Records the native-authorized Phase-A2 integrity session and its exact
      file scope. Additive: the parent amendment, the Phase-A hardening addendum and the Phase-A
      session handshake are not edited or retrospectively broadened.
governs:
  worktree: /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
  branch: codex/jataka-chart-workspace
  session: JATAKA-PHASE-A2-INTEGRITY-20260927
---

# Jātaka Chart Workspace — Phase-A2 Integrity Addendum

## 1. Decision

The native accepted the Phase-A hardening report at local commit `695401d31` ("Items 1, 3, 4 and 5
are implemented and mock-tested. Item 2 and two reading doors remain open. Task 9 remains
blocked.") and authorized a new, narrowly governed Phase-A2 integrity session in the same worktree
and branch.

## 2. Authorized work (local source, tests and local commits only)

1. **Chart-context staleness end to end.** Invariant: data created from former birth details
   remains available as historical evidence but cannot be treated as current chart truth. Mark
   preserved rows stale with orthogonal chart-context metadata inside the atomic correction
   transaction; never replace a prediction lifecycle value with `stale`; preserve raw
   `life_events`, recorded outcomes and provenance. Enforce every identified current-query
   consumer; historical/audit reads may include stale rows with explicit historical-context
   metadata. If a consumer cannot be made safe without a frozen or actively leased contract, stop
   on that path and report it; item 2 is then not claimed complete.
2. **Reading doors.** Gate MCP `prashna_ask` (Pūrṇa-owned door; this exact change only) and
   super-admin `chat/build` on authoritative readiness and correction-history status, with
   four-door parity tests.
3. **Correctness before Task 9.** No `ok` terminal event after a refusal; legacy consult propagates
   the write-through result; `retry` semantics per state; `stale` never counts as Ready; an explicit
   serving-impact classification so only serving-invalidating (or unclassified) runs block
   readings; recompute timezone test fix; reuse of the existing IANA-zone helper. The conservative
   label-only birthplace rule is kept.
4. **Migration 1121 security disposition.** Invoker rights preferred; no `SECURITY DEFINER`.
   Real privilege/RLS/trigger/row-lock behaviour stays Blocked (no database).

## 3. Exact file scope (in addition to the parent amendment and the Phase-A addendum)

Correction transaction and staleness marker:
- `platform/src/lib/charts/**` (incl. `recomputeChart.ts`, readiness, reading gate, new staleness module)
- `platform/src/lib/build/assetInvalidation.ts` and `platform/src/lib/build/__tests__/assetInvalidation.test.ts`
- `platform/supabase/migrations/1122_jataka_chart_context_staleness.sql`,
  `platform/tests/unit/migrations/jataka_chart_context_staleness.test.ts`
- `platform/supabase/migrations/1121_jataka_correction_archive_write_guard.sql` and its test
  (security disposition only; unapplied)

Current-query consumers (exact files; not blanket authority over their directories):
- `platform/src/lib/retrieval/registry/layers/L5_mimamsa/query_predictions.ts`,
  `prediction_lifecycle_sweep.ts`, `query_calibration.ts` and their `__tests__/` files
- `platform/src/lib/retrieval/registry/layers/L4_phala/query_prospective_ledger.ts` and its test
- `platform/src/lib/retrieval/registry/knowledge/source_query_availability.ts` (the one
  `mimamsa_predictions` availability probe only) and its test
- `platform/src/lib/lel/prospective_ledger.ts` and its tests
- `platform/src/app/api/clients/[id]/learning/route.ts` and its `__tests__/`
- `platform/src/lib/pariprashna/samiksha/{reader,badge,review,reviewConfirm}.ts`,
  `platform/src/app/clients/[id]/samiksha/actions.ts` and their tests
- `platform/src/lib/mcp/intervention_ledger_writer.ts` and its test
- `platform/python-sidecar/pipeline/orchestrator/writers/{mi_pramana,mi_gunanaka,mi_pariksha}.py`
  (query predicates only; the `WriterBase` contract is untouched)
- `platform/python-sidecar/services/mi_bhara/db.py`, `platform/python-sidecar/services/mi_sankalpa/db.py`
- `platform/python-sidecar/brahmagyan/mimamsa/lel_intake.py` (`lel_query` and the seed upsert only)
- the matching Python tests under `platform/python-sidecar/tests/**` and
  `platform/python-sidecar/pipeline/orchestrator/writers/tests/**`

Reading doors and error contracts:
- `platform/src/app/api/mcp/prashna_ask/route.ts` and its `__tests__/`, `platform/src/lib/mcp/types.ts`
- `platform-mcp/src/tools/register_prashna_ask.ts` and `register_prashna_ask.test.ts` (refusal
  mapping only)
- `platform/src/app/api/chat/build/route.ts` and a new `__tests__/`
- `platform/src/app/api/pariprashna/route.ts`, `platform/src/lib/pariprashna/pipeline/{persistence_stage,safety_gate}.ts`
- `platform/src/lib/pipelines/shared/{onfinish_writethrough,run_adapter_dispatch}.ts`,
  `platform/src/lib/streams/data_parts.ts`
- `platform/src/app/api/chat/consult/**`, `platform/src/components/clients/EditClientForm.tsx`
- test harnesses whose mocks meet the changed contracts (mock additions only):
  `platform/src/app/api/chat/__tests__/**`, `platform/src/app/api/pariprashna/__tests__/**`,
  `platform/tests/unit/chat-v2/**`, `platform/tests/pariprashna/**`,
  `platform/src/lib/pipelines/**/__tests__/**`, `platform/src/components/clients/__tests__/**`,
  `platform/src/app/dashboard/__tests__/**`, `platform/src/lib/pariprashna/**/__tests__/**`

Governance: this addendum; CCD-015 and its `CAPABILITY_MANIFEST.json` fingerprint rotation;
`CURRENT_STATE_v1_0.md` / `SESSION_LOG.md` close records; own lease/request rows on
`origin/campaign-coordination`.

## 4. Exclusions

Task 9; browser acceptance; migration application; any database or external-service access;
credentials; push, PR, merge, deploy; production data; real-user mutation. Frozen `WriterBase`,
runner/`asset_runner` transaction contracts, the `asset_registry` governed definitions (including
`integrity_check_sql`), unrelated writers, L3 Kāla implementation (`ka_*`, `registry/layers/L3_kala/**`,
`kala_views/**`), Pūrṇa beyond the one `prashna_ask` door change and the one availability probe,
the shared checkout, ports `55432`/`55433`.

## 5. Close condition

Closes with a report stating separately: context-staleness write coverage; every current-query
consumer changed; every historical/audit path preserved; four-door parity results; unresolved
frozen or externally owned consumers; migration files authored and not applied; exact test
commands and results; Task 9 status; final branch and commit; and confirmation that nothing was
pushed, applied, deployed or production-verified.
