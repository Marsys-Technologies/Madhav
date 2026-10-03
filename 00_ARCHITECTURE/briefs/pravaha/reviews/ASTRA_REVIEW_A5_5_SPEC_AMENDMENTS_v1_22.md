---
artifact: ASTRA_REVIEW_A5_5_SPEC_AMENDMENTS
version: "1.22"
reviewer: "Codex gpt-6-astra"
date: "2026-10-03"
verdict: REJECT
reviewed_commit: "4a081d7921e0253c105b9cf2b1e9096d24fd9b98"
authority: "Review only; authorizes nothing."
---

**Is the protected window NOW EXECUTABLE AS PACKAGED with only operational acts remaining — NO.**

References: **C** = [checklist v1.12](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55x/00_ARCHITECTURE/briefs/pravaha/runbooks/PROTECTED_WINDOW_SITTING_CHECKLIST_v1_0.md); **R** = [runbook v1.23](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55x/00_ARCHITECTURE/briefs/pravaha/runbooks/ROLES_AND_SEAL_PROVISIONING_RUNBOOK_v1_0.md); **Q** = [dormant-exception check](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-a55x/00_ARCHITECTURE/briefs/pravaha/runbooks/rehearsal/w2b_dormant_exception_check.sql).

| Round-22 amendment | Closure | Evidence / remaining wording |
|---|---|---|
| 1. Stage-specific qualification | **CLOSED** | C:12,24: synchronization follows row 4; seven/nine/ten manifest entries qualify at their respective stages. |
| 2. Readiness and actual conflicts | **CLOSED** | C:24: all remaining PRs ready, four-field readbacks, `UNKNOWN` re-polled, obsolete conflict removed. |
| 3. One automatic-run rule | **PARTLY** | Operative rules agree, but C:14 still says **“with all jobs skipped”**. Replace with **“with change detection and migration/deployment jobs skipped; the earned-outcome gate itself fails.”** |
| 4. Grants and scheduling | **CLOSED** | R:285 agrees with C:28,31. |
| 5. Split failure procedure | **CLOSED** | C:7,25 and R:16 contain the requested ledger/log/job readbacks and reviewed recovery dispatch without the window flag. |
| 6. zsh commands | **CLOSED** | C:21,24: quoted API argument and parenthesized commands; syntax checks passed after substituting `<repo>`. |

**(a) The exception is explicitly restricted to `role_orchestrator`, but its dormancy proof is insufficient.** Q:3–8 is read-only: one catalog `SELECT`. It correctly checks NOLOGIN, memberships in both directions, and ownership dependencies. **Q:7 counts login identities, not effective roles.** An existing backend that previously executed `SET ROLE role_orchestrator` can remain effective as that role after its membership is revoked, while `pg_stat_activity.usename` still names the original login. Thus the five-field result can pass while a real writer remains. This is a static counterexample, not an observed production session. [PostgreSQL activity fields](https://www.postgresql.org/docs/15/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW), [role implementation](https://github.com/postgres/postgres/blob/REL_15_STABLE/src/backend/commands/variable.c#L820-L913).

**Required wording changes to make this executable:**

1. **C:20, R:82; Q:2,7:** describe the fifth field as **“zero direct-login backends”**, not proof of zero effective sessions. Add:

   > Before granting this exception at row 3, drain existing target-database client connections and record zero other client backends; the retained checker must report neither session_user nor current_user as role_orchestrator. Missing drain evidence = STOP. Until the reviewed follow-up revoke is verified, no session may adopt this role, and its attributes, memberships, ownership and privileges must remain unchanged except for that revoke. Record fresh five-field checks at row 3 and immediately before row 8.

2. **C:20 / R:82 follow-up:** strengthen the asserting post-check to require both the existing `NOT has_table_privilege(...,'UPDATE,DELETE')` **and** `NOT has_any_column_privilege('role_orchestrator','public.kala_gochara_windows','UPDATE')`. The existing assertion can miss surviving column UPDATE grants. [Privilege-check semantics](https://www.postgresql.org/docs/15/functions-info.html#FUNCTIONS-INFO-ACCESS-TABLE).

3. **(b), C:19:** the predecessor rule and three-merge synchronization dependency are sound. However, **“will NOT be on main during this window”** conflicts with the permitted after-SETTLED-1 route. Replace with:

   > Before W1, these W1 migration files must be absent. After SETTLED-1, include every landed predecessor numbered ≤1240 in the same ledger check.

4. Apply the C:14 wording correction in amendment 3 above.

No other new execution blocker found in this delta. No files written, no database accessed, and no re-review of migration SQL, composition or writer code.

