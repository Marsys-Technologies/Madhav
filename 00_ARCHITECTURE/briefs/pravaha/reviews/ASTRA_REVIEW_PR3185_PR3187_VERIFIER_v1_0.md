VERDICT: REJECT — PR 3185 and PR 3187.

I found merge-blocking arithmetic and verification defects despite **165 passing pure tests**.

The supplied checkout was `f58a42e3f`, which lacks the requested modules. I reviewed the matching, clean local stack instead: **3185 at `2bfdb1c7b`; 3187 at `da4f5f546`**, including its complete eight-file diff against `origin/main`. I read `.PRIOR_REVIEW.md` and the supplied rulings, including both ERRATA. No files changed; no database or network used.

References below use:

- **MR** = [measuring_report.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095/scratchpad/wt-ndv/platform/python-sidecar/services/gochara_kernel/measuring_report.py)
- **NM** = [near_miss_verifier.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095/scratchpad/wt-ndv/platform/python-sidecar/services/gochara_kernel/near_miss_verifier.py)
- **ND** = [nd_h_tables.py](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/b494bf37-e4fb-4e8f-b5fd-87e2fcc3f095/scratchpad/wt-ndv/platform/python-sidecar/services/gochara_kernel/nd_h_tables.py)

All probe timestamps below are UTC.

**Merge-blocking findings**

1. **P1 — PR 3185: P4 counts Jupiter OR Saturn, rather than their simultaneous influence.**  
   **MR:420–436**, particularly `P4_without_dvi`, `P4_with_dvi` and `class_union`.

   Concrete input: P4 Jupiter support `[2000-01-01, 2000-01-06)` and Saturn support `[2000-01-04, 2000-01-09)`, over a ten-day horizon. The report returns **8 admitted days**; the P4 intersection is **2 days**. Disjoint supports return positive P4 days too.

   This is not an ambiguity about “P4-alone.” The existing contract explicitly intersects the two agents’ unions: `window_store.py:199–220` and migration `1240_gochara_window_verification_gate.sql:280–299`. Stored admitted P4 records retain their individual support intervals; admission only requires an overlap somewhere (`record_store.py:1469–1481`).

   Intersect **instant intervals before counting calendar days**, then incorporate that result into the class union and contribution calculations. Intersecting day sets would still incorrectly admit disjoint morning/afternoon influences. The P4 variants also omit `via="kb"` altogether.

2. **P1 — PR 3185: the reader promotes testimony into scored admitted-day shares.**  
   **MR:488–492** selects `admission_state='admitted'` without `operator_role='scored'`; `SupportRecord` then loses the role.

   Concrete input: an admitted P1 testimony record with support `[2000-01-01, 2000-01-11)` produces ten `P1_base` days and a 100% share over that horizon.

   Such records are legitimate: `record_store.py:1483–1489` explicitly says scored **and testimony** relationships receive prerequisite result `true`; the record’s role prevents testimony admitting. Migration 1155 stores role and admission separately, and migration 1240’s expected-window calculation filters both.

   Add the scored-role filter and an independently specified testimony exclusion test.

3. **P1 — PR 3185: horizon derivation rejects both an absent log and the documented birth-row vocabulary.**  
   **MR:83, 133–136, 170**.

   Reproduced inputs:

   - `derive_chart_horizon(date(1984,2,5), [], date(2026,10,5))` raises `lel_birth_row_unidentifiable`; it must reach the rebuild-date fallback.
   - A birth row with `category="other"` plus an exact event dated `1998-02-16` raises the same refusal.

   The canonical log uses `category: other`, `subcategory: birth` (`LIFE_EVENT_LOG_v1_2.md:149–150`). The existing event reader identifies `domain="other/birth"` (`platform/scripts/audit/t0_retrodiction/lib/lel.ts:132–138`). The expanded baseline schema contains `domain`; it does not establish `category="birth"`.

   The revised field names match the schema, but the newly mandatory birth-row requirement remains invented. Tests manufacture that requirement through `born(..., category="birth")`, masking the failure.

4. **P1 — PR 3187: the angular minimum certificate does not certify `t_closest`; the verifier accepts a wrong time and refuses the correct one.**  
   **NM:116–137, 327–329**.

   Reproduced with Mars, a 1° band, longitude `100+d(x)`, and a six-day search centred on `2000-01-15 12:00`, where `x` is elapsed days:

   ```python
   d(x) = min(
       1.1,
       0.5 + 0.2*(x + 0.5)**2,
       0.4998 + abs(x - 25/48),
   )
   ```

   This curve respects the 1°/day Lipschitz bound everywhere.

   - True global minimum: **0.4998° at 2000-01-16 00:30**.
   - Certified output: approximately **0.5000° at 2000-01-14 23:59:59.945**.
   - A stored row using the wrong earlier time passes both checks.
   - A row containing the true clearance and true time receives `near_miss_t_closest_mismatch`.

   The error is **24.5 hours**, not ten minutes. Pruning within `CERT_TOL_DEG` legitimately leaves nearly equal minima unresolved in time. Certify the minimizer separately, or expose that uncertainty and compare stored geometry under an explicitly justified policy.

5. **P2 — PR 3187: wrong ordinals and wrong bands have no verification detector.**  
   **NM:224–225, 280–298, 302–335**.

   Concrete input: an otherwise valid row with interval March 1–4, clearance `0.5`, orb `1`, proximity `0.5`, a placed closest time and an empty complete junction field; compare it with matching rederived geometry.

   Both `row_problems` and `compare_sets` return `[]` after either change:

   - `ordinal=999`;
   - `orb_deg=5.0, proximity=0.9`.

   `assign_ordinals` computes ordinals but never compares a stored ordinal. Set matching only binds interval endpoints, clearance, closest time and junction. The wrong orb therefore passes by supplying self-consistent proximity.

   Bind stored identity, orb policy and ordinal to the independently reconstructed object and full-domain ordering.

6. **P2 — PR 3187: Decimal handling stops before the actual comparison.**  
   **NM:219–221 versus 325**.

   Concrete input: the valid row above with `clearance_deg=Decimal("0.5")`, compared with rederived float `0.5`. `row_problems` accepts it; `compare_sets` raises:

   ```text
   TypeError: unsupported operand type(s) for -: 'decimal.Decimal' and 'float'
   ```

   The added Decimal test exercises only `row_problems` (`test_near_miss_verifier.py:441–444`). Normalize and validate numbers at the comparison boundary too.

7. **P2 — both PRs: non-finite inputs can become successful results.**  
   **NM:161–168, 243–254; ND:191–195**.

   Reproduced concrete inputs:

   - Valid near-miss row with `proximity=float("nan")`: both row and set checks accept.
   - `position_at` returning NaN throughout a one-hour Moon search: derivation returns `[]`, rather than geometry unavailable.
   - `dvi_reverts_to_support("property_acquisition", float("nan"))`: returns `False`.

   These are unknown quantities becoming “valid proximity,” “nothing found,” and “guard not exceeded.” Require finite values and named refusals before comparisons or geometry reconstruction.

8. **P2 — PR 3185: the scored-horizon mismatch can change the 40% decision.**  
   **MR:31–36, 48–49, 323–357**.

   The scorer’s convention is established in code, not an unresolved question:

   - `gochara_eval/registry.py:8–21`: **IST calendar dates, inclusive endpoints, 10,334 days**.
   - `gochara_eval/extract.py:65–67`: inclusive clipped day count.
   - `gochara_eval/metrics.py:80–87`: divides admitted days by that 10,334-day denominator.

   MR excludes April 17 and uses 10,333 days. Concrete guard-flipping input: matching Jupiter/Saturn P4 supports

   ```text
   [1998-01-01, 2009-04-26)   # 4,133 days
   [2026-04-17, 2026-04-18)   # observation-end day
   ```

   MR yields **4133/10333 = 39.9981%**, so no reversion. The inclusive scored convention yields **4134/10334 = 40.0039%**, so reversion.

   Consequently, “one day changes no decision” is false. Reconcile the report’s scoring boundary with the scorer before using it for the guard; do not merely document two normal-looking answers. I found no `EVALUATION_PROTOCOL_v2_3` file under `00_ARCHITECTURE` on this branch.

9. **P2 — PR 3187: the complete-search claim drops the shared band detector’s explicit resolution limit.**  
   **NM:142–149, 166–175**; `contact_reconstruct.py:9–13, 28, 75–83`.

   Using the shared band implementation satisfies the ONE-band ruling, but that implementation explicitly does **not** exclude excursions shorter than 60 seconds. NM does not carry that limitation into its result.

   Concrete smooth, speed-bounded Mars input, with `s` seconds after `2000-01-01 00:00`, longitude `100+d(s)`, centre 100°, orb 1°, and a six-hour search:

   ```python
   d(s) = 1 - 0.0001 + sqrt(((s-21)/86400)**2 + 0.00001**2) - 0.00001
   ```

   True minimum is `0.9999°`; the in-band interval lasts approximately **18.93 seconds**. Derivation returns `[]`.

   Preserve the shared detector and its named limitation, and prevent an unqualified complete/verified-empty signal from being attached to this result. The new branch-and-bound cannot recover a stretch the band detector never supplied.

**Further amendments that can follow these PRs, but must precede verification-job acceptance**

- **P2 — incomplete marker accepted:** **MR:249–255, 297–309**. An otherwise accepted view with `marker_horizon=None` passes. A marker containing only `run="all_classes_full"` and the class list has no horizon/schema/digest validation here. Likewise, one populated class plus a complete *declared* class list does not establish a completed full build. The latter limitation is disclosed, but acceptance must not be presented as full-build certification.
- **P2 — junction iterator silently exhausted:** **NM:209–214**. `junction_field(a,b,iter([("sign_ingress", a)]), coverage_complete=True)` returns an empty complete field: the unknown-kind scan consumes the iterator. Materialize once or explicitly reject unsupported input shapes.
- **P3 — stamp checking omits the rule-version claim:** **ND:248–259**. Correct core provenance/role/ruling stamps plus `rule_version="1.0.0"` return `[]`. Add a version check at the eventual composed verifier boundary.
- **P3 — mutation classification is heuristic:** `mutation_check_verifier_side.py:92–112` ignores `returncode` and searches traceback text for `"AssertionError"`. For example, a `<failure message="TypeError: AssertionError is not supported">` is classified CAUGHT although its exception is TypeError. Tighten classification before treating the mutation count as an assurance signal.

**Independent ND-H table check**

I constructed the following expectations from `.ND-H.md` before comparing the implementation’s cells. All these cells match **ND:49–90**:

| Class | CORE | DVI | SUPPORT | K-A | K-B |
|---|---|---|---|---|---|
| achievement_recognition | 10 | 11 | 1, 5, 9 | Sun, Jupiter | — |
| business_launch | 7, 10 | — | 6 | Mercury | — |
| financial_deception | 2, 12 | 6 | 8 | Rahu | — |
| foreign_settlement | 12 | 4 | 7, 9; 10 noted only | Rahu | — |
| parental_event, father | 9, 2 | — | 4, 8 | Sun | Sun |
| property_acquisition | 4 | 11 | 2 | Mars | — |
| psychological_arc | 4 | — | 5, 8 | — | Moon |
| spiritual_turn | 5, 9 | — | 12 | Jupiter, Ketu | — |

Also correct: father frame, unsupported mother row, Saturn’s spiritual testimony restriction, DVI exclusion from P1/P3, strict `>40%`, version `1.2.0`, bereavement’s Sun target and ND-P2 ruling, 1° K-B band, Jupiter/Saturn aspect licences, nodes’ conjunction-only licence, and P4’s Jupiter/Saturn restriction.

A1–A3 remain literal and labelled open. A4 correctly names the scored horizon. No blanket fast/slow admission gate was introduced.

Qualifications: the DVI lord-point case is explicitly unmodelled; psychological-arc P2 exclusion remains labelled **draft**, not sealed authority; the karakatva version is labelled a verifier-side choice. The ERRATA’s withdrawn citations are not reintroduced as verse-level proof in these tables.

**Minimum-search argument, termination and cost**

The lower bound

```text
max(0, (|d0| + |d1| − L·gap) / 2)
```

is sound for a finite, genuinely L-Lipschitz distance function. Therefore the angular certificate is defensible under the stated motion assumption. It does **not** certify a closest-time error, as finding 4 demonstrates. Bisection terminates at the one-second floor; excessive bounds leave an honest uncertified result.

`MAX_SAMPLES=512` limits only the initial grid. For a flat 0.5° distance using Moon’s 16°/day bound, I measured **24,598 evaluations for one day** and **245,782 for ten days**. Across the pinned 31,446-day horizon, that pathological certificate can require approximately **537 million leaf intervals**. There is no practical work-budget refusal.

For a monotonically moving synthetic Moon at 13.176358°/day over the actual horizon, one target required:

| Band | Position calls | Stretches |
|---|---:|---:|
| 1° | 209,438 | 1,151 contacts |
| 3°, the Moon convention | 222,590 | 1,151 contacts |

The cheap synthetic function took about 0.6 seconds; **that is not a Swiss-ephemeris runtime measurement**. Real cost depends on the position provider and number of objects.

The 2-second edge comparison is consistent with two one-second reconstructions. The proximity tolerance has a plausible rounding allowance. The 600-second closest-time allowance has no supporting bound and demonstrably fails. I did not independently establish the astronomical speed maxima.

**Independence, readers and tests**

- **Runtime kernel imports:** MR and ND have none. NM imports only `contact_reconstruct` at line 150. That import is appropriate under the explicit ONE-band ruling, but creates a shared failure surface; the builder’s certifier also uses that module. The speed-table equality test is correctly described as a drift alarm.
- **Test kernel imports:** measuring tests import MR; ND tests import ND; near-miss tests import NM, its `utc` helper, and `contact_reconstruct` for band/bound comparisons. DB tests additionally import the A5.3 fixture/bootstrap helpers. Those are reasonable storage fixtures, not independent astronomical oracles.
- **SQL:** publication, seal, relationship-record and eval-window names and selected columns match migrations 1081, 1153, 1155 and 1156. Queries are SELECT-only and parameterized. The near-miss table is absent on this branch and guarded by `to_regclass`; its eventual schema was not verified.
- **Life-event schema:** checked the baseline, expanded baseline, chart-scoping migration 423, shape migration 457 and later relevant references. Migration 691 defines integrity expectations; it does not establish the invented birth category.
- **Boundary handling:** MR correctly unions overlapping days, clips support intervals, excludes midnight end-days, normalizes aware horizon timestamps and refuses unbounded supports. NM’s Decimal comparison fails as above. Present-but-NULL fields are less robust than missing fields: for example `row_problems(..., t_in=None)` raises an unnamed TypeError.
- **Useful negative controls:** wrong finite clearance, finite proximity, junction contents, extra stored duplicates, zero crossings, wrap-around geometry and clipped stretches are detected. Exact band-edge inclusion works on a plateau. Clipped stretches remain unresolved until followed beyond the horizon, as documented.
- **Tests that protect the wrong claim:** measuring tests at `201–245` positively assert single-agent/union P4 arithmetic. Tests at `48–59` always supply a fabricated birth row, so they do not exercise “no log.” Near-miss Decimal tests stop before set comparison.
- **Tautologies and missing assurance:** `test_measuring_report.py:309–315` recomputes the same report with identical inputs; it does not prove layer noninterference. Shared-band equality tests cannot independently detect defects inside that shared band. The long-stretch test at `test_near_miss_verifier.py:447–451` measures neither sample count nor cost.

I **read but did not execute** the mutation harness. It requires a zero-exit baseline, contains **50 mutants plus one explicitly reported EQUIVALENT**, and all replacement targets occurred exactly once and compiled in memory. The touching-day-range equivalent is justified for the reported counts. A 50/50 kill claim remains unverified here.

I did not verify database execution, production data, real ephemeris accuracy/runtime, builder equality/wiring, stationless-body enforcement, source-identity/precision metadata, or actual layer-on/off scored extracts and endpoints. Those last implementation gaps are acknowledged in the modules; they remain unfinished, not successful verification.
