---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.23"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: ACCEPT_WITH_AMENDMENTS
reviewed_commit: "672420f5cad504148e0b3561f2fe0b8d5baa79d3 (campaign/pravaha review checkout) + 930ca549e0f08df9e8c46628eddf0dee226fce0c (PR 3094)"
authority: "Review only; authorizes nothing."
---

**One page amendment remains. No migration-code blocker found.**

**A. Page**

Round-23 points **1–4 are CLOSED**: the dormant exception is removed; effective table/column privilege assertions replace it; the predecessor wording accommodates after-SETTLED-1 execution; and the earned-outcome gate is correctly described as failing.

**Remaining contradiction:** [checklist line 12](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55y/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md:12) still freezes all merges except rows 4, 7 and **#2996**. Required **#3094** is outside that exception.

**Exact amendment:** add #3094 to the freeze exceptions and state:

> Before row 2’s ledger snapshot, merge PR #3094 and finish its ordinary routine deploy successfully. Record `1302_revoke_role_orchestrator_windows_dml.sql` and its reviewed SHA256 in `_migrations_applied`; include it in the baseline. No protected-train merge precedes this.

This resolves ordering and keeps the expected subsequent ledger difference empty. Row 3 already requires the ledger record and W2(b) = `t` for every holder, repeated before row 8.

1302 is above the `--only` predecessor ceiling of 1240. It neither enters the protected selection nor changes the ten hash-manifest entries, five pending window files, trigger manifest or 1240 guards. Its ordinary deployment precedes the train’s protected-refusal automatic-run rule.

**B. Migration**

- **REVOKE-only privilege change, idempotent, absent-role no-op.** With the supplied owner/grantor facts, `amjis_app` can perform it. A failed assertion rolls back the revokes and prevents the migration’s ledger insert.
- **Post-check is correct:** table INSERT/UPDATE/DELETE plus any-column INSERT/UPDATE covers the requested effective rights. PUBLIC or inherited write privileges correctly cause refusal; that is **not a false failure**. PUBLIC SELECT does not fail these assertions. [Privilege functions](https://www.postgresql.org/docs/15/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE), [REVOKE semantics](https://www.postgresql.org/docs/15/sql-revoke.html).
- **Live-table behavior:** catalog ACL updates, no data rewrite. `SET LOCAL lock_timeout='5s'` bounds each lock wait, not total execution time; failure rolls back. [PostgreSQL implementation](https://github.com/postgres/postgres/blob/REL_15_STABLE/src/backend/catalog/aclchk.c#L1696-L1720), [timeout semantics](https://www.postgresql.org/docs/15/runtime-config-client.html#GUC-LOCK-TIMEOUT).
- **Routine path confirmed:** absent from both protected sets and the workflow’s protected selection; the ordinary runner discovers it.
- **TRUNCATE/REFERENCES/TRIGGER need no additional revocation for W2(b):** that check enumerates UPDATE/DELETE holders. INSERT removal is additional tightening; 1240’s separate TRUNCATE protection remains unchanged.

Nonblocking comment correction: PostgreSQL’s table-level REVOKE already removes corresponding column grants from that grantor; the additional column loop is harmless.

Validation: extracted dispatch selection and all ten composition hashes passed read-only checks. Reviewed the three tests parameterized across PG15/17; the authors’ six-pass result was **not independently rerun**. Fetch was sandbox-blocked, but the exact commit was locally available. No files written or database accessed.

**Is the protected window NOW EXECUTABLE AS PACKAGED with only operational acts remaining—including merge + routine-apply 1302 first—NO. Apply the single freeze/baseline amendment above to make it YES.**

