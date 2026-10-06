VERDICT: REJECT — PR 3185; REJECT — PR 3187.

Reviewed `eddbb8dc7`, including `da4f5f546..HEAD` and the eight-file change against `origin/main`. **188 pure tests passed**, but the probes below reproduce remaining defects. No files changed; no database or network used. The mutation harness was not executed.

References use **MR** = [measuring_report.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4b/platform/python-sidecar/services/gochara_kernel/measuring_report.py), **NM** = [near_miss_verifier.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4b/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py), **ND** = [nd_h_tables.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4b/platform/python-sidecar/services/gochara_kernel/nd_h_tables.py), and **MH** = [mutation_check_verifier_side.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-ver4b/platform/scripts/gochara/mutation_check_verifier_side.py). Line numbers are at reviewed HEAD. Times are UTC unless labelled otherwise.

**These findings must block merge.**

1. **P2 — PR 3185: the scored numerator still differs from the scorer at IST midnight, and this flips the guard.**  
   **MR:475–485**, especially line 485; scored convention declared at **MR:423–430**.

   Give both Jupiter and Saturn this P4 support:

   ```text
   [1998-01-01T00:00Z, 2009-04-25T18:30Z)
   ```

   Its endpoint dates in IST are January 1, 1998 and April 26, 2009.

   | Calculation | Admitted days | Share | Revert DVI? |
   |---|---:|---:|---|
   | `scored_share_report` | 4,133 | 39.9942% | No |
   | Scorer’s inclusive endpoint dates | 4,134 | 40.0039% | Yes |

   I reproduced the second result through `gochara_eval.extract.MergedWindow.days_in_horizon`.

   The denominator is now correctly **10,334**, but the numerator retains the positive-overlap, midnight-exclusive rule. A two-minute interval crossing IST midnight correctly counts two days; one ending exactly at midnight counts one here and two under the scorer’s endpoint convention.

   Calling this conversion an “OPEN point” in **MR:426–427** does not implement the steward’s ruling. `test_measuring_report.py:327–329` currently protects the conflicting midnight behavior.

2. **P2 — PR 3187: an approximate minimum is used as proof that clearance exceeds the eligibility floor.**  
   **NM:148–150, 247–250**, feeding **NM:78–81**.

   Use Mars, centre 100°, orb 1°, a six-day search centred on `2000-01-15T12:00Z`, and longitude `100 + d(x)`, where `x` is elapsed days:

   ```python
   d(x) = min(
       1.1,
       0.0051 + 0.2*(x + 0.5)**2,
       0.0048 + abs(x - 25/48),
   )
   ```

   This respects the 1°/day bound. Its true minimum is **0.0048°**, below `GRAZE_MIN_APPROACH_DEG = 0.005°`.

   Actual result:

   ```text
   state = near_miss
   clearance_deg = 0.005100000000055616
   closest_certified = True
   ```

   The angular certificate is consistent with its ±0.0005° tolerance. The eligibility decision is not: that certificate straddles the cutoff. Refine until the threshold decision is established, or return unresolved. Testing only the sampled upper estimate admits geometry the module says must be refused.

3. **P2 — PR 3187: missing closest-time evidence silently becomes permission to accept any time in the stretch.**  
   **NM:440–445**, particularly:

   ```python
   cands = w.get("closest_candidates") or [(w["t_in"], w["t_out"])]
   ```

   I derived the bounded curve:

   ```python
   d(x) = min(1.1, 0.5 + 0.2*x*x)
   ```

   Then supplied a well-formed stored row with `t_closest = t_in + 1 minute`, far from the minimum.

   - With the derived certificate: `near_miss_t_closest_mismatch`.
   - With `closest_candidates` missing or empty: **`[]`**.
   - With a whole-stretch candidate and `closest_certified=False`: **`[]`**.

   `row_problems` accepts this stored row in all three cases. Require affirmative certification and a nonempty, validated candidate set; unknown evidence must produce a named refusal.

4. **P2 — PR 3185: a present but insufficiently dated log is treated as an absent log.**  
   **MR:242–248**; expressly asserted by `test_measuring_report.py:79–83`.

   Concrete input:

   ```text
   birth: 1984-02-05, identifiable through domain=other/birth
   event: EVT.1995.XX.XX.01, event_date=1995-07-01,
          date_confidence=year_only, shape=point
   rebuild date: 2026-10-05
   ```

   Result:

   ```text
   start=2026-10-05
   basis=build_date
   excluded_undated=1
   chosen=None
   ```

   The owner authorized the rebuild-date fallback when no log exists. This log exists; its qualifying start is unknown. The amendment silently discards that distinction. It needs a named underivable-horizon refusal unless separately ruled otherwise.

5. **P2 — PR 3185: P4 still does not participate in contribution arithmetic.**  
   **MR:600–604, 619–620**.

   Give Venus/P3, Jupiter/P4 and Saturn/P4 identical supports `[2000-01-01, 2000-01-11)`.

   ```text
   Venus exclusive_days = 10
   class_union with Venus = 10
   class_union without Venus = 10
   ```

   Venus contributes **zero exclusive class-admitted days**, because P4 already admits all ten.

   The amendment explicitly narrows `per_agent` to P1–P3 and reports P4 separately. That does not fulfil the ruling to incorporate the P4 intersection into contribution calculations. Keep that narrower diagnostic if useful, but also compute the requested contribution against complete class admission.

6. **P2 — PR 3185: marker integrity remains an assertion without a detector.**  
   **MR:291, 351–352, 372–397**.

   An otherwise accepted view with the correct schema/horizon/classes and:

   ```python
   marker_digest = "garbage"
   ```

   still returns **`[]`**. Missing values are detected; invalid or mismatched digests are not.

   The comment delegates recomputation to the writer’s validator, but `read_measuring_view` does not invoke that validator or require evidence that it ran. The documented acceptance boundary is these two functions together. Require validated integrity there, or explicitly refuse acceptance pending that check.

**Round-1 disposition — original probes replayed**

| Original finding | Status | Current result and evidence |
|---|---|---|
| 1. P4 union instead of intersection | **Partly** | Original Jupiter Jan 1–6 / Saturn Jan 4–9 now yields **2 days**, including `class_union`. Disjoint, abutting morning/afternoon and absent-Saturn cases yield **0**. Mixed K-B/DVI support works. **MR:545–550, 583–598**. Contribution defect remains above. |
| 2. Testimony counted as scored | **Resolved** | Original ten-day P1 testimony input raises `testimony_record_in_scored_share`. SQL now filters both admitted and scored. **MR:563–564, 670–675**. Database execution was not run. |
| 3. Empty log / birth vocabulary | **Resolved for the ruled cases** | Original empty log yields `(2026-10-05, 2084-02-05, build_date)`. Documented `subcategory=birth`, `domain=other/birth`, and provenance subcategory produce the pinned horizon. Plain `category=other` alone still refuses, consistently with the steward’s identifiable-birth requirement. **MR:126–133, 185–192, 243–248**. Finding 4 above is a separate fallback defect. |
| 4. Near-equal minima reject the true time | **Partly** | Original `min(1.1, .5+.2*(x+.5)**2, .4998+abs(x-25/48))` now returns **two candidate intervals**. Both the earlier near-equal minimum and true `2000-01-16T00:30Z` pass; an unrelated time refuses. **NM:163–186**. Missing-certificate fallback remains. |
| 5. Ordinal/orb/identity unbound | **Resolved for the original probes** | `ordinal=999` and `orb=5, proximity=.9` now produce ordinal/orb mismatches. Wrong object ID also refuses. **NM:413–439**. Full-domain completeness remains a caller obligation. |
| 6. Decimal comparison crash | **Resolved** | Original stored `Decimal("0.5")` passes row and set comparison without error. **NM:428–435**. |
| 7. Non-finite values become success | **Partly** | Original NaN proximity now fails row validation; NaN positions raise `geometry_unavailable`; NaN share raises `non_finite_share`. **NM:224–230, 321–323; ND:195–197**. Other finite-value gaps remain below. |
| 8. Scored-horizon mismatch | **Partly** | Original two-support probe now returns **4,135/10,334**, firing the guard. The additional day versus the earlier date-based illustration comes from the UTC endpoint falling at 05:30 IST. Exact IST-midnight disagreement remains, as finding 1 demonstrates. **MR:423–430, 475–485**. |
| 9. Lost 60-second resolution limit | **Resolved in derivation** | Original smooth 18.93-second Mars excursion still yields no stretch, but the result carries the named **60-second limitation**, `complete=False`, and `verified_empty=False`. **NM:192–199, 237–239**. |
| Incomplete marker | **Partly** | Original `marker_horizon=None` now produces `marker_incomplete`; absent/wrong schema and absent digest also refuse. Digest integrity remains unchecked. **MR:351–352**. |
| Junction iterator exhaustion | **Resolved** | Original `iter([("sign_ingress", t_in)])` returns `["sign_ingress"]`, complete. Events also survive comparison of multiple rows. **NM:284, 403–404**. |
| Missing rule-version stamp check | **Resolved** | Original otherwise-correct core row with `rule_version="1.0.0"` produces `stamp_rule_version_mismatch`. **ND:258–259**. |
| Mutation classification heuristic | **Partly** | Original `TypeError: AssertionError is not supported` is now classified as an unexpected exception. Return codes and explicit failure types remain ignored; details below. **MH:110–132**. |
| Present-but-NULL row field | **Resolved in `row_problems`** | Original `t_in=None` now returns `row_field_missing`. Passing it directly to `compare_sets` still raises an unnamed `TypeError`. **NM:318–320, 420–422**. |
| Unbounded certificate cost | **Partly** | The certificate now stops at 40,000 evaluations with `work_budget_exhausted`. The preceding band search has no corresponding budget. **NM:90, 119–123, 187–189, 240**. |
| Tautologies / missing assurance | **Not resolved as integration evidence** | The repeated-identical-report noninterference test remains at `test_measuring_report.py:412–418`. Shared-band comparisons remain shared-oracle checks. Actual layer-on/off execution is still absent. |

**Additional amendments can follow these PRs, but must precede verification-job acceptance.**

- **P2 — incomplete numerical/input refusals.** `classify_stretch(rooted=False, complete=True, clearance_deg=inf, clearance_certified=True)` returns `("near_miss", None)` at **NM:76–82**. A one-hour outside-band search with `vmax_dps=NaN` returns `[]` at **NM:218–240**. NaN K-B separation silently returns `False` at **ND:153**. These need named unknown/invalid-input outcomes.
- **P2 — junction classification can follow an erroneous tolerated edge.** **NM:446** recomputes against stored endpoints. Put a junction exactly at rederived `t_in`, move stored `t_in` forward one second, and store an empty junction: both checks pass. Resolve boundary uncertainty or bind junction verification to independently established membership.
- **P2 — malformed stored marker shapes crash.** Through a scripted connection, `test_slice=True` raises `AttributeError`; `{"horizon":123}` raises `TypeError`. **MR:383, 392–397**. These are legal JSON shapes and should be named refusals.
- **P3 — mutation classification remains overstated.** The isolated classifier returns `CAUGHT` for exit code **2** plus an assertion report, and `SURVIVED` for exit code **3** plus passing testcases. It also ignores an explicit `failure type="TypeError"` when the message begins `AssertionError`. **MH:110–132**. The original misleading-message probe is fixed, but “assertion failures only” is not yet guaranteed.
- **P3 — stale claims.** **ND:239** still calls the scored convention open and references removed `measuring_report.SCORED_HORIZON`. **NM:49** retains the unused 600-second closest-time constant. `test_near_miss_verifier.py:250` still labels a bare empty comparison “VERIFIED empty.”

**The independently reconstructed ND-H table matches every cell.**

| Class | CORE | DVI | SUPPORT | K-A | K-B |
|---|---|---|---|---|---|
| achievement_recognition | 10 | 11 | 1, 5, 9 | Sun, Jupiter | — |
| business_launch | 7, 10 | — | 6 | Mercury | — |
| financial_deception | 2, 12 | 6 | 8 | Rahu | — |
| foreign_settlement | 12 | 4 | 7, 9; 10 noted | Rahu | — |
| parental_event, father | 9, 2 | — | 4, 8 | Sun | Sun |
| property_acquisition | 4 | 11 | 2 | Mars | — |
| psychological_arc | 4 | — | 5, 8 | — | Moon |
| spiritual_turn | 5, 9 | — | 12 | Jupiter, Ketu | — |

Checked against **ND:49–97**. Father frame, unsupported mother, spiritual Saturn testimony, version `1.2.0`, strict `>40%`, and DVI’s P4-only placement match. The ERRATA’s withdrawn citations are not reinstated as verse-level authority.

ND-P2’s bereavement Sun target, inclusive **1°** band, Jupiter/Saturn and node licences, MD/AD karakatva extension, and PD testimony are encoded correctly. A1–A3 remain literal and labelled open. No blanket fast/slow admission gate was added. DVI lord-point handling remains explicitly unmodelled; psychological-arc P2 exclusion remains explicitly **draft**.

**The minimum-search bound is sound under its assumptions, but its certificate has limits.**

For a finite, genuinely L-Lipschitz distance function,

```text
max(0, (|d0| + |d1| − L·gap) / 2)
```

is a valid lower bound. The first pass therefore bounds the minimum’s **value**, subject to the stated speed assumption. The second pass retains possible minimizer intervals and correctly preserves both near-equal minima. Its 300-second subdivision does **not** imply five-minute closest-time accuracy; candidate intervals can span hours.

Termination is bounded by the one-second floor and the new evaluation budget. Measured with pure synthetic callbacks:

| Probe | Position/distance calls | Result |
|---|---:|---|
| Flat 0.5° Moon-bound certificate, one day | 24,958 | Certified |
| Same, three days | 40,000 | Uncertified: budget exhausted |
| Same, 31,446 days | 40,000 | Uncertified: budget exhausted |
| Moving Moon, 86-year horizon, 1° band | 209,437 | 1,151 contacts |
| Moving Moon, 86-year horizon, 3° band | 222,596 | 1,151 contacts |

The moving synthetic runs took approximately 1.3 seconds each here; **these are not Swiss-ephemeris runtime measurements**. A constant exact-band-edge trajectory forces approximately **64.4 million band subdivisions** over that horizon before the certificate budget applies. `contact_reconstruct.py:75–93` also retains sampled positions in its cache.

The angular tolerance is explicit; finding 2 shows why it must be incorporated into threshold decisions. The five-second closest-time slack is described as storage rounding, but stored precision metadata is not checked. I did not independently establish the astronomical speed maxima.

Crossings—including a hidden crossing—were refused as near-misses in the tested cases. Exact-edge plateaus and 0/360 cases worked. Horizon-clipped rootless stretches stayed unresolved.

**Independence, schema and test assurance**

- **Runtime imports:** MR and ND import no kernel code. NM’s sole kernel import is `contact_reconstruct` at **NM:214**. It is appropriate under the ONE-band ruling, with a shared failure surface that must remain disclosed.
- **Test imports:** measuring tests import MR; ND tests import ND; near-miss tests import NM and `utc`, plus `contact_reconstruct` at test lines **333, 350, 391, 530**. DB tests additionally import the A5.3 fixture/bootstrap helpers at **17–19**. Those are storage fixtures, not independent geometric oracles. The mutation harness imports no kernel module.
- **Scorer:** `gochara_eval/registry.py:8–21`, `extract.py:65–67`, and `metrics.py:80–87` establish **IST dates, inclusive endpoints, 10,334 days**. No `EVALUATION_PROTOCOL_v2_3` artifact was found under tracked `00_ARCHITECTURE`.
- **Life-event schema:** checked `001_baseline.sql:463`, expanded baseline `0001_brahma_baseline.sql:2056`, chart-scoping migration 423, shape migration 457, and later relevant migration references. `domain` and `event_type` exist in the expanded schema; `subcategory` is not established as a standalone stored column. The current vocabulary alternatives accommodate that distinction. Production population remains unverified.
- **Reader SQL:** publication, seal, relationship-record and eval-window columns match migrations **1081, 1153, 1155 and 1156**. Queries are parameterized SELECTs. Unbounded support ranges receive named refusals. Aware timestamp normalization and Decimal comparison work in the tested paths. The near-miss table remains guarded by `to_regclass`; no eventual near-miss schema was available to verify.
- **Useful tests now detect** restored P4 union arithmetic, testimony inclusion, wrong ordinals/orbs/object IDs, wrong finite clearance/proximity/junctions, extra duplicates, missing stamps, and missing resolution declarations.
- **Missing tests include** scorer parity at exact IST midnight, threshold-straddling certificates, absent/uncertified candidate evidence, contributions with independently admitting P4, and digest corruption. Several existing tests affirm the problematic behavior identified above.
- **Mutation inspection:** **66 mutants and two declared EQUIVALENTs**. Every replacement target occurred once and every amended source compiled in memory. Both equivalence explanations are justified. Baseline zero-exit is required. I probed only the extracted pure classifier with in-memory XML; the rewriting harness and its claimed kill count remain unverified.

I did **not** verify database execution, production rows, real ephemeris accuracy/runtime, builder-table equality, job wiring, stationless-body enforcement, source/precision identity checks, completed full-build census, or actual layer-on/off scored extracts and all five endpoints. Passing helper tests do not complete those acceptance obligations.

