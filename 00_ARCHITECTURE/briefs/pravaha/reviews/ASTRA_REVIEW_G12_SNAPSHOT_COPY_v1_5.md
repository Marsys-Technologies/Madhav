VERDICT: REJECT

**Not mergeable yet. One P2 defect still permits an invalid hierarchy to become an accepted snapshot.** The round-5 substitution and tier-dependent drift defects are fixed, but R1’s hierarchy class is not fully closed.

Reviewed HEAD `f2af2124dcb733798e0eeb7ec5d9b733532ef360`, both requested diffs, and all three review/ruling files. Database conclusions below are source-traced; no database or network was used.

**Blocking finding**

**P2 — A mahadasha pointing to a foreign parent passes both validators.** Locations: [1305:263](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12R6x/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:263), [1305:399](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12R6x/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:399), [inventory_verifier.py:903](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12R6x/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:903).

Concrete scenario:

1. Start with a complete, eligible, single-build `M → A → P` population.
2. Give `M.parent_row_id` an existing parent belonging to another chart, ayanamsha, or system. The upstream single-column parent FK permits this.
3. Capture all required rows with correctly computed digests.

The ancestry joins exclude that parent. Consequently, M’s copied natural parent fields are NULL and its lord path remains its own lord, while metadata retains the foreign `parent_row_id`. SQL checks parent closure only for levels 2–3; its level-1 check checks only the lord path. Python does the same.

**Executed evidence:** the Python copy contract returned no violations. Its independently derived live population also returned no violations, and every field compared between copy and live matched. The capture trigger’s SQL predicates admit the same case. Recomputed digests therefore do not rescue this through R7.

Require level-1 `parent_row_id`, `parent_level_n`, and `parent_start_iso` to be NULL in both contracts. Add root-parent cases for foreign chart/system/ayanamsha, alongside a valid parentless-root control.

**Ruling-by-ruling assessment**

Here, `1305` denotes `platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql`; test references denote the files under `platform/python-sidecar/tests/l3/gochara/`. “Done” describes the implementation and inspected tests, not an executed database result.

| Ruling | Status | File:line and assessment | Class closure |
|---|---|---|---|
| **R1** | **Partly** | `1305:461,468` builds into `NEW` and validates those exact copies. `test_g12_snapshot_copy.py:1205,1227,1250` covers substitution, another-tier direct insertion, and mixed builds. My substitution probe reported tier, mixed-build and parent-ID violations. | Validate/store separation is closed; hierarchy closure remains open through the root-parent finding. |
| **R2** | **Done** | `1305:288,375,528`; tests `:768,794,807`. Live scope includes every tier; live structural validation disables eligibility. My new-key orphan-AD probe reported overlap and missing parent, unchanged after relabelling. | Tier-dependent inclusion class closed for copy-bearing snapshots. |
| **R3** | **Done** | `1305:257,261`; `staleness.py:147`; test `:1305`; design note’s identity/digest sections updated. Ordinal is metadata and movement matching reads it there. | Outside-horizon sibling changes cannot alter content identity. |
| **R4** | **Done** | Tests `:91,107,1426`. Only identified forbidden-live-read failures become `pytest.fail`; unrelated exceptions propagate. | Previous exception-laundering class closed in this helper. Harness evidence limitations remain below. |
| **R5** | **Done** | `test_a53_verification_job.py:553` requires exactly P1–P4 and a positive count for each. | Empty-path loophole closed for all four guarded paths. |
| **R6** | **Done** | G12 tests `:1474` restore seal-before-migration/replay chronology; `:977` separately attempts and refuses a real first seal. | Requested regression covered. Chronological fixture is pre-1240 and does not establish every populated legacy behaviour. |
| **R7** | **Done** | `1305:508` recomputes both content digests, both metadata digests and input digest; `staleness.py:80,102` ties `self_contained` to consistency. Tests `:1362` cover six tampering cases. | Digest-consistency class closed. A semantically invalid copy accepted by both contracts remains R1’s separate defect. |
| **R8** | **Done** | `1305:407,468`; tests `:240,728,831`. Differences identify natural keys and available row/build/tier details. | Generic unnamed scope-difference refusals addressed across facts and periods. |
| **R9** | **Done** | `1305:445,461`; test `:1283`. Four STABLE readers execute in one SELECT; subsequent capture checks use those JSON values. READ COMMITTED/per-chart-lock assumption documented. | Cross-statement capture inconsistency addressed structurally; concurrent execution unverified. |
| **R10** | **Done** | `1305:135`; test `:1405`. Ordering uses the complete line in C collation. | Duplicate-key ordering ambiguity closed. |
| **R11** | **Done** | `test_a53_inventory.py:276` declares NUMERIC; precision test `test_g12_snapshot_copy.py:642` no longer needs ALTER. | Stub precision mismatch closed. |
| **R12** | **Done** | `1305:7` correctly describes stable UUID5 identities and build/engine changes. | Stale rationale corrected. |
| **R13** | **Done for the requested inventory** | G12 tests `:386,494,1205,1521,1532` add discriminating foreign-parent, missing-dasha-ID, substitution, distinct-start overlap and KP cases. | Previously listed cases covered; universal hierarchy coverage is disproved by the new root-parent case. |

**Additional findings that can follow**

These do not provide another route to an invalid snapshot through ordinary database capture.

- **P3 — Two mutation descriptions overstate what they disable.** [mutation_check_1305.py:101](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12R6x/platform/scripts/gochara/mutation_check_1305.py:101) changes `input_snapshot_without_copy` into another violation; it still refuses. The next mutation renames the G8 refusal; it also still refuses. These measure diagnostic-name assertions, not removal of those gates. There are **47 entries with present targets**, but “47/47” would not demonstrate 47 disabled safeguards being caught. The harness honestly discloses the surviving writer-call mutation and requires a passing baseline. I did not run it.

- **P3 — Malformed-input parity is narrower than the headline.** [inventory_verifier.py:845](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12R6x/platform/python-sidecar/services/gochara_kernel/inventory_verifier.py:845) converts `level_n=1.5` to integer 1. My modified valid-copy probe returned no Python violations. SQL at `1305:337` casts textual `1.5` to integer and would error. The database copy builder cannot produce this from its integer column, so this is defensive checker/type-contract hardening rather than another capture bypass.

- **P3 — Legacy Moon lookup becomes stricter on missing IDs.** [1305:556](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-g12R6x/platform/migrations/1305_gochara_snapshot_owns_l1_copy.sql:556) uses `dasha_copy` for legacy fallback. If an unrelated consumed non-Moon row disappears, `dasha_copy` raises at line 275; the old join simply omitted missing rows. Thus “legacy behaviour unchanged” is too broad. This changes diagnostics for an already-drifted legacy snapshot; it does not reopen first sealing or change the inspected seal-replay short circuit.

**Parity and test quality**

The 58-shape test is a **real differential test**, not a computation using one shared SQL oracle: SQL and Python independently produce violation-code multisets, which `_contract_codes` compares at `test_g12_snapshot_copy.py:120`. The cases also carry hand-written expected codes.

Its limitations matter:

- Both implementations share the root-parent omission. Agreement cannot establish that the contract is complete.
- Invalid cases assert an expected **subset** of codes, so mutually spurious additional codes can escape those expectations.
- The digest readback test uses the production digest helper on both sides. It establishes stored-value consistency, not an independent digest specification. The full-line permutation test supplies additional ordering evidence.
- R1’s named parent-ID/tier assertions, R2’s extra-row/relabel test, R3’s outside-horizon test, R7’s tampering tests and R10’s permutations are discriminating: removing their respective fixes would break the inspected assertions.
- R5’s positive-count assertion closes the former vacuous test; static grep/string tests supplement, rather than replace, the guarded computational tests.

There is also an intentional policy difference outside the pure contract: Python’s capture-time path additionally checks the frozen canonical build and mixed builds across the wider upstream population (`inventory_verifier.py:1012`). SQL’s new copy contract checks the captured population’s one-build condition. The design documents this distinction; the 58-shape parity test does not cover it.

**Legitimate upstream shapes**

The actual writer resolves the author’s two refusal concerns:

- **Another tier can occur in real output.** `ga_dashas_writer.py:981,990` stamps individual rows `divergent_flagged` or the independent comparison’s verdict; lines 3449 onward preserve those verdicts. An in-scope non-verified row can therefore stop capture. That is the required eligibility refusal, not a demonstrated wrongful refusal.
- **A NULL build is not ordinary writer output.** `ga_dashas_writer.py:3307` supplies a UUID when omitted, and the production schema declares `build_id NOT NULL`.
- **A mahadasha with a parent is not ordinary writer output.** `ga_dashas_writer.py:1361` creates it parentless; the later UUID stabilisation rewires existing parent relationships.

I found no new wrongful refusal of healthy writer shapes such as exact adjacency, horizon-crossing periods, boundary-equal containment, or separate `vimshottari_kp` rows.

**Performance, grants and migration safety**

The equality change at `1305:236,243` is **semantically preserved for production-valid rows**: only ayanamsha/system comparisons changed, and both columns are NOT NULL. Nullable parent/build comparisons retain `IS NOT DISTINCT FROM`; KP retains its coalescing rule. Equality would differ for NULL ayanamsha/system values in the permissive stub, but those are outside the production schema.

The change permits use of the natural-key index prefix `(chart_id, ayanamsha_id, system_id, level_n, start_iso, …)` defined in `414_chart_dashas_kp_sublevel_unique_key.sql:42`. It does **not** make all work linear:

- Ordinal generation still counts preceding siblings separately for each row/ancestor.
- The copy hierarchy join operates on JSON-derived rows.
- Difference naming at `1305:424` performs four correlated scans per differing key.

These can be quadratic in the selected population. Scope/index prefixes avoid treating all 530k rows as siblings, but **production-size performance remains unverified** without plans and timing.

The added `ka_gochara_search_input_digest` EXECUTE grant at `1305:799` is justified and least privilege for this call chain. It is an immutable, invoker-rights calculation required by the new consistency detector; it grants no writes or elevated identity. This follows the helper-grant pattern in 1206, 1220 and 1240.

Migration safety otherwise holds at source level:

- Only new migration 1305 changes; no applied migration is edited.
- Four nullable columns and a NOT VALID constraint avoid backfill and existing-row validation scans.
- Prerequisite, reapplication, predecessor-body and G8-order gates remain fail-closed.
- The completeness replacement is byte-identical to 1232 outside the declared block. Moon changes are confined to lookup/projections, with the legacy diagnostic difference noted above.
- Implementation stage/aggregate locks, both affected writer digests, and changed census hashes recomputed correctly.
- PostgreSQL function-definition SHA pins are consistent across source and tests; their actual PostgreSQL values were not reproduced here.

**Verification performed and limits**

Executed: **7/7 existing pure/static test functions**, **58/58 authored shapes through Python** reaching all **22 declared codes**, additional adversarial probes, parsing of **20 changed Python files**, provenance hash checks, and `git diff --check`.

I did **not** execute PostgreSQL integration tests, migration application, role probes, concurrent-capture tests, query plans, production-scale timing, TypeScript suites, or the mutation harness. I did not verify production rows, deployed indexes, migration state, or the claimed 47/47 result. No files were modified.

