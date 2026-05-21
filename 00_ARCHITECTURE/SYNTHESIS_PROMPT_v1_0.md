---
artifact: SYNTHESIS_PROMPT_v1_0
title: "MARSYS-JIS Synthesis Prompt Governance"
version: 1.0
status: CURRENT
created_date: 2026-05-04
session_id: GANGA-P3-R1-S1
canonical_id: SYNTHESIS_PROMPT
closes_gap: GAP.013
---

# SYNTHESIS_PROMPT — Synthesis LLM Governance Specification

## §1 — Purpose and scope

This document governs the system prompt given to the synthesis LLM at query time within the MARSYS-JIS pipeline. It specifies:

- What knowledge layers the synthesis LLM must see before producing any answer (B.11 mandate)
- How the system prompt is structured, versioned, and evaluated
- What constraints the synthesis LLM must obey (B.10, B.3, disclosure tier)
- The eval criteria the answer eval harness (Session 6) will score against

**Scope boundary:** This document covers the synthesis stage only — the final answer generation call to the LLM. It does not govern the planner, retrieval, or context assembly stages. Those stages are governed by their own modules (`manifest_planner.ts`, `context_assembler.ts`).

**Closes:** GAP.013 — zero synthesis governance (no specification existed for what the synthesis LLM must do or what it must be given before it answers).

---

## §2 — B.11 Whole-Chart-Read Protocol (MANDATORY)

### 2.1 The mandate

**Every synthesis call MUST have traversed MSR + UCN + CDLM + CGM + RM before the synthesis LLM is invoked.** This is Architectural Principle B.11 from `PROJECT_ARCHITECTURE_v2_2.md §B`.

B.11 exists because pattern recognition in Jyotish is inherently cross-domain. A signal that appears weak or irrelevant in isolation often becomes the operative trigger when viewed alongside a signal from a different domain. Relevance filtering before synthesis creates the risk of "missing the secret source" — the one signal that unlocks the chart.

### 2.2 Operational definition of "traversed"

A synthesis call satisfies B.11 if and only if the assembled context payload contains retrievable content from **at minimum** MSR, UCN, and CGM. Full compliance includes all five L2.5 artifacts:

| Artifact | Canonical ID | Minimum requirement | Full compliance |
|---|---|---|---|
| Master Signal Register | MSR | ✅ Required | ✅ |
| Unified Chart Narrative | UCN | ✅ Required | ✅ |
| Cross-Domain Linkage Matrix | CDLM | Recommended | ✅ |
| Causal Graph Model | CGM | ✅ Required | ✅ |
| Resonance Map | RM | Recommended | ✅ |

"Retrievable content" means: the assembled context string contains recognizable references to the artifact's canonical ID or its full name (e.g., "MSR", "Master Signal Register", "025_HOLISTIC_SYNTHESIS/MSR").

### 2.3 Runtime guard

The B.11 runtime guard is implemented in `platform/src/lib/synthesis/b11_guard.ts` (Session 7). The guard:

1. Receives the assembled context payload as input
2. Scans for presence of each L2.5 artifact's canonical markers
3. Returns a `B11CheckResult` with `compliant: boolean`, `missingLayers: string[]`, and `annotation: string | null`
4. If `compliant === false`:
   - Emits a structured warning log: `{ event: 'B11_VIOLATION', missing: [...], queryId }`
   - Prepends `[B.11-PARTIAL: missing X, Y]` to the synthesis system prompt context if retrieval of missing layers cannot be triggered synchronously

**Zero overhead in the happy path** — the guard is a string scan with no database or network calls.

### 2.4 What the synthesis LLM must do in response to B.11

The system prompt (§4) encodes B.11 as a behavior instruction: the synthesis LLM must explicitly draw on signals from each present L2.5 artifact when forming its answer. An answer that cites only one artifact is non-compliant even if the context contained all five. The eval harness (§6) scores this as `b11_signal`.

---

## §3 — Layer traversal mandate

Every synthesis call must assemble context in this order before invoking the synthesis LLM:

```
L1 (Facts) → L2.5 (Holistic Synthesis) → L3 (Query-Specific Retrieval)
```

### 3.1 L1 — Chart Facts (FORENSIC)

Source: `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`

The L1 layer is the foundation. It contains only verified, numerically-computed facts about the native's chart (planetary positions, house cusps, divisional chart data, dasha sequences). The synthesis LLM must treat L1 values as read-only ground truth — it must never modify, re-derive, or contradict them.

**Minimum token allocation:** ~2,000 tokens of the most query-relevant L1 data. The context assembler (Session 8) handles selection.

### 3.2 L2.5 — Holistic Synthesis (MSR + UCN + CDLM + CGM + RM)

Source: `025_HOLISTIC_SYNTHESIS/`

The L2.5 layer is the core. It contains cross-domain synthesis work: 499 signals (MSR), a unified narrative (UCN), cross-domain linkages (CDLM), causal relationships (CGM), and resonance patterns (RM). Together these represent the accumulated analytical work on the native's chart — work that cannot be reproduced from L1 alone without losing cross-domain signal relationships.

**Minimum token allocation:** ~8,000 tokens across the five artifacts. Full-corpus Whole-Chart-Read is ~300K tokens; the context assembler allocates budget per query type.

### 3.3 L3 — Query-Specific Retrieval

Source: Pipeline tool results from retrieval tools (msr_sql, cgm_graph_walk, vector_search, etc.)

The L3 layer contains the results of query-specific tool calls. It is assembled after L2.5 to ensure the synthesis LLM sees the holistic context before it sees the targeted retrieval. This ordering prevents the synthesis LLM from "anchoring" on one tool's result before considering the broader chart picture.

**Minimum token allocation:** ~2,000 tokens of the most relevant tool results.

---

## §4 — Synthesis prompt template specification

### 4.1 System prompt structure

The synthesis system prompt has four required sections in this order:

```
[SECTION 1: ROLE + DISCIPLINE]
[SECTION 2: KNOWLEDGE LAYER ACCESS]
[SECTION 3: OUTPUT REQUIREMENTS]
[SECTION 4: CONSTRAINT DECLARATIONS]
```

### 4.2 Section 1 — Role and discipline

The synthesis LLM is addressed as an acharya-grade Jyotish instrument, not a general assistant. The role declaration establishes:

- Identity: "You are MARSYS-JIS, a Jyotish instrument operating at acharya grade."
- Quality standard: "Your analysis must be at the level where an independent senior Jyotish acharya reviewing it would say: 'this is my own level', 'this is above my own level', or 'this reveals things I wouldn't have seen on first pass'."
- Scope: "You operate on a specific native: Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar, Odisha, India. All analysis applies to this native only."

### 4.3 Section 2 — Knowledge layer access

The system prompt declares which layers are present in the context and how the LLM should use them:

```
KNOWLEDGE LAYERS AVAILABLE:
- L1 (FORENSIC): Chart facts — treat as read-only ground truth. Never contradict these values.
- L2.5 (HOLISTIC SYNTHESIS): {list present artifacts}. Draw on ALL present artifacts when forming your answer.
- L3 (RETRIEVAL): Query-specific tool results. Use these as the primary evidence base, interpreted through the L2.5 lens.

B.11 MANDATE: Your answer must demonstrate engagement with signals from at least MSR, UCN, and CGM. An answer that draws only from L3 retrieval without engaging L2.5 holistic context is non-compliant.
```

If a `[B.11-PARTIAL]` annotation is present, the system prompt additionally declares:
```
B.11 PARTIAL: {annotation}. Proceed with available layers; note the limitation in your answer.
```

### 4.4 Section 3 — Output requirements

```
OUTPUT REQUIREMENTS:
1. CITATION DISCIPLINE (B.3): Every interpretive claim must cite the specific L1 fact ID or L2.5 signal ID it draws on. Format: (→ MSR-signal-042) or (→ FORENSIC §3.2). Claims without citations are non-compliant.
2. CALIBRATION LANGUAGE: Use probabilistic framing. Say "this placement suggests", "the pattern indicates", "this is likely to manifest as". Do not use oracular language: "this will happen", "you will definitely", "this is certain".
3. DERIVATION TRAIL: When synthesizing across multiple signals, state which signals you are combining and why.
4. DISCLOSURE TIER: {tier}. Adjust depth and technical vocabulary accordingly.
5. WHOLE-CHART AWARENESS: Before answering the specific query, briefly note any cross-domain tensions or amplifications relevant to the question. This is the B.11 cross-domain check.
```

### 4.5 Section 4 — Constraint declarations

```
HARD CONSTRAINTS (B.10):
- Never compute or assert astrological values not present in L1. If the user asks for a value not in L1, respond with [EXTERNAL_COMPUTATION_REQUIRED: {what needs to be computed, with exact specification}].
- Never modify, re-derive, or contradict L1 fact values.
- Never assert that astrological patterns "will" produce specific outcomes with certainty — Jyotish identifies tendencies and timing windows, not deterministic fate.
- Do not produce generic astrology. Your answer must be specific to this native's chart using the L1/L2.5 data in context.
```

---

## §5 — Prompt versioning protocol

### 5.1 Version scheme

Synthesis prompts are versioned as `SYNTHESIS_PROMPT_v{major}.{minor}`:

- **Major bump** (e.g., v1.0 → v2.0): Structural changes to layer traversal mandate, B.11 enforcement logic, or output requirement schema. Requires eval harness run before shipping to production.
- **Minor bump** (e.g., v1.0 → v1.1): Wording improvements, few-shot example updates, or section reordering without semantic change. Requires review but not a full eval run.

### 5.2 Eval gate

No major version bump ships to production without:
1. Running the eval harness (Session 6) on a representative sample (minimum 15 golden queries)
2. Achieving pass rate ≥ 80% on the five criteria in §6
3. Storing the eval results with the version bump commit

### 5.3 Backward compatibility

The prompt template in §4 defines the minimum structure. Implementations may add query-class-specific sections (e.g., additional instructions for predictive vs. factual queries) as minor additions, provided the four required sections remain intact.

---

## §6 — Evaluation criteria

The eval harness (Session 6, `platform/scripts/answer_eval.ts`) scores each synthesis answer against these five criteria. Each criterion scores 0–1 and is reported as a percentage. A query PASSES if all five criteria score ≥ 0.6.

### 6.1 `layer_coverage` (0–1)

**Question:** Does the response demonstrate engagement with the expected L2.5 layers?

**Method:** Scan the response text for explicit references to each expected artifact (by canonical ID or full name). Score = (referenced layers) / (expected layers). A holistic query expects all five; a factual query expects at minimum MSR and L1 FORENSIC.

**Threshold:** ≥ 0.6 (at least 60% of expected layers referenced).

### 6.2 `b10_compliance` (0–1)

**Question:** Does the response avoid fabricating astrological numerical values?

**Method:** Detect `[EXTERNAL_COMPUTATION_REQUIRED]` markers when the query asks for derived values. Penalize naked numerical claims about planetary positions or degrees that are not present in L1 FORENSIC data. Score = 1.0 if no violations; 0.0 if fabricated values detected.

**Threshold:** ≥ 0.9 (near-zero tolerance for fabrication).

### 6.3 `b11_signal` (0–1)

**Question:** Does the response show evidence of holistic synthesis — cross-layer signal integration?

**Method:** Score presence of:
- At least one cross-domain connection ("this signal from MSR combines with CGM pattern X to suggest…")
- References to multiple L2.5 artifacts in the same interpretive chain
- Acknowledgment of cross-domain tensions or amplifications

**Threshold:** ≥ 0.5 for non-holistic queries; ≥ 0.7 for holistic/discovery queries.

### 6.4 `citation_presence` (0–1)

**Question:** Does the response meet the minimum citation count for the query type?

**Method:** Count citations in the format `(→ ...)`. Score = min(actual_citations, expected_citations) / expected_citations. Expected counts vary by query category (factual: 2+, interpretive: 3+, holistic: 5+, predictive: 3+, discovery: 4+).

**Threshold:** ≥ 0.6.

### 6.5 `calibration_language` (0–1)

**Question:** Does the response use probabilistic framing rather than oracular language?

**Method:** Scan for:
- Probabilistic markers: "suggests", "indicates", "may", "likely", "tends to", "pattern of" → positive
- Oracular markers: "will happen", "definitely", "certainly", "guaranteed to" → negative

Score = (probabilistic_count) / (probabilistic_count + oracular_count + 1). The +1 prevents division by zero and biases toward 0.5 on empty responses.

**Threshold:** ≥ 0.7.

### 6.6 Aggregate pass threshold

A synthesis answer PASSES the eval if:
- `b10_compliance` ≥ 0.9 AND
- At least 3 of the remaining 4 criteria ≥ their individual thresholds

---

## §7 — Known gaps and open items

### 7.1 This document closes

- **GAP.013**: Zero synthesis governance. Before this document, there was no specification for what the synthesis LLM must do, what layers it must be given, or what a compliant answer looks like.

### 7.2 What still needs wiring in code

- **B.11 runtime guard** (GAP.015): Implemented in Session 7 (`platform/src/lib/synthesis/b11_guard.ts`). Wired into `single_model_strategy.ts` to check compliance before synthesis call.
- **Context assembler** (GAP.016): Implemented in Session 8 (`platform/src/lib/synthesis/context_assembler.ts`). Replaces ad-hoc context assembly in `single_model_strategy.ts` with token-budgeted L1/L2.5/L3 packing.
- **Answer eval harness** (GAP.014): Implemented in Session 6 (`platform/scripts/answer_eval.ts` + `platform/scripts/golden_queries.ts`). Scores against §6 criteria.
- **Calibration substrate** (L.5): Prediction registration, outcome capture, Brier score — deferred to P3-R3-S1. Out of scope for this document.

### 7.3 Query-class-specific prompt variants

The §4 template is the base. Query-class-specific variants (predictive, dasha, transit, holistic discovery) will be specified in `SYNTHESIS_PROMPT_v1_1.md` after the Session 6 eval harness establishes a baseline score. Do not author variants before the baseline is captured — variants should be measurable improvements over a known baseline.

---

## §8 — Changelog

| Version | Date | Session | Change |
|---|---|---|---|
| 1.0 | 2026-05-04 | GANGA-P3-R1-S1 | Initial specification — closes GAP.013. Specifies B.11 protocol, layer traversal mandate, synthesis prompt template §4, eval criteria §6, versioning protocol §5. |
