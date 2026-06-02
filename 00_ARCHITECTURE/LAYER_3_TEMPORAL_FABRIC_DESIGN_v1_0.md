---
artifact: LAYER_3_TEMPORAL_FABRIC_DESIGN_v1_0.md
canonical_id: LAYER_3_TEMPORAL_FABRIC_DESIGN
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0; build phase next)
authored_by: Claude (Cowork) 2026-06-02
supersedes_part_of: LAYER_3_TIME_AND_PREDICTION_DESIGN_v1_0.md (split into L3 temporal + L4 predictive)
read_with:
  - 00_ARCHITECTURE/LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0.md (signals + activation index)
  - 00_ARCHITECTURE/LAYER_1_CHART_FACTS_DESIGN_v1_0.md (dashas + on-demand transit/eclipse/vedha engines)
  - 00_ARCHITECTURE/LAYER_4_PREDICTIVE_ENGINE_DESIGN_v1_0.md (the consumer above)
purpose: >
  The deterministic Temporal Fabric: the chart's activity map over time. L3 computes WHERE the dasha
  systems, transits, and active signals ALIGN in time — convergence, intersections, overlaps, and
  point-in-time snapshots. It is deterministic (rebuild = identical), reusable by many consumers, and
  it states only that an alignment EXISTS — never what it means or how likely (that is L4).
---

# Layer 3 — Temporal Fabric · Detailed Design

> **Project Brahma · external name: Kāla / Temporal.** Per BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 +
> BRAHMA_BUILD_UX_SPEC_v1_0: user-facing surfaces show "Kāla / Temporal" — never "L3" or asset codenames
> (internal docs keep L3 for precision). Kāla's assets are built **with their retrieval tool(s)** — per-asset
> primitives (`timeline_query`, `convergence_window`, `period_snapshot`) + the composite `temporal` tool —
> deployed to web + MCP and tested against fresh data in the same swarm arc; verifies only when assets **and**
> tools pass, with a volume-floor amber gate. Includes the new Spatial Activation Index module (v2 §D).

## §A — What L3 is

- **The chart's activity map over time.** Given the chart's dashas (L1), its on-demand transit/eclipse/
  vedha engines (L1), and its signals + their activation windows (L2), L3 computes the **temporal
  structure**: where multiple clocks and signals *coincide*.
- **Deterministic.** Rebuild → identical. No outcomes, no probabilities, no learned weights. It states
  *that* an alignment exists, with its strength as a *count/measure*, not a *likelihood*.
- **Reusable.** Prediction (L4) is one consumer, but the fabric also serves "what's active now,"
  muhurta, and descriptive timing.
- **The boundary test:** if a thing *changes when outcomes arrive*, it is not here — it is L4.

## §B — Governing principles

1. **Deterministic only** — counts and measures, never probabilities or learned weights.
2. **Synthesis over time** — combine L1 timing + L2 activation; never recompute facts or invoke PyJHora.
3. **Cited** — every alignment names the systems/signals it combines.
4. **Tooling per the L0 standard** (one registry, MCP + API, provenance envelope).

## §C — The assets + flow

```
L2 (signal activation index)  +  L1 (dasha periods · transit/eclipse/vedha engines)
        ▼
3.1 DASHA × TRANSIT ALIGNMENT  — the "what × when" coincidences
        ▼
3.2 CONVERGENCE TIMELINE       — where many systems/signals align ("loud" windows), measured
3.3 OBSTRUCTION OVERLAPS       — vedha/malefic windows overlapping active windows (as temporal facts)
3.4 PERIOD SNAPSHOT            — read-view: "what's active on date X / across period Y"
        ▼
   L4 Predictive Engine  (and other temporal consumers)
```

## §D — Per-asset detail

### 3.1 · Dasha × Transit Alignment
- **What:** the classical "what × when" — the moments a running dasha-lord's significations are
  *simultaneously* lit by a transit to the same house/significator. The deterministic coincidence.
- **Inputs:** L1 dasha periods (MD/AD/PD/SD) + on-demand transits to natal points/houses.
- **Build:** for each dasha period, find transits that hit the period-lord's significators within the
  period; emit alignment rows (period, transit, target, exact window).
- **Output:** alignment windows — the timing triggers L4 will weigh.
- **Tool:** `query_alignments(date_range | significator)`.

### 3.2 · Convergence Timeline
- **What:** the lifetime timeline marking windows where **many independent clocks and signals coincide**
  — dasha transitions across systems (Vimshottari, Yogini, Jaimini Chara, Kalachakra), returns, exact
  transits, eclipses, and the L2 signals those activate. The chart's "loud" periods, **measured**.
- **Inputs:** 3.1 + the L2 activation index + multi-system dasha boundaries + on-demand eclipse/return windows.
- **Build:** scan at event resolution; per window, **count/weight** the coinciding elements →
  `convergence_intensity` (a measure, not a probability) + class (baseline → rare alignment); detect clusters.
- **Output:** convergence windows with intensity, class, and the contributing systems/signals.
- **Tool:** `query_convergence(date_range)`.
- **Note:** multi-system *agreement* lives here as a count; turning that count into *confidence* is L4.

### 3.3 · Obstruction Overlaps
- **What:** where an obstruction window (vedha firing, hard malefic transit, cancellation period)
  **overlaps** an active/convergence window — recorded as a temporal fact (these two windows coincide).
- **Inputs:** L1 on-demand vedha/obstruction engines + the convergence/alignment windows.
- **Build:** interval-overlap detection; emit overlap rows (obstruction window, target window, extent).
- **Output:** the raw overlaps L4 will interpret as mitigation.
- **Tool:** `query_obstruction_overlaps(date_range)`.

### 3.4 · Period Snapshot (read-view)
- **What:** "what's active on date X / across period Y" — a read-time roll-up over the activation index +
  the timeline + the alignments + overlaps.
- **Build:** a query/view — not stored.
- **Tool:** `query_period(date | date_range)`.

## §E — Storage & representation

- Alignment, convergence, and overlap rows are **structured rows** in Cloud SQL, keyed by
  `(chart_id, ayanamsha_id, build_id)`, each citing the L1 periods + L2 signals it combines. Small volume.
- The Period Snapshot is a view (not stored). No embeddings (the semantic surface is L2). No new infra —
  an L3 step on the existing build job + a few small tables.

## §F — Boundary to L4 (explicit)

L3 produces **measures of coincidence** (how many clocks/signals align, how strong, how they overlap).
L4 turns those measures into **calibrated, falsifiable predictions** using learned weights. The same
window appears in both: *aligned* in L3, *predicted* in L4. The convergence count is L3; the confidence
is L4. The overlap is L3; the mitigation is L4.

## §G — Open decisions

1. Time resolution (monthly vs event-driven) + the convergence-intensity *measure* (count/weight formula)
   and class thresholds.
2. Alignment significator-matching rules (which transits count as "lighting" a dasha-lord's significations).
3. Horizon — lifetime vs a rolling window for stored alignments/convergence vs on-demand recompute.

---

*End of LAYER_3_TEMPORAL_FABRIC_DESIGN v1.0 — DRAFT, 2026-06-02. The deterministic temporal half of the
post-split L3/L4. Consumed by L4 Predictive Engine.*
