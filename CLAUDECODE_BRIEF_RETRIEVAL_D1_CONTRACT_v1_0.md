---
canonical_id: CLAUDECODE_BRIEF_RETRIEVAL_D1_CONTRACT
version: 1.0
status: READY-FOR-EXECUTION
created: 2026-06-27
author: Cowork (planning) — for execution by Claude Code in Antigravity
classification: CLAUDECODE_BRIEF (per CLAUDE.md §C.0 — governing scope for one or more Claude Code sessions)
session_type: implementation — freeze the RetrievalSurface contract + chart-agnostic CI gate; begin system convergence
parent_design: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4 + RETRIEVAL_DESIGN_D0_FOUNDATIONS_v1_1 (gates DG1–DG4 RULED)
prereq_reading (Claude Code reads these at session open, in order):
  - RETRIEVAL_DESIGN_D0_FOUNDATIONS_v1_0.md  (§4 convergence ruling, §5 contract first-cut, §7 RULED gates)
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_0.md (§A MARO, §B bridge, §C code corrections, §D chart-agnostic, §6 principles)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION_v1_0.md (§H native-contamination findings — the remediation list)
  - RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY_v1_0.md (the archetype×level → tool_role mapping the contract encodes)
recommended_session_sequence:
  - SESSION 0 (do first): run CLAUDECODE_BRIEF_RETRIEVAL_RUNTIME_VALIDATION (read-only) to ground data-plane reality + confirm contamination blast radius
  - SESSION 0.5 (early cleanup, DG4): regenerate CAPABILITY_MANIFEST (resolve 137-vs-117, post-mig-325) + strip MCP-resource tier residue
  - SESSION 1 (this brief): implement + freeze the RetrievalSurface contract + the chart-agnostic CI gate
  - SESSION 2+: convergence (migrate lib/retrieve logic → registry, retire it; fold bridge) UNDER the reverse-citation gate below
hard_constraints:
  - the chart-agnostic gate (principle #14) is non-negotiable: NO native defaults, chart_id required + error-if-missing
  - DESTRUCTIVE-OP SAFETY: any retirement/removal MUST pass the reverse-citation gate in §4 before deletion
  - contract freeze posture (DG3): core + gate freeze HARD; new OPTIONAL fields only via versioned amendment
  - build on platform/src/lib/retrieval/ (the clean registry) — NOT the contaminated platform-mcp/src/tools/
acceptance_criteria: see §6
---

# CLAUDE CODE BRIEF — D1: RETRIEVALSURFACE CONTRACT + CHART-AGNOSTIC GATE

> **What this is.** The implementation handoff for D1. Cowork has completed and grounded the design (D0
> rulings settled); this brief turns it into real TypeScript + CI against the actual code, executed in
> Antigravity where you can compile, test, and run. All design decisions are embedded below so you do not
> re-derive them. Per the project's Cowork-vs-Antigravity split, Cowork plans + briefs; Claude Code implements.

## §0 — Embedded design decisions (do not re-derive; these are RULED)

- **Build on `platform/src/lib/retrieval/`** (the new registry). It is tier-free + chart-agnostic + already
  defines `CapabilityDescriptor` (`registry/types.ts`). The old `lib/retrieve` (has `audience_tier`) and the
  `mcp/primitives_registry` bridge are migrate/fold/retire targets. The old `platform-mcp/src/tools/` carries
  CRITICAL native contamination → remediation target, not a base. (D0 §4, DG1.)
- **The 14 principles bind** (Approach §6). The load-bearing ones for D1: #3 numbers-cited-not-regenerated,
  #8 shared-MARO, #10 eval-gates-seal, #14 chart-agnostic-zero-contamination.
- **Contract freeze posture:** freeze core + chart-agnostic gate HARD; additive optional fields by versioned
  amendment only. (DG3.)

## §1 — Implement the RetrievalSurface contract (TypeScript)

Extend the REAL `CapabilityDescriptor` in `platform/src/lib/retrieval/registry/types.ts`. Add the D0 §5 deltas
as typed fields. Key gap to close: today `required_inputs?` and `CapabilityContext.chart_id?` are BOTH optional
— a per-chart tool is not forced to require chart_id. The contract must make that impossible.

Add (exact field set from D0 §5, DG2-accepted):
- `scope: 'per_chart' | 'global'` (from asset_registry; required).
- `archetype` (one of the 8) + `traversal_level` (L-ORIENT…L-SOURCE) + `tool_role`
  ('umbrella'|'drill'|'leaf'|'graph'|'hybrid_retrieval'|'temporal'|'quality') + `drill_children?: CapabilityUri[]`.
- `emits_references: boolean` (drill/leaf tools return signal_id/fact_id refs, not restated facts — F1).
- `grounds_to?: { l1_fact_ids?: boolean; l0_citation_ids?: boolean }` (F3 layer-resolution).
- `lel_capable: boolean` (+ LEL excluded unless explicit `lel_enabled=true`, transitive).
- promote `output_schema?` onto the main descriptor (needed for structured output across providers).
- `behavioral_overrides?` (optional per-family MARO shaping hooks).

Type-level enforcement: encode the rule "if `scope==='per_chart'` then `required_inputs` MUST include
`'chart_id'`" as tightly as the type system allows (e.g. a discriminated union or a builder that refuses to
construct a per_chart surface without chart_id), with the runtime gate (§2) as the backstop.

## §2 — Implement the chart-agnostic CI gate (principle #14)

A static check, sitting beside the existing `parity_check.ts`, run in CI, that FAILS the build if any registered
capability violates the mandate. It MUST reject:
- a `per_chart` surface whose `required_inputs` omits `chart_id`;
- any literal chart_id in handler source (esp. the native `482012f1-…` and phantom `362f9f17-…`);
- native-default patterns: `?? '<uuid>'`, `.default(<uuid>)`, `?? NATIVE*`, `env.NATIVE_CHART_ID ??`;
- a per-chart handler that lacks error-if-missing on chart_id (does not throw when chart_id absent);
- `'default'` (or any non-chart_id) cache-key buckets on per-chart caches;
- native identifiers (chart_id, "Abhisek Mohanty", birth date/place) in any LLM-visible `description`/`title`.
Provide a clear failure message per violation (file:line + which rule). Add a few unit tests proving the gate
catches each pattern. Wire it into the same CI step as parity_check.

## §3 — Apply the contract to the existing clean registry capabilities

The new registry already has L0=15, L1=19, L2=1, L5=2 capabilities. Retrofit them to the contract: set
`scope`, `archetype`, `traversal_level`, `tool_role`, `emits_references`, `lel_capable` on each; ensure every
per_chart one requires chart_id (most already do — confirm). Scrub the one known native-id leak in a
description (`L1_ganita/get_positions.ts:22` → placeholder `<chart_uuid>`). Confirm the gate passes green on
the retrofitted registry.

## §4 — Convergence work (SESSION 2+) — UNDER THE REVERSE-CITATION GATE

DG1 authorizes migrating `lib/retrieve` query logic into registry capabilities, then retiring it, and folding
the bridge. **This is destructive. The project has been burned before** (`feedback_destructive_brief_reverse_
citation_gate`: a kill-list was trusted and live tables were wiped). Therefore, MANDATORY before ANY removal:

**Reverse-citation gate (Step 0.5 of any retirement):**
1. For every retirement target (a file, export, table, env var, MCP tool) — grep the ENTIRE live codebase for
   active references/imports/calls to it.
2. Any target with active citations is reclassified **KEEP-OR-REPOINT** (migrate the caller first), NOT removed.
3. Only targets with zero live citations after repointing may be removed.
4. Produce the citation report as part of the PR; no deletion lands without it.

Migration order: (a) port `msr_sql` + valuable `lib/retrieve` query logic into registry capabilities (chart_id
required, tier stripped); (b) repoint `/api/chat/consult` to the registry; (c) reverse-citation gate; (d) retire
`lib/retrieve` + fold `mcp/primitives_registry`. The contaminated `platform-mcp/src/tools/` remediation (remove
native defaults, require chart_id, fix `lel_query`, scrub descriptions, fix caches) is its own gated step (D7).

## §5 — What this brief does NOT do

- Does NOT build the router (D2), grounding spine (D3), graph tool (D4), per-asset fan-out (D5), MARO/profiles
  (D-PROFILES), channel integration (D7), or eval harness (D8) — those are later briefs.
- Does NOT touch prod data or run builds beyond what CI/tests require.
- Does NOT remove anything without the §4 reverse-citation gate.

## §6 — Acceptance criteria

- RetrievalSurface contract implemented in `registry/types.ts` with all D0 §5 fields; per_chart⇒chart_id-required
  enforced at the type level as far as feasible.
- Chart-agnostic CI gate implemented beside `parity_check.ts`, with unit tests proving it catches each forbidden
  pattern; CI wired; green on the current clean registry.
- All existing registry capabilities retrofitted to the contract; the one native-id description scrubbed; gate green.
- Contract core + gate documented as FROZEN (DG3); an amendment procedure noted for future optional fields.
- (If Session 2 run) convergence migration done strictly under the reverse-citation gate, with the citation
  report in the PR; nothing deleted that still has live citations.
- No native contamination anywhere the gate can see; no destructive op without its citation report.

## §7 — Close

Set this brief's frontmatter `status: COMPLETE` only when the contract + gate are implemented, tested, CI-wired,
and green, and the design artifacts are updated to mark D1 frozen. Report results back to Cowork so the campaign
tracker + approach plan are updated and D2/D3 briefs can be authored.

*End of CLAUDECODE_BRIEF_RETRIEVAL_D1_CONTRACT v1.0.*
