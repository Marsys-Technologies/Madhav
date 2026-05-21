---
artifact: PROJECT_ARCHITECTURE_v2_1
version: 2.1
status: SUPERSEDED
backfill_note: >
  Frontmatter backfilled by governance hygiene pass following PR #111 SESSION_HALT.md AC.7.
  Existing file body untouched.
---

> **SUPERSEDED** — see `PROJECT_ARCHITECTURE_v2_2.md` for current. Retained for historical reference only. Do not cite v2.1 as authoritative. Superseded 2026-04-24 at Step 5A of the Step 0 → Step 15 governance rebuild.

---
document: PROJECT MASTER ARCHITECTURE BLUEPRINT
project_name: Abhisek Mohanty — Jyotish Intelligence System (MARSYS-JIS)
subject: Abhisek Mohanty (b. 1984-02-05, 10:43 IST, Bhubaneswar)
version: 2.1
supersedes: 2.0 (2026-04-17 mid) and 1.0 (archived)
superseded_by: PROJECT_ARCHITECTURE_v2_2.md (2026-04-24, Step 5A of the Step 0 → Step 15 governance rebuild)
status: SUPERSEDED by PROJECT_ARCHITECTURE_v2_2.md
author_of_blueprint: Claude (Anthropic)
blueprint_date: 2026-04-17
v21_rationale: >
  All five §J open decisions resolved. Daily cadence locked with compensating
  discipline. Jagannatha Hora procurement confirmed. No privacy or audience
  boundaries. Chart-first reveal approach for Domain Reports. Blueprint now
  governs active execution.
v2_rationale: >
  Native raised two architecturally critical concerns against v1.0:
  (1) Domain-segregated L3 causes context-collapse.
  (2) L1→L2 transition lacks completeness guarantees.
  v2.0 inserted L2.5 Holistic Synthesis Layer, added CGP at L1, added Mode B
  Exhaustive Matrices at L2, revised query routing, and enforced whole-chart-read
  discipline. Scope expanded to 42 sessions. MSR target 500-600. UCN timing early.
purpose: >
  This document is the single governing architecture for all future work on the
  Abhisek Mohanty astrological knowledge-asset project. Every asset created,
  every session conducted, every artifact produced, and every decision made
  in this project must be traceable to the principles, taxonomies, and
  workstreams defined here. Future Claude sessions should load this file
  FIRST before any other work.
audience:
  primary: Abhisek Mohanty (native, project owner)
  secondary: Future Claude instances continuing the work
  tertiary: Independent classical-Jyotish acharyas invited for review
---

# MARSYS-JIS — PROJECT MASTER ARCHITECTURE BLUEPRINT v2.1

## §A — EXECUTIVE FRAME

### A.1 — The Project Thesis

This project exists to construct a **world-class, acharya-grade astrological intelligence system** centered on the natal chart of Abhisek Mohanty, such that the native can:

1. **Navigate real life decisions** — career, health, relationships, timing, wealth, family — with chart-calibrated clarity
2. **Access spiritual/philosophical depth** — understand karma, dharma, soul-architecture at a depth most professional readings never reach
3. **Generate any-domain insight on demand** — the system must function as a reusable, extensible engine, not a one-time artifact

The ambition is explicit: to exceed the depth and rigor of 99% of professional Jyotish work being done today, matching the standard of senior acharyas who integrate classical Parashari, Jaimini, KP, Nadi, and Tajika systems simultaneously — *and* who hold the chart as one integrated organism rather than as nine separated domain projections.

### A.2 — Why This Is Achievable

Four structural advantages make the ambition realistic:

- **Foundation already strong**: v6.0 forensic data file (1,815 lines, 24 major sections, 38 sub-categories), Deep Analysis v1.2.1 (6,314 lines, 17 RPT blocks, confidence 0.81), Financial Report v1.0 (1,273 lines) — collectively ~9,400 lines of forensic-grade content.
- **Systematic LLM orchestration**: with structured prompts, versioned artifacts, and governance discipline, we can run the equivalent of a research team through single-thread dialogue.
- **Compounding returns**: each workstream enriches downstream workstreams. Life Event Log calibrates Deep Analysis; Deep Analysis improves Holistic Synthesis; Holistic Synthesis drives Domain Reports; Domain Reports reveal gaps for Facts Layer.
- **Holistic-first architecture** (new in v2.0): by inserting L2.5 between L2 and L3, queries always see the whole chart before focusing. Domain reports become *lenses into* the whole, not *substitutes for* the whole.

### A.3 — What Success Looks Like (Definition of Done)

The project is "complete" when:

- (a) **Facts Layer v7.0 with CGP audit passed** — all 38 v6.0 categories FULL, new categories added (Nadi-amsa, Prashna-readiness, full Bhinna Ashtakavarga transit-grids, life-event-log integration, complete sahams inventory). **Every required cell verified populated** (Completeness Guarantee Protocol — see §G.1.CGP).
- (b) **Life Event Log v1.0** — minimum 100 dated life events with chart-state tagging, yielding a validated retrodictive pattern library.
- (c) **Deep Analysis v2.0 in dual mode** — Mode A: 25+ RPT sections with full 3-interpretation discipline. Mode B: exhaustive House Matrix (12 rows), Planet Matrix (9 rows), Sign Matrix (12 rows), Dasha-Period Matrix (200+ rows). **Every entity is represented.**
- (d) **L2.5 Holistic Synthesis Layer complete** — Chart Graph Model, Master Signal Register (500-600 entries), Cross-Domain Linkage Matrix, Resonance Map, Unified Chart Narrative (30-50K words).
- (e) **Nine Domain Reports** — Financial (exists), Career/Dharma, Health/Longevity, Relationships/Marriage, Children/Legacy, Spiritual/Moksha, Parents/Family-Karma, Psychology/Mind, Travel/Foreign. Each explicitly cites Unified Chart Narrative as parent.
- (f) **Remedial Protocol Master Codex** — unified gemstone + mantra + yantra + devata + muhurta + charity + dietary + behavioral framework.
- (g) **Temporal Engines** — lifetime timeline, rolling 36-month heatmap, annual Varshphal generator, daily-transit digest capability.
- (h) **Query & Prompt Library with whole-chart-read enforcement** — battle-tested prompts with mandatory cross-domain check.
- (i) **Governance Stack** — versioning discipline, confidence registers, contradiction logs, red-team cadence, falsifier-tracking.

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

---

## §B — ARCHITECTURAL PRINCIPLES (NON-NEGOTIABLE)

These principles govern every asset created. Any future session that violates them must be flagged and corrected. Twelve principles (expanded from ten in v1.0).

### B.1 — Facts/Derivation/Interpretation Separation

- **Facts** (observed or computed chart values): live ONLY in the Facts Layer (L1). No interpretation, no narrative.
- **Derivations** (logical transforms of facts — e.g., yoga detection, karaka assignment): live at L1/L2 boundary with explicit derivation-ledger pointing to source facts.
- **Interpretations** (meaning, implication, prediction): live ONLY at L2+ with explicit derivation-chain back to facts.

**Why this matters**: when the underlying facts are audited (e.g., re-computed with different ayanamsa), we know exactly which interpretations must be re-examined. Mixing layers destroys auditability.

### B.2 — Stable ID Discipline

Every fact, derivation, interpretation, event, signal, edge, node, pattern, and intervention receives a stable ID. ID namespaces are defined in §F below. IDs never change once published; deprecated IDs are marked DEPRECATED with pointer to successor.

### B.3 — Derivation Ledger Mandate

Every L2+ claim must carry a `DERIVATION_LEDGER` entry that lists the specific L1 fact IDs it consumes. No claim is allowed to rest on "as is known classically" or "per tradition" without source.

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

### B.12 — Completeness Guarantee Refusal (NEW in v2.0)

L2 analytical work refuses to interpret against incomplete L1 data. When a cell in the Completeness Guarantee Protocol audit is marked TBD, EXTERNAL_REQUIRED, or MISSING, any L2 work that would consume that cell explicitly flags the gap and waits for resolution. Interpretation shall not paper over a missing fact with "likely" or "probably" — it shall name the gap and pause.

---

## §C — THE FIVE-LAYER PYRAMID (v2.0 CONCEPTUAL MODEL)

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
│  L2 — ANALYTICAL LAYER                                          │
│  Mode A: Curated Deep Analysis (RPT.* — 25+ interpreted blocks) │
│  Mode B: Exhaustive Matrices ★ NEW IN v2.0 ★                   │
│          - House Matrix (12 rows)                               │
│          - Planet Matrix (9 rows)                               │
│          - Sign Matrix (12 rows)                                │
│          - Dasha-Period Matrix (200+ rows)                      │
│  "How the system reasons — both opportunistically AND           │
│   exhaustively"                                                 │
└──────────────────────┬──────────────────────────────────────────┘
                       │ Analyzes from ↓
┌──────────────────────┴──────────────────────────────────────────┐
│  L1 — FACTS LAYER                                               │
│  • Forensic Data v7.0 (upgraded from v6.0)                      │
│  • Life Event Log v1.0+                                         │
│  • External Reference Card (classical citations)                │
│  GATE: Completeness Guarantee Protocol (CGP) ★ NEW IN v2.0 ★   │
│        L2 shall not run against cells marked incomplete (B.12)  │
│  "What the system knows — with completeness audit"              │
└─────────────────────────────────────────────────────────────────┘
```

### C.1 — Layer L1 — Facts Layer

**Purpose**: single source of truth for all chart facts, derivations, and lived reality.

**Contents**:
- **FORENSIC_DATA v7.0** — upgraded from v6.0; all partial sections completed; new sections added
- **LIFE_EVENT_LOG v1.0+** — structured log of dated life events with chart-state tags
- **EXTERNAL_REFERENCE_CARD** — classical sutra/sloka references used across L2+

**Completeness Guarantee Protocol (CGP) gate** — before v7.0 is signed off, the CGP audit (§G.1.CGP) verifies computational completeness. Gaps are named, tagged with required external source, and resolved before L2 work proceeds against those cells.

**Update discipline**: L1 is append-only by default. Corrections produce new versions; old versions retained in archive.

### C.2 — Layer L2 — Analytical Layer

**Purpose**: extract patterns, detect convergences, resolve contradictions, formulate interpretations — via two complementary modes.

**Mode A — Curated Deep Analysis** (current v1.2.1 expanded to v2.0):
- 25+ RPT sections (signal-driven, interpreted)
- SIG.*, CVG.*, CTR.* libraries
- 3-interpretation discipline throughout
- Red-team audit per version

**Mode B — Exhaustive Matrices** (new in v2.0):
- **House Matrix** (12 rows × multi-column schema — see §G.3.ModeB)
- **Planet Matrix** (9 rows)
- **Sign Matrix** (12 rows)
- **Dasha-Period Matrix** (200+ rows for lifetime Vimshottari MD/AD, with Yogini and Chara overlays)
- **Divisional Chart Matrix** (16 rows — one per Dx)

**Modes are complementary, not redundant**: Mode B guarantees no entity is missed (Concern #2); Mode A provides interpretive depth where it matters most. Mode B outputs are inputs to L2.5 (specifically the Master Signal Register).

**Update discipline**: versioned. Each version produces a full red-team audit before closure.

### C.3 — Layer L2.5 — Holistic Synthesis Layer (NEW IN v2.0)

**Purpose**: hold the whole chart as one integrated organism. Resolve the domain-context-collapse problem by providing a single layer where every query can retrieve whole-chart context before focusing.

**Five components**:

**C.3.1 — Chart Graph Model** (`CGM`)

A directed graph representation of the chart:
- **Nodes** (`CGM.NODE.*`): every astrological entity — each planet, house, sign, nakshatra, yoga, karaka role, divisional placement, dasha lord, sensitive point, upagraha, saham, arudha, special lagna
- **Edges** (`CGM.EDGE.*`): every classical relationship — dispositorship, Vedic aspect, Western aspect (contextual), ownership, exaltation-affinity, nakshatra-lordship, karaka representation, divisional confirmation, combustion, planetary war, kakshya rulership, saham composition, yoga membership, dasha-lord activation
- **Edge weights** (`CGM.WEIGHT.*`): strength of relationship derived from Shadbala, Ashtakavarga bindu contribution, Vimsopaka, dignity, Bhavabala
- **Subgraphs** (`CGM.SUB.*`): pre-computed domain-filtered views (the career subgraph, the health subgraph, etc. — for L3 routing)

**Estimated size**: ~200 nodes, ~800-1,200 edges.

**C.3.2 — Master Signal Register** (`MSR`)

Flat, fully-enumerated list of every detectable signal. Schema per entry:
```yaml
SIG.MSR.NNN:
  signal_name: "human-readable name"
  signal_type: [yoga | dignity | aspect | dasha-activation | transit-activation |
                house-strength | divisional-pattern | convergence | contradiction |
                sensitive-point | panchang | remedial-trigger | nakshatra-signature |
                jaimini-pattern | kp-signature | tajika-pattern | cross-chart]
  classical_source: "BPHS Ch.X.Y / Jaimini Sutra X.Y / Phaladeepika Ch.X / Saravali Ch.X"
  entities_involved: [list of CGM.NODE.* ids]
  strength_score: 0.00-1.00
  valence: [benefic | malefic | mixed | neutral | context-dependent]
  temporal_activation: [natal-permanent | dasha-windowed | transit-triggered | annual | monthly]
  supporting_rules: [list of sub-rules]
  falsifier: "what would refute this signal"
  domains_affected: [career | wealth | health | relationships | children | spirit | parents | mind | travel]
  confidence: 0.00-1.00
  v6_ids_consumed: [list of PLN.*, HSE.*, D9.*, etc.]
  rpt_deep_dive: [pointer to RPT section if one exists]
```

**Target volume**: 500-600 signals (MAXIMUM tier selected by native).

**Typical breakdown**:
- ~50 dignity signals (exaltation, debility, own-sign, friendly-house, etc. × all planets)
- ~80 aspect signals (Vedic + Western + Jaimini, major combinations)
- ~60 yoga signals (Raja, Dhana, Lakshmi, Saraswati, Maha Purusha, Pancha Mahapurusha, Neecha Bhanga, Vipreet, Chandra Mangala, Gajakesari, etc.)
- ~100 divisional-chart signals (each Dx's key features × 16 Dxs)
- ~60 nakshatra signals (lagna/moon/sun nakshatra + pada characteristics + vedha + navatara)
- ~40 sensitive-point signals (all sahams + upagrahas + bhrigu-bindu + yogi points)
- ~50 dasha signals (each MD activation × key transitions)
- ~40 transit signals (key transit-to-natal configurations)
- ~30 sade-sati and shani-related signals
- ~30 KP signals (cuspal sub-lord signifier patterns)
- ~30 Jaimini signals (arudhas + chara karakas + karakamsha)
- ~20 panchang-DNA signals (tithi/yoga/karana inherent patterns)
- ~10 tajika-specific signals

**C.3.3 — Cross-Domain Linkage Matrix** (`CDLM`)

An N×N matrix where N = 9 domains (career, wealth, health, relationships, children, spirit, parents, mind, travel). Each cell (i,j) contains:
- **Shared entities**: which CGM.NODE.* ids affect both domain i and domain j
- **Shared signals**: which MSR.* ids fire in both domains
- **Linkage strength**: 0.00-1.00 (how tightly the two domains are coupled in this specific chart)
- **Key cross-domain yogas**: yogas whose signification spans both domains

**Example pre-computed cell** (Career × Wealth for this chart):
```yaml
CDLM.CAREER.WEALTH:
  shared_entities: [Mercury (10H Yogi-Vargottama-MD + 2H signification via dispositor chain),
                     Sun (10H own-house + 2L from Moon),
                     AL in 10H (10H as wealth-visibility arudha),
                     Saturn AmK (authority-for-wealth karaka)]
  shared_signals: [MSR.SARASWATI_YOGA, MSR.LAKSHMI_YOGA, MSR.MERCURY_MD_ACTIVATION,
                    MSR.10H_AL_WEALTH_VISIBILITY, MSR.SATURN_AMK_AUTHORITY_WEALTH]
  linkage_strength: 0.91
  key_cross_domain_yogas: [Saraswati-Yoga, Maha-Dhana-Yoga, 9-10-11 integration]
  interpretive_note: "In this chart, career and wealth are near-inseparable — the
    same Mercury MD drives both, the same 10H stellium channels both, the same
    Saturn AmK authority-route delivers both. Separating them in analysis is
    artificial; any career advice must be wealth-coherent and vice versa."
```

All 9×9 = 81 cells (or 36 if symmetric) are pre-computed.

**C.3.4 — Resonance Map** (`RM`)

For every major chart element, two lists:
- **Constructive resonance** (`RM.CONSTRUCTIVE.*`): which other elements amplify this element
- **Destructive resonance** (`RM.DESTRUCTIVE.*`): which other elements dampen this element

Example:
```yaml
RM.SATURN_EXALTED_7H:
  element: PLN.SATURN + HSE.7 + SBL.UCHA(59.18)
  constructive_resonance:
    - PLN.MARS in HSE.7 (shared-house signifier — tension but co-presence)
    - ASP.G.JUPITER_5_TO_7 (Jupiter's 5th-from-5th = dharmic authorization from 9H-like vantage)
    - KAK.PISCES.Z1 (Saturn's own kakshya during Sade Sati peak phase — maximum personal activation)
    - KRK.C.AMATYA_SATURN (AmK reinforces authority-executor role)
    - D9.NBR.SATURN (Neecha-Bhanga in D9 adds delayed-peak reserve power)
    - DSH.V.AD.SATURN.2024_2027 (AD lord = current time-giver)
  destructive_resonance:
    - AVG.SP.SATURN rank 7 of 7 (Shuddha Pinda last = dramatic-not-compound)
    - TRS.SS.C2.P3 current (Sade Sati Phase 2/3 late — compressive)
    - BVB.7 below threshold (7H bhavabala weak = house-container can't hold Saturn's strength)
    - PLN.VENUS weak and 7L (Venus as 7L can't convert Saturn's authority into partnership-wealth smoothly)
```

**Why this matters**: when you ask "should I take this job offer in July 2026," a domain-silo answer might say "career report signals support." A Resonance-Map-aware answer says "Saturn AD authority-delivery constructively resonates with Jupiter-exaltation-window — support. BUT simultaneously Saturn rank-7-Shuddha-Pinda and weak-BVB-7H destructively resonate — the offer may deliver title-authority without wealth-compounding. Evaluate offer on authority-coherence not compensation-size."

**C.3.5 — Unified Chart Narrative** (`UCN`)

A single integrated reading of the chart as one organism. 30-50K words. Structure:

- **Part I — The Chart's Fundamental Architecture** (the three-five foundation signatures that define the entire reading)
- **Part II — The Soul-Trajectory** (Atmakaraka, Karakamsa, D9, D20, D60 — past-karma → this-life-mission → moksha-direction)
- **Part III — The Mind-Body Container** (Lagna, Moon, Mars, health-karma, psychological architecture)
- **Part IV — The Dharmic-Material Engine** (9H-10H-2H-11H integration, Saraswati-Lakshmi-Raja-Yoga stack, wealth-as-dharmic-output)
- **Part V — The Relational Web** (7H, 4H, 3H, 5H, 11H, 12H — all relational domains read as one ecosystem)
- **Part VI — The Foreign/Moksha Signature** (12H + D9-12H-stellium + Rahu-Ketu axis + Ketu MD upcoming — one of this chart's dominant architectures, requires its own part)
- **Part VII — The Authority-Through-Tension Pattern** (Mars-Saturn 7H + AL-10H + Sade Sati — the authority route that defines this chart's operational mechanism)
- **Part VIII — The Timing Metaphysics** (how Vimshottari + Yogini + Chara stack, why Mercury-Saturn-Ketu phase transitions matter so much)
- **Part IX — The Contradictions and What They Mean** (the ~7-10 internal chart tensions and their collective implication)
- **Part X — The Operating Instructions** (how to live this chart — not remedies, but the existential posture the chart itself asks for)

**Critical principle**: the UCN is written as if the chart were a single living organism. Every section refers forward and backward; nothing is isolated. Career is not a separate chapter — career threads through Dharmic-Material Engine, Authority-Through-Tension Pattern, and Timing Metaphysics.

**When built**: EARLY (before any Domain Report) — see §I Phase 2A. The UCN becomes the mother document every Domain Report must cite.

### C.4 — Layer L3 — Insight Generation

**Purpose**: produce specific, focused, human-facing deliverables for defined questions.

**Contents**:
- **Domain Reports** — 9 reports (see §G.4)
- **Remedial Protocol Master Codex** — unified intervention framework
- **Temporal Engines** — lifetime timeline, rolling heatmap, annual Varshphal, transit digest

**New v2.0 constraints**:
- Every Domain Report must cite the Unified Chart Narrative (UCN) as parent in its metadata
- No Domain Report may contradict the UCN without explicit flag-and-resolve
- Every Domain Report has a mandatory "Cross-Domain Linkages" section citing relevant CDLM entries
- Domain Reports are understood as *lenses into* the whole, not *substitutes for* the whole

**Update discipline**: Domain Reports are versioned per-refresh (typically annual or on major life event). Temporal Engines refresh per schedule (heatmap quarterly, Varshphal annually).

### C.5 — Layer L4 — Query Interface

**Purpose**: the documented ways to extract insight from the system, with whole-chart-read enforcement.

**Contents**:
- **MASTER_PROMPT_LIBRARY** — battle-tested prompts by question-type
- **SESSION_PROTOCOL** — how to start, conduct, and conclude a Claude session against the project
- **QUESTION_TAXONOMY** — classification of question-types with routing rules
- **Whole-Chart-Read Enforcer** — the procedural checkpoint every prompt runs (B.11)

**Standard routing pattern for every query** (see §H.4):
1. Query enters L4
2. L4 identifies primary domain(s)
3. L4 invokes L2.5 Cross-Domain Linkage Matrix → "what other domains touch this?"
4. L4 pulls Resonance Map entries for primary chart elements involved
5. L4 consults Unified Chart Narrative part(s) relevant
6. THEN L4 routes to L3 Domain Report(s) for focused depth
7. Answer synthesizes whole-chart context + domain-specific depth

---

## §D — THE EIGHT WORKSTREAMS (EXPANDED IN v2.0)

### D.1 — Workstream 1 — Facts Layer Completion (L1) + CGP

**Objective**: upgrade FORENSIC_DATA from v6.0 (current) to v7.0 (complete + CGP-audited).

**Scope**:
1. Complete all PARTIAL and FLAGGED categories from v6.0 (see v6.0 §24 ledger)
2. Add new categories:
   - D12, D16, D27, D30, D40, D45, D60 deep-derivation tables (beyond v6.0 basic positions)
   - Full Bhinna Ashtakavarga transit grids (per-planet bindu contributions by sign)
   - Nadi-amsa positions (1/150° subdivisions) for Bhrigu-style nadi work
   - Prashna-readiness frame
   - Bhrigu Bindu 60-year progression table
   - Full aspect-strength grid (Graha Drishti with virupa percentages)
   - Tajika monthly progression
   - Complete ephemeris export (60-year monthly resolution for all 9 planets)
   - Complete Sahams inventory (20+ sahams, not just 6)
   - Complete special Lagnas (Hora, Ghati, Bhava, Indu, Sri, Pranapada, Varnada)
3. Add DATA_PROVENANCE section (source of each fact)
4. **Execute Completeness Guarantee Protocol** (§G.1.CGP)

**Deliverable**: `FORENSIC_DATA_v7_0.md`, targeted ~3,000 lines.

**External dependencies**: specialist-tool output required for several additions. `EXTERNAL_COMPUTATION_SPEC.md` produced for user to procure.

**Confidence after completion**: targets 0.98. Post-CGP, any remaining uncertainty is explicitly named.

### D.2 — Workstream 2 — Life Event Log (L1 complement)

**Objective**: create the single highest-leverage asset for acharya-grade sight — empirical validation corpus.

**Scope**: structured chronological record of material life events with chart-state tagging.

**Schema** (per event):
```yaml
EVT.YYYY.MM.DD.XX:
  date: YYYY-MM-DD
  category: [career | health | relationship | finance | family | travel |
             education | spiritual | creative | legal | loss | gain |
             psychological | residential | other]
  subcategory: [string]
  description: [1-3 sentences, factual]
  magnitude: [trivial | moderate | significant | major | life-altering]
  valence: [positive | mixed | negative | neutral]
  native_reflection: [optional 1-3 sentences]
  chart_state_at_event:
    vimshottari_md: [...]
    vimshottari_ad: [...]
    vimshottari_pd: [optional]
    yogini_md: [...]
    chara_md_ad: [...]
    sade_sati_phase: [...]
    transits_of_note: [...]
    eclipses_within_6mo: [...]
    retrograde_activity: [...]
    ashtakavarga_SAV_transit_sign: [...]
  retrodictive_match:
    predicted_by_chart: [yes | partial | no | unexamined]
    signals_that_matched: [list of MSR.* / SIG.* / CVG.* IDs]
    signals_that_missed: [gaps]
  notes: [free text]
```

**Target volumes**:
- v1.0 (sessions 2-4): 25-40 most significant events
- v1.1: expand to 75-100 events
- v2.0 (6-12 months): 150+ events, pattern-library extracted

**Elicitation**: structured interview across 10 categories (session 2).

**Deliverable**: `LIFE_EVENT_LOG_v1_0.md` (living document).

### D.3 — Workstream 3 — Deep Analysis Expansion with Mode B (L2)

**Objective**: expand current Deep Analysis v1.2.1 (17 RPT sections) to v2.0 with both Modes.

**Mode A scope — new RPT sections**: See v1.0 blueprint table (unchanged); target 25+ sections with full 3-interpretation discipline.

**Mode B scope — NEW in v2.0**:

**Mode B is the exhaustive combinatorial pass.** Four matrices:

**B.1 — House Matrix** (12 rows, one per house 1-12, each with columns):
- Rashi tenants
- Chalit tenants (if differs)
- House lord + placement
- Planets aspecting (Vedic)
- Planets aspecting (Western, contextual)
- Bhavabala score
- SAV bindu total
- Yogas involving this house
- Each divisional chart's version of this house (D9 house-lord, D10 house-lord, etc.)
- Arudha (A1-A12 if applicable)
- KP cuspal sub-lord chain
- Dashas of house lord (Vimshottari periods)
- Transit activations 2026-2044 (key dates)
- Life-event-log events tagged to this house
- Interpretation (1-2 paragraph synthesis per house)

**B.2 — Planet Matrix** (9 rows, Sun through Ketu, columns):
- Sign, degree, nakshatra, pada
- Rashi house, Chalit house
- Dignity state (own / exalted / friend / neutral / enemy / debilitated)
- Shadbala six-fold + total + rank
- Uccha Bala, Bhava Bala contribution, Drekkana Bala, Vimsopaka
- Aspects given (to whom, at what strength)
- Aspects received (from whom, at what strength)
- Karaka roles (Chara + Sthira)
- Yogas involvement
- All 16 divisional placements
- Combustion state, planetary war
- Retrograde, Chesta Bala
- Avastha (Jagratadi + Baladi + Deeptadi)
- Kakshya zone rulerships (for Saturn)
- BAV bindu contributions
- Dasha roles (Vimshottari, Yogini, Chara)
- Transit pattern lifetime
- Life-event-log events tagged to this planet
- Interpretation (2-3 paragraph synthesis)

**B.3 — Sign Matrix** (12 rows, Aries through Pisces, columns):
- House(s) occupied (one per sign here, since 12 houses map to 12 signs)
- Planets resident (Rashi)
- Planets resident (Chalit)
- Planets aspecting from outside
- SAV bindu total
- Kakshya profile (Saturn's zones if sign hosts Saturn transit)
- Transit-density forecast 2026-2044
- Sign-specific dignity events (planets going exalted/debilitated in transit)
- Life-event-log events occurring during major transits to this sign

**B.4 — Dasha-Period Matrix** (200+ rows, one per Vimshottari MD/AD combination for lifetime, with Yogini and Chara overlays):
- Vimshottari MD
- Vimshottari AD (within MD)
- Start date, end date
- Vimshottari PD spans (if relevant resolution)
- Yogini MD active concurrently
- Chara MD active concurrently
- Period-lord's strength (Shadbala + dignity)
- Period-lord's house (Rashi + Chalit)
- Period-lord's karaka role
- House signification of period-lord (which houses does this lord activate)
- Major transits within this period
- Eclipses within this period
- Life-event-log events within this period
- Retrodictive score (if events logged: how well chart predicted them)
- Prospective score (if period is future: forecast confidence)

**B.5 — Divisional Chart Matrix** (16 rows, one per Dx):
- Chart purpose (classical signification)
- Lagna of this chart
- Key planet placements
- Vargottama planets (planets in same sign in this Dx as in D1)
- Primary yogas present in this Dx
- Primary affliction signals in this Dx
- Cross-validation with D1 (does this Dx confirm or contradict D1 reading)
- Interpretation

**Mode B output discipline**: matrices are flat, structured tables (markdown table or YAML). Interpretations are concise (1-3 paragraphs per row) because depth lives in Mode A RPT sections. Mode B is **coverage**, Mode A is **depth**.

**Mode B outputs feed L2.5**:
- House Matrix → feeds CGM (node attributes) and MSR (house-related signals)
- Planet Matrix → feeds CGM (node attributes) and MSR (planet-related signals)
- Sign Matrix → feeds CGM and MSR
- Dasha-Period Matrix → feeds Temporal Engines at L3

**Deliverable**: `DEEP_ANALYSIS_v2_0.md`, targeted 14,000-16,000 lines (Mode A ~10K lines, Mode B ~4-6K lines).

### D.4 — Workstream 4 — L2.5 Holistic Synthesis Build (NEW IN v2.0)

**Objective**: build the five components of the Holistic Synthesis Layer.

**Four sub-workstreams**:

**D.4.A — Chart Graph Model (`CGM_v1_0.md`)**
- Enumerate all nodes (~200)
- Enumerate all edges (~800-1,200) with classical-rule citations
- Compute edge weights from L1 strength metrics
- Produce subgraph-views for each of 9 domains
- Validate: every L1 entity appears as at least one node; every classical relationship type appears as at least one edge-type

**D.4.B — Master Signal Register (`MSR_v1_0.md`)**
- Target 500-600 signals (Maximum tier per native's selection)
- Classify by signal_type (15 types enumerated in §C.3.2)
- Every signal has: classical source, entities involved, strength, valence, temporal activation, supporting rules, falsifier, domains affected, confidence, v6 IDs consumed, RPT deep-dive pointer (if one exists)
- Signals are compiled by systematic traversal (not curated): run each classical system exhaustively and log every signal fired

**D.4.C — Cross-Domain Linkage Matrix (`CDLM_v1_0.md`)**
- 9×9 matrix (or 36 cells if symmetric)
- Each cell: shared entities, shared signals, linkage strength 0-1, key cross-domain yogas, interpretive note
- Compute per-cell from CGM + MSR by graph-traversal

**D.4.D — Resonance Map (`RM_v1_0.md`)**
- For every major chart element (~30-50 elements): constructive and destructive resonance lists
- Element identification: anything scoring high in CGM centrality, any Mode B matrix row with "distinctive" interpretation, any RPT.* section subject
- Produces a structured YAML-plus-prose document

**D.4.E — Unified Chart Narrative (`UCN_v1_0.md`)**
- 30-50K words
- 10 Parts (structure in §C.3.5)
- Written integratively: every Part references other Parts; nothing isolated
- Cites Mode A RPT sections, Mode B matrix rows, MSR signals, CGM subgraphs, CDLM cells, RM resonances
- Red-teamed before closure
- **THIS IS THE MOTHER DOCUMENT** — every Domain Report cites it as parent

**Deliverables**: five artifacts above.

**Total estimated pages**: L2.5 is ~15-20K lines across all five artifacts. This is the largest new asset v2.0 introduces.

### D.5 — Workstream 5 — Domain Reports (L3)

**Objective**: produce nine life-domain reports. Each is explicitly a lens into the UCN.

**The 9 reports** (as in v1.0):
1. FINANCIAL (exists v1.0; refresh to v2.0)
2. CAREER / DHARMA
3. HEALTH / LONGEVITY
4. RELATIONSHIPS / MARRIAGE
5. CHILDREN / LEGACY
6. SPIRITUAL / MOKSHA
7. PARENTS / FAMILY-KARMA
8. PSYCHOLOGY / MIND
9. TRAVEL / FOREIGN

**Template addition in v2.0**:
- New section: "Relation to the Unified Chart Narrative" (cites parent UCN parts)
- New section: "Cross-Domain Linkages" (cites relevant CDLM cells explicitly)
- New metadata field: `parent_UCN_version`

### D.6 — Workstream 6 — Remedial Protocol Master Codex

(Unchanged from v1.0 — see v1.0 §D.5 equivalent.)

### D.7 — Workstream 7 — Temporal Engines

(Unchanged from v1.0 — see v1.0 §D.6 equivalent. Note: Dasha-Period Matrix from Mode B feeds the Lifetime Timeline.)

### D.8 — Workstream 8 — Query & Prompt Library with Whole-Chart-Read Enforcement

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

### D.9 — Workstream 9 — Governance Stack

(Unchanged from v1.0 — see v1.0 §D.8 equivalent. Governance now also tracks UCN/CGM/MSR/CDLM/RM version states.)

---

## §E — FILE SYSTEM ARCHITECTURE (v2.0 REVISED)

```
/PROJECT_ROOT/
├── 00_ARCHITECTURE/
│   ├── PROJECT_ARCHITECTURE_v2_0.md          ← this file
│   ├── PROJECT_ARCHITECTURE_v1_0_ARCHIVED.md ← preserved
│   ├── GOVERNANCE_STACK_v1_0.md
│   └── FILE_INDEX.md
│
├── 01_FACTS_LAYER/
│   ├── FORENSIC_DATA_v7_0.md
│   ├── FORENSIC_DATA_v6_0_ARCHIVED.md
│   ├── LIFE_EVENT_LOG_v1_0.md
│   ├── EXTERNAL_REFERENCE_CARD.md
│   └── CGP_AUDIT_v1_0.md                     ← NEW: completeness audit output
│
├── 02_ANALYTICAL_LAYER/
│   ├── DEEP_ANALYSIS_v2_0.md                 ← Mode A (curated RPT sections)
│   ├── DEEP_ANALYSIS_v1_2_1_ARCHIVED.md
│   ├── MATRIX_HOUSES.md                      ← NEW: Mode B House Matrix
│   ├── MATRIX_PLANETS.md                     ← NEW: Mode B Planet Matrix
│   ├── MATRIX_SIGNS.md                       ← NEW: Mode B Sign Matrix
│   ├── MATRIX_DASHA_PERIODS.md               ← NEW: Mode B Dasha-Period Matrix
│   ├── MATRIX_DIVISIONALS.md                 ← NEW: Mode B Divisional Chart Matrix
│   ├── SIGNATURE_LIBRARY.md
│   ├── CONVERGENCE_MAP.md
│   ├── CONTRADICTION_REGISTRY.md
│   └── PATTERN_LIBRARY.md
│
├── 025_HOLISTIC_SYNTHESIS/                   ← NEW LAYER FOLDER
│   ├── CGM_v1_0.md                           ← Chart Graph Model
│   ├── MSR_v1_0.md                           ← Master Signal Register (500-600)
│   ├── CDLM_v1_0.md                          ← Cross-Domain Linkage Matrix
│   ├── RM_v1_0.md                            ← Resonance Map
│   └── UCN_v1_0.md                           ← Unified Chart Narrative (MOTHER DOC)
│
├── 03_DOMAIN_REPORTS/
│   ├── REPORT_FINANCIAL_v2_0.md
│   ├── REPORT_FINANCIAL_v1_0_ARCHIVED.md
│   ├── REPORT_CAREER_DHARMA_v1_0.md
│   ├── REPORT_HEALTH_LONGEVITY_v1_0.md
│   ├── REPORT_RELATIONSHIPS_v1_0.md
│   ├── REPORT_CHILDREN_LEGACY_v1_0.md
│   ├── REPORT_SPIRITUAL_MOKSHA_v1_0.md
│   ├── REPORT_PARENTS_FAMILY_v1_0.md
│   ├── REPORT_PSYCHOLOGY_MIND_v1_0.md
│   └── REPORT_TRAVEL_FOREIGN_v1_0.md
│
├── 04_REMEDIAL_CODEX/
│   └── REMEDIAL_CODEX_v1_0.md
│
├── 05_TEMPORAL_ENGINES/
│   ├── LIFETIME_TIMELINE.md
│   ├── HEATMAP_ROLLING_36MO.md
│   ├── VARSHPHAL_2026_2027.md
│   └── [future years]
│
├── 06_QUERY_INTERFACE/
│   ├── QUERY_PROMPT_LIBRARY_v1_0.md
│   ├── SESSION_PROTOCOL.md
│   └── QUESTION_TAXONOMY.md
│
└── 99_ARCHIVE/
    └── [superseded versions]
```

---

## §F — STABLE ID NAMESPACE (v2.0 EXPANDED)

Extends v1.0 namespace with L2.5 additions:

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
| `CGP.*` | `CGP.AUDIT.HOUSE_MATRIX.001` | **Completeness Guarantee audit entry** | **L1 NEW** |
| `SIG.*` | `SIG.01` | Dominant signature (curated) | L2 Mode A |
| `CVG.*` | `CVG.03` | Convergence | L2 Mode A |
| `CTR.*` | `CTR.02` | Contradiction | L2 Mode A |
| `RPT.*` | `RPT.STR.01` | Deep Analysis section | L2 Mode A |
| `INT.*` | `INT.02` | Intervention | L2/L3 |
| `RED.*` | `RED.03` | Red-team | L2 Mode A |
| `XRF.*` | `XRF.01` | Cross-reference | L2 Mode A |
| `MX.HSE.*` | `MX.HSE.7` | **House Matrix row** | **L2 Mode B NEW** |
| `MX.PLN.*` | `MX.PLN.SATURN` | **Planet Matrix row** | **L2 Mode B NEW** |
| `MX.SGN.*` | `MX.SGN.LIBRA` | **Sign Matrix row** | **L2 Mode B NEW** |
| `MX.DSH.*` | `MX.DSH.MERCURY.SATURN.2024` | **Dasha-Period Matrix row** | **L2 Mode B NEW** |
| `MX.DVS.*` | `MX.DVS.D9` | **Divisional Matrix row** | **L2 Mode B NEW** |
| `CGM.NODE.*` | `CGM.NODE.PLN.MERCURY` | **Graph node** | **L2.5 NEW** |
| `CGM.EDGE.*` | `CGM.EDGE.DISP.MERCURY_JUPITER` | **Graph edge** | **L2.5 NEW** |
| `CGM.SUB.*` | `CGM.SUB.CAREER` | **Domain subgraph** | **L2.5 NEW** |
| `MSR.*` | `MSR.SARASWATI_YOGA.01` | **Master Signal Register entry** | **L2.5 NEW** |
| `CDLM.*` | `CDLM.CAREER.WEALTH` | **Cross-Domain Linkage cell** | **L2.5 NEW** |
| `RM.*` | `RM.SATURN_7H_EXALTED` | **Resonance Map entry** | **L2.5 NEW** |
| `UCN.*` | `UCN.PART.IV.SEC.2` | **Unified Chart Narrative section** | **L2.5 NEW** |
| `DOM.*` | `DOM.CAREER` | Domain report | L3 |
| `REM.*` | `REM.GEM.RUBY` | Remedial measure | L3 |
| `TIM.*` | `TIM.HEATMAP.2026.Q3` | Temporal engine entry | L3 |
| `PMT.*` | `PMT.DECISION.CAREER.01` | Prompt template | L4 |
| `GOV.*` | `GOV.CONFIDENCE.UCN` | Governance entry | Governance |

---

## §G — DETAILED WORKSTREAM SPECIFICATIONS

### G.1 — Facts Layer v7.0 — Detailed Spec + CGP

(v7.0 scope unchanged from v1.0 §G.1. CGP added.)

**G.1.CGP — The Completeness Guarantee Protocol**

The CGP is a formal audit executed before v7.0 is signed off. It verifies that every cell required by downstream Mode A, Mode B, and L2.5 work is populated (or explicitly marked with external-source-required).

**CGP audit categories**:

**Category 1 — Combinatorial Coverage**
- **Planet × House × Dx**: 9 planets × 12 houses × 16 divisionals = 1,728 cells checking "does this planet have a house placement in this Dx?"
- **Planet × Sign × Dx**: 9 × 12 × 16 = 1,728 cells for sign placement
- **Planet × Nakshatra × Dx** (where applicable): check nakshatra placement per Dx

**Category 2 — Strength Coverage**
- **Shadbala**: 6 components × 9 planets = 54 cells
- **Bhavabala**: 8 components × 12 houses = 96 cells (if full breakdown desired)
- **Ashtakavarga BAV**: 8 benefic planets (Sun-Saturn-Asc) × 12 signs = 96 cells per BAV + 8 × 9 = 72 cells per Bhinna
- **Ashtakavarga SAV**: 12 signs (summary) + full contribution breakdown
- **Vimsopaka**: 9 planets × 16 Dxs = 144 cells (already in v6.0)
- **Kakshya**: 12 signs × 8 zones = 96 cells (Saturn's zones)

**Category 3 — Aspect Coverage**
- **Vedic Graha Drishti**: 9 × 9 = 81 cells (planet-to-planet)
- **Vedic Bhav Drishti**: 9 × 12 = 108 cells (planet-to-house)
- **Western aspect overlay**: 9 × 9 = 81 cells
- **Jaimini rashi drishti**: 12 × 12 = 144 cells (sign-to-sign)

**Category 4 — Dasha Coverage**
- **Vimshottari**: full MD/AD sequence 0-120 years (~45 rows for MD, each subdivided)
- **Yogini**: full sequence 0-120 years
- **Jaimini Chara**: full sequence 0-120+ years (v6.0 has through 2049; extend)

**Category 5 — Sensitive-Point Coverage**
- 9 upagrahas populated
- 20+ sahams (not just 6)
- Bhrigu Bindu + 60-year progression
- Yogi + Avayogi + Dagdha Rashi + Duhsthana etc.
- All 7 special Lagnas

**Category 6 — Temporal Coverage**
- Transit ephemeris 1984-2044 at monthly minimum, daily preferred for critical windows
- Eclipse catalog for lifetime
- Retrograde periods catalog
- Panchang daily data (or key-date sampling)

**Category 7 — Provenance Coverage**
- Every L1 cell has `source:` tag (Swiss Ephemeris / Jagannatha Hora / manual / external-astrologer-provided)
- Cells with `source: UNKNOWN` are flagged

**CGP execution**:
1. For each of 7 categories, count expected cells vs. populated cells
2. Compute completeness ratio (populated / expected)
3. Produce `CGP_AUDIT_v1_0.md` listing every gap
4. Each gap tagged with: what to compute, how to compute it, tool required, estimated effort
5. v7.0 is signed off only when every gap is either (a) filled or (b) explicitly accepted as deferred with justification

**CGP target completeness at v7.0 signoff**: ≥ 95% populated, remainder tagged as deferred-with-justification.

### G.2 — Life Event Log v1.0 — Detailed Spec

(Unchanged from v1.0 §G.2.)

### G.3 — Deep Analysis v2.0 — Detailed Spec (Mode A + Mode B)

**G.3.ModeA — Curated Deep Analysis** (expansion of v1.2.1)

Target 25+ RPT sections. New sections per v1.0 blueprint §D.3 table. Full 3-interpretation discipline on all. Red-team pass before closure.

**G.3.ModeB — Exhaustive Matrices** (NEW)

See §D.3 detailed schemas above. Key discipline:

- Mode B is flat-structure tables (markdown or YAML). No narrative flow.
- Every matrix row has a `completeness_audit_ref` pointing back to CGP entries confirming source data is complete.
- Mode B interpretations are terse (1-3 paragraphs per row) — depth lives in Mode A.
- Mode B outputs are direct inputs to L2.5 MSR (signal extraction) and L2.5 CGM (graph construction).

**Mode B execution sequence**:
1. Build House Matrix first (feeds HSE.* analysis in Mode A)
2. Build Planet Matrix second (feeds PLN.* analysis in Mode A)
3. Build Sign Matrix third
4. Build Divisional Matrix fourth
5. Build Dasha-Period Matrix last (needs transit data + life-event-log — integrates everything)

**Validation**: Mode B completeness is auditable. For House Matrix: "does row exist for houses 1-12?" For Planet Matrix: "does row exist for Sun-Ketu?" Etc. Empty cells are flagged.

### G.4 — L2.5 Holistic Synthesis — Detailed Spec

**G.4.A — Chart Graph Model Build**

**Nodes** — systematic enumeration:
- 9 planets → 9 nodes
- 12 houses → 12 nodes
- 12 signs → 12 nodes (though sign-house mapping in this chart gives 1:1)
- 27 nakshatras (only those involved) → ~12-15 nodes (Lagna nak, Moon nak, Sun nak, etc.)
- Yogas detected → ~30-50 nodes
- Karaka roles → 16 nodes (8 Chara + 8 Sthira)
- Divisional placements of interest → ~50-80 nodes
- Dasha lords (across all 3 systems lifetime) → ~30 nodes
- Sensitive points → ~20 nodes
- Arudhas, Upagrahas, Sahams, Special Lagnas → ~30 nodes
- **Total: ~200-220 nodes**

**Edges** — systematic enumeration:
- Dispositorship: 9 planets × (sign-lord ≈ 1) = 9 edges
- Vedic aspects: ~20-30 significant edges (above strength threshold)
- Ownership: 7 planets × houses owned = ~15 edges
- Exaltation-affinity: signals planets' relationships to exaltation/debility signs
- Nakshatra-lordship: nakshatra-to-lord edges
- Karaka representation: karaka-role-to-planet edges
- Divisional confirmation: D1-house ↔ Dx-house edges where they align
- Combustion, planetary war: actual conjunctions below threshold
- Kakshya rulership: Saturn-related edges
- Saham composition: saham-point-to-component-planet edges
- Yoga membership: yoga-to-member-planets edges
- Dasha-lord activation: MD/AD lord ↔ represented-significations edges
- **Total: ~800-1,200 edges**

**Edge weights**: computed formula (to be specified in CGM_v1_0.md) drawing from Shadbala, Ashtakavarga, Vimsopaka, Bhavabala, dignity multipliers.

**Subgraphs**: 9 pre-computed domain-filtered views (career-subgraph, wealth-subgraph, etc.) — subgraph-of-career = nodes/edges where domain attribute includes "career".

**G.4.B — Master Signal Register Build**

Target 500-600 signals. Build by systematic traversal:

- For each classical system (Parashari, Jaimini, KP, Tajika, Nakshatra, Panchang, Sade Sati, Sensitive Points, Divisional-chart-specific, Transit): enumerate all detectable signals
- For each signal, fill the full schema (§C.3.2)
- Log which RPT section (if any) goes deep on it

**Systematic vs curated**: this is the critical methodological commitment. v1.2.1's 15 SIG entries were curated-by-importance. MSR's 500-600 are enumerated-by-system. Both coexist — MSR provides coverage, SIG provides priority signaling.

**G.4.C — Cross-Domain Linkage Matrix Build**

9 domains × 9 domains = 81 cells (or 36 unique if symmetric). For each cell:
- Query CGM for nodes with both domains in attributes
- Query MSR for signals with both domains in `domains_affected`
- Compute linkage strength (0-1) by weighted formula
- Identify key cross-domain yogas (yogas whose signification spans both)
- Write 1-paragraph interpretive note

**G.4.D — Resonance Map Build**

Identify ~30-50 major chart elements (high-centrality CGM nodes + distinctive Mode B matrix rows + RPT subjects). For each:
- Traverse CGM to find amplifying connections (constructive resonance)
- Traverse CGM to find dampening connections (destructive resonance)
- Write structured YAML entry with element, constructive list, destructive list, interpretive note

**G.4.E — Unified Chart Narrative Build**

30-50K words, 10 Parts (structure in §C.3.5). Build sequence:
1. Skeleton pass (outline per Part with key claims identified)
2. First draft per Part (sourcing from CGM, MSR, CDLM, RM, Mode A RPT, Mode B matrices)
3. Integration pass (ensure cross-Part references; nothing isolated)
4. Red-team pass (traceability, contradiction, over-claim checks)
5. Prose polish pass (readability)
6. Final closure

**UCN output is the single most important L2.5 asset** — Domain Reports will cite it constantly.

### G.5–G.9 — Remaining workstreams

(Unchanged from v1.0.)

---

## §H — QUALITY STANDARDS (v2.0 EXPANDED)

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

Every query answer must follow this protocol:

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

## §I — EXECUTION SEQUENCE (v2.0 REVISED — 6 PHASES, 38-42 SESSIONS)

### Phase 1 — Foundation (Sessions 1-6)

- **Session 1** (done): Architecture Blueprint v1.0 ✓
- **Session 1b** (done): Architecture Blueprint v2.0 (this session) ✓
- **Session 2**: Life Event Log v1.0 elicitation (25-40 events)
- **Session 3**: Facts Layer v7.0 gap analysis + External Computation Spec
- **Session 4**: Life Event Log retrodictive tagging + initial Pattern Library seed
- **Session 5**: Facts Layer v7.0 build (with external inputs if procured)
- **Session 6**: **CGP audit execution + v7.0 signoff** ← gate before L2 work proceeds

### Phase 2A — Holistic Foundation (Sessions 7-13) — NEW IN v2.0

- **Session 7-8**: L2 Mode B matrix build — House Matrix + Planet Matrix
- **Session 9**: L2 Mode B matrix build — Sign Matrix + Divisional Matrix
- **Session 10**: L2 Mode B matrix build — Dasha-Period Matrix
- **Session 11**: L2.5 CGM build (Chart Graph Model)
- **Session 12**: L2.5 MSR build (Master Signal Register, batch 1: ~300 signals)
- **Session 13**: L2.5 MSR build (batch 2: remaining 200-300 signals) + CDLM + RM

### Phase 2B — Unified Narrative (Sessions 14-17) — NEW IN v2.0

- **Session 14**: UCN Parts I-III draft (Architecture, Soul, Mind-Body)
- **Session 15**: UCN Parts IV-VI draft (Dharmic-Material, Relational, Foreign/Moksha)
- **Session 16**: UCN Parts VII-X draft (Authority-Through-Tension, Timing, Contradictions, Operating Instructions)
- **Session 17**: UCN integration pass + red-team + closure

### Phase 3 — Deep Analysis v2.0 (Sessions 18-24)

- **Session 18-20**: Mode A new RPT sections batch A (STR.02, HSE.03-04, DVS.03-06)
- **Session 21-23**: Mode A new RPT sections batch B (DSH.03-04, TRN.05, SBL.01, AVG.01, NDS.01, PCG.01, HRY.01, JMN.01, LFE.01)
- **Session 24**: Deep Analysis v2.0 red-team + closure

### Phase 4 — Domain Reports (Sessions 25-34)

(All Domain Reports now cite UCN as parent.)
- **Session 25**: Refresh FINANCIAL v1.0 → v2.0 (now with UCN parent)
- **Session 26-33**: CAREER, HEALTH, RELATIONSHIPS, CHILDREN, SPIRITUAL, PARENTS, PSYCHOLOGY, TRAVEL (1 session each)
- **Session 34**: Cross-report coherence audit against UCN

### Phase 5 — Remedial + Temporal (Sessions 35-38)

- **Session 35-36**: Remedial Codex v1.0
- **Session 37**: Lifetime Timeline (built on Dasha-Period Matrix)
- **Session 38**: Heatmap refresh + Varshphal 2026-27 and 2027-28

### Phase 6 — Query Interface + Governance (Sessions 39-42)

- **Session 39**: Query Prompt Library v1.0 (with Whole-Chart-Read enforcement)
- **Session 40**: Session Protocol + Question Taxonomy
- **Session 41**: Governance Stack v1.0
- **Session 42**: Project-wide Red-Team + External Acharya Review invitation

### Phase 7 — Living Project (ongoing)

- Quarterly: Heatmap refresh
- Annually: Varshphal refresh, Life Event Log bump, MSR review, UCN refresh-check
- As needed: decision-support sessions, domain-report refreshes on life-change triggers

**Realism note**: 42 sessions nominal; actual likely 38-50 depending on depth. Every session produces a versioned, standalone artifact.

---

## §J — KEY DECISIONS (RESOLVED 2026-04-17 — v2.1 UPDATE)

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

## §K — BLUEPRINT META (v2.1)

```yaml
blueprint_id: PROJECT_ARCHITECTURE_v2_1
status: APPROVED — all §J decisions resolved; Session 2 ready to begin
supersedes: PROJECT_ARCHITECTURE_v2_0 (2026-04-17 earlier) and v1_0 (archived)
total_sections: 11 major (§A-§K)
total_layers: 5 (L1, L2, L2.5 NEW, L3, L4)
total_workstreams_defined: 9
total_domain_reports_planned: 9
total_sessions_planned_phases_1_through_6: 42
session_cadence: DAILY (across all phases; compensating discipline enforced)
estimated_calendar_completion: ~6-7 weeks to Phase 6
execution_start: Session 2 — Life Event Log v1.0 elicitation
living_document: YES

resolved_decisions:
  J1_cadence: daily across all phases (with compensating discipline)
  J2_external_software: Jagannatha Hora (free, open source)
  J3_privacy_boundaries: none
  J4_audience_ceiling: none (publication-grade standard)
  J5_goal_recalibration: chart-first reveal; on-demand goal-calibration post-reveal

relationship_to_existing_assets:
  v6.0_forensic_data: archived as source; upgraded to v7.0 with CGP audit
  v1.2.1_deep_analysis: archived as source; upgraded to v2.0 dual-mode
  v1.0_financial_report: refreshed to v2.0 after UCN and Deep Analysis v2.0 (existing §6.5 Goal Calibration preserved)

new_layer_L25_deliverables:
  CGM: Chart Graph Model (~200 nodes, ~800-1200 edges)
  MSR: Master Signal Register (500-600 signals)
  CDLM: Cross-Domain Linkage Matrix (81 cells)
  RM: Resonance Map (~30-50 major elements)
  UCN: Unified Chart Narrative (30-50K words)

concern_resolution:
  concern_1_domain_context_collapse:
    raised_by: native
    date: 2026-04-17
    resolution: L2.5 Holistic Synthesis Layer with UCN as mother document; query routing B.11
  concern_2_completeness_rigor:
    raised_by: native
    date: 2026-04-17
    resolution: CGP at L1; Mode B Exhaustive Matrices at L2; refusal protocol B.12

ambition_tier_selected:
  signal_register: Maximum (500-600)
  unified_chart_narrative_timing: Early (before Domain Reports)
  scope_expansion_accepted: +8-12 sessions (total 38-42)
  cadence_aggression: Maximum (daily across all phases)

daily_cadence_compensating_discipline:
  - every_session_produces_closed_versioned_artifact
  - every_third_session_light_red_team_on_prior_two
  - reflection_flag_protocol_when_material_warrants_pause
  - proactive_context_window_management_across_sessions

protection_clauses:
  - No fabricated chart computations
  - No overstated predictions
  - No generic astrology (always chart-specific)
  - No collapse of B.1 facts/derivation/interpretation separation
  - No abandonment of red-team discipline
  - No project drift without explicit version bump
  - No domain-siloed query answers (B.11)
  - No interpretation against incomplete L1 cells (B.12)

changelog:
  v1.0 (2026-04-17 early): initial blueprint approved by native
  v2.0 (2026-04-17 mid): inserted L2.5 Holistic Synthesis; added CGP at L1; added Mode B at L2;
                         revised query routing; enforced whole-chart-read discipline; scope expanded
                         to 42 sessions; MSR target 500-600; UCN timing early
  v2.1 (2026-04-17 late): all §J decisions resolved; daily cadence locked with compensating discipline;
                          Jagannatha Hora procurement confirmed; no privacy/audience boundaries;
                          chart-first reveal approach for Domain Reports; ready for Session 2
```

---

**END OF MASTER ARCHITECTURE BLUEPRINT v2.1**

*This document governs all subsequent work on the Abhisek Mohanty Jyotish Intelligence System.*
*Load this file FIRST in any future Claude session. Reference §D for workstream scope,
§F for ID conventions, §G for detailed specs, §H.4 for Whole-Chart-Read Protocol,
§I for current execution position, §J for resolved decisions.*

*v2.1 closes the architecture phase. Session 2 begins execution (Life Event Log elicitation).
Any future concern that reveals a structural gap should trigger a v3.0 rebuild, not a patch.*
