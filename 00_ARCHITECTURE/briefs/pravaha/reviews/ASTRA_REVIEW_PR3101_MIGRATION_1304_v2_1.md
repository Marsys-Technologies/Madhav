VERDICT: ACCEPT_WITH_AMENDMENTS

**Safe to merge and let the routine deploy-time runner apply it after the already-required protected window is complete. No P1/P2 blockers remain.** One non-blocking P3 test-coverage amendment remains; I found no new runtime defect.

Reviewed HEAD `78d4704f13300b37f5cc341222f187eb42eb7082`, the full diff against local `origin/main` `e718a9b15`, the round-two delta from `9b62ead81`, and the requested migration/test delta from `df7299f9d`.

**Round-one dispositions**

| Finding | Disposition and evidence |
|---|---|
| **P2: unexpected prior values overwritten** | **Resolved.** [1304:103](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/migrations/1304_ka_gochara_v5_registry_row_small_test.sql:103) locks the row before validation. Lines 109–140 validate every assigned field, scope, and routing fields. The guard accepts either complete configuration, not mixtures. |
| **P2: empty health probe prevents teardown** | **Resolved for this migration.** Health and integrity must both be literal NULL before and after application: [1304:115](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/migrations/1304_ka_gochara_v5_registry_row_small_test.sql:115), lines 179–180. Empty strings are refused. |
| **P3: undocumented freshness-trigger effect** | **Resolved in source and test coverage.** [1304:57](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/migrations/1304_ka_gochara_v5_registry_row_small_test.sql:57) describes the effect accurately. [Test:390](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/python-sidecar/tests/test_migration_1304_ka_gochara_v5_registry_row.py:390) uses the actual 596 function/trigger and checks affected v5 rows, an unchanged control asset, and rerun behavior. Database execution was not verified here. |
| **P3: readbacks still say 7,200** | **Resolved.** Both now say **28800**: [registry readback:5](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/scripts/v5_small_test_registry_row_readback.sql:5), [predispatch readback:7](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/scripts/v5_small_test_predispatch_readback.sql:7). |
| **P3: obsolete counter expected-failure** | **Resolved.** [Conformance:65](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/scripts/__tests__/ka_gochara_v5_registry_conformance.test.ts:65) positively asserts the exact chart/generation-scoped evaluation-window counter and target. |
| **Additional steward ruling: parse `has_substeps`** | **Resolved.** [1243 test:153](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/tests/unit/migrations/ka_gochara_inert_registry_rows_1243.test.ts:153) now extracts the boolean from migration 1304. |

**Remaining follow-up — P3**

The refusal tests do not cover **NULL prior values in nullable columns or reversed dependency order**. The fixture makes `depends_on NOT NULL`, unlike the original schema, and the altered-value matrix uses ordinary non-NULL replacements. See [test:60](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/python-sidecar/tests/test_migration_1304_ka_gochara_v5_registry_row.py:60), [test:312](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/python-sidecar/tests/test_migration_1304_ka_gochara_v5_registry_row.py:312), and [167:22](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/supabase/migrations/167_asset_registry.sql:22).

Add named-refusal/unchanged-row cases for nullable prior fields and `['ga_dashas','ga_positions']`. Otherwise, a future substitution of ordinary inequality for `IS DISTINCT FROM`, or order-insensitive prior validation, could escape this suite. **The current SQL handles these cases correctly**, so this is not a production blocker.

The existing dispatch/teardown tolerance mismatch remains the steward-deferred **PR 3145** follow-up: dispatch normalizes empty health/integrity strings; teardown refuses them. I reproduced both outcomes using the actual validators with an in-memory cursor. This migration now excludes those representations.

**Prior configuration and production derivation**

The migration chain touching this asset’s registry row is:

- **1243:** inserts the inactive row, with `has_substeps=false`, timeout `600`, empty dependencies, the `kala_gochara_windows` counter/size/target, floor `0`, estimate NULL, and health probe NULL. [1243:80](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/migrations/1243_ka_gochara_inert_registry_rows.sql:80)
- **1304:** performs the proposed transition.
- **No intervening checked-in migration changes this row.** I also inspected later registry-touching migrations **1252, 1253, 1254, 1259, 1262, 1288, 1296, 1297 and 1299**; their writes name other assets. Migration 223 supplies the omitted defaults: integrity NULL and rebuild policy false.

Consequently, a row freshly inserted by 1243 satisfies the new guard. However, 1243’s `ON CONFLICT DO NOTHING` preserves an existing row; neither migration history nor this review proves the live production row. A later alteration to any guarded field is deliberately refused, with field names, before the UPDATE.

The comparisons are NULL-safe and order-sensitive. Empty arrays differ from NULL; empty strings differ from NULL; reversed dependencies are rejected. Timeout, floor and estimate are integer columns, so the numeric comparisons introduce no text/number coercion issue. Exactness covers the **16 governed fields**; unrelated descriptive metadata remains unvalidated and untouched.

**Literal consumer agreement**

The final row matches both [dispatch’s map:172](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/scripts/dispatch_v5_small_test_job.py:172) and [teardown’s map:122](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/scripts/teardown_v5_small_test_job.py:122), field by field:

| Field | Migration / both tools |
|---|---|
| `scope` | `per_chart` |
| `is_active` | false |
| `has_writer` | true |
| `has_substeps` | true |
| `writer_timeout_seconds` | 28800 |
| `depends_on` | `['ga_positions','ga_dashas']`, in that order |
| `target_table` | `ka_gochara_eval_window` |
| `count_sql` | `SELECT COUNT(*) FROM ka_gochara_eval_window WHERE chart_id=$1 AND generation='5.0'` |
| `target_floor` | 0 |
| `estimated_seconds` | NULL |
| `asset_kind` | `data` |
| `asset_type` | `data` |
| `health_probe` | NULL |
| `integrity_check_sql` | NULL |
| `rebuild_on_probe_fail` | false |

The seed agrees, including `size_sql`, which neither tool’s map compares. The counter counts what [WindowStore actually inserts:170](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/python-sidecar/services/gochara_kernel/window_store.py:170).

This establishes registry-field compatibility, not satisfaction of every dispatch prerequisite. The shared module separately checks retirement, incoming dependencies, receipts and run ownership at `v5_small_test_shared.py:376`. The normal 1243-derived `catalog_status=CURRENT` is preserved.

**Other safety checks**

- **Routine application and rollback:** 1304 contains no DDL, CREATE, grants, INSERT or DELETE. Its single UPDATE targets only v5. The five-second lock timeout applies to the prior-row lock. The runner wraps this SQL and its tracker insertion in one transaction; any exception rolls both back and stops deployment. Earlier migrations remain committed. [migrate.ts:833](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/scripts/migrate.ts:833)
- **Postconditions and reruns:** every assigned field plus scope/routing is checked. NULL mismatches cannot satisfy the counted predicate. Exact reruns preserve values. Migration 596 stales only existing freshness rows whose `asset_id` is v5; its `OLD IS DISTINCT FROM NEW` condition prevents invalidation on an unchanged rerun. [596:61](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304y/platform/supabase/migrations/596_nirmana_provenance_receipts.sql:61)
- **No automatic build path found:** normal planning, recalibration, DAG scanning, downstream propagation, nightly fresh-chart planning and cockpit stats filter active rows. Relevant selectors include `runPreparation.ts:183`, `recalibrationEnqueue.ts:141`, `dag_edge_guard.py:101`, `runner.py:871`, `fresh_chart_smoke_bootstrap.py:120`, and cockpit `stats/route.ts:306`. No checked-in incoming v5 dependency was found. The watchdog handles existing work; it does not enqueue a build. Explicit steward dispatch remains possible.
- **Timeout:** 28800 fits migration 417’s integer column; no repository upper-bound constraint or validator rejects it. `runner.py:679–705` uses it directly for the deadline; `deploy.yml:2227` sets the task timeout to 86400.
- **Integrity delta:** correct. `asset_runner.py:955` executes without binds; lines 1166–1208 gate post-write acceptance, retaining earlier heavy-writer commits. Lines 1591–1615 implement the green-probe shortcut. Strict NULL plus rebuild false meets the ruling.
- **PR scope:** no existing migration is changed relative to main. Generated census differences are provenance/hash changes, with verified content and seed hashes. Family/level payloads are unchanged. Draft regeneration passes, with the disclosed **revision 25 versus census 26** staleness warning.

**Verification performed and limits**

Seven selected database-free tests passed. The existing static test rejected in-memory mutants assigning activation, an integrity statement, rebuild true, or an empty health probe. Both actual tool validators accepted all 15 final fields. The test matrix contains altered-prior cases for all eight assigned fields, both configurations, missing/active rows, scope, routing, mixed configurations, locking and trigger effects.

**Not verified:** PostgreSQL execution, concurrency/trigger behavior on a running database, Vitest execution—local dependencies are absent—or production row/tracker state, privileges, schedules and protected-window completion. No database or network was accessed. No files were modified.

