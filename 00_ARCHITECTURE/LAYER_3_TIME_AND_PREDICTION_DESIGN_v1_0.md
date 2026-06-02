---
artifact: LAYER_3_TIME_AND_PREDICTION_DESIGN_v1_0.md
canonical_id: LAYER_3_TIME_AND_PREDICTION_DESIGN
version: 1.0
status: SUPERSEDED 2026-06-02 — split (native decision) into LAYER_3_TEMPORAL_FABRIC_DESIGN_v1_0.md (deterministic) + LAYER_4_PREDICTIVE_ENGINE_DESIGN_v1_0.md (probabilistic/learned). Retained for history. New stack: L0→L1→L2→L3(temporal)→L4(predictive)→L5(learning).
authored_by: Claude (Cowork) 2026-06-02
read_with:
  - 00_ARCHITECTURE/LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0.md (signals + activation index L3 consumes)
  - 00_ARCHITECTURE/LAYER_1_CHART_FACTS_DESIGN_v1_0.md (dashas + on-demand transit/vedha engines)
purpose: >
  The design of Layer 3 — Time & Prediction. L3 turns the chart's signals and their activation windows
  (L2) into a calibrated life trajectory: where time concentrates, the testable time-indexed
  predictions, and how obstructions modify them. It is where the project's mission of "time-indexed,
  probabilistic, calibrated predictions" is produced.
---

# Layer 3 — Time & Prediction · Detailed Design

## §A — What L3 is (and what it is no longer)

L3 answers the question facts and signals cannot: **"how does this chart play out over time, and what
can we predict — testably?"**

It is *not* a grab-bag of temporal tables. Through the reorganization, the old L3's deterministic and
structural pieces moved to where they belong:
- the **deterministic temporal engines** (transit/gochara, eclipse, vedha firing, lifetime aspect/
  bhrigu tables) → **L1**, as on-demand capabilities (compute-on-the-fly, not stored);
- **pattern detection, negative space, contradictions** → **L2** (signals/resonance, negative-space
  map, contradiction ledger);
- the **temporal activation index** (when each signal is live) → **L2**.

What remains is the genuinely *synthetic, predictive* work that nothing below can do: combining many
timing systems and active signals **across time** into convergence, predictions, and their modifiers.

**The throughline to the mission:** L3 produces the **time-indexed, probabilistic, falsifiable
predictions** the whole instrument exists to make. **LEL stays isolated** — predictions are generated
*without* ever seeing lived outcomes; the (higher) Learning layer logs each prediction before the
outcome is known, then tests it against LEL ground truth and corrects calibration. L3 = generate;
Learning = score.

## §B — Governing principles

1. **Predict, then test — never the reverse.** Predictions are generated from the chart only; held-out
   outcomes (LEL) are sacrosanct and never an input to L3.
2. **Every prediction is falsifiable.** An event anchor without a stated falsifier is not a prediction.
3. **Synthesis over time only.** L3 combines L2 signals + their activation + L1 timing; it does not
   recompute facts or re-invoke PyJHora.
4. **Cited + confidence-scored** — every convergence and anchor traces to its contributing signals and
   carries a calibrated confidence.
5. **Tooling per the L0 standard** (one registry, MCP + API, provenance envelope).

## §C — The assets + flow

```
L2 (signals + activation index)  +  L1 (dasha periods · on-demand transit/vedha engines)
        ▼
3.1 CONVERGENCE TIMELINE  — where many systems/signals align in time ("the loud periods")
        ▼
3.2 EVENT ANCHORS         — the testable, time-indexed, probabilistic predictions (window + theme + confidence + falsifier)
        ▼
3.3 MITIGATION MAP        — obstruction windows that soften / delay / cancel anchors
3.4 PERIOD SNAPSHOT       — read-view: "what's active on date X / in period Y"
        ▼
   query layer  +  (higher) Learning layer: log prediction → compare to LEL → recalibrate
```

## §D — Per-asset detail

### 3.1 · Convergence Timeline
- **What:** a lifetime (or windowed) timeline marking periods where **multiple timing systems and
  active signals align** — dasha transitions, returns, exact transits, eclipses, and the signals those
  activate, all landing close together. The chart's "loud" periods.
- **Inputs:** the L2 **signal activation index** (when signals are live) + L1 **dasha periods** +
  on-demand transit/eclipse windows.
- **Build:** scan time at event resolution; per window, sum/weight the converging elements (signal
  activations + system transitions); compute a **convergence intensity** + class (baseline → rare
  alignment); detect clusters.
- **Output:** windows with intensity, class, and the contributing signals/systems.
- **Tool:** `query_convergence(date_range)`.

### 3.2 · Event Anchors — *the predictions*
- **What:** the high-intensity convergence windows promoted to **testable predictions.** Each anchor =
  a dated **window** + the **dominant active signals** + a **predicted theme/outcome** + a calibrated
  **confidence** + an explicit **falsifier** (the observable that would disprove it) + an **alternative
  scenario**.
- **Inputs:** the Convergence Timeline + L2 signals (salience/valence/domain/concordance).
- **Build:** at the loud windows, synthesize the predicted theme from the active signals; set confidence
  from signal confidences × convergence breadth × concordance; attach the falsifier + alternative.
- **Output:** the chart's set of dated, themed, confidence-scored, falsifiable predictions — the heart
  of the research instrument.
- **Tool:** `query_anchors(date_range | domain)`.

### 3.3 · Mitigation Map
- **What:** where an **obstruction window** (vedha firing, hard malefic transit, cancellation) overlaps
  an anchor → it **softens, delays, or (rarely) cancels** the predicted event; occasionally **amplifies**.
- **Inputs:** Event Anchors + L1 on-demand vedha/obstruction windows + signals.
- **Build:** detect temporal overlaps; classify the interaction (full/partial mitigation, neutralizing,
  amplification); adjust the anchor's effective confidence/severity and record the modifier.
- **Output:** per-anchor mitigation annotations (so a prediction is never read in isolation).
- **Tool:** `query_mitigation(anchor_id | date_range)`.

### 3.4 · Period Snapshot (read-view)
- **What:** "what's the active pattern on date X / across period Y" — a read-time roll-up over the L2
  activation index + the timeline + the anchors. The successor to the old "unified lattice."
- **Build:** a query/view — not stored.
- **Tool:** `query_period(date | date_range)`.

## §E — What dissolved (no asset or data lost)

| Old L3 / META asset | Where it now lives |
|---|---|
| Pattern Catalog (META_β) | L2 — signals + resonance lens |
| Negative-Space (META_δ) | L2 — negative-space map |
| Divergence Ledger (META_γ) | L2 — contradiction ledger (signal/school) + cross-system temporal deltas surfaced in L3 convergence |
| Derivation Graph (META_ε) | the provenance/derivation ledger already carried by every L1 fact + L2 signal — not a separate asset |
| Unified Lattice (META_ζ) | L3 — the Period Snapshot read-view |
| A15 time-synchronicity | L3 — Convergence Timeline |
| A16 phase-locked anchors | L3 — Event Anchors |
| BRIDGE vedha-anchor | L3 — Mitigation Map |
| A18–A21 lifetime tables | L1 — on-demand temporal capabilities |

## §F — Representation & storage

- Convergence windows, anchors, and mitigations are **structured rows** in Cloud SQL (keyed by
  chart_id, ayanamsha_id, build_id), each citing the L2 signal IDs it rests on. Small volume.
- The Period Snapshot is a view (not stored).
- No new embeddings (the semantic surface is L2's signals). No new infra — an L3 step on the existing
  build job + a few small tables.

## §G — Tools

`query_convergence` · `query_anchors` · `query_mitigation` · `query_period` — typed, provenance-bearing,
on-demand bundles, via MCP + API.

## §H — The prediction / calibration connection (mission-critical)

- L3 **generates** predictions (anchors) from the chart alone.
- The **Learning layer** (above L3) **logs** each prediction with its confidence, horizon, and falsifier
  **before** the outcome is observed (held-out discipline), then **compares** to LEL ground truth and
  **recalibrates** confidence/weights (e.g., the L2 salience weights, the anchor confidence model).
- **LEL is never an L3 input.** This separation is what makes the predictions honest and the instrument
  scientifically testable — the project's stated mission.

## §I — Provenance & verification

- Every convergence window and anchor cites its contributing L2 signals; every mitigation cites the
  obstruction window + anchor. Verification = internal consistency (anchors resolve to real signals;
  windows are well-formed; determinism given fixed inputs) + the **falsifier-present** gate (no anchor
  ships without one). No JH oracle.

## §J — Open decisions

1. **Time resolution** of the Convergence Timeline (monthly? event-driven?) and the convergence-intensity
   formula + class thresholds.
2. **Anchor promotion threshold** — what convergence intensity becomes a prediction.
3. **Confidence + falsifier model** for anchors (how confidence is set; what makes a good falsifier).
4. **Mitigation classification** rules (full/partial/neutralizing/amplifying).
5. **Layer line to Learning** — confirm L3 = generate, Learning = log/score, with LEL isolated.
6. **Horizon** — lifetime vs a rolling window (e.g., ±N years) for stored anchors vs on-demand.

---

*End of LAYER_3_TIME_AND_PREDICTION_DESIGN v1.0 — DRAFT for native review, 2026-06-02. Same drill:
debate §J, close each, then the Layer 3 plan brief.*
