---
canonical_id: RETRIEVAL_DESIGN_D0_FOUNDATIONS
version: 1.1
status: DECISIONS-RESOLVED — gates DG1–DG4 ruled; ready to feed D1
created: 2026-06-27
author: Cowork (planning) — for native Abhisek Mohanty
classification: D0 wave deliverable (first execution wave of RETRIEVAL_SYSTEM_DESIGN_APPROACH)
parent: RETRIEVAL_SYSTEM_DESIGN_APPROACH_v1_4
inputs:
  - RETRIEVAL_SYSTEM_DESIGN_APPROACH (the meta-plan; §A MARO, §B bridge, §C code corrections, §D chart-agnostic)
  - RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC / _ASSET_MATRIX / _TRAVERSAL_MODEL / _TOOL_TOPOLOGY (the 4 ground-truth studies)
  - RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION (code-plane + native-contamination findings)
feeds: D1 (contract freeze), all downstream waves
changelog:
  - v1.0 (2026-06-27): D0 opened. Consolidated current-state map; locked glossary; ratified 14 principles; the system-convergence decision (recommendation + gate); campaign tracker opened; first-cut RetrievalSurface contract extending the real CapabilityDescriptor with the chart-agnostic gate. Decision gates D0-DG1..DG4 open for native.
  - v1.1 (2026-06-27): Native RULED all gates (see §7 resolutions). DG1=build on new registry, migrate/retire lib/retrieve + bridge, remediate old MCP tools. DG2=accept §5 contract deltas. DG3=freeze core+gate hard, additive optional fields by versioned amendment. DG4=fix manifest+tier residue early, model-default in D8. D0 now DECISIONS-RESOLVED; D1 is unblocked.
---

# RETRIEVAL DESIGN — D0 FOUNDATIONS (v1.0)

> **What this is.** The first execution wave of the retrieval-system design. D0 locks what every downstream
> wave cites: the consolidated current-state map (grounded in code + the validation/contamination audits), the
> locked glossary, the ratified fourteen principles, the **system-convergence decision**, and a first-cut of
> the **RetrievalSurface contract** (the "WriterBase for retrieval"). It opens the campaign tracker. It does
> NOT freeze the contract — that is D1, after the native resolves the gates below.

---

## §1 — Consolidated current-state map (you are here, grounded)

The retrieval system as it actually exists today (code-validated; see `RETRIEVAL_GROUNDTRUTH_CODE_VALIDATION`):

**Three retrieval code paths coexist:**
- **`platform/src/lib/retrieval/`** — the NEW canonical capability registry. 3 primitives (tool/resource/
  prompt), 4 adapter families (agentic_loop, bulk_context, openai_function_calling, hybrid; 2 minor stubs),
  URI scheme `marsys://{type}/{layer}/{name}`, **tier-free**, **chart-agnostic** (every per-chart handler
  requires chart_id, no native fallback). Registered capabilities: L0=15, L1=19, L2=1 (`query_ucd`), L5=2,
  L3=0, L4=0. **← the modern, clean target.**
- **`platform/src/lib/retrieve/`** — the OLD chat toolset (`msr_sql`, `chart_facts_query`) used by
  `/api/chat/consult`. Still carries `audience_tier`. **← legacy, to migrate/retire.**
- **`platform/src/lib/mcp/primitives_registry.ts`** — a bridge aliasing `query_signals→msr_sql`. **← bridge,
  to fold into the convergence.**

**The MCP server** (`platform-mcp/`): Streamable HTTP (no SSE), Bearer+OAuth, **~13 wired tools** (not 27;
~14 written-yet-unwired incl. `get_cgm_subgraph`, `vector_search`, all `kala_*`). **Carries CRITICAL native
contamination** (≥5 tools default missing chart_id to the native; `lel_query` serves the native LEL corpus with
no chart selector). **← remediation target, NOT a base.**

**The model layer** (`platform/src/lib/models/`): 5 providers (Anthropic/Google/DeepSeek/OpenAI/NVIDIA),
resolver + health + family-worker + reasoning-modes. Anthropic defaulted-away (`DEFAULT_STACK_ID='gemini'`),
not code-banned; a `gemini`-vs-`nim` default discrepancy to reconcile.

**The data/spine** (mig 325): the MSR/CGM spine is real and schema-correct (bodha_msr_signals + cgm nodes/edges
+ contradictions + 768-dim embeddings via Vertex `bo_samskara`). Seed = 81 assets (exact); per_chart count_sql
correctly scopes by chart_id. All six layers have writers (memory saying L3–L5 unbuilt was STALE). **Open
data-plane question (deferred to the read-only runtime brief): writers existing ≠ data built on a given chart.**

**Governance debt to clear:** two stale manifest copies (137 root / 117 platform, both predate mig 325);
tier residue in MCP resources; the model default discrepancy.

---

## §2 — Locked glossary (terms every wave uses with one meaning)

- **RetrievalSurface contract** — the frozen-once interface by which any asset/layer declares its retrieval
  surface (the retrieval analogue of the FROZEN orchestrator `WriterBase`). Extends the existing
  `CapabilityDescriptor`. Frozen in D1.
- **MARO (Model-Aware Retrieval Orchestrator)** — the shared model-aware core behind BOTH channels; reads a
  family's behavioral profile and shapes surface/bundle/budget/validation/grounding. (Approach §A.)
- **Capability / primitive** — a tool, resource, or prompt in the registry (`CapabilityType`).
- **Umbrella tool / thread tool** — a broad entry tool (L-ORIENT/L-DOMAIN) that returns a de-duplicated
  surface + drill-pointers. **Drill / leaf tool** — a finer-grained tool invoked by reference after an umbrella.
- **Archetype** — one of the 8 retrieval characters of an asset (flat-fact, prose-citation, rich-relational,
  graph-traversal, cross-domain, temporal, orientation-digest, calibration).
- **Traversal level** — L-ORIENT / L-DOMAIN / L-FACTOR / L-DERIVATION / L-TIMING / L-SOURCE (the reading hierarchy).
- **F1 (reference-don't-repeat)** — each fact emitted once with perspectives attached; resolved once at composition.
- **F3 (layer-resolution-DOWN)** — L2 references L1 `fact_id` (value) + L0 ids (citation); hydrated, never restated.
- **LEL toggle / firewall** — `lel_enabled` (default false) gates `lel_origin=true` calibration; transitive.
- **Chart-agnostic** — chart_id from request context, required, error-if-missing, no native default. (§D.)
- **Behavioral profile** — a per-family parameter dossier (granularity, bundle, context curve, output
  reliability, caching, reasoning, arg-decoding), hardened by the eval harness, living artifact.

---

## §3 — Ratified principles (the fourteen — confirmed binding at D0)

Carried verbatim from `RETRIEVAL_SYSTEM_DESIGN_APPROACH §6` (1 route-don't-choose · 2 failure-mode>accuracy ·
3 numbers-cited-not-regenerated · 4 graph-edges+cheap-traversal · 5 hybrid-baseline · 6 pre-render+precompute ·
7 primitives-once-cross-model · 8 shared-MARO-not-per-channel · 9 validate-and-repair-JSON · 10 eval-gates-seal ·
11 living-behavioral-profiles · 12 LLM-design-from-authoritative-docs · 13 topology-is-astrological ·
**14 chart-agnostic-zero-native-contamination**). D0 confirms all fourteen as binding for the campaign.

---

## §4 — THE SYSTEM-CONVERGENCE DECISION (the central D0 ruling)

The most important D0 output. Three retrieval code paths exist; the design must pick one base and a disposition
for the others.

**Recommendation (strong):** **Build on `platform/src/lib/retrieval/` (the new canonical registry).** Rationale,
all code-validated:
- It is already the modern target — 3 primitives, 4 adapters, the URI scheme, designed for both channels.
- It is **tier-free** (principle: no audience tier) where `lib/retrieve` still carries `audience_tier`.
- It is **chart-agnostic and clean** (every per-chart handler requires chart_id, no native fallback) where the
  old MCP tools carry CRITICAL native contamination. Building on the clean layer is the cheapest path to
  principle #14.
- It already defines `CapabilityDescriptor` — the exact thing the RetrievalSurface contract extends.

**Disposition of the others:**
- `lib/retrieve` (old chat toolset) → **migrate its still-valuable query logic (e.g. `msr_sql` filters) into
  registry capabilities, then retire it.** Its `audience_tier` is stripped in the migration.
- `mcp/primitives_registry.ts` (bridge) → **fold into the registry-as-single-source**; the MCP channel becomes
  a thin adapter over registry capabilities (D7), not a separate bridge.
- old `platform-mcp/src/tools/` → **remediation target** (D7): carried forward only after native defaults
  removed, chart_id made required, `lel_query` given a required chart_id, descriptions scrubbed, caches fixed.

This makes the registry the **single source of query logic** both channels consume — which is also the
by-construction cure for MCP↔chat drift (Approach §1.F).

---

## §5 — First-cut RetrievalSurface contract (toward D1; NOT frozen)

The contract extends the real `CapabilityDescriptor` (`platform/src/lib/retrieval/registry/types.ts`). The
existing descriptor is a sound base but has gaps the contract must close. Proposed additions (deltas marked):

```
RetrievalSurface (extends CapabilityDescriptor) {
  // — existing, kept —
  uri; type ('tool'|'resource'|'prompt'); layer; name; description; input_schema;
  required_inputs; llm_hints; handler; mcp_annotations;

  // — Δ chart-agnostic gate (principle #14) —
  scope: 'per_chart' | 'global';                    // NEW — explicit, from asset_registry
  // CONTRACT RULE: if scope==='per_chart' then required_inputs MUST include 'chart_id',
  //   handler MUST read chart_id from context, MUST error if absent, MUST contain NO literal
  //   chart_id and NO native default. (Closes the gap: today required_inputs + context.chart_id
  //   are both OPTIONAL at the type level.)

  // — Δ topology (D-GROUNDTRUTH framework) —
  archetype: <one of the 8>;                         // NEW — drives tool shape
  traversal_level: <L-ORIENT|...|L-SOURCE>;          // NEW — drives umbrella-vs-leaf
  tool_role: 'umbrella' | 'drill' | 'leaf' | 'graph' | 'hybrid_retrieval' | 'temporal' | 'quality'; // NEW
  drill_children?: CapabilityUri[];                  // NEW — umbrella → its drill tools

  // — Δ grounding + dedup (F1/F3/§N.5) —
  emits_references: boolean;                          // NEW — drill tools return signal_id/fact_id refs, not restated facts
  grounds_to?: { l1_fact_ids?: bool; l0_citation_ids?: bool }; // NEW — F3 layer-resolution

  // — Δ LEL firewall (§D) —
  lel_capable: boolean;                              // NEW — does this surface touch lel_origin data
  // CONTRACT RULE: lel excluded unless explicit lel_enabled=true; transitive.

  // — Δ multi-model (MARO) —
  output_schema?: ...;                               // promote from narrowed type — needed for structured output
  behavioral_overrides?: <per-family hints>;         // NEW — optional per-profile shaping hooks (MARO reads)
}
```

**The contract gate (CI-enforced, principle #14 + F1):** a static check that REJECTS any surface where
`scope==='per_chart'` and (`chart_id` not required OR a literal chart_id present OR a native-default pattern
`?? <uuid>` / `.default(NATIVE)` / `env.NATIVE_CHART_ID ??`); rejects `'default'` cache buckets; rejects a
per-chart tool whose handler lacks error-if-missing; rejects native identifiers in `description`. Sits beside
the existing `parity_check.ts` as a hard gate.

---

## §6 — Campaign tracker (opened)

`RETRIEVAL_SYSTEM_DESIGN_CAMPAIGN` is hereby opened (live-state pointer for the multi-session campaign).
Wave status at D0 close: D-GROUNDTRUTH ✓ (4 deliverables + code validation + contamination audit); D0 in
flight (this artifact). Next: D1 (freeze contract) after gates resolved. Open validation items: (a) acharya
review of the traversal model; (b) the read-only runtime brief execution; (c) governance debt (manifests/tier/
model-default).

---

## §7 — Decision gates — RESOLVED (native ruling, 2026-06-27)

- **D0-DG1 — System convergence — RULED: build on the new registry.** Make `platform/src/lib/retrieval/`
  the single source; migrate `msr_sql`/valuable query logic into registry capabilities then **retire
  `lib/retrieve`**; **fold** `mcp/primitives_registry.ts`; the old `platform-mcp/src/tools/` is a
  **remediation target** (D7), carried forward only after native-contamination + tier removal.
- **D0-DG2 — Contract additions — RULED: accept.** The §5 deltas (scope + chart-agnostic gate; archetype/
  traversal_level/tool_role/drill_children; emits_references/grounds_to; lel_capable; output_schema;
  behavioral_overrides) are the D1 contract scope.
- **D0-DG3 — Freeze posture — RULED: freeze core + gate hard, additive by amendment.** The contract core
  shape + the chart-agnostic gate freeze hard (onboard-by-conformance, WriterBase-style). New **optional**
  fields may be added later via a **versioned amendment** (not a silent change). Stability where it matters,
  room to evolve.
- **D0-DG4 — Governance debt — RULED: split.** Regenerate the CAPABILITY_MANIFEST (resolve 137-vs-117 drift,
  post-mig-325) + strip the MCP-resource tier residue in an **early cleanup** (they confuse every wave);
  reconcile the `gemini`-vs-`nim` model-default discrepancy in **D8** with the MARO work.

These rulings are binding inputs to D1.

---

## §8 — D0 → D1 handoff

On gate resolution, D1 freezes the RetrievalSurface contract (§5, hardened per DG2/DG3), and D2 (router) +
D3 (grounding spine) open. The build-on-new-registry decision (DG1) makes D1 concrete: the contract is a
typed extension of the existing `CapabilityDescriptor`, and the chart-agnostic gate becomes a CI check beside
`parity_check.ts`.

*End of RETRIEVAL_DESIGN_D0_FOUNDATIONS v1.0 — decision gates DG1–DG4 open for native.*
