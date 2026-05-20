# RESIDUALS_COMPLETE

Chat V2 R7-R10 arc close-out residuals — final state.

Both residual items from the R7-R10 close-out are resolved.

---

## Item 1 — R9-S2 Conversation Embedding Backfill

**Status: COMPLETE**

| | |
|---|---|
| Script | `platform/scripts/backfill_conversation_embeddings.ts` |
| Before | 0 embeddings |
| After | 73 embeddings (73/73, 100% coverage) |
| Errors | 0 |
| Duration | 53 seconds |
| Script bug fixed | `cm.content` column → `jsonb_array_elements(parts_json)` |
| BACKFILL_SCRIPT_NOT_FOUND.md | Updated to v2.0 RESOLVED |
| Full report | `BACKFILL_RUN_REPORT.md` |

The SQL-backed `query_panchanga` semantic search (R9-S2) now has full historical embedding coverage. New messages continue to embed live via the `conversation_writer.ts` non-blocking hook.

---

## Item 2 — Pre-Existing Test Failures Triage

**Status: COMPLETE**

| | |
|---|---|
| Files triaged | 9 |
| Fixed | 8 |
| Deleted | 1 (stale R5 test) |
| Final suite | 333 files pass / 0 fail / 22 skipped |
| KNOWN_PRE_EXISTING_FAILURES.md | Updated to v1.2 |

Per-file dispositions:

| # | File | Disposition |
|---|------|-------------|
| 1 | ics_builder.test.ts | FIXED (npm install) |
| 2 | test_query_panchanga_e2e.test.ts | FIXED (DB env guard) |
| 3 | sidebar-background.test.tsx | DELETED (stale R5) |
| 4 | PostAnswerProvenance.test.tsx | FIXED (expand-before-assert) |
| 5 | KpiTile.test.tsx | FIXED (CSS variable class names) |
| 6 | AuditRail.test.tsx | FIXED (ACTION_DISPLAY labels) |
| 7 | CostConfirmDialog.test.tsx | FIXED (heading role + button text) |
| 8 | ParamOverrideRow.test.tsx | FIXED (button regex + PARAM_DISPLAY names) |
| 9 | msr_parser.test.ts | FIXED (MSR version string v3_0→v5_0) |

---

## Residuals left deliberately

None. All identified residuals are resolved.

The only remaining outstanding item from `CLOSEOUT_COMPLETE.md` is Phase 4C Wave 2
(4B sunrise derivation, 4D follow-up) which was never a residual of the R7-R10 arc —
it is future work for a separate planning session.

---

*Produced 2026-05-20 on branch `chat-v2/closeout-residuals`.*
