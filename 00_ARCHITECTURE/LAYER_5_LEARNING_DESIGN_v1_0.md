---
artifact: LAYER_5_LEARNING_DESIGN_v1_0.md
canonical_id: LAYER_5_LEARNING_DESIGN
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
read_with:
  - 00_ARCHITECTURE/LAYER_4_PREDICTIVE_ENGINE_DESIGN_v1_0.md (the engine L5 calibrates)
  - 00_ARCHITECTURE/LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0.md (salience weights L5 tunes)
  - 00_ARCHITECTURE/LAYER_0_FOUNDATION_DESIGN_v1_0.md (rule base whose confidence L5 updates)
purpose: >
  The Learning layer: closes the loop. It logs every prediction before its outcome is known, scores it
  against lived reality (LEL — isolated), recalibrates the predictive engine, and — across many charts —
  learns which techniques, rules, and ayanamshas actually work. This is where the mission is realized:
  predictions become testable + self-correcting, and the instrument becomes a research tool for
  astrology as a discipline.
---

# Layer 5 — Learning · Detailed Design (exhaustive)

> **Project Brahma · external name: Mīmāṃsā / Learning.** Per BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 +
> BRAHMA_BUILD_UX_SPEC_v1_0: user-facing surfaces show "Mīmāṃsā / Learning" — never "L5" or asset codenames
> (internal docs keep L5 for precision). Mīmāṃsā is **not** a per-chart build step that fills 0→100%; the
> cockpit shows it as a thin always-present "active — this chart contributes to calibrated learning" band. Its
> retrieval/write tools (`log_prediction`, `record_outcome`, `lel_query`) are built, deployed to web + MCP, and
> tested in the same swarm arc as the layer's machinery. The LEL stays fully isolated (never feeds generation);
> recalibration acts only through the bounded `learning_multiplier`.

## §A — What L5 is

- **The closing of the loop.** L4 generates predictions; **L5 measures them against outcomes and feeds
  the lesson back** — recalibrating L4's ensemble weights and confidence model, L2's salience, and L0's
  rule confidence.
- **Two scopes:**
  1. **Per-native** — calibrate *this* chart's engine from *this* native's lived events (LEL).
  2. **Cross-corpus (research)** — across many charts + outcomes, learn which configurations, rules,
     techniques, and ayanamshas are empirically predictive. This is the mission's second half:
     *a research tool for astrology as a discipline.*
- **Held-out by construction.** Predictions are logged **before** outcomes are known; **LEL is isolated**
  — it is *only* a scoring target, **never** an input to prediction generation (L1–L4).
- **Scientific.** Verified by calibration metrics (Brier, calibration curves), statistical significance,
  and full reproducibility — not by reproducible *output* (outcomes are real-world).

## §B — Governing principles

1. **Held-out is sacrosanct.** The model never sees an outcome before it has logged the prediction.
2. **LEL isolated.** Outcomes score predictions; they never feed generation. (Enforced, not trusted.)
3. **Calibrated honesty.** The system reports its *own* reliability per domain/technique.
4. **Sample-aware.** Don't over-update on thin evidence; respect statistical significance + a cold-start
   prior regime.
5. **Reproducible + audited.** Every prediction → outcome → score → weight-update is logged and replayable.
6. **Correct the method, not the data.** Learning adjusts weights/confidence/rule-support — never edits
   the facts or the held-out outcomes.
7. **One neutral-by-default knob.** All recalibration is a single mechanism — a `learning_multiplier`
   (default 1.0) on every learnable unit-class. The classical/prior layer is never overwritten, only
   modulated; at launch every multiplier is 1.0 (zero impact); the multipliers themselves are the
   empirical findings. (Native decision 2026-06-02.)

## §C — Components (exhaustive)

### Group 1 — Held-out discipline (the spine)
- **C1 · Prediction Ledger** — immutable, append-only log of every L4 prediction *at emission*:
  `prediction_id, chart_id, ayanamsha_id, anchor_id, window, theme, predicted_prob, confidence,
  falsifier, alternative, weights_version, horizon, logged_at, status(open/resolved)`. Nothing is
  back-dated; this is the scientific record.
- **C2 · Outcome Record — the pure-event LEL (isolated).** Lived events as ground truth, **pure events
  only** — what happened, when, in what domain — **no calculations fused in** (full spec:
  `LEL_SCHEMA_AND_INTAKE_v1_0.md`). One canonical store for every client. **Two intake paths, one
  destination:** (a) clean intake via **portal / MCP** (`log_life_event`) — the default for future
  clients + the native going forward; (b) a **one-time migration** of the existing annotated v1.2
  (strip the fused chart_state, keep the events). Isolated schema; generation paths (L1–L4) have **no
  read access** — only L5 scoring reads it. Recorded *after* the matching prediction.
- **C2b · Event Chart-State Index (derived — the separate math).** For each LEL event, computed by
  applying L1/L2/L3/L4 at the event's date → active dashas/transits/Sade-Sati/ashtakavarga, the L2
  signals live then, and what L4 *would have predicted*. L5-owned, **versioned + recomputable** (rebuilt
  as the engine improves; the LEL never changes). **The only place events and calculations meet**, and
  built *after* predictions are logged. This is what keeps the ground truth isolated by construction.

### Group 2 — Scoring
- **C3 · Scoring Engine** — match predictions to outcomes; compute per-prediction: hit/miss, **timing
  error**, and the **Brier score** (probability calibration); aggregate: precision/recall, **calibration
  curves** (do 70%-confidence predictions occur ~70% of the time?), per-domain accuracy.
- **C4 · Per-Technique Accuracy Tracker** — a scoreboard of each predictor's historical hit-rate / Brier /
  timing accuracy (per chart + aggregate). The empirical answer to "which techniques actually work."
- **C5 · Per-Ayanamsha Performance Comparison** — because L1 computes multiple ayanamshas, score which
  ayanamsha's predictions calibrate best, per chart and per corpus. *Empirically resolves the ayanamsha
  question* — a capability unique to computing them all.

### Group 3 — Recalibration via the LEARNING MULTIPLIER (one unifying mechanism)
All recalibration is one mechanism: a **`learning_multiplier` (default 1.0)** on every learnable
unit-class across the stack. `effective_weight = base(classical/prior) × corpus_mult × chart_mult`. At
launch every multiplier is 1.0 → the system behaves as pure classical (zero impact). L5's *only*
recalibration action is to nudge multipliers up (>1) or down (<1) from outcomes, with **Bayesian
shrinkage toward 1.0** (thin evidence → stays ~1.0), a **bounded range** (≈0.5–2.0), and held-out
discipline. The classical layer is never overwritten — only modulated; the multipliers *are* the findings.
- **C6 · Learning-multiplier update (the mechanism)** — from the scores (C3–C5), move each unit-class's
  multiplier toward what the data supports; **two-level** (corpus-learned × per-chart-learned, both start
  1.0), shrinkage-regularized, bounded, versioned (`mult_version`).
- **C7 · Technique multipliers → L4** — per predictor/technique (Vimshottari, Jaimini, AV-transit…):
  which techniques actually predict → coefficient drifts above/below 1.
- **C8 · Signal/template multipliers → L2** — per signal-template/rule-class: templates that precede real
  events gain coefficient; salience/surfacing follows.
- **C9 · Rule multipliers → L0** — per classical rule: the coefficient encodes its empirical track record;
  the rule's classical weight is preserved, the multiplier is the lived-experience adjustment.
- **C6b · Confidence calibration (separate)** — map L4's combined score → a calibrated *probability*
  (Platt/isotonic) so "70%" means 70%.
- **Granularity rule:** attach multipliers at the class level where evidence accrues — rule / technique /
  domain / ayanamsha — **not** every sparse per-chart leaf signal.

### Group 4 — The research engine (cross-chart)
- **C10 · Cross-Chart Pattern Learning** — across the corpus, learn **configuration → outcome**
  correlations with **statistical significance** (effect size, p/Bayes factor, sample size). The
  data-driven evidence base on top of the classical rules.
- **C11 · Rule Validation** — for each L0 rule, the empirical support across charts (validated /
  unsupported / inconclusive) with sample sizes.
- **C12 · New-Rule Discovery (candidate)** — configurations that empirically predict but aren't in the
  classical canon → candidate rules surfaced for review (never auto-promoted). The discovery engine.

### Group 5 — Applications
- **C13 · Birth-Time Rectification** — use backtesting against LEL to find the birth time that best
  retrodicts known events; report the rectified time + its confidence + anchor robustness.
- **C14 · Reliability Self-Report** — the system states its own track record: "in this domain my
  predictions have been X% calibrated, timing ±N." A trust + honesty feature.
- **C15 · Active Learning / Outcome Prioritization** — identify which open predictions, if resolved,
  would most improve the model (information gain) → prioritize soliciting those outcomes.
- **C16 · Drift Monitoring** — track engine accuracy/calibration over time; alert when recalibration is
  due or performance degrades.
- **C17 · Backtesting / Retrodiction Harness** — run L4 **blind** against known events to measure
  per-technique accuracy and tune weights (feeds C4/C7/C13). The validation workbench.

### Group 6 — Governance & wiring
- **C18 · Held-out Enforcement** — a hard gate: a prediction must exist in the Ledger (C1) *before* its
  outcome (C2) can be scored; LEL access is read-only to scoring, blocked from generation paths.
- **C19 · Audit Trail / Reproducibility** — every prediction → outcome → score → weight-update is logged
  and replayable; `weights_version` ties predictions to the model state that made them.
- **C20 · Counterfactual Replay** — re-score historical predictions under a new model to estimate
  improvement *without leaking* (the new model never saw those outcomes during training).
- **C21 · Eval Harness / Golden Sets** — regression eval (queries + expected) so model changes can't
  silently degrade accuracy.

### Group 7 — Surfaces
- **C22 · Native Outcome-Reporting Surface** — a structured way for the native to report lived events +
  corrections, feeding C2 (and only C2 — never generation).

## §D — The feedback loop (the wiring)

```
L4 emits prediction ──► C1 Prediction Ledger (logged before outcome)
                              │
            (time passes; lived event occurs)
                              ▼
        C2 Outcome Record (LEL, isolated) ──► C3 Scoring ──► C4/C5 trackers
                                                   │
        ┌──────────────────────────────────────────┼───────────────────────────┐
        ▼                       ▼                   ▼                            ▼
  C6 confidence calib   C7 ensemble weights   C8 salience → L2          C9 rule confidence → L0
        └────────────► new weights_version ──► L4 (next predictions use it) ◄────┘
        (cross-corpus) C10 pattern learning · C11 rule validation · C12 discovery
```

## §E — The two scopes, explicitly

- **Per-native loop:** LEL → score this chart's predictions → recalibrate this chart's L4 weights +
  rectify birth time. Personal, fast-converging where the native supplies events.
- **Cross-corpus research loop:** many charts' outcomes → learn population-level technique/rule/ayanamsha
  performance → update L0 rule confidence + propose new rules. Slow, statistically-grounded, the
  discipline-level research output. Both share the held-out discipline.

## §F — Storage & infrastructure

- Ledger, outcomes, scores, trackers, weight-versions, and research findings are **structured rows** in
  Cloud SQL (LEL in its isolated schema). Scoring + calibration run as scheduled/triggered Cloud Run Jobs.
  Small data; modest compute. No new services (reuses the GCP footprint). The only sensitive boundary is
  **LEL isolation**, enforced at the DB-grant + code-path level.

## §G — Open decisions

1. **Calibration method** — Platt vs isotonic; per-domain vs global; the cold-start prior regime.
2. **Significance bar** for cross-corpus learning + new-rule promotion (and the human-review gate).
3. **Weight-update cadence** — per-outcome online vs batch recalibration; how `weights_version` is rolled.
4. **Rule-confidence write-back to L0** — policy + safeguards (held-out integrity; no overfitting to one chart).
5. **Birth-time rectification** policy (search interval, scoring rule, when to lock a rectified time).
6. **Cross-chart privacy/consent** — corpus learning across natives under the ethical framework + consent tiers.
7. **Active-learning** prioritization metric (information gain) + how outcomes are solicited.

---

*End of LAYER_5_LEARNING_DESIGN v1.0 — DRAFT, 2026-06-02. The learning/calibration layer; closes the
stack L0 → L1 → L2 → L3 → L4 → L5, and realizes the mission (testable, self-correcting predictions +
a research tool for astrology).*
