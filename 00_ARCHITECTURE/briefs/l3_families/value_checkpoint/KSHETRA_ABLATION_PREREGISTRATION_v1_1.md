---
artifact: KSHETRA_ABLATION_PREREGISTRATION
canonical_id: KSHETRA_ABLATION_PREREGISTRATION
version: "1.1"
status: PREBUILD_AWAITING_G1_FREEZE
produced_on: 2026-10-16
supersedes_for: KĀLA-YANTRA VC-1 only; the Nirmāṇa v1.0 source is preserved
ruling: NR-KALA-R12-20261006
runtime_effect: none
changelog:
  - "1.1: amend ruling-10 protocol for the full repaired G1 baseline, immutable tracker binding, per-stratum censoring and four-way reporting; preparation only under SR-A4-01."
---

# Kṣetra value checkpoint — amended pre-registration

## §1 — Purpose and limits

Does the field's trajectory segment explain **what changed between adjacent chapters** beyond
Saṅgam plus Taraṅga? This is explanatory/discriminative value, not calibration, prediction accuracy,
or causal effect. No experimental result is claimed. No arm is generated or scored by VC-1.
This declaration and its machine-readable companion `preregistration.json` have no runtime effect.
The latter is a procedural declaration, not an experiment runner, scorer or tracker admission hook.

The original Q06 text, retained from v1.0: **“L3-Q06 — How does this chapter differ from the preceding
one? Distinction: recurrence with changes in participants, conditions, clocks, relationships and
uncertainty. Falsifier: matched mechanism identities across intervals; no universal narrative template.”**

A non-approved checkpoint parks **G2**, preserves the G1 repair and evidence, and never changes a
production head. The original §5.2's blanket asset/P1 parking and §6's retired stage-3 timing are
replaced by NR-KALA-R12 and the campaign's VC-1 → VC-2 → D-VC ordering. This author never scores.

## §2 — Baseline and freeze protocol

**Preparation is complete only as a declaration. Execution freeze is pending.**
`/Users/Dev/kalayantra/run/G1_BASELINE.json` was absent when this copy was prepared. G1 head SHA,
code digest, landing commit and tracker record are therefore null in the declaration, not guessed.
A content seal is not an accepted G1 baseline, an execution authorization or an earned checkpoint.

The baseline must be the **full G1** of ALGO §3.20, repairs (a)–(g): canonical graha/system identities
and typed sign/Yoginī lords; canonical clock weights; admitted adapter suppression inputs and effective
negative-space states; pinned `as_of` and axis; canonical-ayanāṃśa rarity with disclosure; working or
removed insight detectors; **all** envelope, switching, Moon/Lagna, clock/scenario, mask and horizon
breakpoints plus adaptive refinement. Keep the functional form and declared seeded coefficients.
Transit evidence consumes the judge by `window_ref`; internal continuous kinematics remain evaluation
knots (B8-6), not served transit verdicts. No G2 or compact approximation is substituted.

The cockpit must perform these steps in order, with independent exact-head acceptance:

1. Obtain the real full-G1 freeze receipt after K5-G1b's obligations are accepted; verify the
   receipt's head, code inventory digest, repair evidence, input/convention pins and merged provenance.
   A syntactically valid digest or a builder's assertion is not that evidence.
2. Create an immutable **external binding receipt** containing `G1_head_sha`, `G1_code_digest`,
   `preregistration_commit` (the full landing SHA), `declaration_sha256` (raw bytes of this markdown),
   `protocol_sha256` (raw bytes of `preregistration.json`), and `baseline_receipt_sha256` (raw bytes of
   the accepted G1 receipt). Record the receipt and these identities in the tracker, and add the
   resulting `tracker_event_ref`. Do not fill in the sealed declaration's null fields in place.
3. Read back the tracker record and prove it precedes **VC-2 READY** and the first generated output
   or inspected result. The controller must retain VC-2's readiness gate until this check and its real
   upstream dependencies are satisfied; merging this preparation alone cannot discharge that gate.
4. Generate every VC-2 arm, commit outputs verbatim and prove their second-run byte equality before
   either judge scores. Only after both judges return may the order map be revealed and D-VC adjudicated.

`DECLARATION_SEAL.json` hashes the two declaration files and the preserved v1.0 source. Regenerate
it by `python3 00_ARCHITECTURE/briefs/l3_families/value_checkpoint/seal_declaration.py --write` **only before**
execution freeze. The landing SHA and tracker binding are deliberately external to avoid a self-hash.
After execution freeze, any change to the protocol, rubric, population, selection, baseline or budget
requires **a new item, new version, new seal and new tracker record before new outputs**. Existing
outputs invalidate that run; never silently re-seal or re-use them. These tests detect declaration drift;
they do not establish a real tracker record, independent review, consent or upstream completion.

## §3 — Population, pairs and arms

Use consenting persons with real outcome records and `evaluation_eligible = true`, within the
campaign's canonical chart scope `482012f1-710e-4a25-994a-93821f5871aa`. The abbreviated second-chart
identity in v1.0 is not an executable identifier. Synthetic/test charts have
`evaluation_eligible = false`: never include them in n, never replace real evidence with fixtures.
Obtain the six calibrated class identities and non-synthetic prior provenance from the accepted G1
inputs; do not guess identifiers or label the G1 model itself empirically calibrated. Missing identities
or priors make the class not evaluable.

Enumerate **every adjacent mahādaśā pair** whose two chapters are fully inside the chart's documented
LEL-covered span. Fix period identity, chronological zero-based pair index, half-open chapter bounds,
LEL coverage reference and event count in the selection inventory before generating outputs. Boundary
instants belong to the later chapter. Event counts count unique LEL event identities in the pair span;
use consented outcome data only for selection/coverage, never as model inputs or judge context.

Select no more than eight pairs per chart by ascending lowercase SHA-256 of UTF-8
`<chart_id>|<pair_index>`, tie-break by integer pair index. An ordinary candidate has an event count
at or below the nearest-rank lower quartile: sorted counts, rank `ceil(0.25 * N)`, one-based, including
ties. First reserve the lowest-hash ordinary candidate, then fill remaining slots in hash order.
At least one ordinary control must remain **scored**, and at least two pairs must remain scored in
an evaluated stratum. If no eligible/control pair exists or censoring removes the control, report
`insufficient_evidence`; do not substitute a dramatic pair or backfill after scoring.

The fixed arms are:

| Arm | Information added |
|---|---|
| A | Saṅgam windows: interval, score/measure and witnesses; no within-interval shape or term composition |
| A′ (`A_prime`) | A plus Taraṅga's monthly waveform: shape, no segment term composition |
| B | A′ plus **G1** trajectory segments, the four stored term components, weakest link and suppression term |

Use the same pinned input snapshot, horizon, periods, conventions and renderer. Shared information is
identical; only the registered additions differ. The PLAN §10 judge/jury/field comparison is implemented
through these named ruling-10 arms, not by silently replacing them with another experiment. Present
all arms in the same plain table layout (interval, witnesses, shape, components; unavailable columns
explicit), with no prose embellishment. Use an equal **1,200 whitespace-delimited word** ceiling per
arm per pair; count table headers and values, omit only the blinded label from the count. Overflow is
`not_evaluable`, never selective truncation. Record actual input and presentation sizes for all arms.
An unavailable required arm is not an empty/quiet result.

Label outputs only P/Q/R. Seed = the first eight hex digits of the **protocol** SHA-256 interpreted
as an unsigned integer. VC-2 must pin the PRNG/shuffle implementation and per-pair order map in its
reproducibility manifest. Shapes make blinding partial; disclose this to judges. Seal the order map
before judging and reveal it only after both score sheets return. Judges never receive LEL events.

## §4 — Independent scoring

Primary: a fresh-context review agent with no prior exposure to the packet or outputs. Secondary:
**Kimi K3, effort max**, using a different tool and the identical sealed inputs, in an isolated
read-only context. These are the original named roles, not a claim that either ran. A replacement
requires a recorded ruling before judging; do not quietly use the author or executor. The executor
hands off only this rubric and blinded outputs. The author sees outputs only after both judges
return, never scores and never adjudicates. Native adjudication remains the ruling-sheet assignment;
D-VC's controller records its authorized decision path, never treating an author's score as adjudication.

For **participants, conditions, clocks, relationships, uncertainty**, independently score each arm:

- **0:** dimension absent.
- **1:** change named, without saying what moved.
- **2:** the specific moved operand (graha, route, clock, edge or σ) identified from the output alone.

**Driver (0/1):** does the arm identify the classical operand driving the change, rather than merely
witness presence? **Recurrence (0/1):** does it identify a matched mechanism identity across chapters
with changed participants, rather than a universal narrative template? Require output-line citations
for nonzero scores. No reward for length, confidence or ornament; no inference of what an arm could
have said. `cannot tell` goes to adjudication, not zero. Preserve both raw sheets. Any disagreement
on driver, dimensions or recurrence goes to native adjudication; never average it away. A pair
adjudicated `ambiguous` is censored across all arms and all score items for its stratum.

## §5 — Verdicts and censoring

A stratum is `(chart_id, event_class)`. Publish its selected eligible n **before** censoring, ambiguous
n, scored n, ordinary-control disposition and censoring rate; also report the per-chart rate and all
exclusions. Rate = ambiguous / selected eligible pairs, not ambiguous / scored pairs. No selected
pairs means `insufficient_evidence`, not 0% censoring. Ambiguous pairs are excluded from every score
and pass/fail denominator, but retained in the censoring denominator and evidence inventory.

**20% ceiling:** if `5 * ambiguous_n > selected_n`, the stratum's claim is blocked regardless of
remaining n or favourable scores. Exactly 20% does not exceed the ceiling. A per-chart rate above 20%
also blocks that chart's claim. Report `insufficient_evidence`; pooling never rescues a blocked stratum.
All six intended class strata must be reported, including unavailable ones; repeated chapter pairs
across classes do not constitute independent persons or extra independent chart-level evidence.

For evaluable, adequately evidenced strata, all three conditions must hold:

1. **Driver:** B > A′ on a strict majority of scored pairs (`2 * wins > scored_n`), and B < A′ on none.
2. **Distinction:** on at least one scored ordinary pair B = 2 in a Q06 dimension where A′ ≤ 1.
3. **Recurrence:** B = 1 on at least half the scored pairs (`2 * recurrence_ones >= scored_n`).

Anything partial is `fail`. Report four-way verdicts **per arm and stratum**, with raw scores for A
and A′ and their exact comparison role, plus the B-versus-A′ incremental claim. A and A′ are
comparators: do not mechanically label them failures because they lack B's additions. Their per-arm
verdict uses the same three criteria against A′; A′ ties itself and thus fails the incremental-driver
criterion if evaluable, explicitly meaning **no added segment claim**, not a failed Saṅgam product.
No separate predictive-performance verdict is inferred.

Verdict precedence is `not_evaluable` (invalid/mismatched freeze, missing required inputs/arms or
independent scoring) → `insufficient_evidence` (no pairs, fewer than two scored pairs, missing scored
ordinary control, unresolved adjudication or ceiling exceeded) → `fail` (any conjunct false) →
`pass` (all conjuncts true). Never pool away a failed/unevaluable stratum. The checkpoint is approvable
only when every intended stratum is pass; otherwise record its exact four-way outcomes and park G2
with preservation. D-VC is an adjudicated checkpoint, never an automatic production flip.

## §6 — Evidence and handoff

VC-2 retains, without scoring: the immutable freeze binding and tracker reference, G1 receipt/head/code
digest, consent and eligibility references (no private outcome text in public artifacts), selection and
LEL coverage inventory, class/prior provenance, source/input hashes and convention pins, renderer and
budget measurements, seeds/order map, verbatim outputs and second-run reproducibility digest.
At D-VC add both raw score sheets and their operand citations, adjudication decisions/reasons,
per-stratum and per-chart counts/rates, per-arm four-way outcomes and the recorded checkpoint decision.
Report omissions and gaps; never manufacture a score, consent, baseline value or green detector.

The cockpit owns tracker writes and actual freeze, VC-2 owns outputs, independent judges own scoring,
and D-VC owns adjudication/recording. Tests here only protect this declaration. No DB suite, ephemeris
calculation, writer change, migration, production operation, populated-chart rebuild or activation is
needed or performed. Existing runtime aggregates and writer digests have no changed inputs; the only
new aggregate is `DECLARATION_SEAL.json`.

## §7 — Interpretations and source anchors

The following are **(I) INTERPRETATION**, fixed before outputs, not measured claims:

- **Preparation versus freeze:** seal the declaration bytes now; bind the missing real G1 receipt and
  landing SHA externally before VC-2 READY. Alternative: invent pins or claim an actual freeze now.
- **Full baseline:** require (a)–(g), following ALGO and KYD-9, even though R12's older text enumerates
  (a)–(f). Alternative: test a partial repair or omit the breakpoint requirement.
- **Scope:** canonical chart only under D-SCOPE; alternative: v1.0's two-chart population. Additional
  consenting charts require a separately authorized version and full identities before outcomes.
- **Strata:** chart × calibrated class, plus per-chart ceiling; alternative: chart-only censoring.
  This prevents a missing class being concealed by pooled evidence. No invented class identifiers.
- **Selection:** nearest-rank quartile, stable indices, reserved lowest-hash ordinary pair and a
  minimum of two scored pairs implement “several” plus the ordinary control. Alternative: unreserved
  first-eight selection or an unspecified percentile/minimum that can be chosen after scoring.
- **Budgets:** identical layout/source information with a 1,200-word ceiling, overflow not evaluable;
  alternative: unbounded text or arm-specific trimming. It is a procedural limit, not a chart value.
- **Adjudication:** route every scored-item disagreement to the native, and censor the entire
  stratum-pair if ambiguous. Alternative: only driver disagreements adjudicated, other scores averaged.
- **Four-way reporting:** apply the incremental criteria per arm against A′, explicitly labelling the
  baseline's self-comparison; all intended strata must pass to approve G2. Alternative: invent an
  independent predictive rubric for A/A′ or pool incomplete class evidence into a pass.

Binding source anchors (repository-relative, line at preparation; the cited sections govern):

- `CLAUDE.md:61` §I; `CLAUDE.md:130` §N.7 and `:139` §N.8 (honest nulls and earned signals).
- `00_ARCHITECTURE/control/kalayantra/plan_model.json:4425` VC-1; `:4466` VC-2; `:4501` D-VC.
- `00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md:30` NR-KALA-R12.
- `00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md:406` §8.1 ruling 10;
  `:457` §9 row 7; `:485` §10 Value.
- `00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md:431` §3.20 G1.
- `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md:43` G3; `:90` KYD-9.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_RULING_SHEET_v1_0.md:61` ruling 10.
- `00_ARCHITECTURE/briefs/nirmana/l3_autonomous/briefs/KSHETRA_ABLATION_PREREGISTRATION_v1_0.md:11`
  Q06 text; `:35` judges; `:53` arms; `:61` selection; `:80` rubric; `:105` conjuncts; `:119` censoring.
