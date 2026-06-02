---
artifact: ASSET_RECONCILIATION_v1_0.md
canonical_id: ASSET_RECONCILIATION
version: 1.0
status: CLOSED 2026-06-02 (design baseline — sealed in M5_REARCHITECTURE_DESIGN_CLOSE_v1_0)
authored_by: Claude (Cowork) 2026-06-02
purpose: >
  Complete inventory + reconciliation of every build asset, answering: which downstream blocks
  are fully producible by an upstream asset and should be merged up, without losing any data.
  Produces the reconciled minimal-but-complete asset map (global vs chart-specific) for the
  watertight rebuild. Feeds the Asset Contract Registry (BUILD_GUARANTOR_SWARM_CHARTER §F).
evidence_base:
  - platform/python-sidecar/pipeline/writers/chart_facts_writer.py
  - platform/python-sidecar/pipeline/writers/forensic_writer.py + pipeline/render/*_renderer.py
  - platform/python-sidecar/pyjhora_adapter/compute.py
  - platform/python-sidecar/pipeline/{time_synchronicity,phase_locked_anchors,sarvatobhadra_chakra,vedha,bhrigu_bindu,graha_aspects,varsha_digest}*.py
  - platform/python-sidecar/pipeline/writers/{tajik_varsha_year_lords,chart_lattice,pattern_catalog,divergence_ledger,negative_space,derivation_graph,vedha_anchor_bridge}*.py
  - platform/migrations/158_build_dependencies.sql, 140–153
caveat: >
  Several writers are stubs or carry conflicting reports; verdicts below are the TARGET
  reconciliation grounded in current code. Exact per-asset current-state is pinned by the
  Nirīkṣaka audit + per-asset deep dives before any implementation.
---

# Asset Reconciliation — Complete Inventory + Merge Map

## §1 — Two findings to act on

**F1 — chart_facts (A3) is disconnected from the engine (bug).** `chart_facts_writer` loads a
static hand-extracted GCS YAML (`CHART_FACTS_EXTRACTION_v1_0.yaml`); the engine `chart_output`
passed to it is unused (`chart_facts_writer.py:55, :94–133`). It is therefore identical for every
client — unacceptable for a multi-chart instrument. **Target: A3 = projection of A1 engine JSONL.**

**F2 — forensic render (A2) adds readability, not data.** ~90% pure formatting of engine values;
the only render-time computation is a rules-based Jaimini matrix + yoga summary counts
(`aspects_renderer.py:145–188`, `yogas_renderer.py:132–145`). **Target: A2 = presentation
projection only; move its small computations into the engine.** A2 and A3 become two sibling
projections of one canonical A1 JSONL.

## §2 — The reconciliation principle

An asset earns its own block only if it performs a computation **no upstream asset can produce**.
Three failure modes to merge up: (a) deterministic positional/arithmetic math → belongs in the
A1 engine pass; (b) pure aggregation/negation over existing facts → a projection or view, not a
writer; (c) a SQL view or provenance trail → a view, not an asset. Genuine multi-asset synthesis
stays. **No data is lost** — merged outputs are still produced, by the correct upstream owner.

## §3 — Reconciled cluster map

### M0 — Global cluster (build once, reused for every chart)
| Unit | Was | Notes |
|---|---|---|
| G-EPH ephemeris (raw) | part of A0 | foundation |
| G-TXT classical texts (raw) | part of A0 | BPHS, Jaimini, KP, Tajaka |
| G-IDX chunk + vector index | part of A0 | data-engineering of G-TXT |
| G-PAN daily panchang almanac | A4 (daily) | from ephemeris; keyed date×location, not chart |
| G-REF global reference tables | **NEW home** | absorbs A17 Sarvatobhadra grid + Hadda table + year-lord sequence + aspect-angle defs (static classical data currently embedded in writers) |

### Chart-specific cluster (per chart_id, on build)
| Layer | Unit | Composition |
|---|---|---|
| **L1 ENGINE** | **A1 — PyJHora** (one deterministic computation → canonical JSONL) | absorbs A5 sensitive points · A6 vargas · A7 dashas · A8 shadbala/ashtakavarga/bala · A9 sade-sati · birth-panchang · **A18 vedha firing · A19 bhrigu transits · A20 tajik year-lords · A21 exact-aspect lifetime · META_δ negative-space** · the render-time Jaimini matrix. Everything deterministic/positional/rule-based. |
| **L1 PROJECTIONS** | A3 chart_facts (→ DB) · A2 forensic render (→ markdown) | two siblings off the A1 JSONL; A3 re-sourced (F1); A2 presentation-only (F2) |
| **L2.5 SYNTHESIS** | A10 MSR → A11 CDLM → A12 CGM → A13 RM · UCD (read-side join) | genuine cross-domain derivations; A14 already retired to UCD read-surface |
| **L3 SYNTHESIS (keep)** | A15 time-synchronicity · A16 phase-locked anchors · META_α chart-lattice · META_γ divergence-ledger · BRIDGE vedha-anchor | true multi-asset synthesis; not upstream-producible |
| **VIEWS / PROVENANCE** | A22 varsha digest · META_β pattern-catalog · META_ε derivation-graph · META_ζ unified-lattice | SQL/materialized views or provenance trails, not writer assets |

## §4 — Per-asset verdicts (complete inventory)

| Asset | Verdict | New home |
|---|---|---|
| A0 (concept) | = the M0 global cluster | M0 |
| A1 engine | KEEP — becomes the single deterministic computation (enumerated superset of v8.0) | L1 engine |
| A2 forensic render | KEEP as **projection only** (move Jaimini matrix upstream) | L1 projection |
| A3 chart_facts | KEEP as projection; **RE-SOURCE from A1 JSONL** (currently static YAML — F1) | L1 projection |
| A4 panchanga | SPLIT: daily almanac → M0 G-PAN; birth-panchang → A1 fact | M0 + A1 |
| A5 sensitive points | MERGE → A1 fact category | A1 |
| A6 vargas | MERGE → A1 fact category | A1 |
| A7 dashas | MERGE → A1 fact category | A1 |
| A8 t1 structural (shadbala/ashtakavarga) | MERGE → A1 fact category | A1 |
| A9 sade sati | MERGE → A1 fact category | A1 |
| A10 MSR | KEEP — synthesis | L2.5 |
| A11 CDLM | KEEP — synthesis | L2.5 |
| A12 CGM | KEEP — synthesis | L2.5 |
| A13 RM | KEEP — synthesis | L2.5 |
| A14 UCN/UCD | ALREADY RETIRED as writer → read-side join (`query_ucd`) | L2.5 read-surface |
| A15 time-synchronicity | KEEP — multi-system convergence synthesis | L3 |
| A16 phase-locked anchors | KEEP — depends on A15 + interpretation | L3 |
| A17 sarvatobhadra | MOVE → global reference (not per-chart) | M0 G-REF |
| A18 vedha | MERGE → A1 (rule-based firing on positions/dashas) | A1 |
| A19 bhrigu bindu | MERGE → A1 (midpoint + transit scan) | A1 |
| A20 tajik year-lords | MERGE → A1 (arithmetic + table lookup) | A1 |
| A21 exact-aspect lifetime | MERGE → A1 (aspect target + transit scan) | A1 |
| A22 varsha digest | DEMOTE → materialized view (yearly aggregation) | view |
| META_α chart-lattice | KEEP — daily snapshot index synthesis | L3 |
| META_β pattern-catalog | DEMOTE → view/index (mirrors existing rows) | view |
| META_γ divergence-ledger | KEEP — cross-system contradiction synthesis | L3 |
| META_δ negative-space | MERGE → A1 (negation of L1 facts) | A1 |
| META_ε derivation-graph | DEMOTE → provenance view | view |
| META_ζ unified-lattice | KEEP as SQL view (already) | view |
| BRIDGE vedha-anchor | KEEP — interaction synthesis | L3 |

## §5 — Net effect

Chart-specific writer-assets collapse from ~24 to: **1 engine + 2 projections + 4 L2.5 synthesis
(+ UCD read-join) + 5 genuine L3 syntheses (A15, A16, META_α, META_γ, BRIDGE) + 4 views.**
Deterministic computation consolidates into one auditable engine pass; duplication (e.g. shadbala
computed twice, vedha/aspect tables re-implemented downstream) is eliminated; chart_facts is
reconnected to the engine. **Every data domain is retained.**

## §6 — Open confirmations (native + per-asset dives)

1. Confirm the merge map (esp. folding A18–A21 + META_δ into A1, and the four view-demotions).
2. RM rename — none found; confirm RM stays "Resonance Map" or supply the intended name.
3. Per-asset deep dives pin exact current-state (stub vs built) and the engine's per-domain output
   contract — starting at M0 (global), then A1.

---

*End of ASSET_RECONCILIATION v1.0 — DRAFT for native review, 2026-06-02. Feeds the Asset Contract
Registry. Verdicts are the target reconciliation; Nirīkṣaka audit confirms exact current-state.*
