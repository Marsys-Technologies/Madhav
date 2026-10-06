VERDICT: REJECT

**Do not merge for automatic production application as-is.** The strict-NULL delta is correct, and the normal 1243 → 1304 transition is transactional and inactive. Two required safety guarantees remain incomplete.

Reviewed HEAD `0fe5520db`, the full `origin/main...HEAD` diff against local `origin/main` `8d63c31b0`, and the requested delta from `df7299f9d`. No P1 found.

Two **P2 blockers** require amendments:

1. **Unexpected prior configurations are overwritten, not refused.**  
   [1304:80–89](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/migrations/1304_ka_gochara_v5_registry_row_small_test.sql:80) updates solely by `asset_id`. An inactive row with an unexpected timeout, dependency list, counter, target table, floor, or estimate is silently converted and passes the post-check. An altered `scope='global'` also survives because scope is neither assigned nor checked, although both dispatch tools require `per_chart`.

   Missing rows and active rows **do** fail and roll back, but through post-checks. Migration 1243 supplies the expected starting values; its `ON CONFLICT DO NOTHING` does not guarantee an existing row has that complete shape.

   **Required:** lock and validate the relevant prior fields, accepting only the documented 1243 shape or the exact 1304 shape for reruns. Add altered-prior-value and scope cases. Existing negative cases cover routing fields, not the overwritten prior values. [Tests:254](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/python-sidecar/tests/test_migration_1304_ka_gochara_v5_registry_row.py:254)

2. **A migration-approved health probe can prevent teardown.**  
   [1304:115](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/migrations/1304_ka_gochara_v5_registry_row_small_test.sql:115) accepts and preserves `health_probe=''`. Dispatch normalizes that to `None`; teardown compares it literally against `None` and refuses. I reproduced this using the actual validator functions with an in-memory cursor: **dispatch accepts; teardown refuses**. [Dispatch:214](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/scripts/dispatch_v5_small_test_job.py:214), [teardown:189](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/scripts/teardown_v5_small_test_job.py:189).

   **Required:** make migration, dispatch, and teardown accept the same health-probe representation. Keep integrity strictly NULL.

The **P3 follow-ups** are:

- **The “no other table” claim omits a trigger effect.** Changing `depends_on`, `target_floor`, or `target_table` fires migration 596’s trigger, marking existing **v5** `asset_freshness` rows stale across charts. It does not update another asset or launch a build, but the effect exists and the minimal test schema omits it. Correct the scope description and cover the trigger. [596:61–81](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/supabase/migrations/596_nirmana_provenance_receipts.sql:61)
- **Both readback instructions still expect 7,200 seconds.** Executable dispatch/teardown maps agree on **28,800**. Update [registry readback:5](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/scripts/v5_small_test_registry_row_readback.sql:5) and [predispatch readback:7](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/scripts/v5_small_test_predispatch_readback.sql:7).
- **The retained count-conformance expected failure is obsolete.** It still expects a records/contacts counter, although the writer now writes evaluation windows. Replace it with a positive assertion for the correct counter. [Conformance test:66–70](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/scripts/__tests__/ka_gochara_v5_registry_conformance.test.ts:66)

Other requested checks:

| Check | Result |
|---|---|
| Routine application | New migration; no DDL, grants, or public-schema CREATE. One asset-ID-scoped UPDATE, five-second lock timeout. Runner wraps SQL and tracker insertion in one transaction; failure rolls back this migration and stops deployment. Earlier migrations remain committed. [migrate.ts:833](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/scripts/migrate.ts:833) |
| Idempotency/post-checks | Reapplication preserves the desired state. Row-count and landed-value checks reject mismatches in their listed fields. `scope` and unexpected prior values are the gaps above. |
| NULL integrity delta | Correct. Execution has no bind parameters; false/error/no-result fails acceptance after heavy substep commits. NULL/empty skips execution; rebuild-on-probe-fail controls the green shortcut. [asset_runner.py:952](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:952), same file:1166–1208 and 1591–1615. |
| Seed/counter | Seed values agree with the intended migration shape. Counter binds chart `$1`, restricts generation `5.0`, and counts the table actually written by [window_store.py:170](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/python-sidecar/services/gochara_kernel/window_store.py:170). |
| Automatic builds/DAG/cockpit | No migration-induced build path found. Planning, recalibration, DAG scanning, downstream propagation, nightly fresh-chart planning, and cockpit stats filter active rows. No incoming v5 dependency exists in the checked-in graph. Explicit steward dispatch can execute an inactive asset. [runPreparation.ts:179](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-1304x/platform/src/lib/build/runPreparation.ts:179) |
| Timeout | 28,800 fits the integer column; no repository CHECK/validator upper bound found. Runner uses it directly as the asset deadline; deployment declares an 86,400-second task timeout. `417_asset_registry_writer_timeout_seconds.sql:28`; `runner.py:679–705`; `deploy.yml:2227`. |
| Test discrimination | Core activation, integrity-statement, rebuild-policy, dependency and control-row regressions are covered. Wrong prior overwritten values, scope, and real trigger effects are not. The 1243 overlay’s `has_substeps` is hardcoded rather than parsed, although the PostgreSQL happy-path assertion checks it independently. |
| Generated/history changes | No existing migration modified relative to main. Census changes are only source revision, seed fingerprint, and content hash; hashes verified. Family/level payloads are unchanged. Draft regeneration passes, warning that stamp 25 trails census 26. |

**Verification limits:** no database or network access; production row/tracker state, privileges, protected-window completion, and live schedules/configuration remain unverified. PostgreSQL suites were not run. Normal pytest startup was blocked by its temporary-file requirement; isolated N-99 and updated Python seed assertions passed. Vitest dependencies are absent. Files remain unchanged.

