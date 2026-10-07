VERDICT: REJECT

The memo should not be sealed as written. Its useful proposals are undermined by four material problems: restricting standalone near-miss windows, extending a P3 decision into P2, incorrect bereavement-density reasoning, and using held-out outcomes to select future rules.

Reviewed checkout: `48ef79483ff1a40611846800b4c120d114c83a86`. The two reviewed service directories have no changes relative to the memo’s cited `dcbf67e60`.

Below, `rules/` and `kernel/` mean `platform/python-sidecar/services/gochara_rules/` and `platform/python-sidecar/services/gochara_kernel/`; document references are under `.brief/`.

## A. Sandhi meaning — AMEND

**Amended rule:** Adopt R2 explicitly as the delegate’s operational interpretation: every certified, complete, rootless near-miss belongs to the separate `near_miss` kind. Add a descriptive junction field, without admission or scoring consequences, recording verified sign/nakshatra crossings of the transiting body and actual MD/AD transitions within its full `[t_in,t_out)` stretch. Record source identities and computation completeness; missing coverage means unknown, not an empty junction set.

R2 is defensible in context, but **not conclusively established by the owner’s wording**. “If it falls in the sandhi” is linguistically conditional; “the dignity of that window that opens up” supports independent product presence. Ruling 12 authorizes resolving that ambiguity. It does not turn the chosen interpretation into a classical definition. (`RULING10.txt:2`; `RULING12.txt:1–3`.)

The proposed flag is implementable:

- Both ingress kinds exist in the substrate, with body/convention identity and solved instants: `kernel/substrate.py:238–247,497–524`.
- The pinned dasha loader exposes the underlying rows: `kernel/dasha_read.py:118–148`.
- Half-open intervals and parent linkage are specified in `GOCHARA_DESIGN_SPECS_v1_4.md:496–507`.

Two corrections matter:

1. **“Contains a junction” is what this measures.** It does not establish that the closest approach occurred at a junction, that the body remained in a sandhi zone, or that the event was gaṇḍānta. A near-miss close to a cusp without crossing it will have no ingress flag. Consequently, this does not fully test R1.
2. **Use the current pin.** The supplied specification names build `1f89fd4c…`; current code records the SETTLED-1 repin to `75524b3e…`. Do not copy the old specification’s dates into this detector. See [permission.py:11](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/8ce6ffaa-67aa-41a8-a3dd-cd26ebae1545/scratchpad/rev-p2/platform/python-sidecar/services/gochara_rules/permission.py:11).

Include ingress at `t_in`, exclude ingress at `t_out`, deduplicate coincident MD/AD boundaries, and preserve uncertainty where event-time precision cannot resolve membership.

## B. Near-miss treatment — AMEND

**Amended rule:** Every certified near-miss, regardless of transiting agent, opens its own independently visible, categorically lower-standing, unscored window. Fast-agent near-misses may additionally annotate overlaps, but their standalone intervals remain visible. No near-miss enters contact-support unions, P4 influence, evaluated candidates, score/peak calculations, ranking, or evaluation-coverage accounting.

The categorical interpretation of **“lower, not zero” is sound**: lower standing and nonzero product presence do not require an invented numerical weight.

The slow-only restriction is not sound here. Independent parsing of the supplied list gives:

| Body | Reported near-misses |
|---|---:|
| Jupiter | 3 |
| Saturn | 5 |
| Mercury | 10 |
| Mars | 3 |
| Venus | 3 |

Thus 16/24 lose standalone windows under B. This reverses the reconciled requirement that a near-miss opens its own window even without a contact window (`G11_DECISION_RECONCILED_v1_0.md:5–8`). A `refiner_no_window` listing does not provide that interval experience.

There is also **no evaluation-density justification** for removing these windows: the proposal already excludes all near-misses from evaluation.

The isolation requirement must cover more than endpoints or NULL scores. A NULL-scored row can still change candidate counts, coverage, merges or qualification if it reaches the wrong consumer. Require identical scored extracts, supports, members, peaks, rankings, candidate counts and all five endpoint results with the near-miss layer enabled/disabled. Preserve contact identity bytes separately.

Current sweep exclusion supports this separation, but does not prove the future implementation: `kernel/window_sweep.py:759–768`. No near-miss may serve as the slow support admitting a scored fast contact; overlapping annotations must not leak through E’s scoring route.

The claimed exact-degree passage, even if verified, would not by itself prove that every rootless approach has a uniformly lower astrological effect. Categorical standing remains an authorized product convention.

## C. Natal Sun for bereavement — AMEND

**Amended rule:** For the existing **father-specific** bereavement class, admit natal Sun as a derived K-B target under explicit ruling provenance. In P3, Jupiter/Saturn may conjunct or aspect it; Rahu/Ketu may conjunct it. In P4, only Jupiter/Saturn contribute to `infl()`. Use the pinned substrate point-contact bands; preserve separate scoring-orb qualification. Keep H and maraka testimony unchanged, and assess the entire class’s admitted-day union against its existing budget.

Sun as a paternal significator is doctrinally reasonable. **Sun signifies father; it does not specifically signify father’s death.** The registry’s own note says “father” (`rules/registry.py:176`). The death-specific application is a derivation, not established merely by that citation.

An acharya could reasonably dispute:

- treating benefic Jupiter contact as equivalent occurrence evidence to malefic affliction;
- deriving bereavement without sufficient natal promise, period condition and relative-specific longevity/maraka context;
- treating “Sun as father’s reference” as an unconditional degree-contact death rule.

### The orb claim is substantially correct, with an important qualification

- `rules/admission.py:32,56–65` defaults the standalone house-lord helper to **5°**.
- The actual point materializer selects `orb_conj_slow` or `orb_drishti_slow`, then passes that band to the contact-span solver: `kernel/record_store.py:99–100,253–269`.
- Both bands are **1°**: [convention.py:85](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/8ce6ffaa-67aa-41a8-a3dd-cd26ebae1545/scratchpad/rev-p2/platform/python-sidecar/services/gochara_kernel/convention.py:85).

**Therefore 1° governs the inspected builder’s point-support geometry; 5° governs the standalone helper’s default calculation.** Their disagreement must not be presented as oracle parity.

Separately, the activity-factor registry still declares its point-scoring orb unratified and returns an unqualified state until resolved (`rules/registry.py:396–443`). A geometry constant does not prove that ND-ORB has been settled for scoring.

### The memo’s budget argument is wrong

Bereavement’s actual H is the ninth and its first/second/seventh/eighth offsets: lagna houses **{9,10,3,4}**, not the earlier parental-illness proposal’s **{9,2,4,8}**. See `rules/registry.py:66–71,131–137`.

Recomputing sign-bin reachability from the implemented full aspects gives:

| H | Jupiter | Saturn |
|---|---:|---:|
| Actual bereavement {9,10,3,4} | **12/12** | **10/12** |
| Earlier parental proposal {9,2,4,8} | 10/12 | 11/12 |

The memo copied the second row into its bereavement argument. Source offsets: `kernel/convention.py:45–48`; whole-sign implementation: `kernel/materialise.py:128–156`.

**Jupiter alone therefore admits bereavement through P3 at every sign position.** With complete residence/aspect coverage, this structurally produces continuous P3 admission. This is a logical consequence of the rule, not a measured production-day result.

P1/P4 cannot constrain it: paths combine by **union**, not conjunction (`SEALED_DOCTRINE_v3_0.md:112–122`). The conditional K-B rollback also does nothing when the class was already outside budget without K-B.

## D. Karakatva satisfying P1 — AMEND

**Amended rule:** Add `karakatva` as an explicitly ruled, `uncited_extension/scored` alternative for P1 prerequisite (2), restricted to MD/AD and to a versioned, affected-person-specific class-karaka mapping. Evaluate the **period anchor lord**, not necessarily the transiting agent. Preserve all existing period and transit predicates; PD remains testimony. Record the derived licence’s provenance on the admission-bearing result.

This is coherent as a **substantive amendment**, not as an interpretation of the current prerequisite. The frozen wording requires a “natal bhāva relationship” and lists occupancy, ownership, dispositorship and association (`GOCHARA_DESIGN_SPECS_v1_4.md:245–261`). Karakatva is natural signification, not natal house relationship.

“Fourth relation kind” is inaccurate: there are already **four distinct names and five registry rows**, because dispositorship has node/non-node variants (`rules/registry.py:319–342`). Karakatva would be the fifth distinct name.

The current implementation:

- scores occupancy and ownership;
- returns testimony for supported dispositor chains;
- has no karakatva branch;
- returns unknown immediately when H is unknown.

See [permission.py:104](/private/tmp/claude-504/-Users-Dev-Vibe-Coding-Apps-Madhav/8ce6ffaa-67aa-41a8-a3dd-cd26ebae1545/scratchpad/rev-p2/platform/python-sidecar/services/gochara_rules/permission.py:104). Preserve the unknown-H behavior unless explicitly amending it too.

**The proposed data is not ready.** `KARAKA_SETS` exists, but the production-source search found no consumer under that symbol. Its rows are nested records, not a direct set of planet names. Several ND-H assignments are absent; parental_event currently contains both Sun and Moon; psychological_arc lacks the proposed Moon assignment. `_karaka_row()` also hardcodes Phaladipika/verse-cited provenance and cannot honestly encode every new UK/ruling-backed mapping (`rules/registry.py:160–219`).

**The density claim is incomplete.** P1 includes not only the anchor’s own/exaltation/debility residence, but Sun/Jupiter transits through another AD lord’s exaltation sign and Sun through its debility sign (`kernel/evaluator.py:498–522`). Moreover, occupying 3–4 sign bins is not a bound on elapsed days within a particular period.

Doctrinally, natural significators delivering their significations during their dashas is a defensible practice premise. An acharya would dispute elevating it to a sufficient event-specific licence regardless of functional lordship, placement, strength, affliction and promised outcome—especially **wealth→loss, father→death, sickness→surgery**. Authorize the engine extension honestly; do not label those event inferences direct textual rules.

## E. Fast agents in P2/P3 — REJECT

**Replacement rule:** Do not impose a universal slow-support prerequisite. Preserve P2’s individual planet rules. Change P3 opener/refiner status only through explicitly versioned, class-and-mechanism-specific rules established before outcome inspection. Until such rows are approved, retain the existing selected P3 contract and report its density failures.

**P2 should be exempt.** Its stated basis gives individual Moon-frame results for Sun, Mars, Mercury and Venus. Requiring a simultaneous slow transit adds a necessary condition absent from the cited rule as represented by the specification and code.

The implementation is explicit:

- P2 gain rows enumerate each planet’s favourable houses: `kernel/evaluator.py:358–378`.
- Adverse scored rows include Sun/Mars/Jupiter in 12/8/1 and Saturn in 8; Sade-Sati rows are testimony: `kernel/evaluator.py:381–404`.
- Venus has nine favourable houses: `rules/favourable_houses.py:47–67`.
- P2 currently requires `house_from_moon`; vedha qualifies rather than excludes: `rules/registry.py:725–739`.

These broad sets raise a legitimate question about mapping generic fortune into specific event occurrence. They do not justify rewriting their planetary prerequisites as though Phaladipika required slow-body concurrence.

**The P3 documentary discrepancy is real.** Sealed doctrine says “slow-body” (`SEALED_DOCTRINE_v3_0.md:147`); frozen specification declares the nine-agent set and unrestricted P3 contact predicate (`GOCHARA_DESIGN_SPECS_v1_4.md:215–229,276–285`). Current code enumerates that set, with Moon-agent transit records removed from stored execution by AM-4 (`kernel/evaluator.py:219–252,583–621,636–639`). I found no explanation in the supplied documents resolving that widening.

Nevertheless, sealed doctrine also allows source-supported agents at their appropriate grain (`SEALED_DOCTRINE_v3_0.md:109–110`). A broad timing hierarchy cannot override a specific fast-agent rule.

A class-specific policy is preferable. Mars may carry acute illness/surgery testimony or triggering mechanisms; Mercury and other fast bodies may matter for examinations and travel. The packet supplies no outcome-independent analysis demonstrating that all such opportunities occur inside slow-agent supports. **Potential signal loss is credible; actual lost predictive signal is unmeasured.**

The “roughly four-fifths” calculation is not established: Sun/Mercury/Venus are correlated, house sets overlap, Mars has additional aspects, and sign-bin fractions are not historical duration fractions.

Finally, this is a substantial frozen-design amendment: prerequisite registry, admission, temporal support, sweep membership, objectives, independent verification, version selection and measurement all change. Adding a Boolean overlap check alone is insufficient.

## P1/P2/P3 findings

| Path | Verified finding | Consequence |
|---|---|---|
| **P1** | The production materializer evaluates the anchor lord’s relationship and clips support to that anchor’s level-specific periods (`kernel/record_store.py:1182–1223,1483–1489`). | Karakatva must use the anchor and propagate its ruling provenance. Updating only the registry table is insufficient. |
| **P2** | Individual fast-agent residence rules currently open supports. P2 is restricted doctrinally to the native’s fortune, but the enumerator constructs adverse rows with `affected_person="native"` without a relative-class exclusion (`kernel/evaluator.py:379–404`). | Explicitly verify exclusion of both father-bereavement and parental-event direct P2 evidence; changing a person map elsewhere does not achieve this. |
| **P3** | Every admitted scored record contributes to the support union (`kernel/window_sweep.py:713–717,791–802`). Bereavement’s Jupiter house support covers all twelve positions. | Slow-only admission cannot cure this class’s structural saturation. The generation must fail the unchanged budget rather than claim success through P1/P4. |

For any future refiner rule, define same-grain identity precisely: chart, generation, class, affected person, frame, path/version and resolution. Compute the opener union first. A refiner contributes only on its intersection with each opener component; it cannot bridge components or contribute outside its own support. Missing opener computation is unknown, not `not_admitted`.

The current P4 implementation demonstrates why both stages matter: its record predicate tests overlap, while the sweep separately constructs the Jupiter/Saturn intersection (`kernel/record_store.py:1469–1481`; `kernel/window_sweep.py:791–800`).

## F. Pre-registered checks — insufficient; amend

**A, B, D and E prescribe calibration on held-out outcomes.** Choosing junction scope from hit rates, promoting near-misses from held-out hits, retaining karakatva by held-out overlap, and restoring fast agents after two additional held-out hits are all rule selection.

“Next generation only” does not fix this. The protocol defines held-out as **not used for calibration**, expressly permits development-event calibration, and calls path ablations non-gating diagnostics (`EVALUATION_PROTOCOL_v2_3.md:280–300`).

Required replacement:

- Freeze one primary candidate before scoring; preserve its result even if it fails.
- Report these ablations separately as diagnostics.
- Use development data for rule selection. If these held-out events inform later choices, disclose that they have become development evidence and obtain independent evaluation data; a new generation label does not restore holdout status.
- Treat C’s density comparison as an engineering diagnostic against the already frozen budget. Evaluate **P3, P4 and the full class union**, including cases where both variants fail.
- Keep all five endpoints, rank eligibility and degeneracy checks. “In band plus more hits” omits timing, honesty and ranking requirements.
- For near-miss-only comparisons, apply the same no-contact condition to controls. Split by body, duration and class; junction-containing stretches have different exposure opportunities. Twenty controls per event are not twenty independent real events.
- Add the inherited G11 geometry, identity, sealing and noninterference checks (`G11_DECISION_RECONCILED_v1_0.md:11–19`).

No significance or validated predictive claim follows from these small, overlapping diagnostic groups.

## G. Factual errors and delegation limits

Beyond the corrections above:

- **P4 admits Jupiter/Saturn only.** C must not be implemented as allowing Rahu/Ketu agents into P4 merely because its sentence groups all four agents together (`kernel/evaluator.py:299–323`).
- **ND-H condition 4 is a reporting obligation**, not the specific reversion mechanism attributed to it. The explicit DVI rollback appears in ND-H item 1 (`ND-H-20261005_DECISION_BY_DELEGATE.md:25,41`).
- **Version creation does not select a version.** Current `BOUND_PATH_REFS` and `SELECTED_PATH_REFS` still name 1.0.0; per-class overrides are separate (`kernel/rule_registry.py:76–110`).
- The memo cannot establish “no doctrinal mechanism” from unsuccessful text searches or unread verse bodies.

Ruling 12 delegates A–E sufficiently to make recommendations on those questions. It does **not clearly authorize expanding E into a new P2 prerequisite**, altering the protocol’s held-out meaning, relaxing adverse budgets, or declaring classical authenticity. Those should not have been closed implicitly.

## FINAL RULES

These are the five replacement rules I would seal as design decisions—not as a claim that implementation or empirical acceptance is complete:

1. **Near-miss classification:** A near-miss is a certified complete rootless point-contact stretch with positive clearance; unresolved geometry remains unresolved. Adopt R2 operationally. Store verified junction occurrences and completeness under the current pinned sky/dasha conventions, without changing admission or score.

2. **Near-miss serving:** Every qualifying agent’s near-miss opens a standalone, visibly lower-standing interval. Store it separately with `score=NULL`, reason `near_miss_unscored`, and geometric proximity. It cannot affect contact identities, evaluated supports, P4, scores, ranks, candidate counts or endpoint accounting. Prove evaluation noninterference.

3. **Father’s Sun target:** Add natal Sun K-B edges for father-bereavement under derived ruling provenance: Jupiter/Saturn conjunction/aspect and nodal conjunction in P3; Jupiter/Saturn only in P4. Use the pinned 1° builder bands for current point geometry; do not substitute the 5° helper default or silently resolve the separate scoring-orb decision. Preserve H, testimony and the full-class adverse budget.

4. **P1 karakatva:** A versioned, person-specific class-karaka assignment may satisfy prerequisite (2) for its MD/AD **anchor lord** under explicit `uncited_extension/scored` authority. Preserve period restrictions, existing transit forms, unknown-input behavior and PD testimony. Implement the mapping, consumer, provenance and independent verifier together; claim no numerical density bound.

5. **Fast-agent policy:** Add no blanket slow-overlap gate to P2 or P3. Preserve P2’s individual planet rules. Retain the selected P3 contract until a separately versioned, outcome-independent class/mechanism rule changes opener/refiner status. Any approved refiner is restricted to overlap with its own grain’s independently admitted opener components and cannot extend or bridge them. Density failure remains failure; it is not permission to tune on held-out events.

**Not verified:** classical-text database contents, quoted loci, Sanskrit, translations/OCR, complete verse conditions, live database contents, actual sky/dasha coverage, the 24 stretches’ ephemeris certification, deployed behavior, historical day shares or predictive performance. I inspected source and documents and independently checked list counts and sign-bin arithmetic; I ran no project tests, builds, database queries or network requests and modified no files. Prior memory supplied orientation only.

