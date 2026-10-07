VERDICT: ACCEPT_WITH_AMENDMENTS

Reviewed HEAD `d7490997b9202f31c9e8593a899a516e3c95ba12` against both requested bases. **No outstanding P1/P2 production defect found under the approved whole-build replay contract.** The amendments concern CI protection and incomplete regression coverage.

**A. Round-1 findings**

| Finding | Disposition | Evidence and remaining limits |
|---|---|---|
| **P1 — Reset depended on nonexistent resume** | **Resolved by the steward-approved contract revision.** | The [writer comment:503](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:503) explicitly promises whole-build replay. The [production call:1179](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/pipeline/orchestrator/asset_runner.py:1179) supplies no completed keys. The [new test:389](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py:389) calls the real driver, confirms earlier commits survive the first failure, then retries and compares with a fresh build. It exercises a subset plan. |
| **P2 — No populated-chain replacement test** | **Resolved for the requested deletion/rollback scenario.** | The [populated fixture:116](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain_populated.py:116) asserts every listed chain table is populated. Lines 129–179 exercise builder-role deletion, preservation and reconstruction; lines 183–195 inject failure after deletion and check rollback. Row comparisons now include record/window contents, beyond counts. |
| **P3 — Certification cannot replace the reset guarantee** | **Partly resolved; verifier limitation remains.** | The [test:562](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py:562) still demonstrates that an out-of-horizon stale end passes clipped certification. Whole-build reset prevents this on the supported path; the new guard also rejects continuation against a differently bounded manifest. Certification itself has not become a detector for this corruption. |

**B–C. Horizon guard and candidate-only deletion**

The dispatch routing is correct:

| `run_substep` phase | Horizon guard? | Reason |
|---|---|---|
| `rules` | No | Shared registry setup. |
| `convention` | No | Shared convention setup. |
| `body:<Body>` | No | Shared, full-domain sky substrate. |
| `manifest` | No | Establishes the requested horizon. |
| `snapshot` | Yes | `_verify_live_inputs`. |
| `inventory:<class>` | Yes | `_verify_live_inputs`. |
| `coverage:<class>` | Yes | `_verify_live_inputs`. |
| `record:<class>:<path>` | Yes | `_verify_live_inputs`. |
| `window:<class>:<path>` | Yes | `_verify_live_inputs`. |
| `verify:<class>` | Yes | `_verify_live_inputs`; this phase reports verification without persisting verifier attestations. |

The routing is in [ka_gochara_v5.py:402–441](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:402). The guard runs before the downstream phase.

**A legitimate full-plan rebuild at a new horizon is not wrongly refused.** The [plan:344](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:344) places `manifest` before `snapshot`. The manifest calls `publish_candidate`, which [inserts a first candidate or updates the existing candidate’s horizon:527–556](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/services/gochara_kernel/ledger.py:527). Snapshot therefore reads the **new** horizon.

For a first-ever build, that insert also satisfies the new candidate-only check. A direct snapshot invocation without a manifest fails at [the manifest-vector lookup:210](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/pipeline/orchestrator/writers/ka_gochara_v5.py:210); direct deletion without one fails in [ledger.py:263](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/services/gochara_kernel/ledger.py:263). Those refusals do not obstruct the full plan.

The [delete preconditions:581](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/services/gochara_kernel/record_store.py:581) are correctly ordered: sealed check, candidate check, then deletes.

**D. Data safety**

I found no new cross-generation deletion, transaction-ownership violation, or legitimate-build blockage. Deletes retain both scope columns and preserve Moon coverage. The sealed probe [takes the chart transaction lock before reading the seal:1004](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/migrations/1153_gochara_sky_event_substrate.sql:1004); sealing takes the same lock.

Replacement remains atomic **within the snapshot substep**. Failure after its commit leaves an incomplete unsealed candidate, which the next dispatch rebuilds from zero.

**E. P3 amendment — The CI guard protects the job, but not its suite membership.**

The new job is self-contained by source inspection: its own PostgreSQL service, dependency installation, checksum-pinned corpus, and required-database/ephemeris flags. Both files are absent from the [serial database command:424](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/.github/workflows/ci.yml:424) and present in the [new command:1188](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/.github/workflows/ci.yml:1188).

However, [test_ci_changes.py:247](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/scripts/governance/__tests__/test_ci_changes.py:247) checks only job existence, dependencies and its condition.

**Concrete failure scenario:** removing `test_a55_replace_chain_populated.py` from that command silently removes its required database execution. I made that mutation **in memory**; all guards consuming the jobs map still passed. General test discovery can subsequently skip its database fixture.

**Amendment:** assert both suite paths occur in a mandatory database-enabled command, with neither excluded nor softened by `continue-on-error`.

**F. Test discrimination and remaining round-1 coverage**

- **Replacement:** extension, narrowing, orphan and populated-reset tests meaningfully distinguish missing replacement. The populated test explicitly requires old rows to disappear.
- **Horizon:** [the six-phase test:477](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py:477) requires `HorizonMismatch` for longer and shorter horizons. Fresh/rebuild scenarios retain the manifest-first positive path.
- **Replay:** the real-driver test is useful integration coverage, but same-horizon retry equality alone does not prove generation reset occurred; it could pass without that reset. The deletion tests supply that discrimination.
- **NULL transitions:** resolved at comparison-helper level for all five nullable columns, in both directions.
- **Point contacts:** partly resolved. The [conflict test:444](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py:444) directly exercises `_insert_contact_row`; it requires exact conjunction coverage but only requires truncated **residence** coverage.
- **Every compared field:** still incomplete. [Lines 123–161](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g7b/platform/python-sidecar/tests/l3/gochara/test_a55_replace_chain.py:123) do not independently mutate all 13 columns.
- **Concurrent sealing:** still missing a replacement-versus-sealer integration test. The lock argument remains sound by inspection.

A second **P3 amendment** is to complete those comparison/public-insertion tests. For example, accidentally bypassing the comparator in `insert_point_contact` would not be caught by tests calling the private helper directly. The populated survivor fixture also protects only one other-generation contact and coverage row, rather than a complete second-generation chain.

**Verification:** 76 database-free tests passed: 12 new unit cases, 41 existing driver/serializer tests, and 23 CI-wiring checks. Implementation-lock and writer-digest checks, census hashes, golden transport checks, and `git diff --check` passed.

**Not verified:** database execution, old-versus-new database mutation runs, live concurrency, full real-ephemeris builds, deployed privileges/migrations, CI execution, or branch-protection requirements. Unrelated merged-main changes were excluded. No database/network operations or file modifications were performed.