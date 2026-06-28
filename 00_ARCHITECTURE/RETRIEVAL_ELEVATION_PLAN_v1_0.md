---
canonical_id: RETRIEVAL_ELEVATION_PLAN
version: 1.0
status: CURRENT — the phased plan for elevating the retrieval system (built in this Cowork session's workstream)
created: 2026-06-28
author: Cowork (planning) — for native Abhisek Mohanty; executed via Claude Code briefs
classification: phased elevation plan (retrieval fork)
grounded_in:
  - RETRIEVAL_ELEVATION_AUDIT_FINDINGS_v1_0.md (Claude Code live audit — retrieval side)
  - RETRIEVAL_MCP_UNIFIED_AUDIT_AND_SYNC_CONTRACT_v1_1 (the frozen seam; §4 the contract this plan honors)
  - RETRIEVAL_GROUNDTRUTH_TOOL_TOPOLOGY_v1_0 (archetype × traversal-level topology)
pairs_with: the MCP elevation plan (separate conversation) — both obey the frozen §4 sync contract
changelog:
  - v1.0 (2026-06-28): Initial phased retrieval-elevation plan, grounded in the live Claude Code audit. Data prereqs (MSR re-run) gate the astrological elevation. Honors the frozen retrieval↔MCP contract; retrieval stays chart-agnostic + frozen, entitlement stays at the channel.
---

# RETRIEVAL ELEVATION PLAN (v1.0)

> The phased plan to elevate the sealed D0–D8 retrieval system to acharya-grade, multi-LLM, and in complete
> sync with the enhanced MCP. Built in this Cowork session; executed as Claude Code briefs. It honors the
> **frozen retrieval↔MCP sync contract** (§4 of the unified audit): retrieval stays chart-agnostic + FROZEN;
> entitlement lives at the channel; both channels consume the same registry. This plan does the retrieval half;
> the MCP plan (separate conversation) does the channel half; the contract keeps them in sync.

## §0 — The governing reality (from the live audit)

Three live-verified facts shape the ordering:
1. **The orphan rate is real (91.5%).** MSR signals cite stale `chart_facts` fact_ids (MSR built 2026-06-20,
   chart_facts rebuilt 2026-06-24, MSR never re-run). **Reasoning-unit elevation is hollow until this is fixed**
   — `assess_marriage` can't ground its bundle if 91.5% of constituent facts don't resolve. → DATA PREREQUISITE.
2. **The registry-serving path is currently broken** (callPlatformPrimitive 401s on the missing
   `x-mcp-audience-tier` header). The keystone "MCP serves the registry" can't be validated end-to-end until
   this one-line fix lands. (Owned by the MCP plan, but this plan depends on it for the keystone.)
3. **MARO is further along than assumed** (profiles MEASURED v1.1.0; getMcpSurfaceSpec exists). So per-model
   work is mostly *exposure/wiring*, not building.

## §1 — Phasing (data prereqs → astrological elevation → multi-LLM exposure → seal)

### PHASE R0 — DATA PREREQUISITES (blocking; do first)
- **R0.1 — Re-run the MSR build against current `chart_facts`** so `constituent_facts_array` resolves at a
  healthy rate (target: the orphan rate collapses from 91.5% toward ~0 for ≥2 charts). This is an L2 Bodha
  build action, not a retrieval-code change, but the retrieval elevation is GATED on it. Verify live before
  proceeding. *(Coordinate with the L2 Bodha workstream — this is the same MSR-rebuild ISSUE-4 surfaced earlier;
  the data proves it didn't take.)*
- **R0.2 — Rebuild the `bodha_contradictions` writer + populate** so the contradiction surface is non-empty
  (currently 0 rows). Contradiction-as-first-class-output (a core astrological elevation) needs data.
- **R0.3 — Acceptance:** orphan rate healthy + contradictions populated for ≥2 charts, verified live.

### PHASE R1 — CONTAMINATION + HYGIENE FIX (safety; parallel-safe with R0)
- **R1.1 — Fix `kala_temporal.ts:156–341`** native FORENSIC hardcoded fallback → chart-agnostic or fail-loud
  (no silent native data for non-native charts). Extend the chart-agnostic CI gate to catch fallback-path
  contamination, not just defaults.
- **R1.2 — Remove dead code** (`bo_2-7.ts` / `bodha_signal_search` unimported) under the reverse-citation gate.
- **R1.3 — Acceptance:** gate green incl. fallback paths; no native data reachable by any non-native chart.

### PHASE R2 — THE KEYSTONE: REGISTRY IS THE SERVED SURFACE (the convergence)
- **R2.1 — Repoint the MCP's in-process tools to the registry** (via the platform seam), retiring the
  raw-SQL/own-pool tools under the reverse-citation gate. (Depends on the MCP plan's one-line primitives-route
  fix landing — coordinate at the seam.) After this, there is ONE retrieval surface, served to both channels.
- **R2.2 — Expose `getMcpSurfaceSpec(family)`** as the contract the MCP consumes to shape its per-model surface
  (it exists; wire it as a published seam output).
- **R2.3 — Acceptance:** every MCP tool resolves to a registry capability; no channel runs its own chart SQL;
  the single-source drift test passes (MCP == chat for the same query, ≥2 charts).

### PHASE R3 — ASTROLOGICAL ELEVATION (the heart; gated on R0)
- **R3.1 — Build domain reasoning-unit tools** (`assess_marriage`, `assess_career`, `assess_health`, …): each
  returns the RECONCILED bundle (house + lord + kāraka + relevant varga + afflictions + yogas + activating
  dasha + classical citations), grounded via resolved `fact_id`s (now that R0 fixed resolution). Derived from
  the traversal model; flag astrological-judgment calls for expert validation.
- **R3.2 — The yoga-activation-by-dasha bridge tool** — joins fired yogas (L2 signals) × timing (L3 dashas);
  the single most-asked Jyotish question shape, currently unreachable in one call.
- **R3.3 — Contradiction/convergence as first-class outputs** on every reasoning unit (now that R0.2 populated
  the data): "here is what agrees, what conflicts, how the tradition resolves it."
- **R3.4 — Whole-chart-read ENFORCEMENT** — make orient-before-domain structural (a domain reasoning unit
  internally loads orientation first; or the router refuses domain calls without it), not merely biased.
- **R3.5 — Make synergy tools real** (synergy_cross_layer / synergy_pipeline currently descriptor stubs).
- **R3.6 — Acceptance:** a domain question returns a reconciled, grounded, cited, contradiction-aware bundle on
  ≥2 charts; orient-first is enforced; astrological-judgment calls flagged for acharya review.

### PHASE R4 — MULTI-LLM CONSUMPTION ELEVATION (gated on R2 + R3)
- **R4.1 — Bundle-elasticity** — implement `response_format: minimal|standard|detailed` on the umbrella +
  reasoning-unit tools, branching for real (the enum exists in MARO types; handlers ignore it today). This is
  what lets Gemini load the exhaustive bundle in one call and Claude assemble from terse pieces.
- **R4.2 — Cross-model conclusion-consistency** — guarantee the umbrella path and the drill-chain converge on
  the same astrological answer (a test across the 4 families: same chart+question → same reconciled verdict,
  different paths). This is the real "every asset leveraged across multi-LLM" bar.
- **R4.3 — `behavioral_overrides`** — populate it for capabilities that need per-family shaping, OR drop it
  from the frozen contract via amendment (it's defined + wired but set by nobody).
- **R4.4 — Acceptance:** same query → same astrological truth across all 4 families despite different retrieval
  paths; elasticity verified at all three resolutions.

### PHASE R5 — RICHNESS (resources + prompts)
- **R5.1 — Register the resources** (chart catalog, classical vocabulary, chart structural skeleton,
  schema-of-what's-available) so big-context models can load the shape of the knowledge.
- **R5.2 — Build prompts as guided readings** ("full natal reading," "marriage timing," "current dasha") —
  zero exist today; these encode whole-chart-read discipline and give portal-like guided entry points.
- **R5.3 — Astrologically-teaching descriptions** — rewrite tool/resource descriptions so the surface itself
  teaches the LLM what each reading consists of.
- **R5.4 — Acceptance:** resources registered + served; guided-reading prompts live; descriptions rich.

### PHASE R6 — RE-SEAL
- **R6.1 — Re-validate against live code+data** (localhost↔prod, read-only).
- **R6.2 — Eval** the elevated surface (the harness exists); confirm the 14 principles still hold + the new
  reasoning-units are grounded + contradiction-aware.
- **R6.3 — Acharya-validation flags** consolidated for expert review.
- **R6.4 — Governance + version bump + re-seal.**

## §2 — Dependency order

```
R0 (data prereqs: MSR re-run + contradictions) ─┐  blocking
R1 (contamination/hygiene) ─ parallel-safe ─────┤
                                                ▼
R2 (keystone: registry = served surface) ── needs MCP one-line fix at the seam
                                                ▼
R3 (astrological elevation) ── gated on R0 (grounding) ───┐
                                                          ▼
R4 (multi-LLM exposure) ── gated on R2 + R3
                                                          ▼
R5 (richness: resources + prompts)
                                                          ▼
R6 (re-seal)
```

## §3 — Sync points with the MCP plan (the frozen seam)
- **The one-line primitives-route fix** (remove `x-mcp-audience-tier` from the guard) is MCP-plan-owned but R2
  depends on it. Coordinate: it lands first, then R2 validates the registry-served path end-to-end.
- **`getMcpSurfaceSpec`** is the published seam output (R2.2) the MCP consumes for per-model surfaces.
- **Entitlement stays at the channel** (Option 1) — retrieval does NOT add entitlement; the MCP plan wires
  `authorizeChartAccess`. This plan must NOT push entitlement into the registry (keeps it frozen).
- **Bundle-elasticity `response_format`** (R4.1) is the parameter the MCP per-model surface uses to serve
  terse-vs-exhaustive — a seam contract both sides rely on.

## §4 — What this plan does NOT do
- Does not build the MCP product layer (identity, chart-selection, session/memory, OAuth) — that's the MCP plan.
- Does not push entitlement into retrieval (Option 1; channel owns it).
- Does not run the MSR rebuild itself (R0.1 coordinates with the L2 Bodha workstream) — but gates on it.

## §5 — Execution model
Per-phase Claude Code briefs (R0…R6), worktree-isolated, reverse-citation gate on every removal, prod-verify
after merge, chart-agnostic gate green throughout. R0 + R1 can run in parallel; R3 is the largest (the
astrological heart) and is gated on R0's data fix. Consider the autonomous-swarm charter pattern for the build
if desired, but R0 (data) should be confirmed healthy before the R3 astrological build leans on it.

*End of RETRIEVAL_ELEVATION_PLAN v1.0 — the retrieval fork. Pairs with the MCP elevation plan under the frozen
sync contract.*
