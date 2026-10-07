VERDICT: REJECT

Reviewed the full change through `e6eb7ff890ff096c296ab432c63f40c840904287`, the delta from `41286d76b`, and `.PRIOR_REVIEW.md`. Findings 1–4 block merge. Finding 5 can be a follow-up.

1. **P1 — Capture validates the upstream hierarchy, but can store a different, broken hierarchy.**

   [1305_gochara_snapshot_owns_l1_copy.sql:409](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:409) validates the eligible upstream population before constructing the submitted copy. Lines 417–424 subsequently compare **content digests**, which exclude row IDs, parent IDs, build and tier ([same file:239](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:239)).

   Concrete counterexample:

   - Valid verified rows are `M → A → P`.
   - Add `M2`, an identical MD interval/lord under another build, with tier `single`. Its natural key, content and ordinal path equal M’s; ordinal counting is partitioned by build.
   - Submit `[M2, A, P]` with correctly recomputed digests.
   - Required-scope validation examines `[M, A, P]` and succeeds. Content equality also succeeds. The stored copy contains A’s `parent_row_id=M`, although M is absent, and includes an ineligible M2.

   The production uniqueness index permits the alternative build. The ordinary writer’s mixed-build check and the later Python checker would reject this arrangement; **this is an INSERT-boundary defect, not a demonstrated false seal**. The database must validate eligibility and parent closure of the actual submitted copy. There is no regression test for this substitution.

2. **P2 — Required scope and drift still depend on verification tier.**

   The extra-row branches retain `verification_pass_status = 'two_pass_verified'` in [1305_gochara_snapshot_owns_l1_copy.sql:303](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:303) and [line 339](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:339).

   After a valid capture, insert an overlapping, parentless AD at a new natural key, tier `single`, with other captured rows unchanged. It is invisible to required-scope validation and content drift. Relabel **only that extra row’s tier** to `two_pass_verified`: it becomes visible and closes the gate.

   [test_g12_snapshot_copy.py:664](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:664) explicitly expects the first arrangement to remain clean. Thus the suite preserves behavior contrary to ruling 2. Relabeling already-copied MD/AD rows is fixed, but tier independence of the complete required scope is not.

3. **P2 — Infrastructure exceptions can still count as caught mutations.**

   [test_g12_snapshot_copy.py:89](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:89) catches **every `Exception`** and converts it into `pytest.fail("the code read live L1…")`. [mutation_check_1305.py:127](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/scripts/gochara/mutation_check_1305.py:127) classifies `Failed:` as `CAUGHT`.

   I exercised the actual helper in memory with `psycopg.OperationalError`, `PermissionError` and `TypeError`. All become assertion-shaped failures that the classifier accepts. A connection failure during a mutant run can therefore receive credit for detecting a live read.

   Structured JUnit classification and the passing-baseline requirement are improvements, but this wrapper defeats the classification. Restrict conversion to an explicitly identified forbidden-read failure; propagate unrelated exceptions.

4. **P2 — The no-live-read test still permits empty guarded paths.**

   [test_a53_verification_job.py:503](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_a53_verification_job.py:503) guards P1–P4, but [line 516](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_a53_verification_job.py:516) asserts populated windows only for P3/P4.

   If P1 or P2 yields zero windows, the test can pass without exercising its populated-window behavior. Assert positive counts for every guarded path to satisfy ruling 4. The joint Jupiter/Saturn fixture and composed-query inspection themselves are corrected.

5. **P3 — The chronological legacy replay regression test was removed. Follow-up.**

   The round delta deletes `test_chronological_a_generation_sealed_with_a_legacy_snapshot_then_1305_applied_replays_and_a_first_seal_is_refused`.

   Its remaining substitute, [test_g12_snapshot_copy.py:813](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py:813), disables protections and manufactures a legacy-shaped snapshot. It checks first-seal refusal and absence of a particular replay violation, but never successfully seals before migration and replays afterward. Restore that chronological coverage; this omission alone need not block merge.

The round-4 findings stand as follows:

| Round-4 finding | Round-5 assessment |
|---|---|
| Missing hierarchy enforcement | **Partly resolved.** SQL now checks parent presence, level and containment at migration lines 380–385; Python does likewise at `inventory_verifier.py:795–804`. Actual-copy substitution remains open: finding 1. |
| Tier relabel closes completeness | **Partly resolved.** `test_g12_snapshot_copy.py:345` now compares all violations and checks soft staleness. New-key rows remain tier-dependent: finding 2. |
| False movement across different ancestors | **Resolved in source and pure testing.** `staleness.py:137–141` requires full ordinal and lord paths. The positive/negative regression at G12 line 358 passed. |
| Empty joint window / composed queries bypass guard | **Partly resolved.** Joint spans overlap; composed SQL is rendered and inspected. I independently exercised both connection/cursor guard paths without connecting. P1/P2 population assertions remain absent. |
| Infrastructure errors counted as caught | **Partly resolved.** Raw JUnit exceptions are distinguished and baseline success is required, but the new wrapper converts unrelated exceptions into catches: finding 3. |

I reconstructed the snapshot-shape inventory from [test_g12_snapshot_copy.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_g12_snapshot_copy.py). The line numbers below identify the tests; database cases were inspected, **not executed**.

| Shape tried | Test line(s) and assessment |
|---|---|
| False supplied fact value, dasha lord, tier or metadata digest | **167:** overwritten with database-produced values; correctly **not an INSERT refusal**. |
| False identity digest | **183:** named refusal. |
| One consumed period omitted, with a correct subset digest | **190:** completeness refusal. Despite its name, this test does not also omit a fact. |
| Entire AD level omitted from submitted copy | **630:** completeness refusal. |
| SUN omitted from submitted copy | **675:** completeness refusal. |
| Upstream SUN absent | **259/275:** named capture refusal; **387:** named post-capture violation. |
| Upstream AD absent / entire required system absent | **259/273–274:** named level refusal. |
| Period absent at either horizon edge | **259/277–279:** SQL PD cases; **836/854–855:** Python AD cases. |
| Internal gap | **380:** SQL PD case; **836/853:** Python AD case. |
| Overlap at distinct starts | **836/856:** Python case. **No isolated SQL refusal test.** Line 249 duplicates a natural key and permits duplicate refusal instead. |
| Duplicate natural-key facts or dashas, both submitted | **232:** named duplicate refusals. |
| Conflicting extra period while old IDs are resubmitted | **249:** refusal; despite its name, no corresponding extra-fact capture case occurs there. |
| Orphan child / child pointing two levels up | **291–303:** SQL PD cases; **836/859–860:** Python equivalents. **No explicit orphan-AD case.** |
| Child outside parent / AD spanning two MDs | **294, 335, 862–863:** containment cases. |
| Parent of another ayanamsha or system | **295–296:** SQL cases, but either missing-level or missing-parent refusal is accepted. **313:** copied ancestry checks ayanamsha only, despite the test name mentioning system. |
| Foreign-chart input IDs | **318:** fact and dasha IDs refused. **No isolated foreign-chart parent-pointer test with otherwise complete in-chart levels.** |
| Missing source ID / omitted key arrays | **406:** missing fact ID; **413:** omitted arrays. **No separate missing-dasha-ID test.** |
| Another-tier second build at capture | **395:** refused by the **writer’s** mixed-build check, not a direct database capture test. |
| Parent replaced by identical-interval row, children retaining old parent ID | **No test.** Finding 1 constructs the database acceptance path. |
| Post-capture tier relabel | **345, 727:** soft metadata behavior; extra-row counterexample remains open. |
| Value change | **503, 515, 546:** hard drift for dasha end, natal longitude and precision-sensitive numeric changes. |
| ID/build/engine-only replacement | **449, 703:** soft metadata behavior, with parent references rewired. |
| Genuine movement / deletion mistaken for movement | **358, 534, 737, 755, 772:** positive and negative movement cases. |
| Legacy snapshot offered for first seal | **605, 813:** application/database refusals. Chronological upgrade-and-replay coverage is absent. |

The foreign-system/ayanamsha capture tests are not fully discriminating: changing the only MD to another scope already triggers the pre-existing missing-level check. Add cases retaining a valid in-scope MD while pointing a child to the foreign parent, and require `required_parent_missing`.

For legitimate shapes, I found no new refusal of a period starting before the horizon, exact adjacency, or a child ending exactly at its parent’s end. SQL uses strict gap/overlap comparisons and inclusive containment; the base fixture already contains these boundaries at [test_a53_inventory.py:54](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_a53_inventory.py:54). Additional in-memory Python cases accepted them and rejected missing levels, gaps, overlaps, duplicates and broken hierarchy across all three levels.

The filler lord is a fixture repair at [test_a53_p1_support.py:78](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/tests/l3/gochara/test_a53_p1_support.py:78), not a production requirement for Ketu. The production writer creates MD/AD/PD rows with parent IDs at [ga_dashas_writer.py:1361](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12e/platform/python-sidecar/ga_writers/ga_dashas_writer.py:1361). Persisted real L1 conformity remains unverified.

The migration and provenance checks otherwise hold at source level:

- Only new migration 1305 changes in the full diff; no older migration is edited. Four nullable columns, a `NOT VALID` constraint and an INSERT trigger preserve existing rows.
- Preflight checks reject reapplication, missing prerequisites, changed predecessor functions and G8-first ordering. Protected deployment selection includes 1305.
- The completeness replacement equals the 1232 body with its declared block replaced. The Moon replacement differs only in the copy lookup and associated field projections.
- Existing chart/seal guards remain present. Migration timeouts and transaction ownership are retained.
- All implementation stage/aggregate locks, both affected writer digests and census fingerprints recomputed correctly. Twenty changed Python files parsed; `git diff --check` passed.

I did **not** use a database or network, modify files, run the integration/mutation suites, verify their passing baseline, inspect the PR body, reproduce PostgreSQL function-definition hashes, test concurrent locking, verify deployed migration state, or inspect real production L1 rows. The database counterexamples above are source-traced; seven existing pure/static test functions and the additional in-memory probes were executed.