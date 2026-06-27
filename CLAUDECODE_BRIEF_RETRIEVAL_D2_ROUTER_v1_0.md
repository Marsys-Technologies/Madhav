---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D2_ROUTER
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — D2 query router
session_type: implementation — the top-level "route, don't choose" architecture
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (principle 1, wave D2)
depends_on: D1 (RetrievalSurface contract frozen)
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (§6 principles 1,2,8; wave D2)
  - RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY_v1_0.md (the traversal-level routing target)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (reasoning-mode handling, per-family)
hard_constraints:
  - chart-agnostic (principle #14): the router passes chart_id from context; never injects a default
  - deterministic-first (principle): prefer rule-driven routing where it suffices; model-driven only where needed
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D2: QUERY ROUTER

> The top-level architecture is "route, don't choose." A router classifies each query and dispatches to the
> cheapest path that can answer it correctly, with a bias toward paths that ERROR on out-of-scope over paths
> that fabricate (principle #2).

## §0 — Embedded decisions
- Five route classes (Approach §3 D2): **numeric/exact → deterministic tool (grounding spine, D3)**;
  **relational / "across-everything / contradictions" → graph tool (D4)**; **narrative → hybrid vector
  retrieval**; **simple → cheap single-shot**; **hard multi-hop → agentic loop (existing agentic_loop adapter)**.
- The router maps a query to a **traversal level** (L-ORIENT…L-SOURCE) and thus to umbrella-vs-drill tools.
- Default first hop for most chart questions = the L-ORIENT umbrella (orientation/UCD), per the traversal model.

## §1 — Query taxonomy + routing policy
Implement a classifier producing {route_class, traversal_level, target_tool(s), budget}. **DG decision to make
in-wave:** rule-driven vs model-driven vs hybrid — recommendation: rule-driven core (deterministic, auditable,
fits deterministic-first) with an optional model-classifier fallback for ambiguous queries; record which fired.

## §2 — Per-route execution + termination
- Single-shot / leaf: one call, return. Umbrella→drill: orientation then reference-keyed drills (F1).
- Graph: dispatch to D4 tool. Agentic: bounded loop via the existing `agentic_loop` adapter with a
  **value-based termination** policy (stop when marginal retrieved value drops, not a hard count).
- Per-route cost/latency budget; honor the smallest-model context floor when a model is in the loop (MARO, D7).

## §3 — Observability (feeds the eval harness, D8)
Log per query: route_class chosen, tools called, traversal trajectory, latency, token cost, termination reason.
This is the trajectory data D8 scores. No PII / no native leakage in logs.

## §4 — Acceptance criteria
- Router implemented as a registry-aware component; classifies into the 5 route classes + traversal level.
- Rule-driven core with recorded routing decisions; (optional) model fallback flagged when used.
- Value-based termination for agentic routes; per-route budgets enforced.
- Trajectory logging in place for D8. chart_id passed through, never defaulted.
- Unit tests over representative queries per route class.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D2_ROUTER v1.0.*
