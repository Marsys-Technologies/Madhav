---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D3_GROUNDING_SPINE
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — D3 grounding spine (semantic/metric layer + reference-don't-restate)
session_type: implementation — the structural cure for hallucinated numbers
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (principles 2,3,6; wave D3)
depends_on: D1 (contract); cross-cuts all per-asset waves
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (principles 2,3,6; §B grounding; wave D3)
  - RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX_v1_0.md (§3 the spine; §4 F3 layer-resolution)
  - CLAUDE.md §N.5 (L1 is authority; reference fact_id, never restate)
hard_constraints:
  - every numeric/computed claim is CITED from a deterministic source, never regenerated (principle #3 / §N.5)
  - missing data returns EMPTY/ERROR, never a fabricated value (principle #2)
  - chart-agnostic (#14)
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D3: GROUNDING SPINE

> The architectural cure for hallucinated chart values: the LLM SELECTS governed metrics / references
> `fact_id`s; it never re-derives a number. Failure mode beats raw accuracy — out-of-scope returns empty.

## §0 — Embedded decisions
- The grounding spine fronts every numeric/computed claim. It is a **governed metric/semantic layer** over the
  deterministic assets (L1 chart_facts + L2 computed-salience etc.) — the LLM picks from a governed vocabulary;
  a deterministic resolver returns the cited value.
- **Reference-don't-restate (F3 / §N.5):** answers carry the L1 `fact_id` (value) + L0 citation ids; the value
  is inherited, never recomputed by the LLM. The MSR `constituent_facts_array` → `chart_facts.fact_id` and
  `classical_sources_jsonb` → L0 ids are the resolution edges (verified real in mig 325).

## §1 — Governed metric layer
Define the metric/dimension vocabulary the LLM may request (e.g. graha condition score, shadbala, salience,
dignity) bound to deterministic resolvers over the real tables. Out-of-vocabulary numeric requests ERROR (with
a helpful message) — never a text-to-SQL guess that could fabricate. Scope v1 to the high-traffic numeric
claims (the long tail can error-and-fallback). **Decision in-wave:** the exact v1 metric set.

## §2 — Reference-resolution service
A composition-time resolver that, given a signal_id / fact_id reference, returns the canonical value + its
citation once (F1: resolve each reference exactly once). Enforce that a value disagreeing with the cited L1
fact is a HALT (per §N.5 — that's a bug, not a stored divergence). Wire the empty-on-missing behavior for
graph/structured grounding.

## §3 — Pre-render vs compute boundary
Decide which relational bundles are pre-rendered to NL at build time (retrievable, cheap) vs computed on query
(long tail). Embody "rich pre-computed ingredients, LLM synthesizes at query" (principle #6). **Decision
in-wave:** the build-time/query-time line for v1.

## §4 — Acceptance criteria
- Governed metric layer with deterministic resolvers; out-of-vocab numeric → error, never fabricate.
- Reference-resolution service enforcing reference-don't-restate + resolve-once; value-vs-fact disagreement halts.
- Empty-on-missing behavior verified. chart-agnostic throughout.
- Tests: a numeric claim is served only via the resolver; an out-of-scope numeric errors; a value mismatch halts.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D3_GROUNDING_SPINE v1.0.*
