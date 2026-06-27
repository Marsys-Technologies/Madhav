---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D6_D7_CHANNELS
version: 1.0
status: PARAMETERIZED — structurally complete; specifics resolved when inputs land (see §0)
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — D6 synergy + D7 channel integration (MCP + chat over MARO)
session_type: implementation — whole-corpus synergy + the two-channel surface
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (waves D6, D7; §A channel asymmetry)
depends_on: D1–D5 + D-PROFILES
detail_pass_required_when: D5 roster exists + D-PROFILES MARO core exists
prereq_reading:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (waves D6/D7; §A.3 channel asymmetry; §C.1.1 build-on-new-registry)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md (§H native contamination in old MCP tools — remediation list)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md (B.i MCP-channel obligations)
hard_constraints:
  - single source of query logic (the registry) → MCP↔chat drift impossible by construction
  - old platform-mcp/src/tools/ remediation ONLY under the reverse-citation gate (destructive safety)
  - chart-agnostic (#14) enforced on every channel surface; declared→profiled / undeclared→universal MCP
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D6 SYNERGY + D7 CHANNELS (parameterized)

> D6 designs the whole-corpus synergy (the system being more than its assets); D7 wires both channels over the
> shared MARO + registry so they cannot drift, and remediates the contaminated old MCP tools. PARAMETERIZED:
> structure is set; specifics resolve once the D5 roster + MARO core exist.

## §0 — Parameterized inputs (resolve at detail-pass)
- `[resolved from D5]` — the final tool roster (which umbrella/drill/graph/temporal tools exist to compose).
- `[resolved from D-PROFILES]` — the MARO core + profiles both channels consume.
- `[resolved from D7 decision]` — the MCP declaration mechanism; the multi-model substrate (LiteLLM-style proxy
  vs native-per-family — memory leans proxy for cost-tracking).

## §1 — D6: whole-corpus synergy
Compose the umbrella + graph + grounding spine into Whole-Chart-Read answers: convergence + contradiction
surfacing across domains/layers (CDLM + CGM), layered hydration (L2→L1→L0). This is the value no single asset
holds. Define the composition orchestration (how the router + umbrella tools + graph tool + grounding spine
assemble one de-duplicated, cited, multi-vantage answer — F1/F3 end to end).

## §2 — D7: channel integration
- **Consolidated workflow-shaped MCP tool set** rebuilt over the registry (~10–15 active, per provider specs),
  with outputSchema + structuredContent + text fallback, cursor pagination, response_format/verbosity, UUIDs
  resolved to names, names avoiding `-` (Gemini). Served over Streamable HTTP (no SSE — matches reality).
- **Chat engine** consumes the SAME registry capabilities via MARO → MCP↔chat drift impossible (single query
  logic). Repoint `/api/chat/consult` to the registry (the lib/retrieve retirement from D1 convergence lands here).
- **Old MCP tools remediation (DESTRUCTIVE — reverse-citation gate mandatory):** for the contaminated
  `platform-mcp/src/tools/` (per validation §H), remove every native default, make chart_id required, give
  `lel_query` a required chart_id, scrub native ids from descriptions, fix `'default'` cache buckets — under
  the reverse-citation gate before any removal.
- Wire declared→profiled / undeclared→universal-best MCP surfaces (MARO + D-PROFILES).

## §3 — What this is NOT
Not the eval/seal (D8). Not new tools (composes the D5 roster). No removal without the citation gate.

## §4 — Acceptance criteria
- D6 composition produces de-duplicated, cited, multi-vantage Whole-Chart-Read answers (F1/F3 verified).
- Consolidated MCP tool set over the registry; provider-spec obligations met; chart-agnostic gate green.
- Chat + MCP share one query source; no drift (a parity test proves identical filter behavior both channels).
- Old MCP tools remediated of native contamination under the reverse-citation gate; citation report in PR.
- Declared/undeclared MCP behavior live. No destructive op without its citation report.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D6_D7_CHANNELS v1.0 (parameterized).*
