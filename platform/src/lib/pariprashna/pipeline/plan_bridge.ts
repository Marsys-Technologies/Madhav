/**
 * plan_bridge.ts — P3-A (ONE ENGINE, ONE DOOR): unified plan type + total,
 * bidirectional `tool_name` ↔ `primitive_id` map.
 *
 * ── What P3-A actually found (read before extending this file) ───────────────
 *
 * The brief's framing ("the web door plans in PipelinePlan/tool_name terms, the
 * MCP door plans in VidhiPlan/primitive_id terms") undersold how much is already
 * unified. Investigation (this lane) found `PipelinePlan`
 * (`@/lib/pipeline/types`) is ALREADY the plan type behind THREE engine call
 * sites: the Paripraśna web door (`plan_stage.ts` below, via `callPipelinePlanner`
 * + `compileFloorForPlan`), the legacy `/api/chat/consult` route, AND the MCP
 * `prashna_ask` engine route (`platform/src/app/api/mcp/prashna_ask/route.ts`) —
 * that route's own header states plainly: "`platform-mcp` has no import path to
 * [callPipelinePlanner/compileFloorForPlan]... prashna_ask's actual engine call...
 * has to live here, in `platform`". So `prashna_ask` (the MCP door's
 * "answer this end-to-end" capability) is NOT built on `VidhiPlan` at all.
 *
 * `VidhiPlan` (`platform-mcp/src/resources/vidhi/plan_builder.ts`) backs a
 * DIFFERENT MCP capability — `plan_retrieval` / the `vidhi_plan` prompt — a
 * "hand me the compiled floor, I will self-execute it" plan for an external LLM
 * caller, expressed in Vidhi's own vocabulary: `primitive_id` (the atom's stable
 * name) + `live_tool` (the MCP-facing tool the primitive is defined against).
 * `platform` and `platform-mcp` are separate deployables/processes (see
 * `@/lib/vidhi/types.ts`'s `QuestionFrame` header) — `VidhiPlan` cannot be
 * imported into `platform`, and this lane's `may_touch` is scoped to
 * `platform/src/lib/pariprashna/**` only, so this file cannot reach into
 * `platform-mcp` to unify the two at the class/object level even if that were
 * otherwise desirable.
 *
 * What CAN be unified here, and what this file does:
 *   1. `UnifiedPlanStep` — one step shape that losslessly represents EITHER
 *      vocabulary: an LLM-planner-authored `ToolCallItem` (tool_name-native, no
 *      Vidhi identity) or a compiled Vidhi `CompiledFloorItem`
 *      (primitive_id + live_tool-native, resolved to a `tool_name` when one
 *      exists). Neither side is rewritten; this is a pure adapter, per §I
 *      "narrow-scoped fix over broad refactor".
 *   2. `PRIMITIVE_TOOL_BINDINGS` — the TOTAL map, one entry per primitive_id in
 *      the live `VIDHI_PRIMITIVES` registry (not per distinct `live_tool` — see
 *      the note below on why that distinction matters), classifying each as
 *      covered (has a resolvable `tool_name`) or honestly enumerated as
 *      uncovered with its `live_tool` (§N.7 item 6: no plausible-looking
 *      mapping in place of "we don't have one").
 *
 * ── Why primitive_id granularity, not live_tool granularity ───────────────────
 *
 * `compiled_floor_adapter.ts`'s `LIVE_TOOL_TO_RETRIEVAL` + `resolveLiveTool`
 * operate on `live_tool` (40 distinct values, as measured by this lane against
 * the live registry — see the test file). But `VIDHI_PRIMITIVES` has 60 entries:
 * several primitives share one `live_tool` (e.g. six condition-facet primitives
 * all declare `live_tool: 'ganita_condition_get'` — see
 * `NAMESPACE_COVERAGE_v2_0.md` RC-10-003). A map that only enumerates the 40
 * distinct tool names is not the map Paripraśna's plan actually needs: the plan
 * carries `primitive_id`s (via the compiled floor), and "is this primitive
 * covered" is the real question the completeness receipt (`completeness_wiring.ts`)
 * answers per-primitive already. This module makes that same TOTAL,
 * primitive_id-keyed judgment reusable, testable, and CI-provable in one place
 * rather than re-derived ad hoc.
 *
 * ── RC-10 is measurably stale against the live registry (finding, not fixed here) ─
 *
 * `NAMESPACE_COVERAGE_v2_0.md` (RC-10/R-9) measured "20/23 bridged, 3 deferred"
 * against a 23-distinct-`live_tool` snapshot. The live registry today
 * (`@/lib/vidhi/registry_data.ts`) has GROWN to 40 distinct `live_tool` values
 * across 60 primitives (ṢAḌ-DARŚANA W5's kala_* views and others were added
 * after RC-10 was written) — of which only 21 currently resolve to a
 * web-executable `tool_name` via `resolveLiveTool`. This module reports the
 * CURRENT, measured reality (19 uncovered `live_tool`s as of this writing, per
 * `getPlanBridgeCoverage()`), not RC-10's frozen count. See this lane's DD
 * finding for the full writeup — closing that specific gap is out of scope for
 * P3-A (it is real engineering per primitive, the same "not mechanical" shape
 * RC-10-001/002/003 already documented for 3 of the 19), and none of the 19 is
 * force-mapped to a plausible-but-wrong URI to make the coverage number look
 * better (the exact defect class §N.7 item 6 / §N.8 exist to catch).
 */

import { VIDHI_PRIMITIVES } from '@/lib/vidhi/registry_data'
import { resolveLiveTool } from '@/lib/pipeline/compiled_floor_adapter'
import type { PipelinePlan, ToolCallItem } from '@/lib/pipeline/types'
import type { CompiledFloorItem } from '@/lib/vidhi/types'

// ─────────────────────────────────────────────────────────────────────────────
// §1. UnifiedPlanStep — one step shape for both plan vocabularies
// ─────────────────────────────────────────────────────────────────────────────

export type UnifiedPlanStepOrigin = 'llm_planner' | 'vidhi_floor' | 'vidhi_machine_band'

/**
 * A single plan step, losslessly representable from either an LLM-planner
 * `ToolCallItem` (web/`prashna_ask` engine door) or a compiled Vidhi
 * `CompiledFloorItem` (the deterministic floor/machine-band, primitive_id-native).
 *
 * Invariant (checked by the constructors below, asserted by the test file):
 * `tool_name` and `primitive_id` are never BOTH null — a step must carry at
 * least one identity. `live_tool` is Vidhi-native metadata, present only when
 * the step originated from a compiled floor item.
 *
 * Deliberately NOT collapsed to a single `id` field: `tool_name` and
 * `primitive_id` are different vocabularies with a many-to-one relationship
 * (several primitive_ids can share one tool_name — see the module header), so
 * silently picking one at random `[0]`-style would be the exact "no `.find()`/
 * `.filter()[0]` without a key check" defect class §N.7 item 2 forbids. Callers
 * that need "the primitive_id(s) this tool_name serves" use
 * `TOOL_NAME_TO_PRIMITIVE_IDS` (§2) explicitly, as a set, never a single guess.
 */
export interface UnifiedPlanStep {
  /** Web-executable identity (what `getToolByName()` / the retrieval registry accepts). Null only when this step has no resolvable tool_name (an uncovered Vidhi primitive). */
  readonly tool_name: string | null
  /** Vidhi-native identity. Null for a step with no Vidhi primitive behind it (an LLM-planner-improvised tool call). */
  readonly primitive_id: string | null
  /** Vidhi's own MCP-facing tool vocabulary (`VidhiPrimitive.live_tool`). Null unless this step came from a compiled floor item. */
  readonly live_tool: string | null
  readonly origin: UnifiedPlanStepOrigin
  readonly params: Readonly<Record<string, unknown>>
  readonly token_budget: number
  readonly priority: 1 | 2 | 3
  readonly reason: string
}

/** Lift an LLM-planner `ToolCallItem` (PipelinePlan.tool_calls) into a UnifiedPlanStep. */
export function fromToolCallItem(item: ToolCallItem): UnifiedPlanStep {
  return {
    tool_name: item.tool_name,
    primitive_id: null, // honest null — see the "deliberately NOT collapsed" note above
    live_tool: null,
    origin: 'llm_planner',
    params: item.params,
    token_budget: item.token_budget,
    priority: item.priority,
    reason: item.reason,
  }
}

/**
 * Lift a compiled Vidhi floor item (`CompiledFloorItem`, from either
 * `contract.floor` or `contract.machine_band`) into a UnifiedPlanStep.
 * `tool_name` resolves via the SAME `resolveLiveTool` `compiled_floor_adapter.ts`
 * already uses for the web engine — never a second, divergent resolution path.
 */
export function fromCompiledFloorItem(
  item: CompiledFloorItem,
  origin: 'vidhi_floor' | 'vidhi_machine_band',
): UnifiedPlanStep {
  return {
    tool_name: resolveLiveTool(item.live_tool) ?? null,
    primitive_id: item.primitive_id,
    live_tool: item.live_tool,
    origin,
    params: item.tool_args,
    token_budget: origin === 'vidhi_floor' ? 600 : 400, // mirrors compiled_floor_adapter.ts's BAND_BUDGET
    priority: origin === 'vidhi_floor' ? 1 : 2, // mirrors compiled_floor_adapter.ts's BAND_PRIORITY
    reason: `vidhi ${origin}: ${item.primitive_id}`,
  }
}

/**
 * Build the full unified step list for a resolved `PipelinePlan` plus its
 * (optional) compiled Vidhi contract. Pure/total: never throws, never drops a
 * step. Order: LLM-authored tool_calls first (plan's own order preserved), then
 * floor, then machine_band — the same precedence `plan_stage.ts` already
 * applies when merging (LLM output first, floor fills gaps).
 */
export function buildUnifiedPlan(
  plan: Pick<PipelinePlan, 'tool_calls'>,
  compiledContract?: { floor: readonly CompiledFloorItem[]; machine_band: readonly CompiledFloorItem[] } | null,
): UnifiedPlanStep[] {
  const steps: UnifiedPlanStep[] = plan.tool_calls.map(fromToolCallItem)
  if (compiledContract) {
    for (const item of compiledContract.floor) steps.push(fromCompiledFloorItem(item, 'vidhi_floor'))
    for (const item of compiledContract.machine_band) steps.push(fromCompiledFloorItem(item, 'vidhi_machine_band'))
  }
  return steps
}

// ─────────────────────────────────────────────────────────────────────────────
// §2. The total, bidirectional tool_name ↔ primitive_id map
// ─────────────────────────────────────────────────────────────────────────────

/** One primitive's binding to a web-executable tool_name, or the honest absence of one. */
export interface PrimitiveToolBinding {
  readonly primitive_id: string
  readonly live_tool: string
  /** Null = uncovered. Never a plausible-looking guess (§N.7 item 6). */
  readonly tool_name: string | null
}

/** The minimal shape `computePrimitiveToolBindings` needs from a primitive registry entry. */
export interface PrimitiveIdentitySource {
  readonly primitive_id: string
  readonly live_tool: string
}

/**
 * Pure, parameterized builder — TOTAL over `primitives` by construction
 * (`.map()`, one output entry per input entry, never a `.filter()` that could
 * silently drop one). Extracted from the module-scope singleton below so
 * `plan_bridge.test.ts` can run the SAME construction logic against a
 * deliberately broken synthetic fixture and prove the completeness assertion
 * built on top of it is capable of failing (§N.8) — a test that only ever runs
 * against the real, already-registered `VIDHI_PRIMITIVES` cannot demonstrate
 * that, since every real primitive is present in the registry array by
 * definition.
 */
export function computePrimitiveToolBindings(
  primitives: readonly PrimitiveIdentitySource[],
  resolve: (liveTool: string) => string | undefined,
): PrimitiveToolBinding[] {
  return primitives.map((p) => ({
    primitive_id: p.primitive_id,
    live_tool: p.live_tool,
    tool_name: resolve(p.live_tool) ?? null,
  }))
}

/**
 * TOTAL over the live `VIDHI_PRIMITIVES` registry: every primitive_id present
 * in the registry at evaluation time has exactly one entry here — there is no
 * code path that can silently drop a primitive. This is the property
 * `plan_bridge.test.ts`'s completeness proof asserts.
 */
export const PRIMITIVE_TOOL_BINDINGS: readonly PrimitiveToolBinding[] = computePrimitiveToolBindings(
  VIDHI_PRIMITIVES,
  resolveLiveTool,
)

/** primitive_id -> tool_name, covered entries only (uncovered primitives are absent, not null-valued). */
export const PRIMITIVE_ID_TO_TOOL_NAME: ReadonlyMap<string, string> = new Map(
  PRIMITIVE_TOOL_BINDINGS.filter(
    (b): b is PrimitiveToolBinding & { tool_name: string } => b.tool_name !== null,
  ).map((b) => [b.primitive_id, b.tool_name]),
)

/**
 * tool_name -> primitive_id[], reverse of the above. A bucket (array), never a
 * single value — several primitive_ids legitimately share one tool_name (see
 * module header), and collapsing that to `[0]` would be the exact
 * unqualified-reduction defect §N.7 item 2 forbids.
 */
export const TOOL_NAME_TO_PRIMITIVE_IDS: ReadonlyMap<string, readonly string[]> = (() => {
  const m = new Map<string, string[]>()
  for (const b of PRIMITIVE_TOOL_BINDINGS) {
    if (b.tool_name === null) continue
    const bucket = m.get(b.tool_name)
    if (bucket) bucket.push(b.primitive_id)
    else m.set(b.tool_name, [b.primitive_id])
  }
  return m
})()

/** Primitives with NO resolvable tool_name, enumerated explicitly (never silently dropped). */
export const UNCOVERED_BINDINGS: readonly PrimitiveToolBinding[] = PRIMITIVE_TOOL_BINDINGS.filter(
  (b) => b.tool_name === null,
)

export interface PlanBridgeCoverage {
  readonly total_primitives: number
  readonly covered_primitives: number
  readonly uncovered_primitives: number
  readonly total_distinct_live_tools: number
  readonly covered_live_tools: number
  /** Distinct `live_tool` names with zero resolvable tool_name, sorted for stable diffs. */
  readonly uncovered_live_tools: readonly string[]
}

/**
 * Live coverage summary, always computed (never cached/stale) from the current
 * `PRIMITIVE_TOOL_BINDINGS`. This is the number a CI assertion or a future
 * observability surface reads — it can only report what the map above actually
 * computed, so it cannot drift from it (§N.8: the signal and its detector are
 * the same code path).
 */
export function getPlanBridgeCoverage(): PlanBridgeCoverage {
  const distinctLiveTools = new Set(PRIMITIVE_TOOL_BINDINGS.map((b) => b.live_tool))
  const uncoveredLiveTools = new Set(UNCOVERED_BINDINGS.map((b) => b.live_tool))
  return {
    total_primitives: PRIMITIVE_TOOL_BINDINGS.length,
    covered_primitives: PRIMITIVE_TOOL_BINDINGS.length - UNCOVERED_BINDINGS.length,
    uncovered_primitives: UNCOVERED_BINDINGS.length,
    total_distinct_live_tools: distinctLiveTools.size,
    covered_live_tools: distinctLiveTools.size - uncoveredLiveTools.size,
    uncovered_live_tools: [...uncoveredLiveTools].sort(),
  }
}
