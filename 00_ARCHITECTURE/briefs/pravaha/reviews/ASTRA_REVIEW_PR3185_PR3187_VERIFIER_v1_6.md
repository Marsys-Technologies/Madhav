VERDICT: ACCEPT_WITH_AMENDMENTS — PR 3185 and stacked PR 3187.

Reviewed `33cf58a9e..4dcba632c3b0`. The eight-row result is correct, but point **(3)** is incompletely implemented. PR 3187’s near-miss code is unchanged; the stack inherits the required amendment below.

**Blocker — P2: missing-ID reporting silently omits non-exact rows.**

At [measuring_report.py:216](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR7x/platform/python-sidecar/services/gochara_kernel/measuring_report.py:216), `month_known` and `year_only` rows exit before the new `rows_without_lel_id` append. The ruling requires reporting missing provenance IDs regardless of confidence.

Concrete reproduction: take readback rows **1, 2 and 6**, change row 1’s confidence to `year_only`, and derive with birth `1984-02-05`, build `2026-10-05`.

- Actual: start `1998-01-01`, `excluded_undated=1`, **`rows_without_lel_id=[]`**.
- Required: the same horizon and count, with row 1’s event ID and `1984-02-05` reported.
- `month_known` reproduces the omission.

The new assertion at [test_measuring_report.py:177](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR7x/platform/python-sidecar/tests/l3/gochara/test_measuring_report.py:177) explicitly expects this incorrect omission. Report every missing-ID row while counting each exclusion once, and correct that assertion.

**Follow-up — P3: multiple missing-ID exclusions lack regression coverage.**

The cases at [test_measuring_report.py:162](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR7x/platform/python-sidecar/tests/l3/gochara/test_measuring_report.py:162) each contain only one missing-ID row. An in-memory mutation truncating `rows_without_lel_id` to its first entry passed **all 102 tests**.

Concrete exposure: two exact rows without IDs, dated `1984-02-05` and `1996-03-03`, alongside valid birth and 1998 rows. Current code reports both; the surviving mutant silently loses the second. Add a case asserting both complete entries.

**Eight-row hand replay**

| Row | Date / provenance ID | Disposition |
|---|---|---|
| 1 | `1984-02-05`; absent ID | Excluded; `rows_without_lel_id` |
| 2 | `EVT.1984.02.05.01` | Birth, identified solely by `other/birth`; set aside |
| 3 | `EVT.1993.XX.XX.01` | Excluded; `flag_exact_but_id_undated` |
| 4 | `EVT.1995.XX.XX.02` | Excluded; `flag_exact_but_id_undated` |
| 5 | `EVT.1995.XX.XX.01`; `year_only` | Excluded by confidence; included in aggregate count |
| 6 | `EVT.1998.02.16.01` | First fully dated event |
| 7 | `EVT.1998.XX.XX.02` | Excluded; `flag_exact_but_id_undated` |
| 8 | `EVT.2000.XX.XX.01` | Excluded; `flag_exact_but_id_undated` |

Result: **`1998-01-01 .. 2084-02-05`**, basis `first_dated_event`, chosen row **6**, **six exclusions**. All three shape readings yield `1998-01-01`. The supplied eight rows produce no refusal.

The [new fixture at line 180](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR7x/platform/python-sidecar/tests/l3/gochara/test_measuring_report.py:180) matches the readback’s dates, domains, IDs, shapes, confidence and intervals. It uses literal readback values, not implementation constants; synthetic event UUIDs are explicitly disclosed. Independent parsing matched all eight rows, and all **40,320 permutations** returned identical results.

**Verification**

- **102 pure tests passed**, with conftests, plugin autoloading, bytecode and cache writes disabled.
- Points **1, 2, 4 and 5** pass. Point **3** passes for exact rows but fails reporting for non-exact rows.
- Only three production functions changed. The other **34 functions/classes are byte-for-byte unchanged**, preserving START/END refusals, shape-reading sensitivity, scored arithmetic, P4 intersection and marker checks.
- The only removed named refusal is `lel_id_missing_on_candidate_first_event`; none were added.
- Both amended harness mutants were caught by assertions in memory. All **84 mutant targets plus two equivalents** occur once and compile.
- No new numerical or acceptance/refusal regression was found beyond the reporting defect above.

**Not verified:** database execution, the production readback’s provenance, remaining production rows, remote PR/CI state, deployment, or the full mutation harness. Its file-writing runner was not executed.

No files were modified. No database or network access was used.

