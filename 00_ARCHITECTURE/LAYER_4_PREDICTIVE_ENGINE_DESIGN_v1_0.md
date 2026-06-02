---
artifact: LAYER_4_PREDICTIVE_ENGINE_DESIGN_v1_0.md
canonical_id: LAYER_4_PREDICTIVE_ENGINE_DESIGN
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
supersedes_part_of: LAYER_3_TIME_AND_PREDICTION_DESIGN_v1_0.md (split into L3 temporal + L4 predictive)
read_with:
  - 00_ARCHITECTURE/LAYER_3_TEMPORAL_FABRIC_DESIGN_v1_0.md (the temporal fabric it consumes)
  - 00_ARCHITECTURE/LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0.md (signals, salience, concordance, contradictions, negative-space)
  - 00_ARCHITECTURE/LAYER_1_CHART_FACTS_DESIGN_v1_0.md (ashtakavarga, dasha-lord condition, tara/chandra bala, Tajaka)
purpose: >
  The Predictive Engine: a probabilistic, multi-technique, multi-school ENSEMBLE that turns the L3
  temporal fabric into time-indexed, calibrated, falsifiable predictions. Its weights are LEARNED — it
  is mutable, versioned by calibration state, and verified by calibration metrics (not reproducibility).
  This is where the project's mission of "time-indexed, probabilistic, calibrated predictions" is produced.
---

# Layer 4 — Predictive Engine · Detailed Design

> **Project Brahma · external name: Phala / Prediction.** Per BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 +
> BRAHMA_BUILD_UX_SPEC_v1_0: user-facing surfaces show "Phala / Prediction" — never "L4" or asset codenames
> (internal docs keep L4 for precision). Phala's assets are built **with their retrieval tool(s)** — per-asset
> primitives (`event_anchors`, `mitigation_map`, `muhurta_finder`, `rectification`) + a composite outlook
> bundle — deployed to web + MCP and tested against fresh data in the same swarm arc; verifies only when assets
> **and** tools pass. Proposed build model: **hybrid** — precompute the major lifetime anchor set at chart-
> build, compute narrow/ad-hoc windows lazily at query time (native to confirm). Muhurta inverts Phala
> (predict→optimize).

## §A — What L4 is

- **A calibrated ensemble of classical predictors.** Not a single dasha+transit chain — *many* timing
  techniques run in parallel as independent predictors, combined with **learned weights**, and trusted
  most where they *agree*.
- **Probabilistic + falsifiable.** Output is a calibrated probability over outcome-types and a timing
  distribution, each with an explicit **falsifier** and an **alternative scenario**.
- **Learned.** Weights evolve as outcomes accumulate (via L5). L4 is mutable, versioned by its
  calibration state, verified by Brier/calibration metrics — *not* by deterministic rebuild.
- **The mission home.** This is where "time-indexed, probabilistic, calibrated predictions, testable
  against lived reality and correctable from outcomes" is realized.
- **LEL is never an input.** Predictions are generated from the chart alone; outcomes are held out (L5).

## §B — Governing principles

1. **Predict, then test — never the reverse.** Outcomes (LEL) never enter L4.
2. **Every prediction is falsifiable.** No anchor ships without a stated falsifier.
3. **Ensemble, not single-method.** Confidence comes from *agreement across independent predictors*.
4. **Calibrated honesty.** Confidences are calibrated probabilities, surfaced with uncertainty and
   alternatives; contradictions become alternative scenarios.
5. **Leverage, don't recompute.** L4 combines existing L0/L1/L2/L3 assets; it never re-derives facts.

## §C — The ensemble architecture

Each classical timing technique is an **independent predictor** over a window; L4 combines them with
learned weights `w_k`:

- **Predictors (the ensemble members):** Vimshottari · Yogini · Jaimini Chara · Kalachakra dashas
  (multi-dasha) · dasha × transit alignment (from L3) · ashtakavarga-weighted transit (Kakshya/bindu) ·
  Tara/Chandra bala favourability · annual Tajaka chart (Varshaphal + Mudda) · eclipse/nodal triggers ·
  Saturn-phase backdrop (Sade Sati/Kantaka) · retrograde/stationary intensification · (research)
  declination/out-of-bounds, planetary speed, heliacal phase.
- **Agreement = confidence.** Where many predictors point to the same window/theme → high confidence;
  where they diverge → an alternative scenario + wider uncertainty. (L3 supplies the *count* of
  agreement; L4 turns it into a *calibrated probability* via `w_k`.)
- **Weights are learned** from L5 backtesting — per technique, per chart, and across the corpus.

## §D — Components

### 4.1 · Event Anchors (the predictions)
- **What:** the chart's set of time-indexed predictions. Each anchor: **window** (from L3 convergence) ·
  **predicted theme/outcome** (from the active L2 signals) · **calibrated confidence** · **falsifier**
  (the observable that disproves it) · **alternative scenario** · **contributing predictors + signals**.
- **Build:** at L3's high-intensity windows, synthesize the theme from the active L2 signals; compute
  confidence via the ensemble (§C) + the confidence terms (§4.3); attach falsifier + alternative.
- **Tool:** `query_anchors(date_range | domain)`.

### 4.2 · The Ensemble Model
- **What:** the registry of predictor techniques + their **learned weights** + the combination function.
- **Build/maintain:** weights initialized from priors; updated by L5 from outcome scoring. Versioned by
  calibration state (`weights_version`).
- **Tool:** `explain_prediction(anchor_id)` → which predictors/weights/signals drove it (explainability).

### 4.3 · Confidence & Calibration Model
- **Confidence terms (the predictors' strengths):** ashtakavarga transit weight (L1) · dasha-lord
  condition — dignity/functional-nature/yogakaraka (L1) · Tara/Chandra bala (L1) · multi-school
  concordance breadth (L2) · multi-dasha agreement (L3) · signal salience/confidence (L2).
- **Output:** a **calibrated probability** (not a raw score), with a timing distribution + uncertainty.
- **Verified by:** Brier score / calibration curves against outcomes (in L5), not reproducibility.
- **Tool:** `query_prediction(window | domain)` → distributional, calibrated output.

### 4.4 · Mitigation Map
- **What:** L3's obstruction *overlaps* interpreted as **modifiers** — softens/delays/cancels (or
  amplifies) an anchor — adjusting its effective confidence/severity.
- **Build:** for each L3 overlap on an anchor window, classify the interaction (full/partial/neutralizing/
  amplifying) and apply the modifier; record it so a prediction is never read in isolation.
- **Tool:** `query_mitigation(anchor_id)`.

### 4.5 · Birth-Time Sensitivity & Rectification
- **What:** model birth-time uncertainty — perturb birth time ±N minutes, recompute anchors, report each
  anchor's **robustness**; and (via L5 backtesting against LEL) **rectify** the time.
- **Build:** sensitivity sweep over the birth-time interval → anchor stability score; rectification picks
  the time that best retrodicts known events (L5).
- **Tool:** `query_birthtime_sensitivity(anchor_id?)`.

## §E — How L4 leverages the assets

- **L0:** Rule Base = *what a configuration portends*; Concordance = multi-school predictors (agreement →
  confidence, divergence → alternatives).
- **L1:** dashas (timing), transit/eclipse/station engines (triggers), **Ashtakavarga** (transit weight),
  dasha-lord dignity/functional-nature (period quality), Tara/Chandra bala (favourability), Tajaka
  (annual resolution), declination/speed (cosmological terms).
- **L2:** active **signals** = predicted themes; **salience** = which predictions matter; **concordance**
  = confidence; **contradiction ledger** = alternative scenarios + uncertainty; **negative-space** = what
  *won't* happen (also a prediction).
- **L3:** convergence windows + alignments + obstruction overlaps = the temporal skeleton predictions hang on.

## §F — The L5 (Learning) interface — *the next layer*

- L4 **emits** each prediction with confidence/horizon/falsifier; **L5 logs it before the outcome is
  known** (held-out discipline), **scores** it against **LEL** (isolated), and **recalibrates** L4's
  ensemble weights + confidence model.
- A **backtesting/retrodiction harness** (L5) runs L4 blind against known events to measure per-technique
  accuracy → the learned weights. **LEL is never an L4 input.** L4 = generate; L5 = score + recalibrate.

## §G — Storage & representation

- Anchors, the ensemble weights, mitigations, and sensitivity scores are **structured rows** in Cloud SQL,
  keyed by `(chart_id, ayanamsha_id, build_id, weights_version)`. **Versioned by calibration state** — a
  new weights_version produces new predictions without re-running L1–L3. Small volume; no new infra.

## §H — Open decisions

1. **Anchor-promotion threshold** — what L3 convergence intensity becomes a prediction.
2. **Ensemble combination function** + initial weights `w_k`; the calibration update rule (Bayesian/empirical).
3. **Confidence → probability mapping** + the calibration metric (Brier) + how uncertainty is expressed.
4. **Falsifier model** — what makes a good, checkable falsifier per anchor type.
5. **Birth-time rectification** policy (interval, scoring against LEL).
6. **L5 scope** — confirm L5 = log/score/recalibrate, LEL isolated; whether cross-chart learning is in L5 or a research layer above.

---

*End of LAYER_4_PREDICTIVE_ENGINE_DESIGN v1.0 — DRAFT, 2026-06-02. The probabilistic, learned predictive
half of the post-split L3/L4. Stack is now L0 → L1 → L2 → L3 (temporal) → L4 (predictive) → L5 (learning).*
