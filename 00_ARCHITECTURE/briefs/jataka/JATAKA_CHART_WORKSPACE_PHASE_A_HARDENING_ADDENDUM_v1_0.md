---
artifact: JATAKA_CHART_WORKSPACE_PHASE_A_HARDENING_ADDENDUM
version: 1.0
status: ACTIVE
authorized_by: native
authorized_on: 2026-09-27
decision: CCD-014
coordination_request: JATAKA-REQ-02
migration_reservation: 1121_jataka_correction_archive_write_guard.sql
parent: 00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PARALLEL_EXECUTION_AMENDMENT_v1_0.md
changelog:
  - v1.0 (2026-09-27): Records the native-authorized Phase-A integrity-hardening follow-up and its
      exact file scope. Additive to the parent amendment; does not edit it.
governs:
  worktree: /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
  branch: codex/jataka-chart-workspace
  session: JATAKA-PHASE-A-HARDENING-20260927
---

# Jātaka Chart Workspace — Phase-A Integrity-Hardening Addendum

## 1. Decision

After accepting the Tasks 1–8 result ("implemented and mock-tested locally; Task 9 and full
browser/recompute acceptance remain blocked"), the native authorized a narrow Phase-A hardening
follow-up in the same worktree and branch. This addendum records that scope expansion; the parent
amendment is unchanged and its assertions, exclusions and Task 9 gate remain in force.

## 2. Authorized work (local source, tests and local commits only)

1. Gate `POST /api/pariprashna/samiksha/confirm` (confirm and dismiss) and
   `POST /api/conversations/[id]/branches` for correction-archived conversations, reusing
   `isCorrectionArchived()` / `archivedReadOnlyResponse()`; verify the Samīkṣā conversation belongs
   to the supplied chart without enumerating inaccessible resources.
2. Chart-context staleness for rows preserved through a correction (`event_chart_state_index`,
   predictions produced under former birth details) — **only if** every current-query consumer can
   be enforced inside this scope. If enforcement requires an excluded surface, stop and report the
   exact dependency; do not implement a partial truth.
3. Shared-readiness parity for every reading door (legacy consult with Paripraśna); a failed small
   refresh may stay Ready only as a non-blocking warning and never masks a failed correction or
   full rebuild.
4. Computation-safe birthplace editing enforced server-side (place, coordinates and timezone change
   together, or the edit is rejected with guidance).
5. A final authoritative archive/readiness recheck at the persistence boundary, with a
   deterministic race test, and an additive database write guard.

## 3. Exact file scope (in addition to the parent amendment's allowlist)

- `platform/src/app/api/pariprashna/samiksha/confirm/route.ts` and `…/confirm/__tests__/**`
- `platform/src/app/api/conversations/[id]/branches/route.ts` and `platform/src/app/api/conversations/__tests__/**`
- `platform/src/lib/pipelines/shared/onfinish_writethrough.ts`, `platform/src/lib/pipelines/shared/run_adapter_dispatch.ts`
  and their existing tests (write-guard wiring only)
- `platform/src/lib/pariprashna/pipeline/persistence_stage.ts` (write-guard wiring only)
- `platform/src/app/api/pariprashna/route.ts` (write-guard wiring only, if required)
- `platform/src/lib/conversations/**`, `platform/src/lib/charts/**`, `platform/src/components/profile/**`
- `platform/src/app/api/chat/consult/**`, `platform/src/app/api/charts/[id]/**`
- `platform/src/components/clients/EditClientForm.tsx` and tests; `platform/src/components/clients/NewClientForm.tsx`
  (export of the existing Places component only — no behaviour change)
- Test harnesses whose DB mocks meet the new readiness or write guard — mock additions only, never a
  weakened gate: `platform/src/app/api/chat/__tests__/**`, `platform/tests/unit/chat-v2/**`,
  `platform/tests/pariprashna/**`, `platform/src/lib/pipelines/**/__tests__/**`
- `platform/supabase/migrations/1121_jataka_correction_archive_write_guard.sql` and
  `platform/tests/unit/migrations/jataka_correction_archive_write_guard.test.ts` (authored, never applied)
- Governance: this addendum; CCD-014 in `CROSS_CUTTING_DECISION_REGISTER_v1_0.md` and its
  `CAPABILITY_MANIFEST.json` fingerprint rotation; `CURRENT_STATE_v1_0.md` / `SESSION_LOG.md` close
  records; own lease/request rows on `origin/campaign-coordination`

## 4. Exclusions (unchanged from the parent amendment, restated)

Task 9; browser acceptance; migration application; any database access; push, PR, merge, deploy;
Firebase/credential/secret/IAM/infrastructure action; ports `55432`/`55433`; the shared checkout;
`platform/python-sidecar/**` and frozen orchestrator/writer contracts; L3 Kāla and Pūrṇa
source/state/ranges (including `platform/src/lib/retrieval/registry/knowledge/**`); `platform-mcp/**`.

## 5. Close condition

Closes with an evidence report distinguishing implemented-and-mock-tested work, staleness
enforcement coverage (or its stop-and-report), excluded consumers needing separately governed
change, the unchanged Task 9 gate, exact test results, and the final local commit.
