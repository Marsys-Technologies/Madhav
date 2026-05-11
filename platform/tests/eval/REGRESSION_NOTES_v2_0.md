---
artifact: REGRESSION_NOTES_v2_0.md
session_id: Planner-Eval-S1
prompt_version: PLANNER_PROMPT_v2_0.md
golden_set_version: "1.1"
model: claude-haiku-4-5
date: 2026-05-11
---

# PLANNER_PROMPT_v2_0 — Golden-Set Regression Notes

## 1. Headline numbers

| metric | v2.0 actual | v1.7 baseline | delta | gate |
|---|---|---|---|---|
| avg_tool_recall | **0.945** | 0.940 | +0.005 | PASS (≥ 0.940) |
| avg_tool_precision | **0.852** | 0.945 | **−0.093** | **FAIL (< 0.945)** |
| avg_asset_bundle_recall | **0.902** | — (first baseline) | n/a | PASS (≥ 0.90) |
| asset_bundle_floor_violations | **2** | — | n/a | **FAIL (≠ 0)** |
| pass_rate | 0.586 | — | n/a | informational |
| required_misses | 0 | — | n/a | clean |
| forbidden_violations | 0 | — | n/a | clean |
| entries scored | 29/29 | 29 | 0 | clean |
| total errors | 0 | — | n/a | clean (NIM unreachable; fell back to Anthropic Haiku per brief §5) |

Conclusion: **recall held; precision regressed −0.093**. The planner is calling
more tools than v1.7 — every failing entry over-fires at least one tool that
isn't in `expected_tools`. Asset-bundle baseline established at 0.902 — over
threshold, but two degenerate edge_case entries return empty bundles entirely.

## 2. Failing entries grouped by category

### 2A. interpretive (4) — over-fires `vector_search` and `cgm_graph_walk`

The shared signature: planner adds `vector_search` (and sometimes
`cgm_graph_walk`) on top of the expected `msr_sql`-only or
`msr_sql + vector_search` pair. Recall stays at 1.00; precision drops to 0.67.

| id | query | expected | predicted | precision |
|---|---|---|---|---|
| GT.007 | "What does my 7th house say about marriage?" | `msr_sql, vector_search` | + `cgm_graph_walk` | 0.67 |
| GT.011 | "Read my D9 Navamsha for marriage indications." | `msr_sql, vector_search` | + `cgm_graph_walk` | 0.67 |
| GT.012 | "What does my 10th house say about my profession?" | `msr_sql, vector_search` | + `cgm_graph_walk` | 0.67 |

### 2B. predictive (1) — over-fires `vector_search`

| id | query | expected | predicted | precision |
|---|---|---|---|---|
| GT.014 | "Where is Saturn transiting in my chart right now…" | `msr_sql, pattern_register` | + `vector_search` | 0.67 |

### 2C. holistic (2) — over-fires both expected and additional registers

| id | query | expected | predicted | recall | precision |
|---|---|---|---|---|---|
| GT.017 | "Give me a comprehensive overview of my life path…" | `cluster_atlas, vector_search, pattern_register, cgm_graph_walk` | `cluster_atlas, msr_sql, vector_search, pattern_register, resonance_register` (missing `cgm_graph_walk`, adds `msr_sql + resonance_register`) | 0.75 | 0.60 |
| GT.020 | "What signals are currently lit or ripening…" | `msr_sql, pattern_register` | + `cluster_atlas, vector_search` | 1.00 | 0.50 |

### 2D. planetary / interpretive-class (3) — over-fires `vector_search` + `cluster_atlas` + `resonance_register`

The single most-degraded category. Planner treats "tell me about planet X"
as a holistic-style sweep across all registers.

| id | query | expected | predicted | recall | precision |
|---|---|---|---|---|---|
| GT.021 | "Tell me everything about Jupiter in my chart." | `msr_sql, pattern_register, cgm_graph_walk` | + `cluster_atlas, vector_search, resonance_register` | 1.00 | 0.50 |
| GT.022 | "What is Mars's role across my divisional charts?" | `msr_sql, pattern_register` | replaces `pattern_register` with `cgm_graph_walk, vector_search` (also misses `pattern_register`) | 0.50 | 0.33 |
| GT.023 | "What patterns and resonances surface for Saturn…" | `pattern_register, resonance_register, msr_sql` | + `cgm_graph_walk, vector_search` | 1.00 | 0.60 |

### 2E. edge_case (2) — under-fires (recall side)

| id | query | expected | predicted | recall | precision |
|---|---|---|---|---|---|
| GT.025 | "Tell me something interesting about the chart." | `pattern_register, contradiction_register, resonance_register, cluster_atlas` | `cluster_atlas, pattern_register, vector_search` (misses `contradiction_register, resonance_register`) | 0.50 | 0.67 |
| GT.026 | "When does my Mercury period begin and what will it activate?" | `msr_sql, pattern_register, vector_search` | `msr_sql, pattern_register` (misses `vector_search`) | 0.67 | 1.00 |

### 2F. edge_case + over-broad holistic (1)

| id | query | expected | predicted | precision |
|---|---|---|---|---|
| GT.029 | "Tell me everything about everything…" | 5 tools | + `resonance_register` | 0.83 |

## 3. Asset-bundle floor violations (2)

Both are degenerate-input edge cases:

- **GT.027** — empty query → planner returned `asset_bundle: []` instead of
  floor `[FORENSIC, CGM]`.
- **GT.028** — single-punctuation query (`?`) → planner returned
  `asset_bundle: []` instead of floor `[FORENSIC, CGM]`.

PLANNER_PROMPT_v2_0 rules R21–R26 require FORENSIC + CGM in every plan; the
prompt does not currently enforce this on degenerate inputs.

## 4. Cross-cutting pattern

Two systematic biases observable in the v2.0 prompt:

1. **`vector_search` over-fires.** Appears in 9 of 12 failing predictions.
   When the query mentions a house/planet/divisional-chart by name, the
   prompt nudges the planner to add semantic search even when MSR + register
   lookup is sufficient.
2. **`cgm_graph_walk` over-fires on planetary/house queries.** Appears in
   6 of 12 failures. The prompt's R-rules for cross-domain linkage may be
   triggering too eagerly on single-house/single-planet questions.

## 5. Remediation surface (for Planner-Prompt-Fix-S1)

Not in scope for this session per brief §5 + §9.1. Captured here for the
next session's plan:

- Tighten the "when to add `vector_search`" rule — restrict to queries that
  explicitly ask for narrative interpretation, not just chart-position lookups.
- Tighten the "when to add `cgm_graph_walk`" rule — restrict to queries that
  explicitly cross domains (career→relationship, health→spirituality) or
  surface contradictions, not "tell me about planet X" queries.
- Add an explicit "degenerate input" rule: if query is empty or
  single-punctuation, still emit floor asset_bundle `[FORENSIC, CGM]` with an
  empty `tool_calls` array.

## 6. Run conditions

- NIM (`nvidia/llama-3.3-nemotron-super-49b-v1`) — unreachable: persistent
  DNS / SSL / connection-reset errors throughout the run. Same failure mode
  as v1.7 baseline's gemini-DNS event 2026-05-11.
- Fell back to `claude-haiku-4-5` per brief §5 retry instruction.
- CHART_ID=test-native (no production chart needed for tool-selection scoring).
- All 29 entries returned a plan; zero import-failure errors; zero
  required_misses; zero forbidden_violations.

*REGRESSION_NOTES_v2_0.md · Planner-Eval-S1 · 2026-05-11*
