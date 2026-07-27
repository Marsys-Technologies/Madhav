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
 * ToolAnnotations object or a description string) is turned into `z.object(shape).strict()`
 * before the tool is registered.
 *
 * P0 CRASH FIX (2026-07-27) — how the strict schema is DELIVERED to the SDK matters:
 * ---------------------------------------------------------------------------------
 * The original T4 implementation wrapped the shape into `z.object(shape).strict()` and passed
 * that constructed ZodObject back through the POSITIONAL `server.tool(name, desc, schema, cb)`
 * overload. That premise ("the SDK recognizes an already-constructed Zod schema instance and
 * passes it through unchanged") is TRUE only for the SDK's internal `getZodSchemaObject()`
 * (used by `_createRegisteredTool` / `registerTool`) — it is FALSE for the positional
 * `.tool()` overload parser. In @modelcontextprotocol/sdk ≥1.29.0 that parser calls
 * `isZodRawShapeCompat(firstArg)`, which returns FALSE for a constructed schema instance, so
 * the ZodObject falls through to the ToolAnnotations branch, whose "nested object" guard
 * (`Object.values(firstArg).some(v => typeof v === 'object')` — always true for a ZodObject,
 * which carries `_zod`/`_def` object internals) THROWS synchronously:
 *   `Tool <name> expected a Zod schema or ToolAnnotations, but received an unrecognized object`
 * This crashed the Node process on the FIRST strict-ified registration reached at request time
 * (`prashna_ask`, registered before the profile gate), taking down the whole MCP server. The
 * bug is general — it fires for ANY strict-ified tool (a flat `{a: z.string()}` shape crashes
 * identically); it is NOT specific to `prashna_ask` or its nested-optional `scope_tuple`.
 *
 * The positional `.tool(name, desc, RAW_SHAPE, cb)` overload only accepts a RAW SHAPE (which
 * the SDK then converts via the non-strict `objectFromShape`). The SDK's supported way to hand
 * it a fully-constructed (strict) schema is `registerTool(name, { inputSchema }, cb)` →
 * `getZodSchemaObject()` passes a schema instance through unchanged, preserving `.strict()`.
 * So this gate now parses the positional `.tool()` overload the same way the SDK does and, when
 * a raw shape is present, re-issues the registration via `registerTool` with a strict
 * `inputSchema`. Calls with no raw shape (no-param tools, annotations-only, an already-built
 * schema) are passed through to the original `.tool()` byte-for-byte. Still no SDK
 * modification and no per-call-site edits across the ~30 tool-registration files.
 *
 * SCOPE WIDENED (ŚODHANA-ŚEṢA W3.4, 2026-07-27): the T1/T5/T7/T8 exclusions below existed for
 * exactly one reason — those builders' files were being concurrently edited mid-campaign and a
 * strict-schema behavior change landing under their feet risked a spurious rejection colliding
 * with their own in-flight fix. All ten ŚODHANA track PRs are now merged to `main`; the
 * merge-conflict reason no longer applies. This gate now also covers: `dossier` (T5),
 * `muhurta_finder` + the 7 `remedy_tools.ts` legacy names (T7), every tool
 * `register_p1_synthesis.ts` registers (T1), and `ganita_yogas_get`/`ganita_yoga_firings_get`
 * (T8). Verified via the T3 envelope battery (`shodhana_t3_serving_battery.test.ts`) plus this
 * file's own real-SDK regression test (`strict_tool_schema_gate.test.ts`, the #812 P0 template)
 * — no newly-covered tool's real callers pass an undeclared param, so none needed a documented
 * loose-param exception.
 *
 * SCOPE (still excluded): the 3 `register_gochara_windows.ts` tools (`kala_gochara_windows` data
 * is untouchable — this campaign's rails do not authorize touching anything in that path, even a
 * schema-strictness change on its serving tools) and every tool `registry_bridge.ts` registers
 * (still PV-locked in the parent ŚODHANA brief's rails; this fast-follow's own §2 rails do not
 * re-clear it, so it stays out of scope here). These remaining names are excluded from
 * strict-ification by NAME here — this file does not edit either of those source files, so it
 * carries zero merge-conflict risk with whoever eventually clears them. If a genuinely
 * load-bearing undeclared field surfaces for some OTHER tool after this gate goes live (the
 * exact risk the T4 brief flagged), add its name to the exclusion set below with a comment
 * explaining why, rather than reverting the whole gate.
 */
import { z } from 'zod'

/**
 * Structural shape this gate needs: the positional `.tool(name, ...)` registration method it
 * monkeypatches, plus the config-object `.registerTool(name, config, cb)` method it re-issues a
 * strict-ified registration through (the positional `.tool()` overload cannot accept a
 * constructed ZodObject in @modelcontextprotocol/sdk ≥1.29.0 — see file banner).
 */
export interface StrictSchemaGateServer {
  tool: (name: string, ...rest: unknown[]) => unknown
  registerTool: (
    name: string,
    config: { description?: string; inputSchema: z.ZodTypeAny; annotations?: Record<string, unknown> },
    cb: unknown,
  ) => unknown
}

/**
 * Tool names deliberately left OUT of the portal-wide strict-schema posture change. As of
 * ŚODHANA-ŚEṢA W3.4 (2026-07-27) this is narrowed to `registry_bridge.ts`'s tools (still
 * PV-locked) and `register_gochara_windows.ts`'s tools (`kala_gochara_windows` data untouchable
 * — this campaign's rails forbid touching anything in that path). The T1/T5/T7/T8 mid-campaign
 * merge-conflict exclusions have been removed now that all ten ŚODHANA tracks are merged. See
 * file banner for full rationale.
 */
export const STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES: ReadonlySet<string> = new Set([
  // tools/retrieval/register_gochara_windows.ts (kala_gochara_windows data untouchable)
  'gochara_activation_get', 'gochara_forecast_get', 'gochara_election_avoidance_get',
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
 * set that carries a raw zod shape is re-issued as a strict registration — an unknown/misspelled
 * param now fails loudly (`Input validation error`) instead of being silently dropped. Call
 * ONCE, on a fresh per-request `McpServer`, before any `register*Tools()` call site runs — order
 * relative to the other two gates does not matter (each wraps whatever `server.tool` currently
 * is at the time it is applied; this gate is innermost when applied first, so the deprecated /
 * profile filters have already run and delegated down by the time it executes, and re-issuing
 * through `registerTool` therefore bypasses no filtering).
 *
 * The strict schema is delivered via `registerTool(name, { inputSchema }, cb)`, NOT by passing a
 * constructed ZodObject back through the positional `.tool()` overload — the latter crashes the
 * SDK (≥1.29.0). See the file banner ("P0 CRASH FIX") for the full mechanism. To stay faithful
 * to the SDK's own dispatch, this parses the positional overload exactly as
 * `McpServer.tool()` does: optional leading description string, then the params schema, then an
 * optional ToolAnnotations object, then the callback.
 */
export function applyStrictSchemaGate(server: StrictSchemaGateServer): void {
  const originalTool = server.tool.bind(server)
  const originalRegisterTool = server.registerTool.bind(server)
  server.tool = (name: string, ...rest: unknown[]) => {
    if (STRICT_SCHEMA_GATE_EXCLUDED_TOOL_NAMES.has(name)) {
      return originalTool(name, ...rest)
    }
    // Mirror the SDK's positional-overload parsing (see McpServer.tool):
    //   tool(name, [description], [paramsSchema], [annotations], cb)
    const args = [...rest]
    let description: string | undefined
    if (typeof args[0] === 'string') {
      description = args.shift() as string
    }
    // A raw zod shape only appears as the params-schema slot; if there is one, and there is a
    // callback after it (length > 1), re-issue the registration strictly via registerTool.
    if (args.length > 1 && isRawZodShape(args[0])) {
      const rawShape = args.shift() as Record<string, z.ZodTypeAny>
      const inputSchema = z.object(rawShape).strict()
      let annotations: Record<string, unknown> | undefined
      if (args.length > 1 && typeof args[0] === 'object' && args[0] !== null && !isRawZodShape(args[0])) {
        annotations = args.shift() as Record<string, unknown>
      }
      const cb = args[0]
      const config = annotations !== undefined
        ? { description, inputSchema, annotations }
        : { description, inputSchema }
      return originalRegisterTool(name, config, cb)
    }
    // No raw shape to strict-ify (no-param tool, annotations-only, or an already-built schema):
    // pass through to the original .tool() untouched.
    return originalTool(name, ...rest)
  }
}
