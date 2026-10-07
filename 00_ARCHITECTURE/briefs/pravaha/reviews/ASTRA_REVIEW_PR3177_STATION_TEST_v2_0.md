VERDICT: ACCEPT_WITH_AMENDMENTS

**Not mergeable yet under the stated acceptance criteria.** Two test/harness amendments remain. The accepted kernel is unchanged: the requested three-file diff from `36717c10f` to HEAD `22cce853492b` is empty.

**Blockers**

- **P2 — Refusal identity is discarded.** [station_golden_matrix.py:102](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR2x/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:102) records only `["REFUSED", type(exc).__name__]`. For the same case, `RuntimeError("root outside its support")` and `RuntimeError("no containing segment")` become identical. The previous generator retained the exception message. Moreover, **the regenerated fixture contains zero refused cases**: introducing a refusal into an existing case fails, but preserving the identity of an existing refusal is untested. Preserve an exact, stable refusal code/reason—separating any floating diagnostics—and add a negative case proving that changing that reason fails.

- **P2 — A non-assertion exception can be classified as CAUGHT.** [mutation_check_station_refine.py:77](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR2x/platform/scripts/gochara/mutation_check_station_refine.py:77) accepts `"DID NOT RAISE"` anywhere in the JUnit failure message. Concrete input: exit code `1` with `<testcase><failure message="RuntimeError: DID NOT RAISE expected refusal"/></testcase>` reaches `CAUGHT`, although the exception is `RuntimeError`. Remove the unrestricted substring match and test rejection of non-assertion failures containing assertion-like text. This conclusion is from inspection; I did not execute the harness.

**Follow-up**

- **P3 — Provenance is absent from the fixture.** [station_golden_matrix.py:155](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR2x/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:155) writes schema, tolerances and cases, but no source commit, generator version/hash or platform. The CLI at line 173 imports whichever checkout supplies `services`; `main_index` is an inline construction, not source-tree isolation. Record the source revision, generator identity, platform/dependencies and ephemeris hashes.

The remaining checks support the numerical regression:

| Concrete proposed kernel change/input | Detection |
|---|---|
| In `substrate.production_arc_index`, remove Mercury arc **568**, containing occurrence **97** of conjunction **295.8493268245402°**, at **2074-01-24 15:52:45 UTC** | Fails index count/rows and crossing count/identity. |
| In `substrate.jd_to_utc`, add **one second**, affecting that crossing | Fails continuous comparison: `1/86400 ≈ 1.157e-5` day exceeds `1e-7`. |
| In `substrate.assign_occurrence_ordinals`, change enumeration from `start=1` to `start=2` | Fails exact ordinal and contact-ID comparison. |
| In the station-storage block, use `fix.jd + 5/86400`; input: Mercury’s first 1998 station, spline JD **2450900.320600343** | The crossing golden is unaffected; the stored-row assertion at `test_station_refine.py:124` fails. |
| Change the stored station’s solver label to `arc_index_bracket` | Stored-row assertion at line 126 fails. A changed point-occurrence solver label also fails the golden’s discrete comparison. |
| Change the old-regime guard to `if n_old > 3`; input: Mars with the existing fake connection returning **3** old rows | The expected refusal at lines 142–148 fails. Refusal-reason preservation has the blocker above. |

These are source-derived detection conclusions. Separately, I exercised the comparator in memory: removing a row, changing order/ordinal/method, shifting one second, and inserting `None`, NaN or infinity all failed; a **4.32 ms** shift survived.

**Tolerance and matching.** The comparison uses absolute differences, with no relative tolerance: [station_golden_matrix.py:127](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR2x/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:127). NaN and infinities fail. A numeric/`None` mismatch fails; matching `None` remains valid for truncated occurrences.

The Swiss root solver declares **`1e-9` day**, or **86.4 μs**, at [contacts.py:122](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR2x/platform/python-sidecar/services/gochara_kernel/contacts.py:122), and stops on that bracket width at line 170. Thus the golden’s **8.64 ms** allowance is **100 times wider**. It is defensible as the steward-approved regression tolerance, but does not establish equality at the solver’s nominal precision: a real 4.32 ms defect can hide inside it. The longitude allowance is **0.00036 arcsecond**, substantially tighter than the spline’s default **1 arcsecond** (`arcs.py:34`). Angular and temporal tolerances are separate bounds; near a station they are not interchangeable.

Rows are paired **by position**, then their ordinal/contact ID and other discrete fields are checked exactly. Counts and lengths are checked first. Consequently an insertion/deletion cannot silently shift pairs, and reordering identities fails. An identity-keyed join is unnecessary for this ordered-equality contract.

**Golden source and coverage.** Commit `9c00991ce` identifies main **`eeba33831ab332cb223d016ffd0e965f2a867971`**, immediately after the PR 3156 wrap fix, as its source. I independently replayed all **235 cases** using that revision’s original `knots.py` and `substrate.py` loaded from Git into memory; the other relevant kernel/rules/ephemeris sources match that tree. **All 235 matched the fixture within tolerance.** This supports the current golden as a main oracle, despite the missing provenance metadata.

Old and new key sets are identical: **five bodies × 47 cases = 235**. **Dropped keys: none.** The twelve former wrap-refusal cases now return occurrences.

**Harness and scope.** A passing, non-skipped baseline is required before mutations. All **17 negative mutation targets and one positive-control target** occur exactly once in HEAD. The round-1 refinement, 8.64-second station move, three 17.28 ms shifts and 4.32 ms survival control perform their stated numerical changes. The “first occurrence dropped” mutation actually drops successive exact occurrences while `occs` remains empty—potentially all domain occurrences—so its description should be corrected.

Since `36717c10f`, the non-merge commits change the four requested artifacts and add `test_station_golden_compare.py`. Other tree changes come from main merges and generated files, including main’s `record_store.py` wrap fix. No additional PR-authored production change was found.

**Verification limits:** all **24 direct test invocations passed** on macOS arm64 with verified pinned ephemeris files. These were direct calls, not a full pytest invocation. I did not run the mutation harness, Linux/CI, database checks or network operations, and did not verify the historical cross-platform measurements. No files were modified.