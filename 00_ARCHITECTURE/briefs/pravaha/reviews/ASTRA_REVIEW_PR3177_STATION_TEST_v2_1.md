VERDICT: ACCEPT_WITH_AMENDMENTS

**Mergeable for the reviewed test delta at `35d1025a0`. Both round-1 P2 blockers are resolved. No P1/P2 blockers remain; the findings below are nonblocking P3 follow-ups.**

**Round-1 findings**

| Finding | Disposition and replay |
|---|---|
| **P2 — Refusal reason discarded** | **Resolved.** [station_golden_matrix.py:90](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:90) retains exception type and message, masking floating diagnostics. Replaying `RuntimeError("root outside its support")` versus `RuntimeError("no containing segment")` through `compute()` now produces discrete differences. Changing only diagnostic float last bits passes. The fixture still contains zero refusals, but a negative reason-change test now exists at `test_station_golden_compare.py:113`. |
| **P2 — Non-assertion failure classified CAUGHT** | **Resolved.** [mutation_check_station_refine.py:89](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/scripts/gochara/mutation_check_station_refine.py:89) requires assertion-like text at the start. The original exit-1/JUnit input, `RuntimeError: DID NOT RAISE expected refusal`, now returns `UNEXPECTED-EXCEPTION`. RuntimeError/TypeError messages containing `AssertionError` or `Failed: DID NOT RAISE` also correctly fail classification. |
| **P3 — Fixture provenance absent** | **Partly resolved.** Source commit, cleanliness, platform, dependency versions, ephemeris hashes and measurement summaries are recorded. Generator version/hash remains absent, as detailed below. |

**Nonblocking follow-ups**

- **P3 — Finish provenance identification.** [station_golden_matrix.py:249](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:249) records a generator pathname and command, without its revision/hash. Concrete check: the named source commit `eeba33831` contains no `station_golden_matrix.py`, so that commit cannot identify the generator used. Add a generator hash or revision. Also, [fixture line 1](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/python-sidecar/tests/l3/gochara/fixtures/station_matrix_golden_main.json:1) records the aggregate root maximum, but the separate **9.3e-9-day ingress maximum** appears only in the docstrings.
- **P3 — Measurement helper can underreport structural differences.** [station_golden_matrix.py:192](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:192) uses unchecked `zip()` and ignores `n`. Concrete replay: changing the synthetic conjunction case’s `n` from **2 to 999** reports `discrete_differences: 0`; removing its final occurrence also reports zero discrete differences. Validate counts and shapes before measuring. **The actual regression comparator rejects both**, so this does not weaken the current regression gate.

**Per-kind tolerances**

The serialization and [field classifier at line 132](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/python-sidecar/tests/l3/gochara/station_golden_matrix.py:132) agree. **No inspected field receives a looser kind than the revised ruling permits.**

| Fields | Absolute tolerance | Harness outside mutation | Inside control |
|---|---:|---:|---:|
| Occurrence `t_exact`, `t_in`, `t_out` | `1e-8` day = **0.864 ms** | `2e-8` day | `5e-9` day |
| Station, arc/segment endpoints; ingress spline/refined roots | `5e-8` day = **4.32 ms** | `1e-7` day | `2.5e-8` day |
| Arc longitudes and ingress levels | `1e-8` degree | `2e-8` degree | `5e-9` degree |

The docstrings record the supplied maxima and environments; fixture provenance records both comparison environments and the three aggregate maxima. Headroom is approximately **3.58×, 3.58× and 7.76×**.

The Swiss solver’s bracket tolerance remains **`1e-9` day**, stopping on bracket width at [contacts.py:170](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/python-sidecar/services/gochara_kernel/contacts.py:170). These regression allowances are **10×/50× wider**. They are defensible against the reported platform measurements, but establish equality only within those allowances. Longitude tolerance is **0.000036 arcsecond**, well below the spline’s one-arcsecond setting; angular and temporal bounds are not interchangeable near stations.

**Real small defects can hide:** my replay accepted a **0.432 ms occurrence bias**, **2.16 ms root bias**, and **5e-9-degree longitude bias**. Counts and identities receive no such allowance. Comparison is absolute; numeric/`None` mismatches, NaN and both infinities fail. Matching `None` remains valid for truncated occurrences.

**Concrete behavior checks**

| Proposed kernel change/input | Detection |
|---|---|
| Remove Mercury arc **568**, containing conjunction **295.8493268245402°**, occurrence **97** | Index structure and occurrence counts/identity fail. Removing occurrence 97 from the comparator input failed. |
| Add **one second** in `substrate.jd_to_utc` | Crossing-time comparison fails; replay confirmed. |
| Change ordinal assignment from `start=1` to `start=2` | Exact ordinal/contact-ID comparison fails. |
| Store `fix.jd + 5/86400` at `substrate.py:572`; Mercury’s first 1998 station | Exact stored-row assertion at [test_station_refine.py:127](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-stnR3x/platform/python-sidecar/tests/l3/gochara/test_station_refine.py:127) fails. |
| Change stored station method to `arc_index_bracket` | Stored-row assertion at line 129 fails; occurrence-method changes also fail the golden. |
| Change old-regime guard to `if n_old > 3`, with the existing three-row Mars fixture | Expected refusal at lines 145–151 fails. Changing a recorded refusal reason now fails too. |

These kernel-change conclusions are source-derived; comparator replays were executed in memory. Rows remain paired **positionally**, with counts checked first and identities checked exactly before continuous values. Insertion, deletion and identity reordering cannot silently shift pairings; reordering failed my replay.

**Golden, harness and scope**

- The golden names main **`eeba33831ab332cb223d016ffd0e965f2a867971`**, after PR 3156. I independently loaded that tree’s original `knots.py` and `substrate.py` from Git into memory; the other relevant sources match. **All 235 cases and 69,044 continuous values matched exactly locally.**
- Coverage remains **five bodies × 47 keys**. **Dropped keys: none.** Round-2 fixture case payloads equal round 1 exactly.
- The harness requires a passing, non-skipped baseline. All **19 negative and four positive-control targets** occur exactly once and produce syntactically valid source. Every tolerance kind has outside/inside coverage, including separate ingress controls. The original refinement design and 8.64-second movement remain represented. The loss mutant is real, although its description remains inaccurate: it drops successive leading exact occurrences, not only the first.
- The requested three-file diff from **`36717c10f` to HEAD is empty**. Subsequent PR-authored changes are confined to the five reviewed test/fixture/generator/harness files. Other tree changes come from main merges and generated artifacts.

**Verification limits:** **28 direct test invocations passed** on macOS arm64, Python 3.14.6, NumPy 2.5.1 and SciPy 1.18.0, with verified pinned ephemeris files. I did not run full pytest, the mutation runner, Linux/CI, or reproduce the author’s historical cross-platform measurements and 18-case uniform-tolerance failure. No database/network access or file modifications occurred.