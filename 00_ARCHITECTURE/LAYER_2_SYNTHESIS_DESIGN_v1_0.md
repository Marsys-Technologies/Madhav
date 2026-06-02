---
artifact: LAYER_2_SYNTHESIS_DESIGN_v1_0.md
canonical_id: LAYER_2_SYNTHESIS_DESIGN
version: 1.0
status: SUPERSEDED 2026-06-02 by LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0.md (the accepted reimagining — signal-centric Chart Intelligence Layer). Retained for history; CGM relocated, lenses/indexes added.
authored_by: Claude (Cowork) 2026-06-02
read_with:
  - 00_ARCHITECTURE/LAYER_1_CHART_FACTS_DESIGN_v1_0.md (the facts L2 derives from)
  - 00_ARCHITECTURE/LAYER_0_FOUNDATION_DESIGN_v1_0.md (the rule base / concordance / ontology L2 uses)
  - 00_ARCHITECTURE/ASSET_RECONCILIATION_v1_0.md (UCN→UCD retirement)
purpose: >
  The detailed design of Layer 2 (Synthesis): the per-chart structured derivations that turn L1
  facts into signals, a graph, cross-domain linkages, and resonances — powered by the Layer 0 rule
  base + concordance + ontology. The narrative reading is NOT stored here; it happens at query time.
---

# Layer 2 — Synthesis · Detailed Design

## §A — What Layer 2 is

- **Structured synthesis over L1 facts.** L2 turns the chart's facts into higher-order *structured*
  objects: a typed graph, a signal corpus, a domain-linkage matrix, and a resonance map. Per chart,
  per selected ayanamsha. It is **not** interpretation-as-prose — the narrative happens at query time.
- **Rule-driven, not hand-authored — the central rebuild shift.** The old L2.5 was *hand-verified*
  and *native-specific* (built for Abhisek; "closed for this chart"). For a multi-client research
  product, L2 must be **chart-parameterized**: apply the **Layer 0 classical rule base** (× concordance
  × ontology) to any chart's L1 facts and *generate* the synthesis deterministically. The reusable IP
  lives in L0 (the rules); the per-chart L2 is *output*, not authored.
- **Deterministic where possible.** The graph (CGM), the rule-fired signals, the linkage matrix, and
  the resonance clustering are all computable. The one thing the old system needed humans for —
  detecting *multi-system convergence* (e.g. "Mercury agrees across 7 systems") — is now done by the
  **L0 Concordance** (which already maps where schools agree/diverge).
- **Clean slate.** No legacy MSR/CDLM/CGM/RM data (all native-specific, all wiped).

## §B — Governing rules

1. **Chart-parameterized, never native-specific.** L2 is generated per chart from L1 + L0 rules; no
   hand-authored per-chart content.
2. **Every L2 object cites its grounding** — the L1 fact IDs it consumes and the L0 rule/verse it
   applies (derivation ledger). A single L1 correction re-propagates mechanically.
3. **No stored narrative.** UCN-as-prose is retired; the unified reading is a **query-time** LLM act
   over L1 facts + L2 structures + L0 rules. L2 stores structure, not essays.
4. **Multi-ayanamsha** — every L2 object keyed by (chart_id, ayanamsha_id, build_id).
5. **Tooling per the L0 standard** (one registry, two transports, capability-over-primitives).
6. **PyJHora-boundary respected** — L2 consumes L1 facts; it never invokes the engine.

## §C — Assets + derivation chain

```
L1 Fact Store  +  L0 (rule base · concordance · ontology)
        │
        ▼
2.1 CGM (Chart Graph)   — deterministic typed graph of the chart
        ▼
2.2 MSR (Signal Map)    — rule-fired signals (+ concordance-detected convergences)
        ▼
2.3 CDLM (Linkage Matrix) — domain×domain structural linkages from MSR + CGM
        ▼
2.4 RM (Resonance Map)  — clustered high-voltage resonance elements
        ▼
2.5 UCD (Chart Digest)  — read-side join of the above (not a stored narrative)
        ▼
   query-time LLM synthesis (L3 / consume loop)
```

## §D — Per-asset detail

### 2.1 · CGM — Chart Graph Model
- **What:** a typed graph of the chart — nodes (planets, houses, signs, nakshatras, yogas, karakas,
  divisional placements, dashas, sensitive points) + typed edges (dispositor, graha/bhava/Jaimini
  aspect, ownership, tenancy, yoga-membership, karaka-role, dasha-activation, divisional-confirmation…).
- **Build:** **fully deterministic, rule-driven** from L1 facts; every node cites its L1 fact source.
- **Role:** the pivot — translates flat facts into a traversable structure that MSR/CDLM/RM read.
- **OPEN:** since it's deterministic, does CGM belong at the *top of L1* (a graph projection of facts)
  or the *base of L2*? (Leaning L2-base, but flag.)

### 2.2 · MSR — Signal Map (Master Signal Register)
- **What:** the chart's corpus of signals — each a grounded assertion (domain, valence, confidence,
  dasha-activation, source citation, anchors) about the chart.
- **Build (the shift):** **rule-fired** — apply L0 rule base to L1 facts/CGM → candidate signals;
  **convergence-detected** — use L0 concordance to flag where multiple schools/rules agree on the same
  point (this replaces the old hand-verification of cross-system convergences). Confidence = rule
  strength × concordance breadth.
- **Per chart, multi-ayanamsha.** Reusable artifact = the rule library (L0) + signal schema; the
  573-style instances are *generated*, not authored.
- **OPEN:** signal schema; how much still needs human review vs fully rule-driven; the rule library's
  overlap with the L0 Rule Base (likely the same asset).

### 2.3 · CDLM — Linkage Matrix
- **What:** domain × domain matrix — how each life domain structurally influences every other
  (linkage type, mechanism, MSR anchors, strength, direction, valence), asymmetric by design.
- **Build:** rule-derived from MSR + CGM (shared planets/karakas/houses between domains).
- **OPEN:** domain taxonomy (the 9 domains) — keep or revise; cell schema.

### 2.4 · RM — Resonance Map
- **What:** clustered high-voltage resonance elements (a planet/pattern with many simultaneous
  designations, or a structural paradox) — constructive vs destructive resonance, net classification.
- **Build:** cluster MSR signals + CGM nodes algorithmically; classify net effect. (Old version was
  hand-curated; target is auto-clustered + thresholded, with optional review.)
- **OPEN:** clustering method; how much is auto vs curated.

### 2.5 · UCD — Chart Digest (read-side join)
- **What:** the "chart summary" surface — a **read-time join** of the strength/linkage/graph/resonance
  summaries (per the 2026-05-29 UCN→UCD retirement). Not a stored narrative asset.
- **Tool:** `query_ucd(chart_id, ayanamsha_id)`.

## §E — The elevation (what changes vs the old L2.5)

| Old L2.5 | New L2 |
|---|---|
| Hand-verified signals, native-specific (closed for Abhisek) | **Rule-driven, chart-parameterized** (any chart) |
| Cross-system convergence detected by a Jyotishi | **Detected by the L0 Concordance** |
| UCN = stored LLM narrative | **No stored narrative; query-time synthesis** |
| Single-ayanamsha (Lahiri) | Multi-ayanamsha |
| RM hand-curated | Auto-clustered + thresholded (optional review) |
| Rule IP embedded in the signals | **Rule IP lives in the L0 Rule Base (reusable)** |

The big idea: **L2 becomes a deterministic + rule-driven synthesis *engine*, run per chart**, with the
classical judgment captured once in L0's rule base + concordance — not re-authored per native.

## §F — Tooling

- Capability tools (both transports): `query_signals` (MSR by domain/confidence/valence/dasha),
  `query_linkages` (CDLM), `get_chart_graph` (CGM subgraph), `query_resonance` (RM), `query_ucd`.
  Token-economical, provenance-bearing, on-demand bundles.
- The L2 *build* is a job (per chart), not an LLM tool.

## §G — Storage

- L2 objects are **structured DB rows** (Postgres), keyed by (chart_id, ayanamsha_id, build_id),
  each citing L1 fact IDs + L0 rule IDs. Consumed by the query layer + L3 via **structured tools** —
  **not RAG** (same logic as L1: structured retrieval, not semantic, for derived structures). Any
  narrative is generated at query time, not stored.

## §H — Provenance & verification

- Derivation ledger on every L2 object (L1 facts + L0 rules consumed). Verification = internal
  consistency: every anchor resolves, every rule cites a real L0 verse, determinism on the rule-fired
  parts, FK integrity to L1. No JH oracle. Built + audited by the swarm.

## §I — Open decisions

1. **CGM placement** — top of L1 (graph projection) or base of L2.
2. **MSR rule-engine** — confirm L2 generates signals from the L0 Rule Base; signal schema; degree of
   automation vs human review; relationship between "MSR rule library" and "L0 Rule Base" (likely one).
3. **Domain taxonomy** — keep the 9 domains (Career/Wealth/Relationships/Health/Children/Spirit/
   Parents/Mind/Travel) or revise.
4. **RM clustering** — method + auto-vs-curated.
5. **Concordance-driven convergence** — confirm the L0 Concordance is how multi-system agreement is
   detected (replacing hand-verification).
6. **Narrative** — confirm no stored narrative; query-time only.

---

*End of LAYER_2_SYNTHESIS_DESIGN v1.0 — DRAFT for native review, 2026-06-02. Same drill: debate §I,
close each, then the Layer 2 plan brief.*
