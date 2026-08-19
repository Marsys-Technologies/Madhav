---
artifact: CALIBRATION_METHOD_SPEC_v0_1_PROPOSAL
canonical_id: PARIPRASHNA_CALIBRATION_METHOD
version: 0.1
status: PROPOSAL — Phase-1 output, awaiting native ratification (not canonical; authorizes no code)
produced_during: PARIPRASHNA-V012-PHASE1 (Cowork, Fable 5, 2026-08-18)
date: 2026-08-18
authoritative_side: claude
relates_to:
  - MACRO_PLAN_v2_0.md §3.5.E (pre-registration/blinding — AUTHORITY), §3.5.G, §CW.PPL
  - PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §14.6/§14.7 (v0.11), T-8
  - PARK_PB-3_L-5 + DVA Rulings 55/79 (the ruled, unbuilt conversational-calibration sink)
  - brahma_mimamsa_prediction_ledger (migration 470 — the live substrate this spec extends)
changelog:
  - "0.1 (2026-08-18): initial proposal."
---

# Prediction & Calibration Method — the science, specified

## §0 — Standing

The built lifecycle (PB-3 + C4 live proof) is the SUBSTRATE this spec
strengthens; nothing here reopens it. The collect-only phase (§14.6 C1) and
DVA Rulings 55/79 stand untouched. This spec defines the method BEFORE the
data accrues — which is precisely when a method must be defined (§3.5.E's own
logic: pre-registration beats post-hoc choice).

## §1 — Two probabilities, never conflated

| Quantity | Source | When | Mutability |
|---|---|---|---|
| **`model_p`** | the instrument's own stated probability at generation (from the confidence-typed claim; absent if the reading stated none) | at emission | **IMMUTABLE from the moment the `detected` row is written** — new column, nullable, never updated |
| **`operator_band`** | the human confirmer's numrange band | at confirm | frozen at confirm (existing trigger) |

Scoring reports BOTH curves where both exist. `model_p` measures the
instrument; `operator_band` measures the instrument+operator system. Today's
implementation stores only the confirm-time band and explicitly nulls
detector confidence — correct as far as it goes; the gap is that a reading
which SAID "more likely than not (≈0.65)" loses its own number unless the
operator re-types it. The structured candidate already carries
`confidence_stated`; persist it as `model_p` at detection. **No silent
post-hoc replacement in either direction** (§3.5.E: native cannot revise
after outcome known — enforce by trigger: `model_p` and window immutable
post-detection; `operator_band` immutable post-confirm; claim-semantics edits
allowed only in `detected` state and audit-logged, per the existing flow).

## §2 — Pre-registration seal

- `detected.created_at` is the pre-registration timestamp (§3.5.E).
- **The window is fixed at emission and never modified** — §3.5.E carried
  verbatim, consistent with §1's trigger rule and the master review's §6.8
  state machine. Detector imprecision (a mis-parsed window on a real claim)
  is handled WITHOUT an edit path: DISMISS the mis-parsed candidate
  (reason-logged, feeding detector precision per §14.3) and let confirmation
  create a correctly-windowed row born `confirmed` from the SAME utterance —
  a new registration with its own seal, priced honestly as later-registered.
  (A bounded pre-confirm edit affordance was considered and REJECTED: it
  cannot be squared with "fixed at emission," and a widened window is a
  silently easier target. The existing detected-state claim-text edit
  affordance survives for semantics only, never for window or probability.)
- Post-confirm: nothing changes but lifecycle state and outcome.

## §3 — Outcome taxonomy and scoring

| Outcome | Definition | Scored? | Rule |
|---|---|---|---|
| happened / did_not_happen | binary resolution within window | YES | Brier (existing); log-loss as a secondary report |
| partial | operator fraction (existing) | YES, flagged | scored at fraction; partials reported as their own stratum, never silently pooled with binaries |
| unverifiable | can't-tell (existing) | NO | excluded from scores; COUNTED in coverage (existing, keep) |
| **censored** (new state semantics) | window still open when a scoring snapshot is taken, or subject withdrew | NO | excluded, reported as censored-n; never treated as did_not_happen |
| lapsed / lapsed_unconfirmed | window closed unresolved / never confirmed | NO | coverage-denominator members — the selection-bias signal |

**Selection-bias reporting is mandatory on every score:** resolution coverage
(resolved / windows-closed) ships beside every Brier figure, per stratum. A
Brier from a 40%-resolved sample is a different claim than from 90% —
already doctrine (§14.7), now a schema rule: the score row carries
`coverage_fraction` NOT NULL.

## §4 — Aggregation: pooling and heterogeneity

- Default reporting grain: `technique × ayanamsha`, pooled across charts
  (v0.11 §14.6 rule 1, kept).
- **Partial pooling (hierarchical) when cells justify it:** chart-level
  estimates shrunk toward the technique pool (a Beta-Binomial/hierarchical
  shrinkage estimator is sufficient; no ML machinery). Preserves chart
  heterogeneity honestly instead of choosing between "per-chart n=3 noise"
  and "pretend charts are identical."
- Strata never silently merged: domain, horizon-length band, and
  `created_from_channel` are reportable dimensions.

## §5 — Metrics: calibration vs discrimination

Report BOTH, never one as the other: calibration (reliability diagram over
binned p; ECE as a summary), discrimination (resolution component of the
Brier decomposition; AUC where n permits). Uncertainty on every figure:
Wilson/bootstrap intervals. A single naked Brier number is the T-8 trap —
banned by presentation rule: **every served score = interval + n + coverage.**

## §6 — Activation: effective sample size, not a magic n

v0.11 said "not below n=30" — a placeholder, replaced: a cell activates for
SERVING (C2 phase) when (a) its score interval half-width ≤ a ratified
threshold (default proposal: ±0.15 on Brier), computed on (b) **effective n**
(after down-weighting near-duplicate predictions — same chart, same
technique, overlapping windows count as correlated, not independent), and
(c) coverage ≥ a floor (default proposal: 60%). Cells below gate serve the
existing honest flag (`insufficient_calibration_data`). Thresholds are
pre-registered HERE, before data exists — changing them later is a versioned
method change (§8).

## §7 — Validity protections

- **Temporal knowledge cutoff:** a scored prediction's generation context is
  bounded by its `now_context_date` (already stamped, D-16). No evidence
  post-dating emission may inform the retrospective judgment of what the
  instrument "knew."
- **Held-out / prospective partition:** prospective (post-registration)
  outcomes are the primary corpus; retrodictive checks (LEL-based) are a
  SEPARATE, clearly-labeled corpus, never pooled — this is the F1-cycle
  discipline (held-out charts) extended to time.
- **NO-LEAKAGE (restated as method):** life events and outcomes never enter
  generation context (arms 1–4 + data-class C3 rule). LEL-drafted outcome
  suggestions (§14.7) remain post-hoc-only and human-confirmed.
- **Anti-anchoring / anti-sycophancy:** when cross-thread recall (A-41)
  ships, the engine composes its CURRENT reading before retrieving prior
  conclusions for the contradiction check — independent-then-compare, never
  recall-then-compose. Testable: the eval corpus includes
  returning-conversation fixtures where the prior reading was wrong.
- **Research-blinded path:** the existing blind-mode JSONL ledger is the
  seam; a blinded evaluation (outcome hidden from the scorer at reading
  time) is available when experimental validity requires it.

## §8 — Method versioning

Scoring-method changes (new metric, changed threshold, changed pooling) are
versioned like formula versions: `calibration_method_version` on every score
row; scores are recomputable but prior published figures are never silently
restated (append a corrected figure beside, per D-18's corrections-visible
rule). **Disclosure: adding `calibration_method_version` to the
`mimamsa_conversational_calibration` sink is a PROPOSED AMENDMENT to the
exact schema DVA Ruling 79 fixed** — it is not covered by "Rulings 55/79
stand untouched" and requires its own disposition at the Gate-9 native point
(it can be ruled together with NCD-7's model_p timing; the alternative — a
later migration against a live table — is strictly worse, which is the case
for amending now).

## §9 — Ratification asks

Thresholds in §6 (interval width, coverage floor), the partial-pooling
default in §4, and the `model_p` column addition (a schema change, so it
lands via the ruled migration path with the Rulings-55/79 work at Gate 9 —
or earlier at Gate 2 if the native prefers capture-completeness sooner;
decision NCD-7).

*End CALIBRATION_METHOD_SPEC v0.1 PROPOSAL.*
