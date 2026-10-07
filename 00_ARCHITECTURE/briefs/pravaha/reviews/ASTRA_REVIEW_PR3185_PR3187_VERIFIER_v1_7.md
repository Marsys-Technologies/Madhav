VERDICT: ACCEPT — PR 3185 and stacked PR 3187.

Reviewed `4dcba632c..6d3966b23` and the complete amendment `33cf58a9e..6d3966b23`.

**Blockers: none.** The previous P2 is fixed. No new wrong-number, false-acceptance, or wrongful-refusal defect was found.

**Follow-ups: none required.** The previous P3 is closed: the new multi-row assertions catch the previously surviving truncation mutant.

The five ruling points hold:

| Point | Verified behavior |
|---|---|
| 1 | Birth identification uses only `domain == "other/birth"` — [measuring_report.py:131](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR8x/platform/python-sidecar/services/gochara_kernel/measuring_report.py:131). |
| 2 | Fully dated requires exact confidence, a dated provenance ID, and equality with the stored date. Undated or mismatched IDs are excluded and reported — [measuring_report.py:173](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR8x/platform/python-sidecar/services/gochara_kernel/measuring_report.py:173). |
| 3 | Missing-ID reporting now precedes the confidence filter. No fallback to `event_id`; the withdrawn refusal is gone — [measuring_report.py:216](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR8x/platform/python-sidecar/services/gochara_kernel/measuring_report.py:216). |
| 4 | A nonempty log without a fully dated event retains `horizon_underivable_log_has_no_dated_event`; zero rows use the rebuild date — [measuring_report.py:260](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR8x/platform/python-sidecar/services/gochara_kernel/measuring_report.py:260). |
| 5 | The eight supplied rows select row 6, `EVT.1998.02.16.01`, giving START `1998-01-01`. |

**Eight-row hand replay**

| Row | Date / ID | Disposition |
|---|---|---|
| 1 | `1984-02-05`; no ID | Excluded; `rows_without_lel_id` |
| 2 | `EVT.1984.02.05.01` | Birth anchor; set aside |
| 3 | `EVT.1993.XX.XX.01` | Excluded; `flag_exact_but_id_undated` |
| 4 | `EVT.1995.XX.XX.02` | Excluded; `flag_exact_but_id_undated` |
| 5 | `EVT.1995.XX.XX.01`; `year_only` | Excluded by confidence; represented in aggregate count |
| 6 | `EVT.1998.02.16.01` | First fully dated event |
| 7 | `EVT.1998.XX.XX.02` | Excluded; `flag_exact_but_id_undated` |
| 8 | `EVT.2000.XX.XX.01` | Excluded; `flag_exact_but_id_undated` |

Result: **`1998-01-01 .. 2084-02-05`**, basis `first_dated_event`, **six exclusions**, no refusal. All three shape readings agree.

**Requested counterexample replays**

- Rows **1, 2, 6**, with row 1 changed separately to `year_only` and `month_known`: both return START `1998-01-01`, **one exclusion**, and row 1’s event ID plus `1984-02-05` in `rows_without_lel_id`.
- Two exact id-less rows dated **`1984-02-05` and `1996-03-03`**, alongside birth and the valid 1998 row: both complete entries survive, **two exclusions**, unchanged horizon.

Reporting itself does not increment the counter. Non-exact rows increment once and `continue`; remaining exact rows enter mutually exclusive classification branches. A 54-case confidence/shape/ID matrix confirmed exact-once counting and complete applicable lists. Duplicate event IDs and null dates on non-exact rows did not lose entries.

**Verification evidence**

- **102 pure tests passed** at stacked HEAD; the local PR 3185 fix’s 102 cases also passed in memory.
- The [fixture at test_measuring_report.py:193](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR8x/platform/python-sidecar/tests/l3/gochara/test_measuring_report.py:193) exactly matches an independent parse of the supplied readback fields. Values are literal; synthetic UUIDs are disclosed. All **40,320 permutations** agree.
- The four relevant harness mutants and previous first-entry-only mutant fail by assertion. Additional mutations violating the ruling also fail tests.
- Only three production functions changed since `33cf58a9e`; the other **34 functions/classes are unchanged**, preserving START/END refusals, shape sensitivity, scored arithmetic, P4 intersection, and marker checks. The withdrawn refusal is the only removed refusal; none were added.

**Not verified:** database execution, readback provenance or remaining production rows, remote PR/CI state, deployment, or the full file-writing mutation runner. PR 3187’s unchanged near-miss implementation was not re-reviewed.

No files were modified. No database or network access was used.

