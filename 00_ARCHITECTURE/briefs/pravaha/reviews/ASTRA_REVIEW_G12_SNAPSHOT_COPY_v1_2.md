VERDICT: REJECT

Reviewed **`8e6d9445d9aa3774bddba96ac1a372cd0126011c`**, including the full change and round delta. Several round-2 defects are fixed. Database population validity and the exhaustive read guard remain incomplete.

Database acceptance scenarios below are **source-traced counterexamples**, not executed PostgreSQL results.

1. **P1 — Required levels and subjects can still be absent from L1 and the accepted snapshot.**

   The required-population functions filter existing rows; they never require every declared subject or level to exist. See [1305:187](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:187), [1305:271](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:271), and the equality checks at [1305:335](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:335).

   **Failure:** L1 has no AD rows—or no Vimshottari rows at all—or lacks SUN. Submit every remaining eligible row with correctly computed digests. Both sides of each comparison contain the same incomplete population, so INSERT passes. Unchanged L1 also produces no population drift. A missing upstream period at either horizon edge has the same problem: overlap selection does not establish horizon coverage.

   The Python population checker also returned `[]` in my in-memory checks for MD-only, empty-system, and horizon-gap populations. It needs explicit required-member and coverage assertions, enforced in the database at capture and drift.

2. **P1 — Submitting both duplicate natural-key rows defeats the conflict check.**

   The database aggregates all eligible rows and compares their digest; it has no natural-key uniqueness predicate. See [1305:161](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:161), [1305:273](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:273), and [1305:335](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:335).

   **Failure:** two SUN facts—or two eligible AD rows from different builds—share the snapshot’s natural key. Submit both IDs and their correct digest. Copy and required population agree, so the duplicate is accepted. Even identical-content duplicates violate uniqueness without introducing ordering ambiguity.

   The existing conflict test inserts an extra row but resubmits the **old IDs**, testing omission rather than acceptance of both duplicates: [test_g12_snapshot_copy.py:199](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:199).

   Findings 1–2 establish snapshot INSERT/drift gaps, not a demonstrated bypass of every downstream seal check.

3. **P2 — Deletion plus another boundary change still becomes a false move.**

   Movement matching checks ordinal, level, system and ayanamsha, but does not establish that the candidate represents the same period: [staleness.py:135](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/services/gochara_kernel/staleness.py:135).

   **Reproduced:** stored Venus MD starts in 2000, ordinal 1; Sun MD starts in 2020, ordinal 2. Delete Venus and shift Sun’s start to 2021. Sun becomes ordinal 1 and is unmatched by natural key. `_changes` reports **Venus moved to 2021**, then **Sun missing**.

   The original deletion-only case is fixed. Ambiguous correspondence must remain missing/extra instead of asserting movement.

4. **P2 — The no-live-read guard is still not exhaustive.**

   The runtime test explicitly excludes P3/P4 windows and verification, and covers only marriage: [test_g12_snapshot_copy.py:576](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:576). The AST check examines calls in the writer alone; the SQL grep retains whole-file exemptions: [test_g12_snapshot_copy.py:403](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:403).

   **Counterexample checked in memory:** add a P3-only `fetch_chart_context(conn, chart_id)` call inside `window_verifier.verify_member_geometry`. The static guard still passes, and the runtime guard excludes that window path.

   Exercise the complete computational boundary with live L1 reads forbidden, including populated window and verification paths.

5. **P3 — Mutation results can mistake infrastructure failure for detection.**

   [mutation_check_1305.py:98–102](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/scripts/gochara/mutation_check_1305.py:98) classifies every nonzero pytest exit as `CAUGHT`.

   **Failure:** collection failure or unavailable required PostgreSQL makes a surviving mutation appear detected. Require a passing baseline and distinguish assertion failures from infrastructure/collection failures.

| Round-2 item | Round-3 assessment |
|---|---|
| Independent database population scope | **Partly.** Fixed selectors catch omissions from populated L1; findings 1–2 remain. |
| Database-produced authentic copy | **Resolved.** Submitted copies and metadata digests are overwritten from database rows: [1305:328–344](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:328). |
| Copy-based computation and exhaustive guard | **Partly.** Copy-bearing readers use stored inputs, including separate copy-only P1 SQL; finding 4 remains. Legacy/missing-copy fallbacks remain explicit. |
| Exact Decimal comparison | **Resolved.** Both guards compare against the original Decimal. The previously accepted precise value now refuses: [targets.py:88](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/services/gochara_kernel/targets.py:88), [inventory_verifier.py:175](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:175). |
| Additional fact crashes reporting | **Resolved.** In-memory reproduction now returns `extra_live`; movement handling is dasha-only: [staleness.py:133–155](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/services/gochara_kernel/staleness.py:133). |
| Tier-only dasha change becomes hard drift | **Resolved in source.** Consumed natural keys are matched independently of current tier: [1305:289–295](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:289). |
| Hard-first details, truncation and movement | **Partly.** Ordering/truncation remain correct; deletion-only matching is fixed; finding 3 remains. |
| SQL first-seal requirement; sealed replay | **Resolved in source.** [1305:403–407](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:403) is reached through the SQL first-seal branch. The separate integrity-only replay branch remains unchanged. |
| Generated pins | **Resolved.** Recomputed implementation lock, v5/v4 writer digests, census source fingerprint and census content hash all match. |

Other requested checks:

- With required rows present in L1, omitting an entire level/system/subject or either overlapping edge period changes the required-population digest and refuses. Foreign-ayanamsha/system rows introduce different keys; foreign-chart IDs fail the chart-scoped lookup. These were source-traced.
- The new legacy test makes an actual SQL seal attempt and expects `input_snapshot_without_copy`: [test_g12_snapshot_copy.py:621](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:621). Existing successful seal/replay tests now inherit a 1305-enabled fixture: [test_a53_r11_seal_brief.py:323](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12c/platform/python-sidecar/tests/l3/gochara/test_a53_r11_seal_brief.py:323). A chronological **sealed legacy snapshot → apply 1305 → replay** test is still absent.
- **1305 remains additive.** No prior migration changed. Completeness equals the 1232 body outside the declared replacement block; Moon-domain edits are confined to its input source. Preflight refuses missing prerequisites, reapplication, unexpected function definitions and G8-first ordering. Actual PostgreSQL definition hashes and role privileges remain unverified. Migration 1306 is absent, so forward stacking is unproved.

I executed four source/pure test functions, targeted in-memory reproductions, syntax parsing of 19 changed Python files, digest checks and `git diff --check`. **I did not run databases, migrations, database tests, the mutation suite, restricted-role/concurrency execution, full builds, seals/replays, or network checks. No files were modified.**

