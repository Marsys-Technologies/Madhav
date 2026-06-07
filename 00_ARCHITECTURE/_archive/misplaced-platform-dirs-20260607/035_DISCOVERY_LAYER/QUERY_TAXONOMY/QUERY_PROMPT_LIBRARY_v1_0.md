---
artifact: QUERY_PROMPT_LIBRARY_v1_0.md
version: 1.0
status: CLOSED
session: 33
date_closed: 2026-04-18
scope: "Library of query prompts for L4 Query Interface — enforces Whole-Chart-Read Protocol (Architecture §H.4)"
architecture_ref: "§G.8 Query Interface"
---

# QUERY_PROMPT_LIBRARY_v1_0
## Abhisek Mohanty Jyotish Intelligence System
### Session 33 | 2026-04-18 | CLOSED

---

## §1 — PURPOSE

L4 Query Interface serves ad-hoc questions from the native. Every query must route through the Whole-Chart-Read Protocol (UCN_v1_1) BEFORE accessing domain-specific content, to prevent context-collapse (the problem that domain-segregated reading produces misleading answers by missing the chart's integrated architecture).

This library provides query-type templates that enforce the protocol.

---

## §2 — PROTOCOL ENFORCEMENT

Every query must include these Phase 1 steps:
1. Read UCN_v1_1 relevant Part(s)
2. Check relevant CDLM row for cross-domain implications
3. Check relevant MSR signals
4. THEN consult Domain Report(s) for focused analysis
5. Integrate whole-chart and focused readings before answering

---

## §3 — QUERY TEMPLATES BY TYPE

### §3.1 — Decision-Support Query

**Template**: "Should I make decision X?"

**Example**: "Should I accept this new role at Company Y?"

**Process**:
1. UCN routing: Career relevant → UCN §IV (Dharmic-Material Engine) + §VIII (Timing Metaphysics)
2. CDLM check: D1 row (Career) primary; D8 (Mind), D2 (Wealth) linkages; D3 (Relationships if role affects)
3. MSR check: MSR.413 (Mercury primary instrument); MSR.396 (ATT/Sade Sati reliability)
4. Domain Reports: REPORT_CAREER_DHARMA (primary), REPORT_FINANCIAL (compensation), REPORT_PSYCHOLOGY (mind impact)
5. Integration: Does the decision align with Mercury-deployment architecture? Does it pass the wealth-as-dharmic-output principle? Does it fit the current Saturn AD institutionalization phase?

**Output format**: Structural assessment (aligns/partially aligns/conflicts with chart architecture); key trade-offs; specific questions for the native to self-answer.

### §3.2 — Timing Query

**Template**: "When should I do X?"

**Example**: "When should I launch the new product line?"

**Process**:
1. UCN routing: §VIII (Timing Metaphysics)
2. Dasha context: Mercury MD / Saturn AD current; key transitions named
3. Heatmap check: 36-month heatmap for the relevant quarter
4. Panchang muhurta: Shubha day/tithi for the specific action-type
5. BB/special-point activations in the window

**Output format**: Optimal window range; second-best alternatives; windows to avoid; specific muhurta guidance if relevant.

### §3.3 — Relational Assessment Query

**Template**: "How should I think about relationship with person X?"

**Example**: "Is this partnership healthy / how should I navigate this conflict?"

**Process**:
1. UCN routing: §V (Relational Web) + §VII (ATT pattern)
2. CDLM: D3 row + relevant cross-domains (D1 if professional partnership)
3. MSR: MSR.391 (7H convergence); MSR.396 (ATT)
4. Report: REPORT_RELATIONSHIPS primary

**Output format**: Architectural characterization of the relationship-type; where productive tension (ATT) vs. destructive tension distinction lies; recommended behavioral posture.

### §3.4 — Health Query

**Template**: "Should I be concerned about health-signal X?"

**Process**:
1. UCN routing: §III (Mind-Body)
2. Constitutional review: Pitta-Vata, Mercury 6L
3. Current window: 36-month heatmap health-risk windows
4. Report: REPORT_HEALTH_LONGEVITY

**Output format**: Constitutional context; whether signal fits known patterns (Vata-leading-indicator from 2021); recommended investigation; clinical-professional consultation flag if warranted.

### §3.5 — Career-Strategic Query

**Template**: "What's the right career move for the next 2-5 years?"

**Process**:
1. UCN routing: §IV + §VIII
2. Current dasha context + upcoming transitions
3. Report: REPORT_CAREER_DHARMA + REPORT_FINANCIAL

**Output format**: Phase-specific recommendations (current Mercury MD institutionalization vs. pre-Ketu MD preparation); what the chart says about next-phase optimal deployment.

### §3.6 — Spiritual Practice Query

**Template**: "What should my practice look like right now?"

**Process**:
1. UCN routing: §VI (Foreign/Moksha) + §X (Operating Instructions)
2. Current dasha: where in the Mercury MD → Ketu MD arc?
3. Codex: REMEDIAL_CODEX_v1_0 Parts 1-2
4. Report: REPORT_SPIRITUAL

**Output format**: Practice calibration for current phase; upcoming transitions (Ketu AD depth-prep); Venkateshwara-alignment practices.

### §3.7 — Meta-Query / Existential Query

**Template**: "What is this chart asking me to become?"

**Process**: Pure UCN-level query — UCN §X (Operating Instructions) is the primary answer. No domain-specific needed unless specific operational guidance requested.

**Output format**: UCN's Chart's Central Request articulation + current-phase expression.

---

## §4 — ANTI-PATTERNS TO AVOID

Queries that bypass the Whole-Chart-Read protocol are high-risk:

1. **"Just answer the question"**: A request to skip UCN routing. Produces context-collapsed answers. Always reroute through the protocol.
2. **"Will X happen?"**: Prediction requests beyond the scope of chart-as-architecture. The chart reveals structure, not predetermined outcomes. Reframe as "How should I navigate X?"
3. **"Is X a good planet/bad planet?"**: Decontextualized planetary-rating queries. Planets are never good/bad in isolation; they function within architecture. Reframe as "How does planet X function in my chart architecture?"
4. **"What's my yoga?"**: Yoga-stamp-collecting queries. Yogas function through dasha activation and chart-architecture. Reframe as "What does yoga X mean in my chart's overall architecture?"
5. **"Should I do remedy X for planet Y?"**: Remedy-without-context queries. Per Remedial Codex, most classical planet-remedies misread this chart. Route through REMEDIAL_CODEX_v1_0 before prescribing.

---

## §5 — CONFIDENCE DECLARATION PROTOCOL

Every answer must include:
- Confidence level (0.00-1.00)
- Sources cited (UCN §, MSR.IDs, Domain Report §)
- Known gaps affecting the answer
- Falsifier (what would make this answer wrong)

---

*End of QUERY_PROMPT_LIBRARY_v1_0.md — Session 33 — 2026-04-18 — CLOSED*
