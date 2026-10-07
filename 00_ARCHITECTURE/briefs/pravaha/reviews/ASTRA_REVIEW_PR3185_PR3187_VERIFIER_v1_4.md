VERDICT: ACCEPT — PR 3185; REJECT — PR 3187.

**PR 3185 is mergeable at `5c49c204b798`. PR 3187 has one new blocking P2 regression.** Both original round-4 reproductions are fixed, but the junction amendment can assign an event to the wrong neighboring stretch.

**Round-4 blocker disposition**

| Blocker | Status | Probe replay and evidence |
|---|---|---|
| Dated `event_id` substitutes for missing `provenance.lel_id` | **Resolved** | The original `EVT.1998.02.16.01`, date `1998-02-16`, `exact`, `point`, `provenance={}` now refuses with **`lel_id_missing_on_candidate_first_event`**. Supplying the valid provenance ID with a UUID top-level ID correctly derives `1998-01-01 .. 2084-02-05`. Missing/null provenance cannot use the fallback. [measuring_report.py:169](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR5x/platform/python-sidecar/services/gochara_kernel/measuring_report.py:169), refusal at line 229. |
| Approximate reconstructed endpoint treated as exact junction boundary | **Resolved for the original probe** | Replayed `d(x)=min(1.1, .75+.25*x*x)`, with the original event at `2000-01-16T12:00:00.500000Z`. Honest `junction=[]` now passes; the false junction claim gets **`near_miss_junction_mismatch`**. Moving the event 0.5 seconds inside reverses those outcomes correctly. Both entry-side directions also pass. Exact-edge events return **`junction_membership_unresolved`**. [near_miss_verifier.py:320](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR5x/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py:320), comparison at line 521. |

**P2 — PR 3187: the geometry check can borrow membership from another stretch. Must block merge.**

At [near_miss_verifier.py:338–349](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR5x/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py:338), a positive band margin anywhere within the expanded ±2-second interval adds the junction. Being inside the band proves membership in *some* stretch; it does not establish membership in the particular stretch being checked.

Concrete smooth, speed-bounded input:

```python
TC = 2000-01-15T12:00:00Z
x = elapsed_days_from_TC
delta = 1e-7

d(x) = 0.5 + sqrt((sqrt(x*x + delta*delta) - 0.5)**2
                  + delta*delta) + 3e-6

body = "mars"
position = 100° + d(x)
centres = [100°]
orb = 1°
horizon = [TC - 2 days, TC + 2 days)
junction = ("dasha_md_ad_boundary", TC + 1 second)
```

The derivative’s magnitude is at most **1°/day**, satisfying the stated Mars bound. The detector returns two certified near-misses:

| Stretch | True interval, UTC | Reconstructed boundary near the gap |
|---|---|---|
| 1 | `Jan 14 12:00:00.259200 .. Jan 15 11:59:59.740944` | Exit `Jan 15 12:00:00` |
| 2 | `Jan 15 12:00:00.259056 .. Jan 16 11:59:59.740800` | Entry `Jan 15 12:00:00.659180` |

The event at **`Jan 15 12:00:01` belongs only to stretch 2**. Its separation is `0.999991425494°`.

Store the analytical intervals, closest times at Jan 15/16 midnight, clearance `0.5000031`, proximity `0.4999969`, ordinals 1/2, matching object/orb identities, and otherwise valid unscored fields. Both rows pass `row_problems`.

| Stored junctions: stretch 1 / stretch 2 | Round 4 | HEAD |
|---|---|---|
| `[] / ["dasha_md_ad_boundary"]` — honest | Accepted | **Wrongly refused** |
| `["dasha_md_ad_boundary"] / ["dasha_md_ad_boundary"]` — false | Refused | **Falsely accepted: `compare_sets == []`** |

I compared both revisions by loading the old source in memory.

The **60-second named limit remains present**. It concerns potentially undetected excursions; here the detector actually returned both components. The amendment then assigns an event across their known separation.

The fix must preserve membership in the particular reconstructed component while refining its boundary. Ambiguous component assignment should produce the named unresolved result. Add this two-stretch regression in both directions. The new tests at [test_near_miss_verifier.py:673](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR5x/platform/python-sidecar/tests/l3/gochara/test_near_miss_verifier.py:673) cover isolated boundaries but miss neighboring components.

**Other verification**

- **207 pure tests passed**, with bytecode/cache writes and repository conftests disabled. Database tests were read, not executed.
- **ND-H:** all 40 tier/kāraka cells matched my separately transcribed expected table; frame, noted house, mother registration, `1.2.0`, and A1–A3 labels matched. **216 ND-P2 bereavement licence combinations** passed, including the inclusive 1° edge. No amendment reinstates withdrawn ERRATA citations.
- **Shares:** 400 independently calculated support cases, each on both grids, matched path shares, P4 intersection, K-B variants, class union, fast/slow splits, clipping and agent-removal contributions. Checked-in abutting/absent-agent tests also passed. The scored-role refusal and SQL’s positive `operator_role = 'scored'` filter remain intact.
- **Scored horizon:** the scorer uses **IST dates, inclusive endpoints, 10,334 days**, as shown by `gochara_eval/registry.py:8–21`, `extract.py:65–67`, and `metrics.py:80–87`. The original guard probe gives **4,134/10,334 = 40.0038707%**, correctly triggering reversion. A support crossing `18:30Z` counts two scored dates and one UTC build date. No mixed-convention ratio reproduced. No `EVALUATION_PROTOCOL_v2_3` artifact was found under `00_ARCHITECTURE`.
- **Horizon and readers:** empty-log fallback, nonempty-undated refusal, birth vocabulary, provenance conjunction, NULL/Decimal/aware-time and unbounded-range cases passed their pure tests. SQL names match migrations 1081/1153/1155/1156; LEL fields match baseline 001, 423, 457 and the later 691 contracts. Reader statements are parameterized SELECTs.
- **Near-miss protections:** crossing, clearance/proximity, near-equal minima, wrong closest time, duplicates, ordinal/orb/object binding, wrap, exact-band and clipped-stretch tests passed. Stored-value and callback finite checks remain effective on the tested derivation paths.

**Minimum certificate, independence and mutation evidence**

The unchanged Lipschitz lower bound,

```text
max(0, (abs(d0) + abs(d1) − speed_bound × elapsed_time) / 2)
```

is sound under its stated speed assumption. It certifies minimum value within tolerance, while candidate intervals and the stored-time separation check constrain `t_closest`. Termination is bounded by the one-second floor and evaluation budgets.

My 31,446-day synthetic Moon sweep used **209,398 calls at 1°** and **222,555 at 3°**, taking approximately **0.44/0.47 seconds** with trivial callbacks. A flat one-day Moon minimum needed 24,958 evaluations; three days exhausted the 40,000-evaluation certificate budget and remained uncertified. These are synthetic timings, not real-ephemeris qualification.

Runtime kernel imports remain:

| Module | Kernel imports | Judgment |
|---|---|---|
| `measuring_report.py` | None | Independent |
| `nd_h_tables.py` | None | Independent |
| `near_miss_verifier.py:222` | `contact_reconstruct` | Required ONE-band reuse; shared failure surface |

Tests import their respective subjects, NM’s `utc`, and `contact_reconstruct` at near-miss test lines 336/353/394/533. Those shared-detector comparisons establish consistency, not independent geometry. DB tests additionally import A5.3 fixture helpers.

The mutation harness was **not run**. Static inspection found **80 mutants and two documented equivalents**; every replacement target occurs once and every replacement compiles in memory. Baseline success is required, and both equivalence explanations remain justified. No kill-count claim was verified.

**Carried P3 hardening — follow-up only; unchanged merge disposition**

| Item | Concrete exposure | Evidence |
|---|---|---|
| Finite helper arguments | `clearance_deg=inf`, NaN speed override, NaN K-B separation | `near_miss_verifier.py:76–84,226–230`; `nd_h_tables.py:153` |
| Marker shapes | `test_slice=True`; `{"horizon":123}` can raise raw exceptions | `measuring_report.py:409,418–422` |
| Mutation classification | Explicit `TypeError` with an assertion-prefixed message can count as caught; exit 3 with passing cases becomes survived | `mutation_check_verifier_side.py:130–148` |
| Candidate interval validation | Reversed `[tc+2s, tc−2s]` can pass through slack | `near_miss_verifier.py:514` |
| Stale claims | Obsolete fallback/convention wording and unused closest-time tolerance | `measuring_report.py:248–249`; `nd_h_tables.py:239`; `near_miss_verifier.py:49` |

I did **not** verify database execution, production rows, real ephemeris accuracy/runtime, astronomical speed maxima, physical justification of tolerances, builder-table equality, job wiring, stationless-body enforcement, source/precision identity binding, full-domain provenance, complete-build census, or actual layer-on/off scored outputs. Those remain separate job-acceptance obligations.

No files were modified. No database or network access was used.

