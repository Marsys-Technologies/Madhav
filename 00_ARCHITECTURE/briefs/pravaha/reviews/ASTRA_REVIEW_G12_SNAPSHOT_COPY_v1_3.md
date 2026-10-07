VERDICT: REJECT

Reviewed `8168723071fe1bc1e6b198e9d3b1a7023ef3244a`, including the full requested diff and G12 round delta. Database acceptance scenarios below are **source-traced**, not executed PostgreSQL results.

1. **P1 — Inconsistent parent/child periods can still produce an accepted snapshot.**

   The new validator checks each level independently; it never checks parent existence, parent level, containment, or parent chart/system/ayanamsha. See [1305.sql:323](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:323).

   **Failure:** within horizon `[Jan 1, Jan 20)`, provide MDs `[Jan 1, Jan 10)` and `[Jan 10, Jan 20)`, but one AD `[Jan 1, Jan 20)` pointing to the first MD, plus an orphan PD covering the horizon. Every level tiles the horizon without duplicates, gaps, or overlaps. Submitting all eligible IDs with their correct digests satisfies the capture checks at [1305.sql:366](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:366).

   I reproduced `[]` from the Python checker for this inconsistent hierarchy. It likewise validates levels independently: [inventory_verifier.py:776](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:776). A foreign-ayanamsha parent can also enter the copied ancestry because the parent lookup checks only chart and row ID: [1305.sql:248](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:248).

2. **P2 — Tier-only metadata changes now incorrectly close the completeness gate.**

   The required-scope validator filters on `two_pass_verified` at [1305.sql:329](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:329), and the drift branch invokes it at [1305.sql:463](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:463).

   **Failure:** after capture, relabel all AD rows from `two_pass_verified` to `single`, changing no computational values. Completeness returns `input_snapshot_required_scope / required_level_missing`, closing the gate, while staleness reports metadata-only drift.

   The regression test misses this because `_drift_violations` filters exclusively for `input_snapshot_drift`: [test_g12_snapshot_copy.py:89](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:89), [test_g12_snapshot_copy.py:627](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:627). This reintroduces the previously resolved metadata-only refusal under a different violation name.

3. **P2 — Matching lord plus ordinal still permits ambiguous false moves.**

   Movement matching ignores the parent identity and full lord path: [staleness.py:137](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/python-sidecar/services/gochara_kernel/staleness.py:137).

   **Reproduced:** stored Venus AD under Venus MD has ordinal `1.1`; another Venus AD under Sun MD has ordinal `2.9`. Delete the first MD tree and the earlier ADs under Sun, then shift the surviving Venus AD’s start by one day. It becomes ordinal `1.1`.

   `_changes` reports the deleted **Venus/Venus period moved to the Sun/Venus period**, then reports the original Sun/Venus period missing. The differing ancestry is already available in the copies. This correspondence must remain missing/extra under ruling 3.

4. **P2 — The expanded no-live-read test still does not cover the complete boundary.**

   The new test invokes P1–P4 windows and the verification job, but its fixture places Jupiter’s P4 interval in December while Saturn’s is January–February: [test_a53_verification_job.py:124](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/python-sidecar/tests/l3/gochara/test_a53_verification_job.py:124). Therefore P4 has no joint window; the sweep requires intersecting Jupiter/Saturn support: [window_sweep.py:791](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/python-sidecar/services/gochara_kernel/window_sweep.py:791).

   **Failure:** a live-reader helper called only while processing a populated P4 window remains unexercised. There is no assertion that these guarded paths contain populated windows.

   Additionally, the connection guard converts every non-string/non-bytes query to `""`: [test_a53_verification_job.py:432](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/python-sidecar/tests/l3/gochara/test_a53_verification_job.py:432). I reproduced a `psycopg.sql.SQL(...).format(sql.Identifier("public", "chart_facts"))` query reaching the wrapped driver with `seen == []`. The guard must inspect composed queries too.

5. **P3 — The mutation harness still counts runtime infrastructure errors as caught mutations.**

   A passing baseline is now required, but `classify` accepts any exit-1 run containing a `FAILED` line; it does not inspect the exception: [mutation_check_1305.py:97](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12d/platform/scripts/gochara/mutation_check_1305.py:97).

   **Reproduced:** `FAILED … - psycopg.OperationalError: connection lost` returns `CAUGHT`. So do `PermissionError` and `TypeError`. A database failure during the test body is classified differently from the same failure during fixture setup, despite neither proving assertion-based detection.

   Use structured test reports that distinguish assertion failures, other call-phase exceptions, setup failures, and collection failures.

| Steward ruling | Round-4 assessment |
|---|---|
| 1. Required members and coverage at capture/drift | **Partly.** Explicit assertions now exist at both hooks; the drift invocation introduces finding 2. |
| 2. Required-population natural-key uniqueness | **Resolved in source.** Both fact and dasha duplicates are explicitly rejected, including submission of both duplicate IDs. |
| 3. Ambiguous correspondence stays missing/extra | **Partly.** The original different-lord example is fixed; finding 3 remains. |
| 4. Complete computational boundary with connection-level failures | **Partly.** Verification and additional window paths were added; finding 4 remains. |
| 5. Green baseline and assertion/infrastructure distinction | **Partly.** Baseline, collection, and setup handling improved; finding 5 remains. |

Other requested checks:

- **Half-open coverage:** the SQL selects periods with `start < horizon_end` and `end > horizon_start`. Its strict gap/overlap comparisons permit exact adjacency and periods extending beyond either horizon edge. My pure checks accepted those legitimate shapes and rejected gaps, overlaps, duplicates, and missing edges at all three levels.
- **Missing and foreign rows:** direct missing-subject/level cases now have named refusals. Omitting eligible rows, or submitting another chart/system/ayanamsha’s rows, fails lookup or required-population equality in source. The ancestry exception is finding 1.
- **Database-produced copy:** submitted content and metadata digests are still overwritten from database rows; identity digests are checked.
- **Migration:** 1305 remains additive; no prior migration changed in the full diff. Completeness is byte-identical to 1232 outside the declared replacement block. Moon-domain changes are confined to its input source. Preconditions, definition pins, reapplication refusal, G8-first refusal, and protected-runner wiring remain present.
- **Pins:** independently recomputed implementation stages/lock, v5 and v4 writer digests, census writer fingerprint, and census content hash all match.

I executed four existing pure/static test functions, targeted in-memory counterexamples, coverage checks, syntax parsing of 19 changed Python files, digest checks, and `git diff --check`.

**Not verified:** PostgreSQL execution or actual INSERT outcomes; migrations, privileges, concurrency, full computational tests, mutation baseline/suite, Vitest, sealing/replay execution, production function hashes, or forward stacking with 1306, which is absent. No database or network access occurred. No files were modified.

