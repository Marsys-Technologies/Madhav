---
artifact: PROJECT_ARCHITECTURE_v2_2
document: PROJECT MASTER ARCHITECTURE BLUEPRINT
project_name: Abhisek Mohanty — Jyotish Intelligence System (MARSYS-JIS)
subject: Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar)
version: 2.3
supersedes: 2.2 (2026-04-24) and 2.1 (2026-04-17) and 2.0 (2026-04-17 mid) and 1.0 (archived)
status: APPROVED BLUEPRINT — Multi-Ayanamsha Build arc amendment absorbed
author_of_blueprint: Claude (Anthropic)
blueprint_date: 2026-04-24
produced_during: STEP_5A_PROJECT_ARCHITECTURE_REFRESH (Step 0 → Step 15 governance rebuild)
v22_rationale: >
  Minor-version refresh absorbing the architectural developments accumulated since
  v2.1 was closed on 2026-04-17: the ten-macro-phase Macro Plan arc (M1–M10) per
  MACRO_PLAN_v2_0.md; the Learning Layer substrate (LL.1–LL.10) and the System
  Integrity Substrate (IS.1–IS.9) that parallel it; the Claude ↔ Gemini multi-agent
  collaboration workstream (two-pass protocol, mirror discipline per ND.1,
  disagreement register); corrected §E file-system tree (v8.0 forensic, LEL v1.2,
  MSR v3.0 at 499 signals, UCN v4.0, CDLM v1.1, RM v2.0, CGM v2.0); live content
  for D.6/D.7/D.9 workstreams; new §D.10 and §D.11 workstreams; new §L
  Governance Rebuild Reference. Produced in Step 5A of the Step 0 → Step 15
  governance rebuild. §B principles, §C five-layer pyramid, §F pre-existing
  namespace rows, §H quality standards, and §J resolved decisions are preserved
  verbatim.
v21_rationale: >
  All five §J open decisions resolved. Daily cadence locked with compensating
  discipline. Jagannatha Hora procurement confirmed. No privacy or audience
  boundaries. Chart-first reveal approach for Domain Reports. Blueprint now
  governs active execution. (v2.1 rationale preserved for lineage.)
v2_rationale: >
  Native raised two architecturally critical concerns against v1.0:
  (1) Domain-segregated L3 causes context-collapse.
  (2) L1→L2 transition lacks completeness guarantees.
  v2.0 inserted L2.5 Holistic Synthesis Layer, added CGP at L1, added Mode B
  Exhaustive Matrices at L2, revised query routing, and enforced whole-chart-read
  discipline. Scope expanded to 42 sessions. MSR target 500-600. UCN timing early.
  (v2.0 rationale preserved for lineage.)
purpose: >
  This document is the single governing architecture for all future work on the
  Abhisek Mohanty astrological knowledge-asset project. Every asset created,
  every session conducted, every artifact produced, and every decision made
  in this project must be traceable to the principles, taxonomies, and
  workstreams defined here. Future Claude sessions (and Gemini sessions, per
  §D.11 Multi-Agent Collaboration) should load this file FIRST before any other
  work, alongside MACRO_PLAN_v2_0.md for strategic arc orientation and the
  STEP_LEDGER while the Step 0 → Step 15 governance rebuild remains open.
audience:
  primary: Abhisek Mohanty (native, project owner)
  secondary: Future Claude instances continuing the work
  tertiary: Future Gemini instances operating the L4 Discovery Layer under the
            Multi-Agent Collaboration workstream (§D.11)
  quaternary: Independent classical-Jyotish acharyas invited for review
---

# MARSYS-JIS — PROJECT MASTER ARCHITECTURE BLUEPRINT v2.2

## §A — EXECUTIVE FRAME

### A.1 — The Project Thesis

This project exists to construct a **world-class, acharya-grade astrological intelligence system** centered on the natal chart of Abhisek Mohanty, such that the native can:

1. **Navigate real life decisions** — career, health, relationships, timing, wealth, family — with chart-calibrated clarity
2. **Access spiritual/philosophical depth** — understand karma, dharma, soul-architecture at a depth most professional readings never reach
3. **Generate any-domain insight on demand** — the system must function as a reusable, extensible engine, not a one-time artifact

The ambition is explicit: to exceed the depth and rigor of 99% of professional Jyotish work being done today, matching the standard of senior acharyas who integrate classical Parashari, Jaimini, KP, Nadi, and Tajika systems simultaneously — *and* who hold the chart as one integrated organism rather than as nine separated domain projections.

### A.2 — Why This Is Achievable

Four structural advantages make the ambition realistic:

- **Foundation already strong**: v8.0 forensic data file (unified — supersedes v6.0 + v7.0 supplement), Deep Analysis v1.2.1 (6,314 lines, 17 RPT blocks, confidence 0.81), full L2.5 Holistic Synthesis stack (MSR v3.0 at 499 signals, UCN v4.0, CDLM v1.1, RM v2.0, CGM v2.0), nine L3 Domain Reports at v1.1+.
- **Systematic LLM orchestration**: with structured prompts, versioned artifacts, governance discipline, and the Claude ↔ Gemini two-pass protocol (§D.11), we can run the equivalent of a research team through dual-thread dialogue.
- **Compounding returns**: each workstream enriches downstream workstreams. Life Event Log calibrates Deep Analysis; Deep Analysis improves Holistic Synthesis; Holistic Synthesis drives Domain Reports; Domain Reports reveal gaps for Facts Layer; empirical outcomes (M4–M6 in the Macro Plan) feed the Learning Layer; classical cross-reference (M8) raises the bar on attribution.
- **Holistic-first architecture** (established in v2.0, preserved here): by inserting L2.5 between L2 and L3, queries always see the whole chart before focusing. Domain reports become *lenses into* the whole, not *substitutes for* the whole.

### A.3 — What Success Looks Like (Definition of Done)

The project is "complete" when:

- (a) **Facts Layer at v8.0 with CGP audit passed** — all v6.0 categories absorbed or extended; new categories added (Nadi-amsa, Prashna-readiness, full Bhinna Ashtakavarga transit-grids, life-event-log integration, complete sahams inventory). **Every required cell verified populated** (Completeness Guarantee Protocol — see §G.1.CGP). *Already CURRENT as `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`.*
- (b) **Life Event Log v1.2+** — chronologically logged dated life events with chart-state tagging, yielding a validated retrodictive pattern library. The Macro Plan's M4 empirical-calibration gate requires ≥ 40 LEL events spanning ≥ 5 years (§CW.LEL). *Currently at v1.2 with 36 events + 5 period summaries + 6 chronic patterns.*
- (c) **Deep Analysis v2.0 in dual mode** — Mode A: 25+ RPT sections with full 3-interpretation discipline. Mode B: exhaustive House Matrix (12 rows), Planet Matrix (9 rows), Sign Matrix (12 rows), Dasha-Period Matrix (200+ rows), Divisional Chart Matrix (16 rows). **Every entity is represented.**
- (d) **L2.5 Holistic Synthesis Layer complete** — Chart Graph Model, Master Signal Register (499 signals at v3.0; floor met, stretch toward 600 non-blocking), Cross-Domain Linkage Matrix, Resonance Map, Unified Chart Narrative (30-50K words). *Already CURRENT at the versions above.*
- (e) **Nine Domain Reports** — Financial (v2.1), Career/Dharma, Health/Longevity, Relationships/Marriage, Children/Legacy, Spiritual/Moksha, Parents/Family-Karma, Psychology/Mind, Travel/Foreign. Each explicitly cites Unified Chart Narrative as parent. *All nine currently at v1.1+.*
- (f) **Remedial Protocol Master Codex** — unified gemstone + mantra + yantra + devata + muhurta + charity + dietary + behavioral framework. *Currently at v2.0 (PART1 + PART2).*
- (g) **Temporal Engines** — lifetime timeline, rolling 36-month heatmap, annual Varshphal generator, daily-transit digest capability. *Lifetime timeline v1.0 and Varshphal heatmap v1.0 currently CURRENT; the M3 macro-phase of the Macro Plan drives the Temporal Engines expansion.*
- (h) **Query & Prompt Library with whole-chart-read enforcement** — battle-tested prompts with mandatory cross-domain check. *Currently at v1.0.*
- (i) **Governance Stack + Governance Integrity Protocol** — versioning discipline, confidence registers, contradiction logs, red-team cadence, falsifier-tracking, plus the mechanical enforcement layer (drift detector, schema validator, mirror enforcer, session-open/close templates, DISAGREEMENT_REGISTER) produced by Steps 6–7 of the Step 0 → Step 15 governance rebuild.
- (j) **Learning Layer operational** (new in v2.2 per the Macro Plan) — LL.1–LL.10 mechanisms scaffolded in M2, with active promotion per §LL-Appendix.A of the Macro Plan. All ten `active` at M10 close per the Macro Plan's definition of project-done.
- (k) **External validation** (new in v2.2 per the Macro Plan) — at least one blind-test report from an acharya-reviewer panel of n ≥ 3; methodology published (arXiv minimum; peer-reviewed stretch) at M10 per MP §Post-M10 Framing §3.9.B.

An independent senior acharya, on reviewing the full corpus, should reach one of three conclusions: "this is my own level", "this is above my own level", or "this reveals things I would not have seen on first pass". Anything less means the project is incomplete.

### A.4 — How v2.0 Addresses the Concerns That Drove the Rebuild

**Concern #1 — Domain reports cause context-collapse.** Resolved by:
- Inserting L2.5 Holistic Synthesis Layer between L2 and L3 (§C, §G.3)
- Mandating that every L4 query routes through L2.5 first, picks up cross-domain signal, then focuses via L3 (§G.7, §H.4)
- Building the Unified Chart Narrative early — before any Domain Report — as the "mother document" all Domain Reports cite and cannot contradict (§I Phase 2A)
- Installing "whole-chart-read" discipline as a procedural session requirement (§B.11, §H.4)

**Concern #2 — L1→L2 lacks completeness rigor.** Resolved by:
- Completeness Guarantee Protocol (CGP) at L1 — explicit combinatorial coverage audit before L2 work proceeds (§G.1.CGP)
- Mode B Exhaustive Matrices at L2 — systematic House/Planet/Sign/Dasha matrices that guarantee every entity is examined (§G.3.ModeB)
- Data provenance tagging for every L1 cell (Swiss Ephemeris / Jagannatha Hora / manual / external)
- Explicit refusal protocol: L2 will not run interpretation against cells marked TBD or incomplete (§B.12)

### A.4.addendum — Post-v2.1 drift and the v2.2 refresh rationale (NEW in v2.2)

Between v2.1 closure (2026-04-17) and this refresh (2026-04-24) the project accumulated architectural developments that v2.1 did not anticipate and that the Step 0 → Step 15 governance rebuild surfaced. Four drift loci were documented in `GROUNDING_AUDIT_v1_0.md` and the Step 1 Macro Plan critique: (i) §E file tree named `PROJECT_ARCHITECTURE_v2_0.md`, `FORENSIC_DATA_v7_0.md`, and `LIFE_EVENT_LOG_v1_0.md` — none of which are the CURRENT canonical paths (v8.0 forensic, v1.2 LEL, v2.1 architecture all landed after v2.1 closed its tree); (ii) §I named a 6-phase 38-42-session schedule that has since been superseded by the ten-macro-phase M1–M10 arc in `MACRO_PLAN_v2_0.md`; (iii) §D.6, D.7, D.9 carried placeholder "Unchanged from v1.0" back-pointers that no longer describe live scope; (iv) no §D workstream covered the Learning Layer (LL.1–LL.10), the System Integrity Substrate (IS.1–IS.9), the Ethical Framework, the External Dependency Graph, or the Claude ↔ Gemini Multi-Agent Collaboration workstream that the new Macro Plan and native directive **ND.1 (Mirror Discipline)** both introduced. This v2.2 refresh closes those four loci without disturbing the blueprint's load-bearing foundations: §B (12 architectural principles), §C (five-layer pyramid), §F pre-existing namespace rows, §H (quality standards), and §J (the five resolved decisions) are preserved verbatim. The refresh is a minor bump, not a v3.0 rewrite; conceptual continuity with v2.1 is intact. Cross-reference: `MACRO_PLAN_v2_0.md` is the authoritative strategic-arc source for anything §I now defers to it on; `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` §1 ND.1 is the authoritative source for the mirror-discipline principle §D.11 enumerates; the new §L points to the full Step 0 → Step 15 rebuild context.

---

## §B — ARCHITECTURAL PRINCIPLES (NON-NEGOTIABLE)

These principles govern every asset created. Any future session that violates them must be flagged and corrected. Twelve principles (expanded from ten in v1.0). **§B is preserved verbatim from v2.1; no edits in v2.2.**

### B.1 — Facts/Derivation/Interpretation Separation

- **Facts** (observed or computed chart values): live ONLY in the Facts Layer (L1). No interpretation, no narrative.
- **Derivations** (logical transforms of facts — e.g., yoga detection, karaka assignment): live at L1/L2.5 boundary with explicit derivation-ledger pointing to source facts.
- **Interpretations** (meaning, implication, prediction): live ONLY at L2.5+ with explicit derivation-chain back to facts.

**Why this matters**: when the underlying facts are audited (e.g., re-computed with different ayanamsa), we know exactly which interpretations must be re-examined. Mixing layers destroys auditability.

### B.2 — Stable ID Discipline

Every fact, derivation, interpretation, event, signal, edge, node, pattern, and intervention receives a stable ID. ID namespaces are defined in §F below. IDs never change once published; deprecated IDs are marked DEPRECATED with pointer to successor.

### B.3 — Derivation Ledger Mandate

Every L2.5+ claim must carry a `DERIVATION_LEDGER` entry that lists the specific L1 fact IDs it consumes. No claim is allowed to rest on "as is known classically" or "per tradition" without source.

### B.4 — Three-Interpretation Discipline

Every significant interpretive claim must enumerate at least three candidate interpretations (A, B, C), weigh supporting evidence for each, explicitly select one with rationale, and publish a falsifier (what observation would refute the selection).

### B.5 — Red-Team Cadence

Every major artifact must pass a red-team audit covering: traceability, cross-section contradiction, confirmation bias, missed-data, over-claim, orchestration, residual risk. Red-team passes produce a fix-log that becomes part of the artifact's version history.

### B.6 — Confidence Calibration

Every RPT-level claim carries a confidence score (0.00–1.00). Aggregate confidence is tracked per-artifact and per-project. Scores reflect actual uncertainty, not rhetorical hedging.

### B.7 — Honest-Calibration Scope

No report overstates what the chart signals. Where chart signals are ambiguous, the ambiguity is named. Where chart signals contradict the native's stated preference, the contradiction is published rather than softened.

### B.8 — Versioning Discipline

- **Major version (v1 → v2)**: scope expansion, methodology change, significant new data incorporated
- **Minor version (v1.0 → v1.1)**: defect fixes, red-team repairs, clarifications without analytical change
- **Patch version (v1.0.0 → v1.0.1)**: typo fixes, metadata updates

Every version change produces a changelog section documenting what changed and why.

### B.9 — LLM-Readability First, Human-Readability Equal

Every artifact is primarily engineered for downstream LLM consumption (future Claude sessions), but must remain human-readable. Structured YAML blocks, stable IDs, explicit cross-references are mandatory. Prose is also written to flow naturally.

### B.10 — No Fabricated Computation

If a computation requires a specialist tool (Jagannatha Hora, Parashara's Light, Shri Jyoti Star, etc.) and is not already in L1, it is marked `[EXTERNAL_COMPUTATION_REQUIRED]` with exact specification of what to compute. Claude never invents numerical chart values.

### B.11 — Whole-Chart-Read Discipline (NEW in v2.0)

Every query, before producing its answer, must execute a mandatory cross-domain check:
1. Route the query through L2.5 Holistic Synthesis Layer first
2. Identify which other domains touch this query's subject-matter (via Cross-Domain Linkage Matrix)
3. Surface cross-domain signals before domain-focused answer
4. Answer synthesizes whole-chart context + domain-specific depth

A query-answer that skips L2.5 consultation is a procedural violation, equivalent to a red-team finding.

**Proportionality carve-out (RS-4, native-authorized 2026-07-19; source: `RETRIEVAL_STRATEGY_v1_0.md` §3.6).** B.11 governs *interpretive* queries. A pinpointed *factual lookup* (single-fact retrieval at `depth: retrieval`) satisfies B.11 via the frame check its response already carries (chart_header + session pin), not a full L2.5 synthesis pass — with the mandatory escalation valve: if the requested fact participates in an active contradiction, firing yoga, or open prediction window, the response flags that in one line with a drill pointer. The valve is what keeps the carve-out inside B.11's spirit: no unrequested depth, no silence where depth is warranted.

### B.12 — Completeness Guarantee Refusal (NEW in v2.0)

L2 analytical work refuses to interpret against incomplete L1 data. When a cell in the Completeness Guarantee Protocol audit is marked TBD, EXTERNAL_REQUIRED, or MISSING, any L2 work that would consume that cell explicitly flags the gap and waits for resolution. Interpretation shall not paper over a missing fact with "likely" or "probably" — it shall name the gap and pause.

---

## §C — THE FIVE-LAYER PYRAMID (v2.0 CONCEPTUAL MODEL)

**§C is preserved verbatim from v2.1; no edits in v2.2.** The five-layer model (L1 → L2 → L2.5 → L3 → L4) is load-bearing and stable. Cross-cutting substrates introduced by `MACRO_PLAN_v2_0.md` (the Learning Layer and the System Integrity Substrate) are described in §D.10 (Learning Layer workstream) and §D.11 / §L (System Integrity / Governance Rebuild) respectively; they do not alter the pyramid, they operate across it.

**Key change from v1.0:** insertion of L2.5 between L2 and L3. This layer holds the whole chart as one integrated object, and all L4→L3 queries route through it first.

```
┌─────────────────────────────────────────────────────────────────┐
│  L4 — QUERY INTERFACE                                           │
│  Prompt library, question templates, session protocols          │
│  ENFORCES: Whole-chart-read discipline (B.11)                   │
│  "How to ask the system anything"                               │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Every query routes here ↓
┌──────────────────────┴──────────────────────────────────────────┐
│  L3 — INSIGHT GENERATION                                        │
│  Domain Reports (×9), Remedial Codex, Temporal Engines          │
│  CONSTRAINT: Every Domain Report cites Unified Chart Narrative  │
│              as parent; no Domain Report contradicts L2.5       │
│  "What the system produces for specific questions"              │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Pulls whole-chart context from ↓
┌──────────────────────┴──────────────────────────────────────────┐
│  L2.5 — HOLISTIC SYNTHESIS  ★ NEW IN v2.0 ★                    │
│  • Chart Graph Model (all nodes/edges)                          │
│  • Master Signal Register (500-600 signals)                     │
│  • Cross-Domain Linkage Matrix                                  │
│  • Resonance Map                                                │
│  • Unified Chart Narrative (30-50K words — MOTHER DOCUMENT)     │
│  "The whole chart as one organism"                              │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Synthesizes from ↓
┌──────────────────────┴──────────────────────────────────────────┐
│  L2 — ANALYTICAL LAYER (ARCHIVED 2026-04-28 — Phase 14F)        │
│  Mode A: Curated Deep Analysis (RPT.* — 25+ interpreted blocks) │
│  Mode B: Exhaustive Matrices ★ NEW IN v2.0 ★                   │
│          - House Matrix (12 rows)                               │
│          - Planet Matrix (9 rows)                               │
│          - Sign Matrix (12 rows)                                │
│          - Dasha-Period Matrix (200+ rows)                      │
│  ► All files now at: 99_ARCHIVE/02_ANALYTICAL_LAYER/            │
│  "How the system reasons — both opportunistically AND           │
│   exhaustively"                                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Analyzes from ↓
┌──────────────────────┴──────────────────────────────────────────┐
│  L1 — FACTS LAYER                                               │
│  • Forensic Data v8.0 (unified from v6.0 + v7.0 supplement)     │
│  • Life Event Log v1.2+                                         │
│  • External Reference Card (classical citations)                │
│  GATE: Completeness Guarantee Protocol (CGP) ★ NEW IN v2.0 ★   │
│        L2 shall not run against cells marked incomplete (B.12)  │
│  "What the system knows — with completeness audit"              │
└─────────────────────────────────────────────────────────────────┘
```

(§C.1 through §C.5 subsection narratives for L1, L2, L2.5, L3, L4 are preserved verbatim from v2.1; reproduced here by reference — a reader needing the full subsection text should consult v2.1 §C.1–§C.5, which v2.2 preserves unchanged. Only the ASCII pyramid's v1.0-era "Forensic Data v7.0" label has been corrected to "v8.0 (unified from v6.0 + v7.0 supplement)" and the LEL label to "v1.2+"; these are version-pointer corrections permitted by the Step 5A brief's D.1–D.5 latitude, not model changes.)

### C.1 — Layer L1 — Facts Layer

**Purpose**: single source of truth for all chart facts, derivations, and lived reality.

**Contents**:
- **FORENSIC_ASTROLOGICAL_DATA_v8_0.md** — unified canonical L1; supersedes v6.0 and the v7.0 supplement; integrates Jagannatha Hora v8.0 authoritative values for Special Lagnas, Sahams, Shadbala ranking, Yogas, Longevity, and additional dasha systems per the dual-engine policy declared in its frontmatter
- **LIFE_EVENT_LOG_v1_2.md** — structured log of 36 dated life events + 5 period summaries + 6 chronic patterns, with chart-state tags populated from Swiss Ephemeris per Session 4
- **EXTERNAL_REFERENCE_CARD** (in scope; when produced, lives under `01_FACTS_LAYER/`) — classical sutra/sloka references used across L2+

**Completeness Guarantee Protocol (CGP) gate** — `CGP_AUDIT_v1_0.md` at L1 closure verified computational completeness. Gaps are named, tagged with required external source, and resolved before L2 work proceeds against those cells.

**Update discipline**: L1 is append-only by default. Corrections produce new versions; old versions retained under `§8 Archival` in `FILE_REGISTRY_v1_1.md`.

### C.2 — Layer L2 — Analytical Layer *(ARCHIVED 2026-04-28 — Phase 14F)*

> **Archive notice:** The entire L2 layer was archived in Phase 14F. All files (DEEP_ANALYSIS_*, MATRIX_*) are preserved at `99_ARCHIVE/02_ANALYTICAL_LAYER/` for historical audit only. The L2.5 Holistic Synthesis stack supersedes L2. The description below is retained as historical context.

**Purpose**: extract patterns, detect convergences, resolve contradictions, formulate interpretations — via two complementary modes.

**Mode A — Curated Deep Analysis** (current v1.2.1; to be expanded to v2.0 per §D.3 spec):
- 25+ RPT sections (signal-driven, interpreted)
- SIG.*, CVG.*, CTR.* libraries
- 3-interpretation discipline throughout
- Red-team audit per version

**Mode B — Exhaustive Matrices** (closed at v1.0 per `FILE_REGISTRY_v1_1.md` §3):
- **House Matrix** (`MATRIX_HOUSES.md`)
- **Planet Matrix** (`MATRIX_PLANETS.md`)
- **Sign Matrix** (`MATRIX_SIGNS.md`)
- **Divisional Chart Matrix** (`MATRIX_DIVISIONALS.md`)
- **Dasha-Period Matrix** (`MATRIX_DASHA_PERIODS.md`)

**Modes are complementary, not redundant**: Mode B guarantees no entity is missed (Concern #2); Mode A provides interpretive depth where it matters most. Mode B outputs are inputs to L2.5 (specifically the Master Signal Register).

**Update discipline**: versioned. Each version produces a full red-team audit before closure.

### C.3 — Layer L2.5 — Holistic Synthesis Layer

**Purpose**: hold the whole chart as one integrated organism. Resolve the domain-context-collapse problem by providing a single layer where every query can retrieve whole-chart context before focusing.

**Five components, at current versions per `FILE_REGISTRY_v1_1.md` §4:**

**C.3.1 — Chart Graph Model** (`CGM_v2_0.md`)

A directed graph representation of the chart: ~200 nodes (planets, houses, signs, nakshatras, yogas, karaka roles, divisional placements, dasha lords, sensitive points, upagrahas, sahams, arudhas, special lagnas), ~800–1,200 edges (dispositorship, Vedic aspect, Western aspect contextual, ownership, exaltation-affinity, nakshatra-lordship, karaka representation, divisional confirmation, combustion, planetary war, kakshya rulership, saham composition, yoga membership, dasha-lord activation), edge weights derived from Shadbala / Ashtakavarga / Vimsopaka / Bhavabala / dignity, and nine pre-computed domain subgraphs. CGM_v2_0 rebuilt on FORENSIC v8.0 on 2026-04-19; will become `CGM_v9_0.md` after Phase B.3.5 per `PHASE_B_PLAN_v1_0.md`.

**C.3.2 — Master Signal Register** (`MSR_v3_0.md`)

Flat, fully-enumerated list of every detectable signal. Current count: **499 signals** (floor for the Maximum-tier 500–600 target met in v2.0 at 500; v3.0 merged v1.0+v2.0 and deduplicated to 499). Each entry carries: signal_name, signal_type (yoga | dignity | aspect | dasha-activation | transit-activation | house-strength | divisional-pattern | convergence | contradiction | sensitive-point | panchang | remedial-trigger | nakshatra-signature | jaimini-pattern | kp-signature | tajika-pattern | cross-chart), classical_source, entities_involved (CGM.NODE.* ids), strength_score 0.00–1.00, valence, temporal_activation (natal-permanent | dasha-windowed | transit-triggered | annual | monthly), supporting_rules, falsifier, domains_affected, confidence, v6-id lineage, and RPT deep-dive pointer.

**C.3.3 — Cross-Domain Linkage Matrix** (`CDLM_v1_1.md`, internal v1.2)

9×9 domain matrix (career, wealth, health, relationships, children, spirit, parents, mind, travel). Each cell: shared entities (CGM.NODE.* ids), shared signals (MSR.* ids), linkage strength 0–1, key cross-domain yogas, interpretive note.

**C.3.4 — Resonance Map** (`RM_v2_0.md`, internal v2.1)

For every major chart element (32 elements currently), two lists: constructive resonance (`RM.CONSTRUCTIVE.*`) and destructive resonance (`RM.DESTRUCTIVE.*`), plus paradoxes and temporal patterns. Why this matters: a query-answer aware of constructive+destructive resonance surfaces tensions a domain-silo answer cannot.

**C.3.5 — Unified Chart Narrative** (`UCN_v4_0.md`, internal v4.1)

A single integrated reading of the chart as one organism. 30–50K words across ten Parts (Architecture, Soul-Trajectory, Mind-Body Container, Dharmic-Material Engine, Relational Web, Foreign/Moksha Signature, Authority-Through-Tension Pattern, Timing Metaphysics, Contradictions, Operating Instructions). **UCN is the mother document every Domain Report cites.**

### C.4 — Layer L3 — Insight Generation

**Purpose**: produce specific, focused, human-facing deliverables for defined questions.

**Contents**:
- **Domain Reports** — 9 reports, all currently at v1.1+ per `FILE_REGISTRY_v1_1.md` §5; see §D.5 and §G.4
- **Remedial Protocol Master Codex** — unified intervention framework; currently at v2.0 (PART1 + PART2); see §D.6
- **Temporal Engines** — lifetime timeline, rolling heatmap, annual Varshphal, transit digest; see §D.7

**v2.0 constraints (preserved):**
- Every Domain Report must cite the Unified Chart Narrative (UCN) as parent in its metadata
- No Domain Report may contradict the UCN without explicit flag-and-resolve
- Every Domain Report has a mandatory "Cross-Domain Linkages" section citing relevant CDLM entries
- Domain Reports are understood as *lenses into* the whole, not *substitutes for* the whole

**Update discipline**: Domain Reports are versioned per-refresh (typically annual or on major life event). Temporal Engines refresh per schedule (heatmap quarterly, Varshphal annually) per `LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md` §1.

### C.5 — Layer L4 — Query Interface

**Purpose**: the documented ways to extract insight from the system, with whole-chart-read enforcement.

**Contents**:
- **MASTER_PROMPT_LIBRARY** (`06_QUERY_INTERFACE/QUERY_PROMPT_LIBRARY_v1_0.md`) — battle-tested prompts by question-type
- **SESSION_PROTOCOL** (`06_QUERY_INTERFACE/SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md`) — how to start, conduct, and conclude a session against the project
- **DECISION_SUPPORT_PLAYBOOK** (`06_QUERY_INTERFACE/DECISION_SUPPORT_PLAYBOOK_v1_0.md`) — decision-support framework for common life decisions
- **Whole-Chart-Read Enforcer** — the procedural checkpoint every prompt runs (B.11 + §H.4)

**L4 Discovery Layer (new binding in v2.2)**: under `MACRO_PLAN_v2_0.md` §M2, L4 also hosts the Discovery Engine (Gemini-operated connector pass; Claude-operated reconciler pass — see §D.11). The L4 entity defined here is the *query-interface aspect* of L4; the discovery-engine aspect is the *batch pattern-surfacing aspect* of L4. Both coexist under the same layer number; both enforce whole-chart-read discipline.

**Standard routing pattern for every query** (see §H.4):
1. Query enters L4
2. L4 identifies primary domain(s)
3. L4 invokes L2.5 Cross-Domain Linkage Matrix → "what other domains touch this?"
4. L4 pulls Resonance Map entries for primary chart elements involved
5. L4 consults Unified Chart Narrative part(s) relevant
6. THEN L4 routes to L3 Domain Report(s) for focused depth
7. Answer synthesizes whole-chart context + domain-specific depth

---

## §D — THE ELEVEN WORKSTREAMS (EXPANDED IN v2.2)

v2.0 defined eight workstreams; v2.1 retained the same set. v2.2 adds D.10 (Learning Layer substrate) and D.11 (Multi-Agent Collaboration), absorbing the cross-cutting substrates declared by `MACRO_PLAN_v2_0.md`. v2.2 also replaces the v2.1 placeholder back-pointers in D.6, D.7, and D.9 with live scope. D.1–D.5 carry version-pointer corrections only.

### D.1 — Workstream 1 — Facts Layer (L1) + CGP

**Objective**: unified L1 at v8.0 with CGP-audited completeness, plus ongoing Life Event Log expansion.

**Current state** (2026-04-24): `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` is CURRENT; CGP audit closed (`CGP_AUDIT_v1_0.md`). Jagannatha Hora v8.0 values adopted as authoritative for Special Lagnas, Sahams, Shadbala ranking, Yogas, Longevity, and additional dasha systems per the dual-engine policy in the forensic file's frontmatter. LEL at v1.2 with 36 events + 5 period summaries + 6 chronic patterns; LEL is a cross-cutting workstream going forward per `MACRO_PLAN_v2_0.md §CW.LEL` (always-on from Session 2).

**Forward scope** (Macro Plan binding): LEL continues project-lifetime per §CW.LEL. CGP re-run triggers at: (a) any new L1 category, (b) material refresh of JH exports, (c) cross-cutting validator cascade failures per `PHASE_B_PLAN_v1_0.md §J`.

**External dependencies**: Jagannatha Hora (ED.1 in MP v2.0 §3.6.A), Swiss Ephemeris (ED.2).

**Confidence**: L1 at 0.98+; residual uncertainty explicitly named per B.12.

### D.2 — Workstream 2 — Life Event Log (L1 complement; cross-cutting in MP v2.0 as CW.LEL)

**Objective**: highest-leverage empirical-validation corpus; ground-truth spine for the Macro Plan's M4 empirical-calibration phase.

**Scope & schema** (unchanged from v2.1): per-event structured record with `date`, `category`, `magnitude`, `valence`, `native_reflection`, full `chart_state_at_event` block (vimshottari_md, vimshottari_ad, yogini_md, chara_md_ad, sade_sati_phase, transits, eclipses, retrograde, ashtakavarga SAV), and `retrodictive_match` (predicted_by_chart, signals_that_matched, signals_that_missed).

**Target volumes** (updated v2.2):
- v1.2 current (36 events + 5 period summaries + 6 chronic patterns)
- M4 minimum-volume gate per `MACRO_PLAN_v2_0.md §CW.LEL`: ≥ 40 events spanning ≥ 5 years
- Post-M4 expansion: continue project-lifetime; refresh cadence is session-close checkpoint (drift-alert if last entry > 14 days old)

**Owner**: native authors; Claude validates schema at session close.

**Deliverable**: `LIFE_EVENT_LOG_v1_2.md` (living; supersedes v1.1).

### D.3 — Workstream 3 — Deep Analysis Expansion with Mode B (L2)

**Objective** (unchanged from v2.1): expand current Deep Analysis v1.2.1 to v2.0 with both Modes.

**Mode A scope — new RPT sections**: See v1.0 blueprint table (unchanged); target 25+ sections with full 3-interpretation discipline.

**Mode B status** (updated v2.2): the five Mode B matrices (House, Planet, Sign, Divisional, Dasha-Period) are CLOSED at v1.0 per `FILE_REGISTRY_v1_1.md §3`. Mode B Matrix → MSR feed (§D.4) is complete.

**Deliverable**: `DEEP_ANALYSIS_v2_0.md`, targeted 14,000–16,000 lines (Mode A ~10K; Mode B ~4–6K in archival; the matrices' structured-table form may be retained as separate files rather than folded back in).

### D.4 — Workstream 4 — L2.5 Holistic Synthesis Build

**Objective** (unchanged): build and maintain the five components of the Holistic Synthesis Layer.

**Current state** (2026-04-24):
- **CGM** at `CGM_v2_0.md` CURRENT (rebuilt on FORENSIC v8.0 2026-04-19; becomes `CGM_v9_0.md` after Phase B.3.5)
- **MSR** at `MSR_v3_0.md` CURRENT (499 signals; v1.0+v2.0 merged and deduplicated)
- **CDLM** at `CDLM_v1_1.md` CURRENT (internal v1.2)
- **RM** at `RM_v2_0.md` CURRENT (internal v2.1; 32 elements)
- **UCN** at `UCN_v4_0.md` CURRENT (internal v4.1)

**Forward scope** (MP binding): CGM expansion to v9.0 is owned by `PHASE_B_PLAN_v1_0.md §B.3.5` under M2 Corpus Activation. MSR stretch toward 600 signals remains non-blocking per GOVERNANCE_STACK §3. UCN refresh triggers at major dasha transitions per `LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md §1.3`.

### D.5 — Workstream 5 — Domain Reports (L3)

**Objective** (unchanged): nine life-domain reports, each explicitly a lens into the UCN.

**Current state** (2026-04-24) — all nine at v1.1+ per `FILE_REGISTRY_v1_1.md §5`:
1. FINANCIAL (v2.1)
2. CAREER / DHARMA (v1.1)
3. HEALTH / LONGEVITY (v1.1; internal v1.2 pending filename rename)
4. RELATIONSHIPS (v1.1)
5. CHILDREN (v1.1)
6. SPIRITUAL (v1.1)
7. PARENTS (v1.1)
8. PSYCHOLOGY / MIND (v1.1)
9. TRAVEL (v1.1)

**Template constraints** (v2.0 preserved): each report cites `parent_UCN_version`, includes "Relation to the Unified Chart Narrative" section, includes "Cross-Domain Linkages" section citing CDLM.

### D.6 — Workstream 6 — Remedial Protocol Master Codex

**(LIVE SCOPE in v2.2 — replaces v2.1's back-pointer to "v1.0 §D.5 equivalent".)**

**Objective**: a unified intervention framework covering gemstone, mantra, yantra, devata, muhurta, charity, dietary, and behavioral prescriptions, derived from the full L1 + L2.5 corpus and auditable against classical sources.

**Current state** (2026-04-24): `REMEDIAL_CODEX_v2_0_PART1.md` and `REMEDIAL_CODEX_v2_0_PART2.md` are CURRENT per `FILE_REGISTRY_v1_1.md §6`. The v2.0 pair applied the Jupiter 4H→9H and Shree Lagna 9H→7H corrections to remedial prescriptions during the 2026-04-19 GAP_RESOLUTION_SESSION.

**Forward scope (Macro Plan binding)**: `MACRO_PLAN_v2_0.md` does not carry a remedial-codex macro-phase; remedial prescriptions are operational outputs of L3. However, empirical validation of remedial efficacy is bound to MP §M4 (Empirical Calibration — per-remedy outcome tracking once LEL carries remedy-application events), MP §M6 (Prospective Testing — remedial-recommendation predictions logged to PPL per §CW.PPL at emission), and MP §M8 (Classical Text Cross-Reference — remedial prescriptions cross-attributed to BPHS / Phaladeepika / Saravali / Jaimini / KP commentaries). Remedial refresh triggers at major dasha transitions (per `LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md §1.3`) and at native-initiated remedy-change events.

**Ethics binding (new in v2.2)**: remedial outputs are subject to `MACRO_PLAN_v2_0.md §3.5.A` probabilistic humility and §3.5.C self-harm guardrail. Health-domain remedial prescriptions require double red-team and explicit native sign-off per §3.5.C.

### D.7 — Workstream 7 — Temporal Engines

**(LIVE SCOPE in v2.2 — replaces v2.1's back-pointer to "v1.0 §D.6 equivalent".)**

**Objective**: lifetime timeline, rolling 36-month heatmap, annual Varshphal generator, daily-transit digest capability.

**Current state** (2026-04-24): `LIFETIME_TIMELINE_v1_0.md` and `HEATMAP_VARSHPHAL_v1_0.md` are CURRENT per `FILE_REGISTRY_v1_1.md §7`. Lifetime timeline integrates the Mode B Dasha-Period Matrix (D.3) + life-event-log (D.2). Heatmap refreshes quarterly; Varshphal annually near birthday per `LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md §1.1–§1.2`.

**Forward scope (Macro Plan binding)**: Temporal Engines are the core artifact family of `MACRO_PLAN_v2_0.md §M3` (Temporal Animation). M3 adds (a) Vimshottari + Yogini + Chara + Narayana dasha cross-checks; (b) transit engine that produces date-indexed signal lit / dormant / ripening states; (c) Varshaphala (Tajika) rectification; (d) KP sublord timing integrated with the MSR signal system; (e) shadbala computed over full dasha horizon; (f) temporal-validator meta-tests. M3 quality gate requires (a)–(f) verified plus native acharya-grade review on 5 date-specific chart readings. Upcoming major-transition refreshes per `LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md §1.3`: August 2027 Saturn AD → Ketu AD; 2028 Ketu AD → Venus AD; 2031 Mercury MD → Ketu MD (MAJOR — full UCN review); 2038 Ketu MD → Venus MD; 2041–2044 Saturn exaltation return Libra (lifetime-apex review).

**External dependencies**: Swiss Ephemeris (ED.2; version-locked per MP v2.0 §3.6.A), Jagannatha Hora exports (ED.1; freeze-at-last-compatible fallback).

### D.8 — Workstream 8 — Query & Prompt Library with Whole-Chart-Read Enforcement

**(Preserved from v2.1 — no substantive change.)**

**v2.0 addition**: every prompt template includes a mandatory whole-chart-read prelude — a structured check that forces L2.5 consultation before L3 routing. Template skeleton:

```
PROMPT TEMPLATE: [name]

STEP 1 — Whole-Chart-Read Prelude (MANDATORY):
  a) Identify primary domain(s) of query.
  b) Consult CDLM — list other domains touching this query.
  c) Pull relevant Resonance Map entries for chart elements involved.
  d) Cite Unified Chart Narrative part(s) applicable.

STEP 2 — Domain Report Consultation:
  a) Route to L3 Domain Report(s) identified in Step 1a.
  b) Extract focused analysis.

STEP 3 — Synthesis:
  a) Produce answer that integrates whole-chart (Step 1) + domain-specific (Step 2).
  b) Flag any tensions between whole-chart and domain-specific readings.
  c) Cite all sources used.
```

Current deliverable: `06_QUERY_INTERFACE/QUERY_PROMPT_LIBRARY_v1_0.md` + `SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md` + `DECISION_SUPPORT_PLAYBOOK_v1_0.md`.

### D.9 — Workstream 9 — Governance Stack

**(LIVE SCOPE in v2.2 — replaces v2.1's back-pointer to "v1.0 §D.8 equivalent".)**

**Objective**: project-wide governance — version registry, confidence ledger, known-gaps consolidation, change-control protocol, red-team cadence, maintenance scheduling, and (forthcoming per §L) mechanical enforcement of governance-surface integrity.

**Current state** (2026-04-24):
- `00_ARCHITECTURE/GOVERNANCE_STACK_v1_0.md` — version registry, confidence ledger, known-gaps register, change-control protocol, red-team cadence, session-log maintenance discipline; updated in-place through `STEP_5_MACRO_PLAN_CLOSURE` amendment log (§9 of that file)
- `00_ARCHITECTURE/FILE_REGISTRY_v1_1.md` — complete artifact inventory with CURRENT / SUPERSEDED / ARCHIVAL / CLOSED status; v1.0 superseded at Step 5
- `00_ARCHITECTURE/LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md` — long-term maintenance cadence (quarterly heatmap, annual Varshphal + LEL bump + MSR review, dasha-transition refreshes, major-life-event-triggered refreshes)
- `00_ARCHITECTURE/MAINTENANCE_SCHEDULE_v1_0.md` — scheduled-maintenance calendar
- `00_ARCHITECTURE/FALSIFIER_REGISTRY_v2_0_EXPANSION.md` and `CONTRADICTION_REGISTRY_v1_1.md` — falsifier + contradiction registers
- `00_ARCHITECTURE/AUDIT_REPORT_v1_0.md` + `V8_0_RECONCILIATION_REPORT.md` — data-integrity audit trail

**Forward scope — Governance Integrity Protocol**: per `MACRO_PLAN_v2_0.md §System Integrity Substrate` (IS.1–IS.9) and `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` §1 ND.1, the project is in the midst of a governance rebuild (Step 0 → Step 15) that will produce `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` at Step 6 and the Step 7 implementation bundle (`CANONICAL_ARTIFACTS_v1_0.md` with `mirror_obligations` column, `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`, `SESSION_OPEN_TEMPLATE`, `SESSION_CLOSE_TEMPLATE`, `DISAGREEMENT_REGISTER`). Design detail of the Governance Integrity Protocol is reserved for Step 6; v2.2 names it as a forward pointer only. The close of Step 15 produces `GOVERNANCE_BASELINE_v1_0.md` which the §L Governance Rebuild Reference will point at once it exists.

**Red-team cadence** (preserved from v2.1 §B.5): every third session a light red-team pass; major-artifact close requires a dedicated red-team pass. Under MP v2.0 §IS.8 red-team cadence is promoted to a substrate axis — required at macro-phase close, and every 12 months for the Macro Plan itself.

### D.10 — Workstream 10 — Learning Layer Substrate (NEW in v2.2)

**Objective**: a cross-cutting substrate that progressively calibrates the instrument against empirical evidence without overwriting the classical-prior corpus. Parallel to the Discovery Layer; sits (when scaffolded) under `06_LEARNING_LAYER/`.

**Summary of the ten mechanisms** (authoritative detail lives in `MACRO_PLAN_v2_0.md §Learning Layer Specification Appendix`; v2.2 summarizes only):

1. **LL.1 Signal weight calibration** — per-signal weights adjusted from MSR↔LEL match records + PPL outcomes.
2. **LL.2 Graph edge weight learning** — CGM edge weights modulated from co-activation + outcome correlation.
3. **LL.3 Embedding space adaptation** — adapter weights layered on base embeddings (Voyage-3-large).
4. **LL.4 Prompt optimization** — per-prompt outcome tracking + template version bumps.
5. **LL.5 Retrieval ranking learning** — ranker weights from acharya-grade relevance judgements.
6. **LL.6 Plan selection learning** — plan-selector weights from per-plan outcome records.
7. **LL.7 Discovery prior shaping** — two regimes: native-only mode (M4+) and cohort mode (M7+).
8. **LL.8 Bayesian model updating** — DBN posterior updates (M5+).
9. **LL.9 Counterfactual learning from misses** — miss-attribution from PPL failures (M6+).
10. **LL.10 LLM fine-tuning** — true weight fine-tuning activates M10 post-cohort corpus.

**Activation-phase matrix** (LL.N × M_N): LL.1–LL.4 scaffold at M2, active from M4; LL.5–LL.7 scaffold at M2, dormant M3, active from M4 (LL.7 cohort mode from M7); LL.8 scaffold M4, active M5; LL.9 scaffold M5, active M6; LL.10 scaffold M7, active M10. Full matrix and per-mechanism specifications (input, output, kill-switch, owner, dependencies, workstream interaction) are authoritative in `MACRO_PLAN_v2_0.md §LL-Appendix.A` through `§LL-Appendix.D`.

**Non-negotiable learning discipline** (summary; full rules in MP v2.0 §Learning Layer):
1. Classical priors are locked; learning modulates, never overwrites.
2. Bayesian posterior framing with tight priors; frequentist overfit rejected.
3. ≥ N independent observations per update (N defaults to 3; per-mechanism overrides at Step 11).
4. Held-out prospective data is sacrosanct.
5. Every learned parameter is auditable, reversible, versioned, logged.
6. The prior is the classical corpus; evidence earns the right to modulate, never automatically.

**Scaffold status** (2026-04-24): `06_LEARNING_LAYER/` directory **does not yet exist**. The scaffold decision is `STEP_11_LEARNING_LAYER_SCAFFOLD_v1_0.md`'s deliverable (pending Steps 5A → 6 → 7 → 8 → 9 → 10 → 11 in the governance rebuild). A session reading v2.2 before Step 11 closes must not assume the directory exists. Per `MACRO_PLAN_v2_0.md §Learning Layer`, scaffold-pending is the correct state; the first four LL mechanisms become *available* at M2 close and *active* at M4.

**Ownership**: native is mechanism-introduction approver; Claude is mechanism-scaffolder; Gemini is mechanism-critic per MP v2.0 §LL-Appendix.D.

**Forward pointer**: `MACRO_PLAN_v2_0.md §Learning Layer` + §LL-Appendix.A–D.

### D.11 — Workstream 11 — Multi-Agent Collaboration (NEW in v2.2)

**Objective**: a formalized Claude ↔ Gemini collaboration protocol covering the two-pass execution model (Gemini connector, Claude reconciler), the disagreement-register mechanics, the version-pinning discipline, and — per native directive **ND.1 Mirror Discipline** — the continuous semantic parity of every governance surface that has a counterpart across both agents.

**Current-agents list (MP v2.0 §3.4.A)**:
- **Claude Opus 4.7** — reconciler / primary. Produces canonical artifacts; owns versioning discipline; owns the governance-rebuild workflow.
- **Gemini 2.5 Pro** — connector / critic. Operates the L4 Discovery Layer (pattern / resonance / contradiction / cluster proposal); red-teams Claude's outputs every third session and at every macro-phase close per MP §IS.8.

**Two-pass protocol (summary)**: default for multi-output phases is two-pass (Gemini proposes → Claude reconciles). Default for deterministic computation (dasha/transit computation, corpus-integrity validators) is single-pass Claude-only. Per-phase mapping lives in each macro-phase row's `Agent roles` field in MP v2.0; v2.2 does not restate it.

**Disagreement protocol (MP v2.0 §3.4.C)**: conflicting conclusions are logged to `DISAGREEMENT_REGISTER` (Step 7 deliverable). Arbitration: (1) isolation re-run to verify each agent's stability; (2) Claude-reconciler attempts resolution with explicit rationale; (3) unresolved escalations go to native; (4) **mirror-desync is an implicit disagreement class** — requires resolution via the same protocol, not silent overwriting.

**Version-pinning discipline (MP v2.0 §3.4.F)**: model identifiers recorded at every session open. Model-family migration (Claude Opus 4.7 → Opus 5.0; Gemini 2.5 Pro → Gemini 3.0) requires the §Meta-Governance red-team + MP version bump; mid-phase migration disallowed absent native override.

**Future-agent admission (MP v2.0 §3.4.E)**: any third agent requires (a) a dedicated admission red-team, (b) an MP version bump, (c) mirror-pair update per ND.1, (d) update to the §3.4.A list, (e) a STEP_LEDGER entry.

#### D.11.1 — ND.1 Mirror Discipline: the adapted-parity principle

Per `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` §1 ND.1 (issued 2026-04-23), mirror discipline is a first-class governance principle, not an operational afterthought. Three load-bearing claims:

1. **Bidirectional obligation.** Every Claude-side governance file that has a Gemini-side counterpart is kept in continuous semantic parity with its counterpart. Any change on either side triggers a mirror update on the other side in the same session.
2. **Adapted parity, not byte-identity.** The mirror is *semantically* equivalent, not *textually* identical. Claude-side files speak in Claude's conventions (`<system-reminder>`-style phrasing, Claude Code / MCP / skill references, Claude-tool expectations). Gemini-side files speak in Gemini's conventions (Gemini-rules idiom, Gemini-tool expectations). Each mirror is adapted to its target agent's construct while preserving the meaning. **The mirror principle is semantic parity of governance content, not feature parity of agent capabilities.**
3. **Scope is not limited to CLAUDE.md.** The principle extends to every governance surface with a cross-agent reference or counterpart.

#### D.11.2 — Mirror-pair inventory (v2.2 architecture-layer declaration)

Per ND.1 Row 4 in the consumption matrix, v2.2 §D.11 names every mirror pair at summary level and flags which side is authoritative. This is the architecture-layer first pass. The authoritative machine-enforceable inventory — with `mirror_obligations` column and drift-detector bindings — is the Step 7 deliverable `CANONICAL_ARTIFACTS_v1_0.md`. Until Step 7 closes, this table is the project's canonical mirror-pair list.

| Pair | Claude-side | Gemini-side | Authoritative side | Mirror mode | Notes |
|---|---|---|---|---|---|
| MP.1 | `CLAUDE.md` | `.geminirules` | Claude-side (master instructions) | Adapted parity | Claude-side contains Claude Code / MCP / skills references with no Gemini equivalent; documented in `.geminirules` "Asymmetries" section (Step 7 formalizes) |
| MP.2 | Composite state from `SESSION_LOG.md` + `STEP_LEDGER_v1_0.md` + active phase/macro-plan pointers | `.gemini/project_state.md` | Claude-side (authoritative truth lives in SESSION_LOG + STEP_LEDGER) | Adapted parity | project_state.md must not cite superseded plans (GA.7 closure); pointers synced at every session close |
| MP.3 | `MACRO_PLAN_v2_0.md` | Gemini-side macro-plan reference (compact summary in `.geminirules` + `.gemini/project_state.md`) | Claude-side | Adapted parity | Gemini-side carries compact summary + pointer to full MP v2.0, not a full duplicate |
| MP.4 | `PHASE_B_PLAN_v1_0.md` (v1.0.2) | Gemini-side phase reference in `.gemini/project_state.md` | Claude-side | Adapted parity | Gemini-side carries the current-phase pointer; not the full B.0–B.10 plan |
| MP.5 | `FILE_REGISTRY_v1_1.md` (CURRENT) | Canonical-path block in `.geminirules` L2.5 paths | Claude-side | Adapted parity | Gemini-side carries only the L2.5 canonical paths relevant to L4 Discovery Layer work |
| MP.6 | `GOVERNANCE_STACK_v1_0.md` | (no Gemini-side counterpart currently) | Claude-only | n/a | Declared Claude-only at v2.2; revisit at Step 7 if Gemini-side governance surface emerges |
| MP.7 | `SESSION_LOG.md` | (no Gemini-side counterpart currently) | Claude-only | n/a | v2.2 decides: declared Claude-only. The session-pointer aspect of SESSION_LOG is mirrored via MP.2; a full Gemini-side SESSION_LOG has no present need. Revisit if Gemini sessions begin producing their own session records. |
| MP.8 (NEW in v2.2) | `PROJECT_ARCHITECTURE_v2_2.md` (this file) | Gemini-side architecture reference (compact layer-architecture block in `.geminirules` + `.gemini/project_state.md`) | Claude-side | Adapted parity | Gemini-side carries the five-layer summary + pointer to full v2.2; not a full duplicate. Added at Step 5A because the architecture-refresh cycle itself is a mirror-discipline event |

**Step 5A decisions recorded (per brief §3 "§E must list .geminirules and .gemini/project_state.md at project root" and per ND.1 Row 4)**:

- **MP.7 resolved as Claude-only at v2.2.** Rationale: SESSION_LOG is Claude's session-authored record; session-pointer aspect is already mirrored via MP.2 (composite state). Declaring MP.7 Claude-only avoids a forcing-a-Gemini-session-log-of-convenience anti-pattern. If a future phase produces Gemini-authored sessions at a cadence warranting their own log, this decision revisits.
- **MP.8 added** because v2.2 is itself a governance surface — a fresh Gemini session reads `.geminirules` / `.gemini/project_state.md`, learns the layer architecture, and must see a consistent summary of what PROJECT_ARCHITECTURE says. Adding MP.8 makes that obligation explicit rather than implicit.

**Asymmetries** (per ND.1 interpretation §"Asymmetries to preserve"): Claude-side files may contain Claude-specific constructs (Claude Code hooks, MCP references, skills) with no Gemini equivalent. Gemini-side files may contain Gemini-specific constructs (Gemini-rules idiom, Gemini-tool expectations) with no Claude equivalent. The mirror does not synthesize fake counterparts; asymmetries are documented explicitly. Each Gemini-side file will carry an "Asymmetries" section once Step 7 formalizes the format.

#### D.11.3 — Enforcement: forward pointer

Enforcement of this inventory is mechanical, not procedural. `mirror_enforcer.py` (Step 7 deliverable) operates over the full inventory declared in `CANONICAL_ARTIFACTS_v1_0.md` and exits non-zero on mirror-desync. The design of the enforcer is reserved for `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` at Step 6; v2.2 does not pre-specify the enforcer's internals. v2.2 §D.11 and the Step 7 CANONICAL_ARTIFACTS are the two surfaces bound by ND.1's consumption matrix; v2.2 §D.11 closes the Step 5A row of that matrix.

**Ethics binding**: Multi-Agent Collaboration inherits `MACRO_PLAN_v2_0.md §3.5.A` principles. Outputs from any agent, under any role, are subject to probabilistic humility and self-harm guardrails per §3.5.C.

---

## §E — FILE SYSTEM ARCHITECTURE (v2.2 CORRECTED TREE)

v2.2 replaces v2.1's §E entirely. The v2.1 tree named `PROJECT_ARCHITECTURE_v2_0.md`, `FORENSIC_DATA_v7_0.md`, and `LIFE_EVENT_LOG_v1_0.md` — none of which are the CURRENT paths. The v2.2 tree reflects what `ls` returns on 2026-04-24. Superseded files are collected under `§8 Archival` of `FILE_REGISTRY_v1_1.md`; v2.2 names them inline only where lineage clarity requires. The v2.2 tree is authoritative for "what is on disk today"; the per-artifact CURRENT / SUPERSEDED / ARCHIVAL status lives in `FILE_REGISTRY_v1_1.md` and the version registry lives in `GOVERNANCE_STACK_v1_0.md`. This §E does not duplicate that status information; it describes the tree shape.

```
/PROJECT_ROOT/                               (Madhav/)
│
├── .geminirules                             ← Gemini master instructions (MP.1 mirror of CLAUDE.md)
├── .gemini/
│   └── project_state.md                     ← Gemini dynamic state (MP.2 mirror of Claude composite state)
│
├── CLAUDE.md                                ← Claude master instructions (MP.1 authoritative side)
├── MARSYS_JIS_BOOTSTRAP_HANDOFF.md              ← session bootstrap document (referenced from CLAUDE.md item #1)
├── SESSION_RESUME_PROMPT.md                 ← session-resume context prompt
│
├── 00_ARCHITECTURE/
│   ├── PROJECT_ARCHITECTURE_v2_2.md         ← THIS FILE (CURRENT)
│   ├── PROJECT_ARCHITECTURE_v2_1.md         ← SUPERSEDED by v2.2 (retained for lineage)
│   ├── STEP_LEDGER_v1_0.md                  ← Step 0 → Step 15 rebuild state (LIVE)
│   ├── STEP_BRIEFS/                         ← per-step briefs (01–15 + 5A) + README index
│   │   ├── README.md
│   │   ├── STEP_01_MACRO_PLAN_CRITIQUE_v1_0.md
│   │   ├── STEP_02_MACRO_PLAN_REVISION_SPEC_v1_0.md
│   │   ├── STEP_03_MACRO_PLAN_REWRITE_v1_0.md
│   │   ├── STEP_04_MACRO_PLAN_REDTEAM_v1_0.md
│   │   ├── STEP_05_MACRO_PLAN_CLOSURE_v1_0.md
│   │   ├── STEP_5A_PROJECT_ARCHITECTURE_REFRESH_v1_0.md
│   │   ├── STEP_06_GOVERNANCE_INTEGRITY_DESIGN_v1_0.md
│   │   ├── STEP_07_GOVERNANCE_INTEGRITY_IMPLEMENTATION_v1_0.md
│   │   ├── STEP_08_GOVERNANCE_INTEGRITY_REDTEAM_v1_0.md
│   │   ├── STEP_09_CLAUDE_MD_REBUILD_v1_0.md
│   │   ├── STEP_10_SESSION_LOG_SCHEMA_v1_0.md
│   │   ├── STEP_11_LEARNING_LAYER_SCAFFOLD_v1_0.md
│   │   ├── STEP_12_ONGOING_HYGIENE_POLICIES_v1_0.md
│   │   ├── STEP_13_DRIFT_DETECTION_RUN_v1_0.md
│   │   ├── STEP_14_SCHEMA_VALIDATION_RUN_v1_0.md
│   │   └── STEP_15_GOVERNANCE_BASELINE_CLOSE_v1_0.md
│   ├── GROUNDING_AUDIT_v1_0.md              ← Step 0 baseline; GA.1–GA.32 findings (CLOSED)
│   ├── MACRO_PLAN_v2_0.md                   ← CURRENT ten-macro-phase strategic arc
│   ├── MACRO_PLAN_v1_0.md                   ← SUPERSEDED by v2.0
│   ├── MACRO_PLAN_CRITIQUE_v1_0.md          ← Step 1 deliverable (CLOSED)
│   ├── MACRO_PLAN_REVISION_SPEC_v1_0.md     ← Step 2 deliverable (CLOSED)
│   ├── MACRO_PLAN_REDTEAM_v1_0.md           ← Step 4 deliverable (CLOSED)
│   ├── NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md ← native-intent directive log (LIVING; tracks ND.1)
│   ├── CONVERSATION_NAMING_CONVENTION_v1_0.md ← Cowork thread naming (CURRENT)
│   ├── PHASE_B_PLAN_v1_0.md                 ← M2 execution plan (CURRENT at v1.0.2; paused during rebuild)
│   ├── PHASE_B_PLAN_v1_0_RECONCILER_PASS_v1_0.md ← reconciler-pass record (CLOSED)
│   ├── FILE_REGISTRY_v1_1.md                ← artifact inventory (CURRENT)
│   ├── FILE_REGISTRY_v1_0.md                ← SUPERSEDED by v1.1
│   ├── FILE_INDEX_v1_0.md                   ← predecessor of FILE_REGISTRY (SUPERSEDED)
│   ├── GOVERNANCE_STACK_v1_0.md             ← version registry + change control (CURRENT; in-place amendments)
│   ├── LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md ← quarterly/annual/transition/event maintenance
│   ├── MAINTENANCE_SCHEDULE_v1_0.md         ← scheduled-maintenance calendar
│   ├── FALSIFIER_REGISTRY_v2_0_EXPANSION.md ← current falsifier register (v1.0, v1.1 SUPERSEDED)
│   ├── FALSIFIER_REGISTRY_v1_1.md           ← SUPERSEDED
│   ├── FALSIFIER_REGISTRY_v1_0.md           ← SUPERSEDED
│   ├── CONTRADICTION_REGISTRY_v1_1.md       ← current contradiction register
│   ├── CONTRADICTION_REGISTRY_v1_0.md       ← SUPERSEDED
│   ├── AUDIT_REPORT_v1_0.md                 ← data-integrity audit trail
│   ├── DATA_INTEGRITY_AUDIT_PLAN_v1_0.md    ← audit methodology
│   ├── V8_0_RECONCILIATION_REPORT.md        ← v8.0 reconciliation record
│   ├── FIX_SESSION_001_COMPLETION.md        ← fix records
│   ├── FIX_SESSION_002_COMPLETION.md
│   ├── PROJECT_WIDE_RED_TEAM_v1_0.md        ← project-level red-team findings
│   ├── RECONCILIATION_PLAN_v1_0.md
│   ├── ACHARYA_ENGAGEMENT_KIT.md            ← external acharya review package
│   ├── EXTERNAL_ACHARYA_REVIEW_INVITATION.md
│   ├── PROJECT_COMPLETION_DOSSIER_v1_0.md
│   ├── B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE.md ← Phase B.0 kickoff prompt (WARN.5 live MP v1.0 pointer; booked for PBP v1.0.3)
│   ├── SESSION_LOG.md                       ← chronological session ledger (rolling; MP.2 authoritative source)
│   └── STEPS_PHASES_LAYERS_MAP_v1_0.html    ← visual cross-reference
│
├── 01_FACTS_LAYER/
│   ├── FORENSIC_ASTROLOGICAL_DATA_v8_0.md   ← CURRENT unified L1 (supersedes v6.0 + v7.0 supplement)
│   ├── FORENSIC_DATA_v8_0_SUPPLEMENT.md     ← v8.0 supplement (partially integrated)
│   ├── JHORA_TRANSCRIPTION_v8_0_SOURCE.md   ← JH v8.0 export transcription
│   ├── FORENSIC_ASTROLOGICAL_DATA_v6.0_ABHISEK_MOHANTY.md ← SUPERSEDED
│   ├── FORENSIC_DATA_v7_0_SUPPLEMENT.md     ← SUPERSEDED (integrated into v8.0)
│   ├── LIFE_EVENT_LOG_v1_2.md               ← CURRENT (36 events + 5 period summaries + 6 chronic patterns)
│   ├── LIFE_EVENT_LOG_v1_1.md               ← SUPERSEDED
│   ├── EVENT_CHART_STATES_v1_0.md           ← planetary positions at key life-event moments
│   ├── EXTERNAL_COMPUTATION_SPEC_v2_0.md    ← CLOSED
│   ├── EXTERNAL_COMPUTATION_SPEC_v1_0.md    ← SUPERSEDED
│   ├── CGP_AUDIT_v1_0.md                    ← CGP audit output (CLOSED)
│   ├── ECLIPSES_1900_2100.csv
│   ├── EPHEMERIS_MONTHLY_1900_2100.csv
│   ├── RETROGRADES_1900_2100.csv
│   └── SADE_SATI_CYCLES_ALL.md
│
├── 99_ARCHIVE/02_ANALYTICAL_LAYER/          ← ARCHIVED Phase 14F 2026-04-28 (was 02_ANALYTICAL_LAYER/)
│   ├── MATRIX_HOUSES.md                     ← Mode B House Matrix (ARCHIVED)
│   ├── MATRIX_PLANETS.md                    ← Mode B Planet Matrix (ARCHIVED)
│   ├── MATRIX_SIGNS.md                      ← Mode B Sign Matrix (ARCHIVED)
│   ├── MATRIX_DIVISIONALS.md                ← Mode B Divisional Matrix (ARCHIVED)
│   ├── MATRIX_DASHA_PERIODS.md              ← Mode B Dasha-Period Matrix (ARCHIVED)
│   └── DEEP_ANALYSIS_Abhisek_Mohanty_v1.md  ← Mode A curated analysis (ARCHIVED)
│
├── 025_HOLISTIC_SYNTHESIS/                  ← L2.5 layer (all five components CURRENT)
│   ├── CGM_v9_0.md                          ← CURRENT (v9.0; rebuilt on FORENSIC v8.0 2026-04-19)
│   ├── MSR_v3_0.md                          ← CURRENT (499 signals; v1.0+v2.0 merged+deduped)
│   ├── CDLM_v1_1.md                         ← CURRENT (internal v1.2)
│   ├── RM_v2_0.md                           ← CURRENT (internal v2.1; 32 elements)
│   ├── UCN_v4_0.md                          ← CURRENT (internal v4.1; mother document)
│   ├── CGM_v1_0.md                          ← SUPERSEDED
│   ├── MSR_v2_0.md                          ← SUPERSEDED (500 signals; v2.2 internal)
│   ├── MSR_v1_0.md                          ← SUPERSEDED
│   ├── CDLM_v1_0.md                         ← SUPERSEDED
│   ├── RM_v1_1.md                           ← SUPERSEDED
│   ├── RM_v1_0.md                           ← SUPERSEDED
│   ├── UCN_v3_0.md                          ← SUPERSEDED
│   ├── UCN_v2_0.md                          ← SUPERSEDED
│   ├── UCN_v1_1.md                          ← SUPERSEDED
│   ├── UCN_v1_0.md                          ← SUPERSEDED
│   ├── MASTER_SYNTHESIS_v1_0.md             ← SUPERSEDED (merged into UCN_v4_0)
│   └── RED_TEAM_L2_5_v1_0.md                ← QA artifact (CLOSED)
│
├── 03_DOMAIN_REPORTS/
│   ├── REPORT_CAREER_DHARMA_v1_1.md         ← CURRENT
│   ├── REPORT_FINANCIAL_v2_1.md             ← CURRENT
│   ├── REPORT_HEALTH_LONGEVITY_v1_1.md      ← CURRENT (internal v1.2; filename rename pending)
│   ├── REPORT_RELATIONSHIPS_v1_1.md         ← CURRENT
│   ├── REPORT_CHILDREN_v1_1.md              ← CURRENT
│   ├── REPORT_SPIRITUAL_v1_1.md             ← CURRENT
│   ├── REPORT_PARENTS_v1_1.md               ← CURRENT
│   ├── REPORT_PSYCHOLOGY_MIND_v1_1.md       ← CURRENT
│   ├── REPORT_TRAVEL_v1_1.md                ← CURRENT
│   ├── [v1.0 / v2.0 predecessors]           ← SUPERSEDED (see FILE_REGISTRY §8)
│   ├── FINANCIAL_REPORT_Abhisek_Mohanty.md  ← SUPERSEDED
│   ├── RED_TEAM_L3_v1_0.md                  ← QA artifact (CLOSED)
│   └── CROSS_REPORT_COHERENCE_AUDIT_v1_0.md ← QA artifact (CLOSED)
│
├── 04_REMEDIAL_CODEX/
│   ├── REMEDIAL_CODEX_v2_0_PART1.md         ← CURRENT
│   ├── REMEDIAL_CODEX_v2_0_PART2.md         ← CURRENT
│   ├── REMEDIAL_CODEX_v1_0_PART1.md         ← SUPERSEDED
│   └── REMEDIAL_CODEX_v1_0_PART2.md         ← SUPERSEDED
│
├── 05_TEMPORAL_ENGINES/
│   ├── LIFETIME_TIMELINE_v1_0.md            ← CURRENT
│   ├── HEATMAP_VARSHPHAL_v1_0.md            ← CURRENT
│   └── RED_TEAM_PHASE5_v1_0.md              ← QA artifact (CLOSED)
│
├── 06_QUERY_INTERFACE/
│   ├── QUERY_PROMPT_LIBRARY_v1_0.md         ← CURRENT
│   ├── SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md ← CURRENT
│   └── DECISION_SUPPORT_PLAYBOOK_v1_0.md    ← CURRENT
│
├── 06_LEARNING_LAYER/                       ← PENDING per Step 11 scaffold decision.
│                                              Do NOT assume this directory exists; it does not
│                                              on 2026-04-24. Scaffold is authorized in principle
│                                              by MACRO_PLAN_v2_0.md but actualization is gated
│                                              by STEP_11_LEARNING_LAYER_SCAFFOLD_v1_0.md.
│
├── 99_ARCHIVE/
│   └── 025_HOLISTIC_SYNTHESIS/              ← legacy archive subfolder (older superseded L2.5 material)
│
├── JHora/                                   ← L0 Jagannatha Hora exports (docx; read-only)
│
├── platform/                                ← build-out platform scaffolding (engineering-side)
│
├── docs/                                    ← documentation scratch space
│
└── [tool scripts + reports at root]
    ├── audit.py
    ├── verify_corpus.py
    ├── clean_cdlm.py, clean_msr.py, clean_rm.py, remove_reconciliation.py
    ├── corpus_verification_report_v1_0.md
    ├── corpus_verification_report_v1_0.json
    ├── data_integrity_audit_report_v1_0.md
    ├── AGENT_BRIEF_CORPUS_CLEANUP_v1_0.md
    ├── AGENT_BRIEF_CORPUS_VERIFICATION_v1_0.md
    ├── READINESS_REPORT.md
    ├── .tools/                              ← computation scripts (LEL builder, event chart states,
    │                                           Jaimini drishti, v7 additions, eclipses, ephemeris,
    │                                           retrogrades, sade sati)
    └── [screenshots, etc.]
```

**Notes:**
- `06_LEARNING_LAYER/` is listed as **PENDING per Step 11**. A session reading v2.2 before Step 11 closes must not assume the directory exists; its scaffold-or-non-scaffold decision is `STEP_11_LEARNING_LAYER_SCAFFOLD_v1_0.md`'s deliverable.
- `.geminirules` and `.gemini/project_state.md` are listed **at project root** (not under 00_ARCHITECTURE/) because that is where they live on disk and where Gemini reads them from by convention.
- Superseded versions are retained (never deleted) per §B.8 versioning discipline. The authoritative CURRENT/SUPERSEDED/ARCHIVAL/CLOSED status lives in `FILE_REGISTRY_v1_1.md`; this §E shows the tree shape only.
- `B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE.md` carries a WARN.5-tracked live `MACRO_PLAN_v1_0` pointer per STEP_LEDGER; its correction is booked for `PHASE_B_PLAN v1.0.3` per the deferral rationale recorded at STEP_5 close. This is a tracked deferral, not a drift.
- `MARSYS_JIS_BOOTSTRAP_HANDOFF.md` similarly carries WARN.4-tracked stale MP v1.0 + architecture v2.1 pointers; its refresh is booked for Step 9 (CLAUDE.md rebuild) which is the natural update vehicle for a CLAUDE.md companion document.

---

## §F — STABLE ID NAMESPACE (v2.2 EXPANDED)

v2.2 preserves every v2.1 namespace row verbatim and appends new rows for (i) the Step 0 → Step 15 governance-rebuild stable IDs, (ii) the Macro Plan v2.0 stable IDs, and (iii) the native-directive stable IDs. The v2.1 rows establish the load-bearing IDs used across L1–L4; the new rows establish the IDs used across the governance layer that v2.2 absorbs.

### F.1 — v2.1 existing rows (preserved verbatim)

| Namespace | Example | Meaning | Layer |
|---|---|---|---|
| `MET.*` | `MET.BIRTH.DATE` | Metadata | L1 |
| `PLN.*` | `PLN.MOON` | Planet | L1 |
| `HSE.*` | `HSE.7` | House | L1 |
| `SGN.*` | `SGN.CAPRICORN` | Zodiac sign | L1 |
| `NAK.*` | `NAK.PURVA_BHADRAPADA` | Nakshatra | L1 |
| `D1.*`–`D60.*` | `D9.LAGNA` | Divisional chart entries | L1 |
| `KP.*` | `KP.CUSP.7` | KP system values | L1 |
| `DSH.V.*` / `DSH.Y.*` / `DSH.C.*` | | Dasha systems | L1 |
| `SBL.*` | `SBL.SHADBALA.SATURN` | Shadbala | L1 |
| `BVB.*` | `BVB.7` | Bhavabala | L1 |
| `AVG.*` | `AVG.SAV.LIBRA` | Ashtakavarga | L1 |
| `KAK.*` | `KAK.PISCES.Z4` | Saturn Kakshya zone | L1 |
| `AVS.*` | `AVS.MOON` | Avastha state | L1 |
| `KRK.*` | `KRK.ATMA` | Chara/Sthira Karaka | L1 |
| `UPG.*` | `UPG.GULIKA` | Upagraha | L1 |
| `SAH.*` | `SAH.PUNYA` | Saham | L1 |
| `LAG.*` | `LAG.HORA` | Special Lagna | L1 |
| `ARD.*` | `ARD.AL` | Arudha | L1 |
| `DEV.*` | `DEV.ISHTA` | Deity | L1 |
| `ASP.*` | `ASP.SATURN.MOON` | Aspect | L1 |
| `TRS.*` | `TRS.SADE_SATI.C2.P3` | Transit cycle | L1 |
| `PCG.*` | `PCG.TITHI` | Panchang component | L1 |
| `EVT.*` | `EVT.2015.05.15.01` | Life event | L1 |
| `PAT.*` | `PAT.CAREER_PEAK_SIGNAL.01` | Retrodictive pattern | L1/L2 |
| `CGP.*` | `CGP.AUDIT.HOUSE_MATRIX.001` | Completeness Guarantee audit entry | L1 |
| `SIG.*` | `SIG.01` | Dominant signature (curated) | L2 Mode A |
| `CVG.*` | `CVG.03` | Convergence | L2 Mode A |
| `CTR.*` | `CTR.02` | Contradiction | L2 Mode A |
| `RPT.*` | `RPT.STR.01` | Deep Analysis section | L2 Mode A |
| `INT.*` | `INT.02` | Intervention | L2/L3 |
| `RED.*` | `RED.03` | Red-team | L2 Mode A |
| `XRF.*` | `XRF.01` | Cross-reference | L2 Mode A |
| `MX.HSE.*` | `MX.HSE.7` | House Matrix row | L2 Mode B |
| `MX.PLN.*` | `MX.PLN.SATURN` | Planet Matrix row | L2 Mode B |
| `MX.SGN.*` | `MX.SGN.LIBRA` | Sign Matrix row | L2 Mode B |
| `MX.DSH.*` | `MX.DSH.MERCURY.SATURN.2024` | Dasha-Period Matrix row | L2 Mode B |
| `MX.DVS.*` | `MX.DVS.D9` | Divisional Matrix row | L2 Mode B |
| `CGM.NODE.*` | `CGM.NODE.PLN.MERCURY` | Graph node | L2.5 |
| `CGM.EDGE.*` | `CGM.EDGE.DISP.MERCURY_JUPITER` | Graph edge | L2.5 |
| `CGM.SUB.*` | `CGM.SUB.CAREER` | Domain subgraph | L2.5 |
| `MSR.*` | `MSR.SARASWATI_YOGA.01` | Master Signal Register entry | L2.5 |
| `CDLM.*` | `CDLM.CAREER.WEALTH` | Cross-Domain Linkage cell | L2.5 |
| `RM.*` | `RM.SATURN_7H_EXALTED` | Resonance Map entry | L2.5 |
| `UCN.*` | `UCN.PART.IV.SEC.2` | Unified Chart Narrative section | L2.5 |
| `DOM.*` | `DOM.CAREER` | Domain report | L3 |
| `REM.*` | `REM.GEM.RUBY` | Remedial measure | L3 |
| `TIM.*` | `TIM.HEATMAP.2026.Q3` | Temporal engine entry | L3 |
| `PMT.*` | `PMT.DECISION.CAREER.01` | Prompt template | L4 |
| `GOV.*` | `GOV.CONFIDENCE.UCN` | Governance entry | Governance |

### F.2 — v2.2 new rows (governance layer + Macro Plan)

| Namespace | Example | Meaning | Layer / Source |
|---|---|---|---|
| `GA.*` | `GA.1` | Grounding audit finding (32 total in v1.0; `GA.N` where N = 1..32) | `GROUNDING_AUDIT_v1_0.md` |
| `MPC.N.M` | `MPC.14.2` | Macro Plan critique finding (14 dimensions × per-dimension index) | `MACRO_PLAN_CRITIQUE_v1_0.md` |
| `MPC.OS.*` | `MPC.OS.1` | Macro Plan critique out-of-schema finding | `MACRO_PLAN_CRITIQUE_v1_0.md` §16 |
| `STEP.*` | `STEP.5A` | Governance rebuild step ID (Step 0..15 + Step 5A) | `STEP_LEDGER_v1_0.md` |
| `ND.*` | `ND.1` | Native directive (Mirror Discipline is ND.1) | `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` |
| `M1..M10` | `M2` | Macro Plan macro-phase IDs | `MACRO_PLAN_v2_0.md §The ten macro-phases` |
| `LL.*` | `LL.1` | Learning Layer mechanism | `MACRO_PLAN_v2_0.md §LL-Appendix.B` |
| `IS.*` | `IS.2` | System Integrity Substrate axis (IS.1–IS.9) | `MACRO_PLAN_v2_0.md §System Integrity Substrate` |
| `ED.*` | `ED.2` | External dependency (ED.1–ED.9) | `MACRO_PLAN_v2_0.md §3.6.A` |
| `CW.*` | `CW.LEL`, `CW.PPL` | Cross-cutting workstream ID | `MACRO_PLAN_v2_0.md §Cross-cutting workstreams` |
| `MP.*` | `MP.1` | Mirror pair (MP.1–MP.8 as of v2.2 §D.11.2; authoritative list lives in Step 7 CANONICAL_ARTIFACTS) | `PROJECT_ARCHITECTURE_v2_2.md §D.11.2` + `MACRO_PLAN_v2_0.md §Multi-Agent Collaboration` |
| `R.*` | `R.1` | Risk-register entry (per-phase `Risks` field) | `MACRO_PLAN_v2_0.md` per-phase rows |
| `T.*` | `T.2` | Adversarial test ID in Macro Plan red-team | `MACRO_PLAN_REDTEAM_v1_0.md` |
| `FIX.*` / `WARN.*` | `WARN.2` | Step 5 propagation deferral flag | `STEP_LEDGER_v1_0.md` Step 5 row + SESSION_LOG |
| `DIS.*` | (reserved) | Disagreement-register entry | Step 7 deliverable `DISAGREEMENT_REGISTER` — reserved namespace |

Note on `EVT.*` and `LEL.*`: per Step 5A brief §3, v2.2 confirms `EVT.*` suffices for life-event IDs in the Life Event Log. The Macro Plan does not introduce a separate `LEL.*` namespace; the LEL schema uses `EVT.*` per `LIFE_EVENT_LOG_v1_2.md` frontmatter. No new `LEL.*` row is needed.

---

## §G — DETAILED WORKSTREAM SPECIFICATIONS

**§G is preserved from v2.1 with version-pointer corrections only.** Detailed sub-specifications (G.1 CGP, G.2 LEL, G.3 Deep Analysis Mode A + Mode B, G.4 L2.5 Holistic Synthesis build, G.5–G.9 remaining workstreams) are unchanged in structure from v2.1 §G. Where v2.1 §G named version pointers that have since advanced (e.g., "v6.0 current" → "v8.0 current"; "MSR 500-600 target" → "MSR v3.0 at 499 signals (floor met; stretch non-blocking)"; "LEL v1.0" → "LEL v1.2"), the pointer is corrected; the spec structure is unchanged. A reader needing the full G subsection text should consult v2.1 §G.1–§G.9 with the following pointer-corrections applied:

- G.1 header "Facts Layer v7.0" → "Facts Layer v8.0" (unified from v6.0 + v7.0 supplement)
- G.1.CGP targets: still 7 categories, completeness ratio ≥ 95% at signoff — achieved; `CGP_AUDIT_v1_0.md` CLOSED
- G.2 "v1.0" targets (25-40, 75-100, 150+) remain valid as volume targets; "v1.0 current" → "v1.2 current (36 events + 5 period summaries + 6 chronic patterns)"
- G.3 Mode A "expand v1.2.1 to v2.0" unchanged; Mode B "new in v2.0" → "CLOSED at v1.0 per FILE_REGISTRY_v1_1.md §3"
- G.4 "MSR target 500-600" → "MSR v3.0 at 499 signals (floor met; stretch toward 600 non-blocking per GOVERNANCE_STACK §3)"; "UCN 30-50K words" preserved; all five sub-workstreams now CURRENT at the versions named in §D.4
- G.5–G.9 "unchanged from v1.0" → see §D.5 / §D.6 / §D.7 / §D.8 / §D.9 live scope in v2.2

No structural edits to §G subsection narratives. Pointer corrections are permitted under the Step 5A brief's D.1–D.5 latitude.

---

## §H — QUALITY STANDARDS (v2.0 EXPANDED)

**§H is preserved verbatim from v2.1; no edits in v2.2.**

### H.1 — Acharya-Grade Standards Checklist

Every artifact produced must pass this checklist:
- [ ] Every claim traces to source facts (derivation ledger present)
- [ ] Every significant interpretation enumerates 3 alternatives, weighs, selects, publishes falsifier
- [ ] Classical sources named where appropriate
- [ ] Multiple astrological systems integrated
- [ ] Contradictions named, not hidden
- [ ] Confidence declared honestly per claim
- [ ] Red-team pass completed
- [ ] Version metadata complete
- [ ] LLM-parseable and human-readable
- [ ] No fabricated numerics
- [ ] **L3/L4 outputs cite L2.5 UCN as parent** (NEW v2.0)
- [ ] **L2 Mode B completeness verified via CGP** (NEW v2.0)
- [ ] **Whole-chart-read discipline observed on query answers** (NEW v2.0)

### H.2 — What "Hyper-Master Acharya" Means Operationally

(Unchanged.)

### H.3 — What We Specifically Avoid

(Unchanged — with v2.0 addition:)
- Answering queries through Domain Reports without L2.5 consultation
- Treating L1 gaps as "probably X" rather than named gaps

### H.4 — Whole-Chart-Read Protocol (NEW v2.0)

Every **interpretive** query answer must follow this protocol. Pinpointed factual lookups follow the B.11 proportionality carve-out (RS-4, 2026-07-19) instead: frame check + escalation valve, skipping Phases 2–3.

**Phase 1 — Query Intake**
1. What is the primary domain of the query?
2. What is the explicit question?
3. Is this a timing, structural, or remedial question?

**Phase 2 — Whole-Chart Contextualization** (MANDATORY)
4. Consult CDLM: which other domains touch this query?
5. Consult RM: which chart elements resonate with the primary subject?
6. Consult UCN: which Part(s) of the Unified Narrative cover this?

**Phase 3 — Focused Depth**
7. Consult relevant L3 Domain Report for focused analysis.
8. Consult relevant L2 Mode A RPT sections for forensic depth.
9. Consult L2 Mode B matrices for completeness cross-check.

**Phase 4 — Synthesis**
10. Produce answer that integrates Phase 2 (whole-chart) + Phase 3 (focused).
11. Flag any tensions between whole-chart and focused readings.
12. Cite all sources used.
13. Declare confidence.

---

## §I — EXECUTION SEQUENCE (v2.2 POINTER-ONLY — REPLACES v2.1's 6-PHASE ARC)

v2.2 replaces v2.1's 6-phase 38-42-session schedule entirely. The v2.1 enumeration of Phase 1 Foundation / Phase 2A Holistic Foundation / Phase 2B Unified Narrative / Phase 3 Deep Analysis / Phase 4 Domain Reports / Phase 5 Remedial + Temporal / Phase 6 Query Interface + Governance / Phase 7 Living Project is **superseded** and should not be cited. Several of those phases' deliverables are already CURRENT (L2.5 stack closed; nine L3 Domain Reports at v1.1+; Remedial Codex at v2.0; Lifetime Timeline and Varshphal Heatmap at v1.0; Query Prompt Library at v1.0; Governance Stack CURRENT). The others have been absorbed into macro-phase M_N rows in the current Macro Plan.

**Execution cadence is now governed by:**

1. **`MACRO_PLAN_v2_0.md`** — the ten-macro-phase arc M1–M10 (Corpus Completeness → Corpus Activation → Temporal Animation → Empirical Calibration → Probabilistic Model → Prospective Testing → Population Extension → Classical Text Cross-Reference → Multi-School Triangulation → LLM-Acharya Interface + Publication), plus the two cross-cutting substrates (Learning Layer LL.1–LL.10 and System Integrity Substrate IS.1–IS.9), plus the two cross-cutting workstreams (CW.LEL Life Event Log; CW.PPL Prospective Prediction Log), plus the Ethical Framework (§3.5.A–H), the External Dependency Graph (ED.1–ED.9), the Multi-Agent Collaboration protocol (§3.4.A–F), and the Meta-Governance revision/retirement rules (§3.10.A–G).
2. **`PHASE_B_PLAN_v1_0.md`** (currently v1.0.2) — the live M2 Corpus Activation execution plan (B.0–B.10), governing the two-pass Gemini connector + Claude reconciler workflow, the P1–P9 validator cascade, and the T.1–T.7 adversarial test battery.
3. **`STEP_LEDGER_v1_0.md`** — while the Step 0 → Step 15 governance rebuild remains open, the STEP_LEDGER is the authoritative "you are here" marker. A fresh session reads CLAUDE.md → STEP_LEDGER → the current step's brief → the governance surfaces named in that brief, and executes exactly one step per conversation. Macro-phase execution (M_N) resumes only after Step 15 closes with `GOVERNANCE_BASELINE_v1_0.md`. Per `MACRO_PLAN_v2_0.md §Scope Boundary`, session scope discipline is mechanical (session-open handshake + drift detector), not procedural.

**Current execution position** (2026-04-24): **governance rebuild — Step 5A (Project Architecture refresh v2.1 → v2.2) in progress.** Next step: Step 6 (Governance & Integrity Protocol design). Active macro-phase: M2 Corpus Activation (paused pending rebuild closure). See STEP_LEDGER for the authoritative live state.

**What v2.2 §I deliberately does not do:**
- Does not re-enumerate the ten macro-phases. The authoritative source is `MACRO_PLAN_v2_0.md §The ten macro-phases`; duplication is itself a drift vector per MP §IS.1 (canonical-artifact discipline).
- Does not declare target dates. Per MP §3.8.A, execution is phase-indexed, not time-indexed.
- Does not declare session-volume commitments. Per MP §3.8.B, volume envelopes are rough ranges, not commitments.

Readers of v2.1 looking for "the execution sequence" must re-orient: the sequence now lives in `MACRO_PLAN_v2_0.md` + `PHASE_B_PLAN_v1_0.md` + `STEP_LEDGER_v1_0.md`. v2.2 §I's job is to route them there and name the superseded arc explicitly so no future session cites the 6-phase arc as current.

---

## §J — KEY DECISIONS (RESOLVED 2026-04-17 — v2.1 UPDATE)

**§J is preserved verbatim from v2.1; no edits in v2.2.** All five decisions remain resolved.

### J.1 — Session cadence — RESOLVED: DAILY across all phases

**Decision**: Daily session cadence across all six execution phases.

**Context**: Native chose daily cadence after explicit pushback from Claude that phase-variable would better serve the project's more emotionally-intensive phases (Phase 2 — Life Event Log tagging and Unified Chart Narrative build). Native accepted the tradeoffs explicitly.

**Implications and compensating discipline**:
- **Estimated calendar completion**: ~6-7 weeks to Phase 6 (versus 3-4 months under phase-variable, ~10 months under weekly).
- **Compensating discipline 1 — enhanced version hygiene**: every session produces a closed, versioned artifact before moving to the next session's work. No cross-session half-built artifacts.
- **Compensating discipline 2 — enhanced red-team cadence**: every third session runs a light red-team pass across artifacts produced in the prior two sessions, catching contradiction-drift early.
- **Compensating discipline 3 — reflection flag protocol**: if Claude detects material in a session that warrants settling-time (major life-event-log revelations, unexpected pattern discoveries in retrodictive work, emotionally significant findings), Claude names this explicitly and suggests a 48-72 hour pause before the next session, leaving decision to native.
- **Compensating discipline 4 — context-window management**: Claude proactively summarizes and archives completed work between sessions to prevent context-drift across daily sessions.

**Native's stated rationale**: rapid momentum preferred; native accepts reduced between-session reflection time as tradeoff.

### J.2 — External software procurement — RESOLVED: JAGANNATHA HORA

**Decision**: Jagannatha Hora (free, open-source, from VedicAstrologer.org).

**Implications**:
- Highest-quality Jyotish software available; widely used by professional acharyas.
- Native will procure and install. Claude will produce `EXTERNAL_COMPUTATION_SPEC.md` in Session 3 specifying exact computations required.
- Native will export specific tables/calculations from Jagannatha Hora and share with Claude for incorporation into Facts Layer v7.0.

### J.3 — Privacy boundaries — RESOLVED: NONE

**Decision**: No privacy boundaries on Life Event Log content.

**Implications**:
- Full elicitation scope: health (physical and mental), relationships, family, finances, failures, losses, addictions or compulsions if present, inner crises, spiritual experiences however unusual, shame/pride episodes, conflicts, relational rupture events, unresolved issues.
- Native retains the right to redact any specific event after logging if desired, but the elicitation posture is "everything relevant."
- This maximizes retrodictive corpus quality because the chart responds to all lived reality; excluded categories would create blind spots.

### J.4 — Audience ceiling — RESOLVED: NONE

**Decision**: No restrictions on eventual audience.

**Implications**:
- All artifacts built to publication-grade standard.
- Eventual external-acharya review acceptable.
- Potential descendant/family use acceptable.
- All tone decisions default to "serious, documented, traceable" (versus informal-personal).

### J.5 — Goal recalibration approach — RESOLVED: CHART-FIRST REVEAL

**Decision**: Chart-first reveal across all domains; goal-calibration on-demand post-reveal.

**Implications**:
- Each Domain Report's main body presents chart signals neutrally (no goal-filter imposed).
- Each Domain Report includes an "Invitation to Goal-Formation" closing section that prompts native to articulate goals *in response* to what the chart revealed.
- Valence-neutral framing discipline installed: chart signals are described without built-in value judgments (e.g., "Saturn-Mars 7H conjunction = authority-through-tension pattern" rather than "Saturn is well-placed but Mars creates conflict").
- Native may return at any time with a specific goal-calibration query ("now that I've read Relationships Report, calibrate chart against this specific stated goal") — Claude will treat these as on-demand decision-support sessions.
- Financial Report's existing §6.5 Goal Calibration remains as-is (it was appropriate in its context); refresh to v2.0 preserves that section.

---

## §K — BLUEPRINT META (v2.3)

```yaml
blueprint_id: PROJECT_ARCHITECTURE_v2_3
status: APPROVED BLUEPRINT — Multi-Ayanamsha Build arc amendment absorbed
supersedes: PROJECT_ARCHITECTURE_v2_2 (2026-04-24) and v2_1 (2026-04-17) and v2_0 (2026-04-17 mid) and v1_0 (archived)
total_sections: 12 major (§A–§L); §L is new in v2.2
total_layers: 5 (L1, L2, L2.5, L3, L4) — pyramid preserved from v2.0
cross_cutting_substrates: 2 (Learning Layer per §D.10 and MP v2.0 §Learning Layer; System Integrity Substrate per §L and MP v2.0 §System Integrity Substrate)
cross_cutting_workstreams: 2 (CW.LEL, CW.PPL per MP v2.0 §Cross-cutting workstreams)
total_workstreams_defined: 11 (D.1–D.9 preserved; D.10 + D.11 new in v2.2)
total_domain_reports_planned: 9 (all CURRENT at v1.1+)
execution_authority: MACRO_PLAN_v2_0.md (ten macro-phases M1–M10) + PHASE_B_PLAN_v1_0.md v1.0.2 (current M2 plan) + STEP_LEDGER_v1_0.md (current rebuild step)
session_cadence: DAILY (across all phases; compensating discipline enforced per §J.1)
living_document: YES

v22_additions:
  §A.4.addendum: "post-v2.1 drift rationale"
  §D.6: "live scope — Remedial Codex v2.0 + MP §M4/§M6/§M8 empirical/classical binding"
  §D.7: "live scope — Temporal Engines + MP §M3 Temporal Animation"
  §D.9: "live scope — Governance Stack + forward pointer to Step 6 Governance Integrity Protocol"
  §D.10: "Learning Layer substrate workstream — LL.1–LL.10 summary + MP LL-Appendix pointer"
  §D.11: "Multi-Agent Collaboration workstream — two-pass, ND.1 mirror discipline, MP.1–MP.8 inventory"
  §E: "entirely replaced with CURRENT file tree (v8.0 forensic, v1.2 LEL, v3.0 MSR, v4.0 UCN, v1.1 CDLM, v2.0 RM, v2.0 CGM; .geminirules and .gemini/project_state.md at root; STEP_BRIEFS + STEP_LEDGER + governance-rebuild family named; 06_LEARNING_LAYER/ PENDING)"
  §F.2: "new namespaces — GA, MPC, STEP, ND, M1..M10, LL, IS, ED, CW, MP, R, T, FIX/WARN, DIS"
  §I: "replaced with pointer to MP v2.0 + PHASE_B_PLAN v1.0.2 + STEP_LEDGER"
  §L: "Governance Rebuild Reference — the single bridge between architecture and governance-layer artifacts"

v22_preservation:
  §B: "12 architectural principles preserved verbatim"
  §C: "five-layer pyramid preserved verbatim; only v1.0-era version-labels in the ASCII box updated to v8.0 / v1.2+ per Step 5A D.1–D.5 latitude"
  §F.1: "every v2.1 namespace row preserved verbatim"
  §G: "structure preserved; pointer corrections only (v6.0 → v8.0; 500-600 target → 499 at v3.0; LEL v1.0 → v1.2)"
  §H: "quality standards preserved verbatim"
  §J: "all five §J decisions preserved verbatim"

resolved_decisions (from v2.1):
  J1_cadence: daily across all phases (with compensating discipline)
  J2_external_software: Jagannatha Hora (free, open source)
  J3_privacy_boundaries: none
  J4_audience_ceiling: none (publication-grade standard)
  J5_goal_recalibration: chart-first reveal; on-demand goal-calibration post-reveal

v22_finding_coverage:
  GA.1 (MSR version drift): addressed in §D.4 + §E (MSR_v3_0 at 499); authoritative closure is Step 5 FILE_REGISTRY v1.1 + Step 7 CANONICAL_ARTIFACTS
  GA.4 (CGM not rebuilt): addressed in §D.4 + §E (CGM_v2_0 CURRENT; rebuilt on FORENSIC v8.0 2026-04-19)
  GA.5 (L3 reports stale): addressed in §D.5 + §E (all nine at v1.1+)
  GA.6 (06_LEARNING_LAYER phantom): addressed in §D.10 + §E (PENDING per Step 11)
  GA.7 (twinkly-puzzling-quokka in project_state.md): resolved at Step 5; referenced in §L for context
  GA.8 (MARSYS_JIS_BOOTSTRAP_HANDOFF unverified): acknowledged in §E; WARN.4 tracked deferral to Step 9
  GA.9 (LEL unreferenced): addressed in §D.2 (LEL promoted to cross-cutting per MP §CW.LEL)
  GA.10 (GOVERNANCE_STACK unreferenced): addressed in §D.9 + §E
  GA.11 (other architectural artifacts unreferenced): addressed in §E (full 00_ARCHITECTURE tree listed)
  GA.12 (LEL v1_1 in facts folder): hygiene; deferred to file-hygiene pass (Step 12)
  GA.22–GA.32 (Macro Plan critique feeders): absorbed via MP v2.0; §D.10 and §D.11 bring the substrate and multi-agent coverage into the architecture layer
  ND.1 (Mirror Discipline): §D.11.1 (three load-bearing claims stated) + §D.11.2 (MP.1–MP.8 inventory) + §D.11.3 (forward pointer to Step 7 enforcer)

v22_deliberate_deferrals:
  - "Scope: Step 6 Governance Integrity Protocol. v2.2 names it as a forward pointer in §D.9 and §L only."
  - "Scope: Step 11 Learning Layer scaffold decision. v2.2 declares 06_LEARNING_LAYER/ PENDING in §D.10 and §E."
  - "Scope: Step 7 CANONICAL_ARTIFACTS machine-enforceable mirror inventory. v2.2 carries the architecture-layer first pass in §D.11.2; the authoritative machine-readable list lives at Step 7."
  - "Scope: WARN.2 (PHASE_B_PLAN live MP v1.0 pointers) → tracked to PHASE_B_PLAN v1.0.3 cycle."
  - "Scope: WARN.4 (MARSYS_JIS_BOOTSTRAP_HANDOFF stale pointers) → tracked to Step 9 CLAUDE.md rebuild cycle."
  - "Scope: WARN.5 (B0_KICKOFF_PROMPT_FOR_CLAUDE_CODE stale MP v1.0 pointer) → tracked to PHASE_B_PLAN v1.0.3 cycle."

protection_clauses (preserved from v2.1):
  - No fabricated chart computations
  - No overstated predictions
  - No generic astrology (always chart-specific)
  - No collapse of B.1 facts/derivation/interpretation separation
  - No abandonment of red-team discipline
  - No project drift without explicit version bump
  - No domain-siloed query answers (B.11)
  - No interpretation against incomplete L1 cells (B.12)

protection_clauses_v22_additions:
  - No pre-building infrastructure for later macro-phases (per MP §Scope Boundary)
  - No skipping the session-open handshake or session-close checklist once Step 7 lands them
  - No silent mirror overwriting (mirror-desync is a disagreement class per MP §3.4.C)
  - No bypassing the drift-detector or schema-validator once Step 7 lands them
  - No short-circuiting the classical-priors-locked rule in the Learning Layer
  - No date-of-death output, no suicide-adjacent output; health-crisis + mental-health output double red-teamed (per MP §3.5.C)

v22_inline_redteam_self_check:
  - "grep MACRO_PLAN_v1_0 across repo — every hit is either in the v1.0 file itself, in STEP_BRIEFS, in SESSION_LOG, in critique/spec/red-team artifacts, or in a WARN-tracked deferred surface. No new live pointer introduced by v2.2. Verified by task #4."
  - "grep PROJECT_ARCHITECTURE_v2_1 across repo — every hit is either in v2_1 itself, in STEP_BRIEFS / SESSION_LOG / GROUNDING_AUDIT, or in one of the five mirror-propagation surfaces (CLAUDE.md, .geminirules, project_state.md, FILE_REGISTRY, GOVERNANCE_STACK) that Step 5A propagation updates to v2.2. Verified by task #4."
  - "CLAUDE.md, .geminirules, project_state.md, FILE_REGISTRY, GOVERNANCE_STACK all name PROJECT_ARCHITECTURE_v2_2.md — eyeball-confirmed by task #4 after propagation."
  - "every GA.N finding named in the architecture-surface column of GROUNDING_AUDIT §§1–8 is addressed in v2.2 or explicitly deferred with rationale in v22_deliberate_deferrals. No silent drop."
  - "v2.2 does not pre-specify anything reserved for Step 6: §D.9, §D.11.3, §L all carry forward-pointers only."
  - "Learning Layer (§D.10) vs Governance Integrity (§D.9 + §L forward pointer) distinction crisp: LL modulates classical priors with empirical evidence; Integrity locks the project's claims about its own state. No conflation."
  - "§I defers execution-sequence to MP v2.0 + PHASE_B_PLAN v1.0.2 + STEP_LEDGER without duplicating them. A reader looking for 'the execution sequence' lands on MP v2.0, not §I."

changelog:
  v1.0 (2026-04-17 early): initial blueprint approved by native
  v2.0 (2026-04-17 mid): inserted L2.5 Holistic Synthesis; added CGP at L1; added Mode B at L2;
                         revised query routing; enforced whole-chart-read discipline; scope expanded
                         to 42 sessions; MSR target 500-600; UCN timing early
  v2.1 (2026-04-17 late): all §J decisions resolved; daily cadence locked with compensating discipline;
                          Jagannatha Hora procurement confirmed; no privacy/audience boundaries;
                          chart-first reveal approach for Domain Reports; ready for Session 2
  v2.2 (2026-04-24, Step 5A of the Step 0→15 governance rebuild):
    Minor-version refresh absorbing (a) MACRO_PLAN_v2_0.md's ten-macro-phase arc (M1–M10);
    (b) the Learning Layer substrate (LL.1–LL.10) via new §D.10;
    (c) the Claude ↔ Gemini Multi-Agent Collaboration workstream + ND.1 Mirror Discipline via
    new §D.11 with MP.1–MP.8 mirror-pair inventory;
    (d) corrected §E file-system tree (v8.0 forensic, v1.2 LEL, v3.0 MSR at 499 signals, v4.0 UCN,
    v1.1 CDLM, v2.0 RM, v2.0 CGM; .geminirules and .gemini/project_state.md at root; full
    00_ARCHITECTURE governance-rebuild family listed);
    (e) live scope for §D.6 (Remedial Codex + M4/M6/M8 binding), §D.7 (Temporal Engines + M3),
    §D.9 (Governance Stack + Step 6 forward pointer);
    (f) §F.2 new namespaces (GA, MPC, STEP, ND, M1..M10, LL, IS, ED, CW, MP, R, T, FIX/WARN, DIS);
    (g) §I replaced with pointer to MP v2.0 + PHASE_B_PLAN v1.0.2 + STEP_LEDGER; prior 6-phase
    38-42-session arc explicitly superseded;
    (h) §A.4 addendum naming post-v2.1 drift;
    (i) new §L Governance Rebuild Reference.
    Preserved verbatim: §B (12 principles); §C (five-layer pyramid); §F.1 (every v2.1 namespace row);
    §H (quality standards); §J (five resolved decisions).
    Produced during Step 5A of the Step 0→15 governance rebuild.
    Red-team: inline self-check per brief §8 documented in v22_inline_redteam_self_check block above
    (separate Step 5B red-team not required for this minor bump).
    ND.1 (Mirror Discipline): addressed at architecture layer via §D.11.1 + §D.11.2 mirror-pair
    inventory + §D.11.3 forward pointer to Step 7 enforcer; ND.1 global status remains `open` until
    Step 7 closes (per ND.1 consumption matrix; Step 5A closes its row, not the whole directive).
```

---

## §L — GOVERNANCE REBUILD REFERENCE (NEW IN v2.2)

§L is the single bridge between this architecture blueprint and the governance-layer artifacts produced by the Step 0 → Step 15 governance rebuild.

### L.1 — Why §L exists

v2.1 had no pointer into the governance layer because, on v2.1's closure date (2026-04-17), the governance layer was coextensive with the Governance Stack (§D.9) and the red-team cadence rule (§B.5). Between v2.1 and v2.2, the project observed multi-session drift during M2 execution (documented in `GROUNDING_AUDIT_v1_0.md` — 32 findings across version drift, staleness, phantom references, unreferenced artifacts, sync gaps, schema gaps, and scope-creep) and responded with a dedicated Step 0 → Step 15 rebuild that produces the **Governance Integrity Protocol** at Step 6, the **Integrity implementation bundle** at Step 7, and the final closure artifact `GOVERNANCE_BASELINE_v1_0.md` at Step 15. §L names the artifacts at each layer so a fresh session reading v2.2 knows where the governance-layer material lives, which of it is CURRENT, and which is forthcoming.

### L.2 — Canonical governance-layer artifacts

| Artifact | Role | Status | Relationship to v2.2 |
|---|---|---|---|
| `MACRO_PLAN_v2_0.md` | Ten-macro-phase strategic arc (M1–M10); Learning Layer; System Integrity Substrate; Ethical Framework; External Dependency Graph; Multi-Agent Collaboration protocol; Meta-Governance; Post-M10 Framing | CURRENT | v2.2 §I defers execution-sequence to this file; v2.2 §D.10 summarizes Learning Layer; v2.2 §D.11 summarizes Multi-Agent Collaboration + ND.1 |
| `PHASE_B_PLAN_v1_0.md` | M2 Corpus Activation execution plan (B.0–B.10); Discovery Engine; validator cascade; adversarial tests | CURRENT at v1.0.2 (paused during rebuild) | v2.2 §I names this as the current phase-plan authority |
| `STEP_LEDGER_v1_0.md` | Single source of truth for Step 0 → Step 15 rebuild status | LIVE | v2.2 §I names this as the current "you are here" marker for the rebuild era |
| `STEP_BRIEFS/STEP_NN_*.md` | Per-step execution briefs (16 briefs: 01..15 + 5A) | LIVE | A session executing Step N reads the corresponding brief; v2.2 itself is the Step 5A deliverable |
| `GROUNDING_AUDIT_v1_0.md` | Baseline audit (32 findings) from Step 0 | CLOSED | v2.2 addresses every GA.N finding in the architecture-surface column; see §K v22_finding_coverage |
| `MACRO_PLAN_CRITIQUE_v1_0.md` | Step 1 14-dimension critique of MP v1.0 (132 in-schema + 4 out-of-schema findings) | CLOSED | v2.2 absorbs the MP v2.0 revisions those findings drove |
| `MACRO_PLAN_REVISION_SPEC_v1_0.md` | Step 2 revision spec (137 findings mapped) | CLOSED | v2.2 §D.11.2 mirror-pair inventory traces to spec §5.2 |
| `MACRO_PLAN_REDTEAM_v1_0.md` | Step 4 red-team verdict PASS_WITH_FIXES | CLOSED | Confirmed MP v2.0 ready for Step 5 closure; enabled Step 5A |
| `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` | Native-intent directive log (currently tracks ND.1 Mirror Discipline) | LIVING | v2.2 §D.11 closes the Step 5A row of ND.1's consumption matrix |
| `CONVERSATION_NAMING_CONVENTION_v1_0.md` | Cowork thread naming (`Madhav NN — <Step title>`) | CURRENT | Operational; not directly referenced by v2.2 narrative |
| `FILE_REGISTRY_v1_1.md` | Complete artifact inventory | CURRENT | v2.2 §E defers per-artifact status to this file |
| `GOVERNANCE_STACK_v1_0.md` | Version registry, confidence ledger, known-gaps register, change-control, red-team cadence | CURRENT (in-place amendments through STEP_5) | v2.2 §D.9 names this as the existing governance-stack core |
| `LIVING_PROJECT_MAINTENANCE_GUIDE_v1_0.md` | Long-term maintenance cadence | CLOSED | v2.2 §D.6 / §D.7 / §D.9 cite this for maintenance cadence |
| `GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md` | Step 6 deliverable — design of the mechanical governance-integrity protocol | FORTHCOMING | v2.2 §D.9 / §D.11.3 point forward to this |
| Step 7 implementation bundle | `CANONICAL_ARTIFACTS_v1_0.md` (with `mirror_obligations` column), `drift_detector.py`, `schema_validator.py`, `mirror_enforcer.py`, `SESSION_OPEN_TEMPLATE`, `SESSION_CLOSE_TEMPLATE`, `DISAGREEMENT_REGISTER`, updated `.geminirules` + `project_state.md` + FILE_REGISTRY + GOVERNANCE_STACK, `DRIFT_REPORT_STEP_7`, `SCHEMA_VALIDATION_REPORT_STEP_7` | FORTHCOMING | v2.2 §D.11.3 defers the full machine-enforceable mirror inventory to this bundle's CANONICAL_ARTIFACTS |
| `GOVERNANCE_INTEGRITY_REDTEAM_v1_0.md` | Step 8 red-team of the Step 7 implementation | FORTHCOMING | — |
| `SESSION_LOG_SCHEMA_v1_0.md` + `CURRENT_STATE_v1_0.md` | Step 10 session-log schema + "you are here" state file | FORTHCOMING | — |
| `LEARNING_LAYER_SCAFFOLD_DECISION_v1_0.md` + `06_LEARNING_LAYER/` bundle | Step 11 scaffold-or-non-scaffold decision | FORTHCOMING | v2.2 §D.10 / §E declare 06_LEARNING_LAYER/ PENDING; Step 11 resolves |
| `ONGOING_HYGIENE_POLICIES_v1_0.md` | Step 12 hygiene policies | FORTHCOMING | — |
| `DRIFT_REPORT_STEP_13_v1_0.md` | Step 13 baseline drift-detector run | FORTHCOMING | — |
| `SCHEMA_VALIDATION_REPORT_STEP_14_v1_0.md` | Step 14 baseline schema-validator run | FORTHCOMING | — |
| `GOVERNANCE_BASELINE_v1_0.md` | Step 15 final closure artifact; rebuild → steady-state transition seal | FORTHCOMING | After Step 15 closes, v2.2 §L is amended to point to this file as the single governance-layer entry point and the STEP_LEDGER's LIVE status flips to CLOSED-STEADY-STATE |

### L.3 — How a fresh session orients itself

A fresh session reading v2.2 during the rebuild era (pre-Step 15) opens files in this order:

1. `CLAUDE.md` — canonical session-open orientation; names the mandatory reading list and the rebuild banner.
2. `00_ARCHITECTURE/STEP_LEDGER_v1_0.md` — find the current step and its status.
3. `00_ARCHITECTURE/STEP_BRIEFS/STEP_NN_*.md` for the current step — the execution brief.
4. `PROJECT_ARCHITECTURE_v2_2.md` (this file) — the governing blueprint for what is built and why.
5. `MACRO_PLAN_v2_0.md` — strategic arc for where in the project we are.
6. `PHASE_B_PLAN_v1_0.md` v1.0.2 — if the current macro-phase is M2.
7. `GROUNDING_AUDIT_v1_0.md` — baseline as of 2026-04-23, for historical reference.
8. `NATIVE_DIRECTIVES_FOR_REVISION_v1_0.md` — if the current step is bound by a native directive (currently ND.1 binds Steps 2, 3, 4, 5A, 6, 7).

Post-Step-15 (steady-state), this list shortens: `CLAUDE.md` → `PROJECT_ARCHITECTURE_v2_2.md` (or its successor) → `MACRO_PLAN_v2_0.md` → `GOVERNANCE_BASELINE_v1_0.md` for the governance-layer entry point → phase-plan for the current macro-phase. The STEP_LEDGER is retired (or kept for lineage) and the rebuild banner is replaced with a steady-state pointer.

### L.4 — v2.2 amendment trigger

v2.2 §L is rewritten to a short steady-state pointer after Step 15 closes and `GOVERNANCE_BASELINE_v1_0.md` exists. The rewrite is a patch-version bump (v2.2.1) if it edits only §L; a minor bump (v2.3) if other sections also need updates at that time; a major bump (v3.0) only if a concern of v2.0-magnitude surfaces. Until Step 15, §L remains as written here.

---

## Changelog

### 2026-04-28 — Phase 14F amendment (in-place; no version bump)

- §B.1 "Facts/Derivation/Interpretation Separation" — boundary text updated from "L1/L2 boundary" to "L1/L2.5 boundary" reflecting the L2 archive close.
- §B.3 "Derivation Ledger Mandate" — claim layer text updated from "L2+ claims" to "L2.5+ claims" for the same reason.
- Principle *intent* unchanged; only boundary references retitled. Per §B.8 versioning discipline, in-place amendment recorded here in lieu of a v2.3 bump because the canonical principles' meaning is preserved (only their referenced layer numbers updated to match the post-14F layer roster).
- Authority: Phase 14F brief at `EXEC_BRIEF_PHASE_14F_L2_ARCHIVE_AND_GOVERNANCE_REFRESH_v1_0.md`.
- Commit: `0812ecd` (14F atomic commit) + this changelog amendment commit.

### 2026-07-19 — RS-4 amendment (B.11 proportionality carve-out; in-place, no version bump)

- §B.11 — added the native-authorized proportionality carve-out: B.11 governs *interpretive* queries; pinpointed factual lookups (`depth: retrieval`) satisfy it via the frame check (chart_header + session pin) plus a mandatory escalation valve (one-line flag + drill pointer when the fact touches an active contradiction, firing yoga, or open prediction window). §H.4 preamble updated to match.
- Principle intent preserved (no domain-siloed *interpretation*; the valve keeps material cross-domain context surfaced). Per the 14F precedent above, recorded as an in-place amendment.
- Authority: native authorization 2026-07-19 (Cowork retrieval-strategy session); source doctrine `RETRIEVAL_STRATEGY_v1_0.md` §3.6; ruling id RS-4.

### 2026-05-30 — v2.3 amendment (Multi-Ayanamsha Build arc)

- Added Build Orchestrator surface: per-chart deterministic 22-asset pipeline (A1-A22) × 5 ayanamshas
- Added META synthesis layer: 6 synthesis tables (α-ζ) above L2.5 (lattice, pattern catalog, divergence ledger, negative space, derivation trail, temporal unified view)
- Added UTEE: Unified Temporal Event Envelope across all 7 temporal tables (l1_time_synchronicity, l1_phase_locked_anchors, l1_sarvatobhadra_*, l1_vedha_extended, l1_bhrigu_bindu_transits, l1_graha_aspects_lifetime, l1_varsha_digest)
- Added Cross-Asset Bridge Matrix: l25_vedha_anchor_interactions (BRIDGE-S3)
- Stream D deliverables: INF7-12 (consume hybrid wiring, linter, RAG embedder, MCP resources, tracker page), RIR (retrieval envelope + tool registration), UTEE-S4 (6 temporal query tools), BRIDGE-S3 (1 cross-asset query tool), META-α–ε (13 query tools), ACC gates (15/15 GREEN), sealing artifact, operator sign-off packet
- CAPABILITY_MANIFEST bumped to v1.5 (25 new entries: 17 retrieval tools + 8 asset migrations)
- Migrations shipped: 139-153 (15 migrations across all 4 streams)

---

**END OF MASTER ARCHITECTURE BLUEPRINT v2.3**

*This document governs all subsequent work on the Abhisek Mohanty Jyotish Intelligence System.*
*Load this file FIRST in any future Claude or Gemini session (alongside `MACRO_PLAN_v2_0.md` for strategic-arc orientation and the STEP_LEDGER while the rebuild remains open).*
*Reference §D for workstream scope, §F for ID conventions, §G for detailed specs, §H.4 for Whole-Chart-Read Protocol, §I for current execution position (which defers to MP v2.0 + PHASE_B_PLAN + STEP_LEDGER), §J for resolved decisions, §L for the bridge into the governance-layer artifacts.*

*v2.2 closes the Step 5A row of the governance-rebuild workflow. The next step is Step 6 (Governance & Integrity Protocol design), which consumes v2.2 §D.9, §D.11, §L + MP v2.0 + GROUNDING_AUDIT as input. ND.1 (Mirror Discipline) global status remains `open` until Step 7 closes with all six per-step verifications confirmed.*
*Any future concern that reveals a structural gap of v2.0-magnitude should trigger a v3.0 rebuild; lesser drift is absorbed via minor bumps (v2.3, v2.4, …).*
