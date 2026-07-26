/**
 * strict_tool_schema_gate.ts — ŚODHANA T4 (MC-024): portal-wide unknown-param rejection
 * ========================================================================================
 * MC-024 finding: unknown/unsupported tool params (e.g. a misspelled filter name) were
 * silently accepted-and-ignored by every `server.tool()` registration in this codebase —
 * the MCP SDK's `getZodSchemaObject()` (@modelcontextprotocol/sdk/dist/esm/server/mcp.js)
 * wraps a raw zod shape via `objectFromShape()` (zod-compat.js), which is a plain
 * `z.object(shape)` — DEFAULT `.strip()` mode, so an unrecognized key is dropped before the
 * handler ever sees it, with NO error surfaced to the caller. A handful of tools (e.g.
 * `dossier`) already reject unknown params loudly via their own explicit `.strict()` zod
 * object — this inconsistency across the portal (silent-drop here, loud-reject there) is
 * itself the defect: a consumer cannot distinguish "filter unsupported" from "filter
 * accepted but empty result."
 *
 * FIX: monkeypatch this request-scoped `McpServer` instance's `.tool()` registration method
 * (same established pattern as `mcp_profile.ts::applyProfileGate` and
 * `deprecated_tool_gate.ts::applyDeprecatedToolGate` — both already monkeypatch this exact
 * method for their own cross-cutting concerns) so that whichever argument in the call is a
 * raw zod shape (a plain object whose every value is a Zod schema instance — as opposed to a
 * ToolAnnotations object or a description string) gets wrapped in `z.object(shape).strict()`
 * before being handed to the real SDK registration. The SDK's own `getZodSchemaObject()`
 * recognizes an already-constructed Zod schema instance (`isZodSchemaInstance`) and passes it
 * through UNCHANGED instead of re-deriving it via the non-strict `objectFromShape` — so this
 * is a drop-in behavioral upgrade with no SDK modification required, and no per-call-site
 * edits across the ~30 tool-registration files needed.
 *
 * SCOPE (ŚODHANA T4 rails): every tool EXCEPT the ones this builder was told to stay out of —
 * `dossier`, `muhurta_finder`, the 7 `remedy_tools.ts` legacy names, the 3
 * `register_gochara_windows.ts` tools (kala_gochara_windows data is untouchable), every tool
 * `register_p1_synthesis.ts` registers (T1's territory — verdict-verb logic lives there),
 * `ganita_yogas_get`/`ganita_yoga_firings_get` (T8's yoga-firings territory), and every tool
 * `registry_bridge.ts` registers (PV-locked, DO NOT TOUCH). These names are excluded from
 * strict-ification by NAME here — this file does not edit any of those source files, so it
 * carries zero merge-conflict risk with the builders who own them. If a genuinely
 * load-bearing undeclared field surfaces for some OTHER tool after this gate goes live (the
 * exact risk the T4 brief flagged), add its name to the exclusion set below with a comment
 * explaining why, rather than reverting the whole gate.
 */
import { z } from 'zod'

/** Structural shape this gate needs — any object with a `.tool(name, ...)` registration method. */
export interface StrictSchemaGateServer {
  tool: (name: string, ...rest: unknown[]) => unknown
}

/**
 * Tool names deliberately left OUT of the portal-wide strict-schema posture change (ŚODHANA
 * T4 rails — files/logic owned by other builders in the same campaign, or explicitly marked
 * untouchable). See file banner for the per-name rationale.
 */
export const STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES: ReadonlySet<string> = new Set([
  // tools/dossier.ts
  'dossier',
  // tools/muhurta_finder.ts
  'muhurta_finder',
  // tools/retrieval/remedy_tools.ts
  'query_remedies', 'query_remedies_for_chart', 'list_remedies_by_category', 'read_remedy',
  'query_tantric_remedies', 'query_remedies_by_planet', 'query_mantras',
  // tools/retrieval/register_gochara_windows.ts (kala_gochara_windows data untouchable)
  'gochara_activation_get', 'gochara_forecast_get', 'gochara_election_avoidance_get',
  // tools/register_p1_synthesis.ts (T1's territory)
  'mimamsa_insight_get', 'bodha_discoveries_get', 'kala_life_arc_get',
  'synth_tail_divergence_get', 'synth_chart_brief_get', 'prashna_undertaking_get',
  // yoga-firings serving (T8's territory)
  'ganita_yogas_get', 'ganita_yoga_firings_get',
  // tools/registry_bridge.ts (PV-locked, DO NOT TOUCH)
  'get_chart_orientation', 'get_domain_reading', 'get_signals', 'traverse_graph',
  'get_positions', 'get_dashas', 'get_temporal_windows', 'get_projections',
  'get_classical_citation', 'get_remedies', 'get_chart_quality', 'list_assets',
  'tool_search', 'assess_marriage', 'assess_career', 'assess_health', 'assess_wealth',
  'yoga_activation_by_dasha', 'get_cgm_subgraph', 'query_chart_facts', 'chart_snapshot',
  'get_graha_yuddha', 'vector_search', 'judgment_query', 'graha_portrait', 'pact_query',
])

function isZodSchemaLike(v: unknown): v is z.ZodTypeAny {
  return !!v && typeof v === 'object' &&
    typeof (v as { parse?: unknown }).parse === 'function' &&
    typeof (v as { safeParse?: unknown }).safeParse === 'function'
}

/**
 * A `server.tool()` argument is a raw zod SHAPE (as opposed to a `ToolAnnotations` metadata
 * object or a description string) iff it is a plain, non-empty object every value of which is
 * itself a Zod schema instance. `ToolAnnotations` values are booleans/strings; a description
 * argument is a string, not an object — neither is mistaken for a shape by this check. An
 * already-constructed Zod schema instance (a tool that already builds its own `z.object()`,
 * e.g. `dossier`) is excluded too — re-wrapping it would be redundant, not wrong, but it is
 * also simply never reached here since those tool names are in the exclusion set above.
 */
function isRawZodShape(v: unknown): v is Record<string, z.ZodTypeAny> {
  if (!v || typeof v !== 'object' || Array.isArray(v) || isZodSchemaLike(v)) return false
  const values = Object.values(v as Record<string, unknown>)
  if (values.length === 0) return false
  return values.every(isZodSchemaLike)
}

/**
 * Monkeypatches `server.tool()` IN PLACE (same pattern as `applyProfileGate` /
 * `applyDeprecatedToolGate`) so every registration call for a tool name NOT in the exclusion
 * set gets its raw zod shape argument (if any) wrapped in `z.object(shape).strict()` before
 * reaching the real SDK registration — an unknown/misspelled param now fails loudly
 * (`Input validation error`) instead of being silently dropped. Call ONCE, on a fresh
 * per-request `McpServer`, before any `register*Tools()` call site runs — order relative to
 * the other two gates does not matter (each wraps whatever `server.tool` currently is at the
 * time it is applied, so the chain composes regardless of application order).
 */
export function applyStrictSchemaGate(server: StrictSchemaGateServer): void {
  const originalTool = server.tool.bind(server)
  server.tool = (name: string, ...rest: unknown[]) => {
    if (STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES.has(name)) {
      return originalTool(name, ...rest)
    }
    const wrapped = rest.map(arg => (isRawZodShape(arg) ? z.object(arg).strict() : arg))
    return originalTool(name, ...wrapped)
  }
}
