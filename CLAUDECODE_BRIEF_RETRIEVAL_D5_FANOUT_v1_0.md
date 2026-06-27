---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT
version: 1.0
status: PARAMETERIZED — structurally complete; per-asset specifics resolved when inputs land (see §0)
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF — D5 per-asset / per-layer retrieval-surface fan-out
session_type: implementation — apply the topology framework to all ~70 assets (layer-sub-waved)
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 (wave D5); RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY (the rules)
depends_on: D1 (contract), D3 (grounding), D4 (graph)
detail_pass_required_when: D1 contract frozen + runtime data validated + manifest reconciled
prereq_reading:
  - RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY_v1_0.md (R1–R6 rules; 8 worked examples)
  - RETRIEVAL_GROUNDTRUTH_ASSET_MATRIX_v1_0.md (per-asset comprehension + 8 archetypes)
  - RETRIEVAL_GROUNDTRUTH_TRAVERSAL_MODEL_v1_0.md (traversal levels per asset)
hard_constraints:
  - chart-agnostic (#14) on every tool; F1 dedup + completeness + retrievability by construction
  - apply the topology decision rules R1–R6 per asset — do not invent shapes ad hoc
acceptance_criteria: see §4
---

# CLAUDE CODE BRIEF — D5: PER-ASSET FAN-OUT (parameterized)

> Apply the tool-topology framework to every one of the ~70 assets, layer by layer, producing the full tool
> roster. The decision rules are settled (R1–R6); the per-asset specifics get a detail-pass once the contract
> is frozen and the data/manifest reality is confirmed.

## §0 — Parameterized inputs (resolve at detail-pass)
- `[resolved from D1]` — the frozen RetrievalSurface contract fields every tool declares.
- `[resolved from runtime brief]` — which assets actually have DATA populated per chart (writers exist for all,
  but population is the open data-plane question) — drives whether a tool is live or stubbed-pending-data.
- `[resolved from D0.5 manifest reconciliation]` — the single authoritative asset list (seed 81 is the queryable
  source of truth; the reconciled manifest the docs/tools catalog) — so the roster has one source.
- `[resolved from acharya validation]` — the traversal-model ordering (currently research-grounded) — affects
  umbrella/drill hierarchy where it depends on the reading sequence.

## §1 — Layer sub-waves
Per the topology framework's archetype×level rules, build sub-wave by sub-wave: D5.0 L0 + D5.1 L1 together,
D5.2 L2, then D5.3–D5.5 L3/L4/L5 (lighter — service-type assets are call-not-query). For EACH asset: apply
R1 (classify archetype) → R2 (traversal level) → R3 (map to tool shape) → R4 (consolidate siblings, don't
mirror) → R5 (umbrella owns multi-vantage reconciliation) → R6 (drill-by-reference). Produce the tool's
RetrievalSurface descriptor.

## §2 — Guarantees by construction
F1 dedup (umbrella-first + reference-drill); completeness (full enumeration parity, salience-as-column-not-
filter, no silent truncation); retrievability (hybrid for prose, structured hydration for facts). The 8 worked
examples in the topology framework are the templates — most assets fold into one of ~8 umbrella/family tools +
a few consolidated leaves, NOT one tool per asset.

## §3 — What this is NOT
Not new tool shapes (use R1–R6). Not the router/graph/grounding (consumed from D2/D3/D4). Not channel wiring (D7).

## §4 — Acceptance criteria
- Every asset in the reconciled catalog has a contract-conformant RetrievalSurface descriptor + tool binding.
- Roster collapses ~70 assets into ~8 umbrella/family tools + consolidated leaves (per topology §5).
- F1/completeness/retrievability gates green per layer; chart-agnostic gate green on all.
- Assets without populated data are explicitly stubbed-pending-data (from runtime findings), not faked.
- Detail-pass log noting which §0 parameters were resolved and how.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D5_FANOUT v1.0 (parameterized).*
