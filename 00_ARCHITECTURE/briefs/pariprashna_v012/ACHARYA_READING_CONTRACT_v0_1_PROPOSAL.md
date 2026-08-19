---
artifact: ACHARYA_READING_CONTRACT_v0_1_PROPOSAL
canonical_id: ACHARYA_READING_CONTRACT
version: 0.1
status: PROPOSAL — Phase-1 output, awaiting native ratification (not canonical; authorizes no code)
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_v012/PARIPRASHNA_V012_PHASE1_REVIEW_v0_1.md (master review; §7)
  - 00_ARCHITECTURE/PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md (v0.11 — substrate under review)
  - CLAUDE.md §J, §N.6, §N.7, §N.8; PROJECT_ARCHITECTURE_v2_2.md §B; MACRO_PLAN_v2_0.md §3.5
changelog:
  - "0.1 (2026-08-18): initial proposal."
---

# The Acharya Reading Contract — `AcharyaReadingReceipt` v1

## §0 — What this is, and why it is not new doctrine

Every governing principle this contract enforces **already exists** in the
repo's doctrine. What does not exist is a single, versioned, machine-checkable
artifact that a served reading must produce to CLAIM those principles were
honored. Today the claim rests on prompt instructions plus scattered receipts
(PlanReceipt on the plan, completeness receipt on the floor, grades on
citations, verdict_objects in L5). The contract binds them into one object,
per turn, with §N.8 discipline: **every field is earned by a detector, or it
is null.**

The reader never sees this object as prose. They see fluent, plain,
acharya-grade prose (D-14/D-15). The receipt is the audit affordance behind
it — expandable in the dock, exportable in the sealed reading, persisted with
the turn.

**Doctrine trace (each field cites its authority):**

| Doctrine | What it demands | Where the receipt carries it |
|---|---|---|
| B.1 / B.3 | facts ≠ derivations ≠ interpretations; every L2+ claim lists consumed L1 fact ids | `facts_consumed`, `derivation_chains` |
| B.4 | ≥3 candidate interpretations + selected + falsifier for every significant interpretive claim | `interpretation_sets[]` |
| B.6 / B.7 | calibrated 0–1 confidence; ambiguity named, contradictions published | `confidence` (typed), `contradictions` |
| B.10 | no fabricated computation | `external_computation_required[]`, null-not-guessed values |
| B.11 + RS-4 | whole-chart read for interpretive queries; frame-check carve-out for factual | `coverage` |
| §N.6 Serving Density | catalog ≠ confirmed; honest empty via flags | `evidence_grades`, `honest_gaps` |
| §N.7 Narration Fidelity | prose restates cited facts, never re-derives | `prose_binding` (claim-span → receipt-entry map) |
| §N.8 Earned Signal | every status computed by a detector that measures the claim | receipt-level rule: unearned field = null |
| MP §3.5.A/G | probabilistic humility; calibration band or the output is invalid | `confidence`, `calibration_disclosure` |
| MP §3.5.C | safety hard stops | `safety_decision` |
| D-14 / D-15 | zero internal register in prose; one register for everyone | receipt is data, never prose; `register_lint_report` |
| D-16 | per-turn provenance, copied never referenced | `provenance` (see TurnProvenance spec, master review §7.3) |

## §1 — The receipt schema (normative shape; field-level MUST/SHOULD)

```yaml
AcharyaReadingReceipt:
  receipt_version: 1                     # MUST; schema evolution gate
  turn_id: uuid                          # MUST
  chart_id: uuid                         # MUST — from the authenticated call, never the question text

  query:                                 # MUST
    query_class: factual | interpretive | timing | remedial | predictive | sensitive
    scope_tuple: {intent, domains[], width, depth, horizon, intervention, entitlement}
    time_horizon: {start?, end?, atemporal?}
    clarification: {asked: bool, question?, answered?, confidence: 0..1}

  coverage:                              # MUST — B.11 enforcement record
    mode: whole_chart | frame_check      # frame_check ONLY for depth:retrieval (RS-4)
    floor_items: [{id, status: served|empty|dark, cr_ref?}]   # the compiled acharya floor
    completeness: {served: int, total: int|null}              # B.10: null is honest
    escalation_valve_fired: bool         # RS-4: contradiction/yoga/window touch on a factual query

  facts_consumed:                        # MUST — B.1/B.3
    - {fact_id, ayanamsha_id, value_hash}          # references, never restated values (§N.5)

  derivation_chains:                     # MUST for every interpretive claim — B.3
    - {claim_span_id, signal_ids[], fact_ids[], classical_refs[]}

  cross_domain:                          # MUST for interpretive — B.11 Phase 2 record
    signals_surfaced: [{signal_id, domain_pair, direction}]
    convergences: [{id, members[], strength}]
    contradictions: [{id, members[], disposition: surfaced|adjudicated|open}]  # B.7: never softened

  interpretation_sets:                   # MUST for every SIGNIFICANT interpretive judgment — B.4
    - claim_span_id: …
      candidates:                        # ≥3 or an explicit waiver (below)
        - {label, reading, supporting: [refs], refuting: [refs]}
      selected: {label, rationale}
      falsifier: "observable outcome that would disprove the selected reading"
      waiver?: {reason}                  # permitted ONLY for: deterministic restatement of a
                                         # single classical rule with no interpretive freedom;
                                         # waiver rate is a tracked health metric

  timing:                                # MUST for timing/predictive classes
    method: vimshottari | gochara_v3 | kp_sublord | tajaka | composite
    dasha_context: {md, ad, pd}          # as consumed, by fact reference
    windows: [{start, end, source_refs[]}]
    promise_context?: {pratijna_version, class_verdicts_consumed[]}   # v4.1+ earned-tier only

  confidence:                            # MUST — the typed spine of the contract
    - claim_span_id: …
      type: deterministic_fact | structural_prior | classical_prior
            | empirically_calibrated | unresolved
      value?: 0..1                       # present ONLY when type supports it
      basis: {n?, interval?, priors_version?, formula_version?}
      # RULE (T-8, §N.8): a value whose sample cannot support its precision is
      # served as interval-or-nothing; `empirically_calibrated` REQUIRES a
      # passing activation gate (calibration spec §6). Structural priors NEVER
      # wear calibrated language.

  evidence_grades:                       # MUST — §N.6
    - {citation_index, grade: verified | corroborating | catalog_only | prior_reading | unverified}

  honest_gaps:                           # MUST — §N.6 rule 3, T-5
    - {description, reason: data_dark | not_computed | external_required | below_activation}

  safety_decision:                       # MUST — MP §3.5.C runtime record
    classes_detected: [mortality | self_harm | mental_health | health_crisis | none]
    action: served | reframed | withheld_hard_stop | escalated_native_signoff
    disclosure_class: native_self | cohort_subject | acharya_reviewer | public   # §3.5.B axis
    consent_verified: bool               # non-native charts: §3.5.D

  calibration_disclosure:                # MUST for predictive claims — §3.5.G
    {point?, interval?, method_ref, known_failure_modes_ref}
    # absent band ⇒ the predictive claim is INVALID output, blocked pre-wire

  prediction_candidates:                 # SHOULD — detected structured candidates (calibration spec)
    - {candidate_id, claim_text, window, model_p?, emitted_at}

  prose_binding:                         # MUST — §N.7: the prose is a restatement, provably
    - {claim_span_id, block_id, char_range}

  register_lint_report:                  # MUST — D-14 evidence
    {delta_scrubs: int, block_scrubs: int, classes: []}

  omitted:                               # SHOULD — what was retrieved and NOT used, with reason
    - {ref, reason: budget_trim | below_grade | out_of_scope}

  provenance: TurnProvenance             # MUST — master review §7.3 (versions, hashes, snapshots)
  receipt_hash: sha256                   # MUST — over the canonicalized receipt
```

## §2 — The "significant interpretive judgment" trigger (B.4 scope)

B.4 cannot mean three candidates for every sentence. The trigger, proposed:

A claim is **significant** iff any of: (a) it asserts a domain outcome or
disposition (career/marriage/health/wealth verdict-class prose); (b) it is
time-indexed (a window, a period quality); (c) it is remedial; (d) it will be
detected as a prediction candidate; (e) the adjudicator marks competing
classical rules in tension. Everything else is elaboration and inherits the
set of its parent claim. Expected density: 1–4 interpretation_sets per
interpretive reading. **The waiver rate and set-count per reading are
production health metrics** (registered in the TA v0.11 §17.8 observability
set) — a reading with zero sets that answered "will my career recover?"
failed the contract, detectably.

## §3 — Enforcement points (where each field is EARNED, §N.8)

| Field | Detector / producer | Exists today? |
|---|---|---|
| coverage | floor compiler + completeness receipt (live on Door 1) | YES — extend to receipt |
| facts_consumed / derivation_chains | envelope citation extraction + MSR constituent facts | PARTIAL (citations yes; chains need envelope refs threaded) |
| interpretation_sets | NEW synthesis-stage structured output + validator (reject a significant claim without a set) | NO — the contract's main new build |
| confidence typing | verdict_object grades (L5), pratijna tiers, calibration gate | PARTIAL — typing enum is new; sources exist |
| evidence_grades | S-3 grade pipeline + groundingRollup | YES (client-side today; move server-side) |
| safety_decision | NEW SafetyPolicyGate (safety spec §3) | NO — required before any non-native serving |
| prose_binding | block/claim-span mapping at commit | NO — pairs with the A-37 block-typing work |
| register_lint_report | register_leak_lint counters | YES |
| provenance | D-16 stamp, extended | PARTIAL (see TurnProvenance) |

## §4 — What the reader sees (the contract's product face)

Prose only, one register. The receipt surfaces as: the settled band's counts;
grade glyphs on chips; the dock's grounding card; **and two NEW reader-facing
affordances this contract makes possible:** (1) *"Read it another way"* — the
non-selected B.4 candidates, rendered in the same plain register on demand
(the single most acharya-like affordance available: a real acharya tells you
what else the chart could mean and why they read it this way); (2) *"What
would change my mind"* — the falsifier, stated plainly. Both are affordances,
never forced into the main prose flow (P2, D-15).

## §5 — Ratification asks

1. Adopt `AcharyaReadingReceipt` v1 as the serving contract (NCD-3 in the
   decision packet).
2. Ratify the §2 significance trigger.
3. Ratify the confidence-type enum and the rule that `empirically_calibrated`
   requires a passing activation gate.
4. Name the receipt the artifact AC-15's rubric scores against (master review
   §11, Gate 6).

*End ACHARYA_READING_CONTRACT v0.1 PROPOSAL.*
