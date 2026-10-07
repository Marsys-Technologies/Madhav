VERDICT: REJECT — PR 3185; REJECT — PR 3187.

**Neither PR is mergeable at `1ef6639bf`.** The amendments fix several important defects, and **197 pure tests pass**, but five reproduced correctness defects remain. The hardening items below are separate from those merge blockers.

Reviewed `eddbb8dc7..HEAD` and all eight files in `origin/main...HEAD`. No files changed; no database or network access used. The mutation harness was **not run**.

References: **MR** = [measuring_report.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR3x/platform/python-sidecar/services/gochara_kernel/measuring_report.py), **NM** = [near_miss_verifier.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR3x/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py), **ND** = [nd_h_tables.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR3x/platform/python-sidecar/services/gochara_kernel/nd_h_tables.py), **MH** = [mutation_check_verifier_side.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/68c17fac-f597-4ede-b72b-52a624b4f9a1/scratchpad/rev-verR3x/platform/scripts/gochara/mutation_check_verifier_side.py). All times below are UTC unless labelled otherwise.

**The following five P2 findings must block merge.**

1. **PR 3185 — horizon derivation uses the wrong ID field and retains the superseded dating-disagreement refusal.**  
   **MR:169–178, 214–223.**

   `_id_dated` reads `event_id`, whereas the binding ruling requires **`provenance.lel_id`**. This matters for the existing intake: `brahmagyan/mimamsa/lel_intake.py:1183–1186` constructs a UUID-valued `event_id`; lines **1314–1317** store the human `EVT.*` ID in provenance.

   With an identifiable birth row, this fully dated event:

   ```python
   {
       "event_id": "12345678-1234-1234-1234-123456789abc",
       "event_date": date(1998, 2, 16),
       "date_confidence": "exact",
       "shape": "point",
       "provenance": {"lel_id": "EVT.1998.02.16.01"},
   }
   ```

   produces **`lel_dating_rules_disagree`**, instead of the ruled `1998-01-01` start.

   Separately, the original-style input containing an exact-flagged `EVT.1995.XX.XX.01` row before a valid 1998 event still raises that disagreement. Under the new conjunction ruling, the 1995 row must simply be excluded and reported.

   The reverse error also reproduces: a matching, dated top-level `event_id` with **undated `provenance.lel_id`** is accepted as fully dated. Thus this can both reject valid evidence and derive a horizon from disqualified evidence.

   Read the provenance ID and apply the conjunction directly. `test_measuring_report.py:128–140` currently protects the superseded refusal.

2. **PR 3185 — the new contribution field still understates Jupiter/Saturn’s contribution to complete class admission.**  
   **MR:620–627.**

   Give these three records identical `[2000-01-01, 2000-01-11)` support:

   ```text
   Jupiter / P3
   Jupiter / P4
   Saturn  / P4
   ```

   Actual:

   ```text
   Jupiter exclusive_days_vs_class = 0
   class_union with Jupiter       = 10
   class_union without Jupiter    = 0
   ```

   Removing Jupiter removes its P3 support **and breaks P4**. Its contribution against complete class admission is ten days. The same defect reproduces for Saturn. With only the two P4 records, `per_agent` is empty.

   The amendment subtracts the unchanged P4 intersection from each agent’s P1–P3 days. That fixes Venus’s original example, but does not compute each agent’s contribution against complete class admission. Recompute class admission after removing that agent’s records, including its P4 influence.

   `test_measuring_report.py:269` now explicitly expects the incorrect Jupiter result.

3. **PR 3185 — the digest-shape check accepts a malformed 65-character digest.**  
   **MR:55, 362–365.**

   Input:

   ```python
   marker_digest = "d" * 64 + "\n"
   ```

   Through **both** `read_measuring_view` and `measuring_refusals`, the result is **`[]`**. Python’s `$` anchor permits a match immediately before a final newline.

   Use a full-string match or an explicit length check. The new integrity disclosure is otherwise correct: `marker_digest_verified=None` with the required reason. No digest recomputation or writer import is requested.

4. **PR 3187 — candidate-interval membership can certify a materially wrong `t_closest`.**  
   **NM:167–188, 468–476.**

   A lower bound establishes that an interval *might contain* a minimizer. It does not establish that every instant inside that interval is sufficiently close to the minimum.

   Concrete bounded curve, with Mars, centre 100°, orb 1°, a six-day horizon centred on `2000-01-15T12:00Z`, and `x` measured in days from that centre:

   ```python
   d(x) = min(1.1, 0.5 + sqrt(x*x + 0.000001) - 0.001)
   ```

   This is 1°/day Lipschitz. Its true minimum is **0.5° at 12:00**.

   The derivation produces a certified candidate interval:

   ```text
   [2000-01-15T11:54:49.306641Z,
    2000-01-15T12:02:19.306641Z]
   ```

   Store:

   ```text
   clearance_deg = 0.5
   proximity     = 0.5
   t_closest     = 2000-01-15T11:54:50Z
   ```

   **Both `row_problems` and `compare_sets` return `[]`.** Actual separation at that stored time is **0.502724711831°**—outside even the combined 0.0005° certificate and 0.001° clearance tolerances.

   Preserve multiple near-equal minima, but also independently check the separation at the stored closest time against the certified minimum, or provide stronger bounds on accepted candidate times.

5. **PR 3187 — a tolerated endpoint shift still conceals a real junction.**  
   **NM:448–450, 477–481.**

   Replay the prior probe using a genuine derived stretch:

   ```text
   d(x) = min(1.1, 0.5 + 0.2*x*x)
   junction_source = an MD/AD boundary exactly at rederived t_in
   stored t_in    = rederived t_in + 1 second
   stored junction = []
   junction_complete = True
   ```

   **Both row and set checks pass.** Recomputing membership on the rederived interval correctly returns `["dasha_md_ad_boundary"]`.

   The comparison accepts the endpoint displacement, then uses the displaced stored endpoint to verify the junction. Bind membership to independently established geometry; boundary uncertainty can produce a named unresolved result.

   This was previously listed as follow-up work. Under this round’s explicit false-acceptance criterion, it blocks.

**Round-2 blockers: original probes replayed**

For the curve inputs below, `x` is elapsed days from `2000-01-15T12:00Z`.

| Round-2 finding | Status | Current result and evidence |
|---|---|---|
| 1. IST-midnight numerator | **Resolved** | Matching Jupiter/Saturn supports `[1998-01-01T00:00Z, 2009-04-25T18:30Z)` now give **4,134/10,334 = 40.0038707%**; guard fires. **MR:437–445, 490–506**. |
| 2. Approximate minimum crosses eligibility floor | **Resolved** | Exact original `min(1.1, .0051+.2(x+.5)², .0048+abs(x−25/48))` now returns **unresolved / clearance_below_min_approach**, estimate **0.00484831949°**. **NM:253–273**. |
| 3. Missing closest evidence permits any time | **Resolved for the original inputs** | On `min(1.1,.5+.2x²)`, stored `t_in+1 minute` refuses. Missing/empty candidates and `closest_certified=False` now produce **near_miss_closest_evidence_missing**. **NM:468–476**. Candidate validation hardening remains below. |
| 4. Present undated log falls back to rebuild date | **Partly** | Birth plus year-only `EVT.1995.XX.XX.01` now gives **horizon_underivable_log_has_no_dated_event**. Exact-flagged undated rows still encounter the superseded disagreement logic; see finding 1. **MR:222–223, 247–258**. |
| 5. P4 missing from contribution arithmetic | **Partly** | Original Venus/P3 plus Jupiter/P4 plus Saturn/P4 ten-day input now gives Venus **exclusive_days_vs_class=0**. Jupiter/Saturn counterfactuals remain wrong; finding 2. **MR:620–627**. |
| 6. Digest integrity asserted without detector | **Partly** | `"garbage"` now refuses, and integrity is honestly null with the steward’s reason. Final-newline malformed digest still passes; finding 3. **MR:301–303, 362–365**. |

**Disposition of every carried round-1 row**

| Carried finding | Status | Replay result and current evidence |
|---|---|---|
| P4 union instead of intersection | **Partly** | Jupiter Jan 1–6 / Saturn Jan 4–9 gives **2 days**, including class union. Abutting, disjoint and absent-agent cases give zero. Mixed K-B/DVI support works. Contribution remains finding 2. **MR:475–487, 565–570, 603–618**. |
| Testimony counted as scored | **Resolved** | Ten-day P1 testimony input raises **testimony_record_in_scored_share**. SQL positively filters admitted **and** scored. **MR:583–584, 693–698**. |
| Empty log / birth vocabulary | **Resolved for original inputs** | Empty log gives `(2026-10-05, 2084-02-05, build_date)`. Subcategory, domain and provenance-subcategory birth spellings work; plain `category=other` refuses. **MR:131–138, 194–197, 247–258**. |
| Near-equal minima | **Partly** | Original `min(1.1,.5+.2(x+.5)²,.4998+abs(x−25/48))` preserves two candidates; the true `2000-01-16T00:30Z` and earlier near-equal minimum pass. An unrelated time refuses. Candidate membership still permits finding 4. **NM:167–188, 468–476**. |
| Ordinal/orb/identity binding | **Resolved for original probes** | Ordinal 999, orb 5°, and wrong object ID each refuse by name. **NM:462–467**. |
| Decimal crash | **Resolved** | Stored `Decimal("0.5")` passes row and set comparison. **NM:318–320, 456–463**. |
| Non-finite values | **Partly** | NaN proximity refuses in row validation; NaN position raises **geometry_unavailable**; NaN share raises **non_finite_share**. Remaining helper-input gaps below. **NM:239–241, 344–346; ND:195–197**. |
| Scored-horizon convention | **Resolved** | Original two-support input gives **4,135/10,334**; the exact-midnight probe now also agrees with the scorer. **MR:437–445, 490–506**. |
| Lost 60-second limit | **Resolved in derivation** | Original 18.93-second excursion remains undetected, but returns the named **60-second** limit, `complete=False`, `verified_empty=False`. **NM:195–202, 248–250**. |
| Incomplete marker | **Partly** | Missing horizon/schema/digest each refuse. Integrity disclosure now follows the ruling; malformed-newline gap remains. **MR:362–365**. |
| Junction iterator exhaustion | **Resolved** | `iter([("sign_ingress", t_in)])` retains its event; multi-row regression also passes. **NM:307, 426–427**. |
| Missing rule-version stamp check | **Resolved** | Otherwise-correct core row at `1.0.0` produces **stamp_rule_version_mismatch**. **ND:258–259**. |
| Mutation classification | **Partly** | Misleading TypeError message and exit-code-2 assertion report now refuse credit. Explicit failure types and nonzero survivor exits remain mishandled. **MH:126–142**. |
| Present-but-NULL field | **Resolved for original probe** | `t_in=None` produces **row_field_missing** in both row and set checks, without a TypeError. **NM:341–343, 442–446**. |
| Unbounded search cost | **Resolved as a bounded-work obligation** | Certificate stops at 40,000 evaluations; band search now stops at 3,000,000 position calls with a named error. **NM:122–125, 190–192, 235–238**. |
| Tautologies / missing assurance | **Partly** | Repeated-identical-report assertion and its noninterference claim were removed as requested. Actual on/off integration proof remains absent. **test_measuring_report.py:421–426**. |

**Hardening that can follow merge, but must precede verification-job reliance**

These reproduce the remaining round-2 follow-ups. They concern malformed caller inputs, failure reporting or assurance; the normal derivation failures above are separately merge-blocking.

| Priority / prior item | Status | Concrete replay and evidence |
|---|---|---|
| **P3 — finite helper inputs** | **Not resolved** | `classify_stretch(rooted=False, complete=True, clearance_deg=inf, clearance_certified=True)` still returns near-miss. An outside-band one-hour search with NaN speed returns an empty, incomplete search. NaN K-B separation returns `False`. Validated finite geometry does not generate these inputs, but the public boundaries need named refusals. **NM:76–84, 224–231; ND:153**. |
| **P3 — malformed marker shapes** | **Not resolved** | Scripted reader with `test_slice=True` raises `AttributeError`; `{"horizon":123}` raises `TypeError`. Neither becomes a named refusal. **MR:396, 405–409**. |
| **P3 — mutation classifier** | **Partly** | Exit code 2 plus an assertion report is now rejected. Exit code **3** plus passing cases still returns **SURVIVED**; `failure type="TypeError" message="AssertionError: ..."` still returns **CAUGHT**. **MH:127–142**. |
| **P3 — stale claims** | **Not resolved** | ND still calls the scored convention open and references removed `SCORED_HORIZON`; NM retains unused 600-second tolerance; the empty-comparison test still says “VERIFIED empty.” MR’s horizon docstring still describes the removed nonempty-log fallback. **ND:239; NM:49; test_near_miss_verifier.py:250; MR:236–237**. |
| **P3 — candidate evidence shape** | **Partly** | Missing evidence now refuses. A certified reversed interval `[tc+2s,tc−2s]` passes because slack bridges it; a certified interval extending outside the stretch also passes. Such intervals are not emitted by the current derivation, but the promised “validated candidate set” is not implemented. **NM:470–476**. |

**ND-H and ND-P2 comparison**

I independently reconstructed these cells from the supplied ruling before comparing the module. All eight classes match **ND:50–97**.

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

Father frame, unsupported mother, spiritual Saturn testimony, `1.2.0` stamps, DVI’s P4-only placement and strict `>40%` agree. The ERRATA’s withdrawn citations are not reinstated as verse authority.

ND-P2’s natal-Sun bereavement target, inclusive **1°** band, agent/relation licences, MD/AD karakatva extension and PD testimony agree. A1–A3 remain literal and labelled open. No blanket fast/slow gate appears. DVI lord-point handling remains explicitly unmodelled; psychological-arc P2 exclusion remains explicitly draft.

**Scored arithmetic, minimum certification and cost**

The scorer itself uses **IST calendar dates, inclusive endpoints, 10,334 days**: `gochara_eval/registry.py:8–21`, `extract.py:65–67`, `metrics.py:80–87`. No `EVALUATION_PROTOCOL_v2_3` artifact was found under `00_ARCHITECTURE` on this checkout.

The amended scored numerator and denominator agree with that convention. **505 independent boundary/union cases matched**, including local-midnight crossings, exact-midnight endpoints and both observation-mask edges. Build shares remain separately labelled UTC half-open with **31,446 days**. I found no remaining mixed-convention guard ratio.

The minimum-value bound is sound for a finite, genuinely L-Lipschitz distance function:

```text
lower = max(0, (|d0| + |d1| − L·gap) / 2)
```

Golden-section refinement supplies an upper estimate; branch-and-bound provides the global value certificate. The amendment now uses the tolerance when deciding the clearance floor. Finding 4 concerns the subsequent use of candidate intervals to accept stored times.

Measured with synthetic callbacks:

| Probe | Evaluations / position calls | Result |
|---|---:|---|
| Flat 0.5°, Moon bound, one day | 24,958 | Certified |
| Same, three days | 40,000 | Uncertified; budget exhausted |
| Same, 31,446 days | 40,000 | Uncertified; budget exhausted |
| Moving Moon, 86 years, 1° band | 209,470 | 1,151 contacts |
| Moving Moon, 86 years, 3° band | 222,614 | 1,151 contacts |
| Exact-band-edge plateau, 86 years | 3,000,000 | Named work-budget refusal |

Moving runs took about **0.5 seconds** each; the capped plateau took **8.1 seconds**. These are synthetic Python timings, not Swiss-ephemeris performance measurements.

Crossings, including a hidden crossing, were not accepted as near-misses. Exact-edge plateaus and 0/360 wrap cases worked. Horizon-clipped rootless stretches remained unresolved. The angular tolerance is explicit; astronomical speed maxima and the claimed five-second storage-rounding allowance remain unqualified by independent source/precision evidence.

**Independence, readers and tests**

- **Runtime kernel imports:** MR and ND have none. NM imports only `contact_reconstruct` at **NM:220**, appropriately implementing the ONE-band ruling. Its shared geometry remains a shared failure surface.
- **Test imports:** measuring tests import MR; ND tests import ND; near-miss tests import NM/`utc` and `contact_reconstruct` at lines **333, 350, 391, 530**. DB tests import MR and A5.3 fixture/bootstrap helpers at **17–19**. Measuring tests additionally import scorer registry/extract for parity. MH imports no kernel module.
- **Schema:** checked baseline `life_events` at `001_baseline.sql:463`, expanded baseline at `platform/supabase/migrations/0001_brahma_baseline.sql:2056`, migration **423**, migration **457**, and later references including **691**. `domain`/`event_type` exist; standalone `subcategory` is not established. The provenance-ID mismatch is finding 1.
- **SQL:** publication, seal, record and window names/columns match migrations **1081, 1153, 1155, 1156**. Reader statements are parameterized SELECTs. Unbounded support ranges refuse by name; empty support remains empty. Aware horizon normalization and stored Decimal comparisons pass. The absent near-miss table remains explicitly unknown through `to_regclass`.
- **Useful regression tests** now detect P4 union arithmetic, testimony inclusion, midnight counting, missing closest evidence, incorrect ordinals/orbs/identity, non-finite stored values and missing search limits.
- **Remaining assurance gaps:** tests protect the obsolete dating refusal and incorrect Jupiter contribution; they miss the five blocker probes above. Shared-band equality checks prove consistency, not independent geometric correctness. The noninterference helper detects changed supplied outputs, but no actual layer-on/off execution was demonstrated.
- **Mutation inspection:** **74 mutants plus two declared EQUIVALENTs**. Every replacement target occurs once and every replacement compiles in memory. Both equivalence explanations are justified. A zero-exit baseline is required. Only the extracted classifier was exercised with in-memory XML; no mutation kill count is verified.

I did **not** verify database execution or production rows, real ephemeris accuracy/runtime, astronomical speed maxima, builder-table equality, job wiring, stationless-body enforcement, source/precision identity binding, full-domain search provenance, completed full-build census, or actual layer-on/off scored extracts and all five endpoints. Those remain acceptance obligations after the reproduced merge blockers are corrected.

