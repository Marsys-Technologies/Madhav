---
artifact: plans_v1_0.md
version: 1.0
status: CURRENT
session: Madhav_M2A_Exec_13
date_authored: 2026-04-27
scope: "QueryPlan type taxonomy for the MARSYS-JIS router (B.7). Governs how classify_query() classifies natural-language queries and how downstream components consume the plan."
references:
  - "PHASE_B_PLAN_v1_0.md §B.7"
  - "035_DISCOVERY_LAYER/QUERY_TAXONOMY/SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md"
  - "035_DISCOVERY_LAYER/QUERY_TAXONOMY/QUERY_PROMPT_LIBRARY_v1_0.md"
  - "035_DISCOVERY_LAYER/QUERY_TAXONOMY/DECISION_SUPPORT_PLAYBOOK_v1_0.md"
---

# plans_v1_0 — QueryPlan Type Taxonomy
## MARSYS-JIS Discovery Layer — B.7 Router + Plan Library
### Session Madhav_M2A_Exec_13 | 2026-04-27

---

## §1 — Purpose

This document defines the five primary QueryPlan types emitted by the MARSYS-JIS router, plus one static fallback type. It is the authoritative taxonomy reference for:

- `router.py` → `classify_query()` — uses `router_v1_0.md` prompt, which embeds this taxonomy
- `schemas.py` → `QueryPlan.plan_type` Literal — must list all 6 values
- Downstream retriever, synthesizer, and portal — consume `plan_type` and `wcr_forced` to determine retrieval strategy

The taxonomy maps onto the Session Protocol Question Taxonomy (`SESSION_PROTOCOL_QUESTION_TAXONOMY_v1_0.md`) category A–G classification scheme, but is coarser-grained and machine-executable rather than human-instructional.

---

## §2 — The Five Primary Plan Types

### §2.1 — `interpretive_multidomain`

| Field | Value |
|---|---|
| Routing trigger | Query spans ≥2 chart domains; requires synthesis of cross-domain signals |
| WCR required | **Yes** — auto-include ≥1 UCN chunk via `mode="auto"` |
| Significance range | 0.70–1.0 |
| Typical domains | 2–4 from: career, wealth, relationships, health, spirituality, timing, psychology |
| Opus decision criteria | Query explicitly references multiple life-domains, or chart signals that span domains (e.g., a yoga that simultaneously affects career + relationships), or asks for integrated architectural framing |

**Architectural rationale.** This class directly enforces Architecture Principle B.11 (Whole-Chart-Read discipline). A domain-siloed answer to a multi-domain question produces context-collapse — the most architecturally dangerous failure mode. `wcr_forced=True` on these queries is non-negotiable.

**Correspondence.** SESSION_PROTOCOL Category B (Decision-Support), Category E (Meta/Existential), QUERY_PROMPT_LIBRARY §3.1 (Decision-Support), §3.5 (Career-Strategic when cross-domain); DECISION_SUPPORT_PLAYBOOK §2.1–§2.7 decision templates.

**Examples from the corpus:**

*Example 1.* "What does Saturn's exaltation in the 7H Libra mean for Abhisek's marriage and partnerships — considering both the Sasha Mahapurusha Yoga and the 7H Bhavabala rank-12 structural weakness?"
→ domains: `["relationships", "career", "wealth"]`; wcr_forced: true; significance: 0.90

*Example 2.* "How does the Mercury Pentagram's five-planet integration affect Abhisek's readiness for the Ketu MD transition in 2031?"
→ domains: `["career", "spirituality", "timing", "psychology"]`; wcr_forced: true; significance: 0.95

---

### §2.2 — `interpretive_single`

| Field | Value |
|---|---|
| Routing trigger | Query is domain-specific but requires chart-layer depth (cannot be answered from surface keywords) |
| WCR required | **Yes** — auto-include ≥1 UCN chunk via `mode="auto"` |
| Significance range | 0.45–0.85 |
| Typical domains | Single domain: career, or relationships, or health, etc. |
| Opus decision criteria | Query is clearly about one domain, but the domain requires UCN/MSR context to answer correctly — e.g., a health query that activates 6H lords and must check Vata constitution, or a spirituality query that requires Chart's Central Request framing |

**Architectural rationale.** Even single-domain queries in this chart require the UCN frame because the planets are structurally interlinked (Mercury Pentagram). An isolated domain answer without the UCN anchor misreads signals. WCR is mandatory for these to prevent the "accurate but misleading" failure.

**Correspondence.** SESSION_PROTOCOL Category A (Structural), Category D (Assessment); QUERY_PROMPT_LIBRARY §3.3 (Relational), §3.4 (Health), §3.6 (Spiritual).

**Examples from the corpus:**

*Example 3.* "What is the Jyotish basis for Abhisek's recurring cognitive-overload pattern? Cite specific chart signals."
→ domains: `["health", "psychology"]`; wcr_forced: true; significance: 0.75

*Example 4.* "What does the 12H Pisces empty house say about Abhisek's spiritual practice orientation?"
→ domains: `["spirituality"]`; wcr_forced: true; significance: 0.65

---

### §2.3 — `factual`

| Field | Value |
|---|---|
| Routing trigger | Query requests a specific named fact: planet degree, house lord, dasha date, yoga name, MSR signal ID |
| WCR required | No — factual lookup does not require UCN anchor |
| Significance range | 0.20–0.55 |
| Typical domains | Usually 1, often just `["chart_facts"]` |
| Opus decision criteria | The query is fully answerable from a single L1 or L2 lookup without synthesis; no interpretive claim is being made |

**Correspondence.** SESSION_PROTOCOL Category F (Meta-Methodological / Clarification); QUERY_PROMPT_LIBRARY §5 (Confidence Protocol for narrow queries).

**Examples from the corpus:**

*Example 5.* "What is Saturn's exact degree in Abhisek's D1 chart?"
→ domains: `["chart_facts"]`; wcr_forced: false; significance: 0.30

*Example 6.* "What is MSR signal MSR.413 and which chart factors does it cite?"
→ domains: `["chart_facts"]`; wcr_forced: false; significance: 0.25

---

### §2.4 — `timing`

| Field | Value |
|---|---|
| Routing trigger | Query contains prediction language or asks about dasha windows, event timing, "when will", "what period" |
| WCR required | No (but retrieve may benefit from UCN chunks if timing query is domain-complex) |
| Significance range | 0.60–0.95 |
| Typical domains | `["timing"]` always; may add 1–2 domain qualifiers |
| Opus decision criteria | The primary focus is time-indexing: when does a pattern activate, what dasha/antardasha window is relevant, what is the heatmap state for a date range |

**Correspondence.** SESSION_PROTOCOL Category C (Timing); QUERY_PROMPT_LIBRARY §3.2 (Timing Query); DECISION_SUPPORT_PLAYBOOK §2.4 health intervention timing, §2.7 Venus AD family planning.

**Examples from the corpus:**

*Example 7.* "What are the key dasha transitions between now and 2031 that Abhisek should plan around?"
→ domains: `["timing"]`; wcr_forced: false; significance: 0.80

*Example 8.* "When does the BB-UL crystallization window peak and what does it mean for relationship decisions?"
→ domains: `["timing", "relationships"]`; wcr_forced: false; significance: 0.78

---

### §2.5 — `meta`

| Field | Value |
|---|---|
| Routing trigger | Query is about the instrument itself: methodology, how the system works, cross-session continuity, architecture explanation |
| WCR required | No |
| Significance range | 0.10–0.40 |
| Typical domains | `["meta"]` |
| Opus decision criteria | The query addresses the MARSYS-JIS system, its architecture, its derivation ledger logic, or how to use it — not chart content |

**Correspondence.** SESSION_PROTOCOL Category G (External / Non-Chart boundary); QUERY_PROMPT_LIBRARY §4 Anti-pattern F (Clarification/Meta).

**Examples from the corpus:**

*Example 9.* "Why does the system always consult UCN before answering domain questions? What is the Whole-Chart-Read Protocol?"
→ domains: `["meta"]`; wcr_forced: false; significance: 0.20

*Example 10.* "What confidence level does the system assign to its predictions and how is that calibrated?"
→ domains: `["meta"]`; wcr_forced: false; significance: 0.15

---

## §3 — Static Fallback Type: `exploratory`

`exploratory` is **not emitted by Opus**. It is emitted by `router.py` exclusively on API failure (any `anthropic` SDK exception or JSON parse error in the Opus response).

| Field | Fixed value |
|---|---|
| plan_type | `"exploratory"` |
| actor | `"static_fallback"` |
| significance_score | `0.5` |
| domains | `["all"]` |
| wcr_forced | `False` |
| routing_rationale | `""` (empty string) |

The presence of `exploratory` in a logged plan is a sentinel for an API outage routing event. Downstream components that see `plan_type="exploratory"` should apply conservative retrieval (default hybrid_rrf, k=10) and should surface a system note to the user if appropriate.

---

## §4 — Significance-Scoring Rubric

Opus assigns `significance_score` using additive rules with type-specific caps. This rubric is used verbatim in `router_v1_0.md` prompt.

**Additive components:**

| Component | Score delta |
|---|---|
| Base (any query) | 0.20 |
| Each additional chart domain beyond the first | +0.20 (cap at 1.0 total) |
| Timing / prediction language present ("when", "will", "dasha", "period", "window") | +0.15 |
| Contradiction or UCN-layer explicit reference (CTR, CVG, UCN, architecture, whole-chart) | +0.10 |

**Plan-type ceilings (applied after additive scoring):**

| plan_type | ceiling |
|---|---|
| `interpretive_multidomain` | 1.00 |
| `interpretive_single` | 0.85 |
| `timing` | 0.95 |
| `factual` | 0.55 |
| `meta` | 0.40 |
| `exploratory` | 0.50 (fixed, not computed) |

**Worked example.** Query: "How does the Venus-Jupiter mutual reception affect Abhisek's wealth and relationships when Saturn AD activates the 11H in 2025-2027?"
- Base: 0.20
- Additional domains: wealth + relationships = +0.20 (total 2 domains, 1 additional)
- Timing language ("when", "2025-2027", "AD"): +0.15
- Total raw: 0.55
- Plan type: `interpretive_multidomain` (spans wealth + relationships) → ceiling 1.00
- Final score: 0.55 (within range, no ceiling hit)

---

## §5 — WCR Enforcement Rule

After Opus classification, `router.py` applies a deterministic post-processing rule:

```python
if plan.plan_type in {"interpretive_multidomain", "interpretive_single"}:
    plan.wcr_forced = True
```

This rule is **not part of the Opus prompt** — it is enforced by the router after parsing the Opus response. Opus does not set `wcr_forced`; it only sets `plan_type`. The router sets `wcr_forced` deterministically based on `plan_type`.

Downstream: when `wcr_forced=True`, the retrieval call MUST use `mode="auto"` (which invokes `_apply_whole_chart_read()` in `retrieve.py`). The router endpoint (`/rag/route`) does not call retrieve — it returns only the plan. The compose logic (portal or query handler) is responsible for passing `mode="auto"` when `wcr_forced=True`.

---

## §6 — Plan Type → Downstream Behavior Matrix

| plan_type | wcr_forced | Recommended retrieve mode | UCN chunks in results |
|---|---|---|---|
| `interpretive_multidomain` | True | `auto` (mandatory) | ≥1 guaranteed by WCR |
| `interpretive_single` | True | `auto` (mandatory) | ≥1 guaranteed by WCR |
| `factual` | False | `bm25` preferred | Not required |
| `timing` | False | `hybrid_rrf` preferred | Optional benefit |
| `meta` | False | `vector` preferred | Not required |
| `exploratory` | False | `hybrid_rrf` (default) | Not required |

---

*End of plans_v1_0.md — version 1.0 — session Madhav_M2A_Exec_13 — 2026-04-27*
