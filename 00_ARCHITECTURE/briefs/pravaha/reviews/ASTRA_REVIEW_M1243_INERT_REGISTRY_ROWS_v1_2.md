---
artifact: ASTRA_REVIEW_M1243_INERT_REGISTRY_ROWS
version: "1.2"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: "9dc0f12c278bcbdf255fe8398ddfb6a8474ee413"
authority: "Review only; authorizes nothing."
---

The split closes the three v1.1 objections. **No migration or predicate change is required; the remaining amendments correct documentation.**

| Check | Judgment |
|---|---|
| **1. Routine apply without public CREATE** | **PASS by source inspection.** 1243 contains one two-row `INSERT … ON CONFLICT DO NOTHING`, plus checks inside an anonymous `DO`. No persistent object creation, grants, sequence defaults, or update operation. The checked-in registry trigger is UPDATE-only and cannot fire here. `DO` requires language USAGE, not public-schema CREATE. [PostgreSQL documentation](https://www.postgresql.org/docs/current/sql-do.html) |
| **2. Every loader, including ingress** | **PASS.** Monitor, snapshot, and all five definitions loaders use `runtimeEvidenceSql`, including `loadCurrentRegistryRows`. The expression checks receipts OR build-run rows for exactly the two IDs; other IDs receive NULL. Only `=== false` permits exclusion. Missing/NULL evidence retains the candidate; query errors propagate or produce source-unavailable. No executable call of the removed function remains. |
| **3. R20-2 through actual callers** | **PASS.** Baseline construction and both registry comparisons evaluate candidate exclusion against the complete registry before removing supporting writers. An active or inactive `bo_grounding` dependent preserves either candidate in the denominator. |
| **4. Documented limit and fallback** | **Predicate accepted; documentation amendment required below.** Watchdog pruning can erase the sole build-run evidence, and throughput is deliberately ignored. The same-change procedural commitment matches the approved fallback. The separate claim of permanent receipt survival is incorrect. |
| **5. Other consumers** | **No additional breaking regression found.** Planning, recalibration, readiness, clearing, and co-writer checks exclude these inactive rows. Registry listings can display them. Snapshot campaign totals and layer completion remain unchanged. |

**A1 — Correct the receipt-permanence claim.**  
[definitions.ts:104](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243c/platform/src/lib/nirmana-elevation/definitions.ts:104) says the v4.1 teardown does not delete receipts and evidence remains true “for good.” However, [teardown deletes the registry row](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243c/platform/scripts/dispatch_a25_v41_candidate_job.py:192), and the [receipt FK specifies `ON DELETE CASCADE`](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243c/platform/supabase/migrations/596_nirmana_provenance_receipts.sql:12). A successful build can persist an unknown receipt without an output-digest specification, so specification-related RESTRICT constraints do not guarantee retention.

Replace that claim with: receipts survive watchdog run pruning while retained, but registry teardown can cascade-delete them. Extend the known-limit paragraph accordingly. Keep the commitment that **every real dispatch, including successful runs, requires the same-change disposition and exclusion-list removal**. Permanent removal depends on that commitment.

**A2 — Align test descriptions with the split.**  
In [staged-inert-candidates.test.ts](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-m1243c/platform/src/lib/nirmana-elevation/__tests__/staged-inert-candidates.test.ts:23), remove “throughput” from the evidence descriptions at lines 23 and 76; change line 78’s “evidence function returned NULL” to “evidence column is NULL.”

**Verification:** 25 targeted in-memory checks passed using the actual implementation, covering baseline/comparison behavior, both candidate IDs, supporting dependents, NULL/error handling, digest stability, and snapshot totals. `git diff --check` passed; checkout remains clean. No files written or production database accessed. PostgreSQL rehearsal was unavailable under the read-only sandbox; supplied steward privilege facts were not independently reverified. GitHub access was unavailable, so this verdict covers the exact commit above; its continued equality with the remote PR head is unverified.