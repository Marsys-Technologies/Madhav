---
artifact: NIRMANA_L0_L5_RECEIPT_COUPLING_FIX_ADDENDUM
version: 1.0
status: ACTIVE
authorized_by: native
authorized_on: 2026-09-27
decision: CCD-017
predecessor: 00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A3_SOURCE_INTEGRITY_ADDENDUM_v1_0.md
changelog:
  - v1.0 (2026-09-27): Records the native-authorized, separately governed follow-up that
      diagnoses and corrects the L0/L5 receipt-checker coupling responsible for the two failing
      nirmana-analysis-receipts.test.ts cases left open at the Jātaka Phase-A3 close. Additive:
      the Phase-A3 addendum, close checklist and SESSION_LOG entry are not edited or reopened.
governs:
  worktree: /Users/Dev/.codex/worktrees/jataka-chart-workspace/Madhav
  branch: codex/jataka-chart-workspace
  starting_commit: a97fc8ffb0268954fb4bf8c7fb7e838c4bf6e558
  session: NIRMANA-L0-L5-COUPLING-FIX-20260927
---

# Nirmāṇa L0/L5 Receipt-Checker Coupling Fix — Addendum

## 1. Decision

Phase-A3 is closed and is not rewritten. This is a new, separately governed follow-up
authorizing only the diagnosis and correction of the cross-layer coupling in the Nirmāṇa
analysis-receipt spine responsible for the two failing
`platform/src/generated/__tests__/nirmana-analysis-receipts.test.ts` cases
("produces the pinned receipt count for every layer", "re-derives each layer aggregate from the
live inventory, so a hand-edited pin fails") — carried forward, documented and not fixed, at
`briefs/nirmana/JATAKA_PHASE_A3_L0_FROZEN_PINS_DRIFT_FINDING_v1_0.md`.

## 2. Authority

Native message (2026-09-27): starts from branch `codex/jataka-chart-workspace` at
`a97fc8ffb0268954fb4bf8c7fb7e838c4bf6e558` (local-only, no upstream), Phase-A3 lease released and
remotely verified at `89cda9092`, migration 1123 unapplied, Beyond-Ācārya v7 complete and not to
be revisited, Task 9 blocked. Authorizes only: diagnosis and correction of the `L0_FROZEN_PINS`
coupling; focused regression tests; necessary narrow generated-code or governance updates; local
commits and governed session records.

## 3. Explicit non-authorization

- Changing L0's accepted membership, hashes, generations, receipts, evidence, or frozen source.
- Another L5 re-pin unless the fix genuinely changes L5 source identity.
- Weakening or deleting the failing assertions.
- Hand-editing generated JSON.
- Database access, migrations, rebuilds, credentials, push, PR, merge, deployment, or production
  work.
- Task 9.

## 4. Diagnosis invariant (binding)

The correct outcome must satisfy both:
1. A legitimate reviewed L5-only successor does not require, rewrite, or re-accept L0.
2. Any real change to frozen L0 membership, identity, hashes, generation, or receipt evidence
   still fails closed.

Refreshing `L0_FROZEN_PINS` to the current branch's values, without correcting the underlying
cross-layer coupling, does not satisfy this invariant and is explicitly out of scope for this
addendum's authority. If investigation proves the fix requires changing ratified L0 evidence
rather than correcting cross-layer validation logic, this session stops and reports rather than
proceeding.

## 5. Exact file scope

May touch:
- `platform/src/generated/nirmana-analysis-receipts.ts` and its test
  (`platform/src/generated/__tests__/nirmana-analysis-receipts.test.ts`)
- `platform/scripts/generate/nirmana_analysis_layer_pins.py` — only if the receipt-checker's own
  comparison/regeneration logic is not the true site of the coupling and the generator itself
  must be corrected; `L0_FROZEN_PINS` byte-for-byte unchanged unless evidence proves the constant
  itself is incorrectly constructed
- `platform/src/generated/nirmana-analysis-layer-pins.json` — through the canonical generator
  only, never hand-edited
- New focused regression tests for the invariants in §4
- This addendum; `00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md` (CCD-017);
  `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (new §2 entry only); `00_ARCHITECTURE/SESSION_LOG.md`;
  `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` (own lease row only)

Must not touch:
- `00_ARCHITECTURE/briefs/jataka/JATAKA_CHART_WORKSPACE_PHASE_A3_SOURCE_INTEGRITY_ADDENDUM_v1_0.md`
  and its close checklist/SESSION_LOG entry (Phase-A3 is closed, not reopened)
- `00_ARCHITECTURE/briefs/nirmana/purna_anvesana/BEYOND_ACARYA_ACCEPTANCE_v6.json` or `_v7.json`
- Any L0 writer source, `bg_*` migration, or the frozen manifest
- `platform/migrations/**`, `platform/supabase/migrations/**` (no new migration is anticipated
  for a generator-logic fix; if one proves necessary, stop and report rather than reserving one
  under this addendum)
- Database access of any kind
- L3 Kāla, Pūrṇa source beyond the two named Beyond-Ācārya files (untouched), any chart-workspace
  Task 9 surface

## 6. Close condition

This addendum closes when the two named tests pass (or the investigation proves an L0-evidence
change is required, in which case it stops and reports without proceeding), the full verification
set in the native's message passes, and a governed session-close record is emitted.
