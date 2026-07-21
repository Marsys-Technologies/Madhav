/**
 * mcp_surface_profile_builder.ts — R-1 projection compiler, 6th artifact (W5 L2)
 * ================================================================================
 * RETRIEVAL_PLANE_ELEVATION_PLAN_v1_0.md §R-4 item 1: "Projections from R-1 become
 * real served surfaces: MCP-full (expert), MCP-compact (~25–35 umbrellas +
 * marsys_drill dispatcher, leaves reachable via drill_pointers), MCP-consult (per
 * OT-10: prashna_ask + ~5 orienting tools)." Ruling RC-1 (master brief §C):
 * "≤20 umbrellas for non-Claude families." Item 2: "Profile selection = entitlement
 * (OT-10 b+c): OAuth scope / connect URL selects the projection; a plain guest
 * cannot reach raw tools."
 *
 * This module builds THREE named, generated projections — full / compact≤20 /
 * consult — as a 6th output of the SAME projection compiler `generate_projections.ts`
 * already extended once this wave (W5 L1's `web_tool_bridge_builder.ts`). It is NOT
 * a second, parallel compiler: it is a pure function over the same `CapabilityDescriptor[]`
 * (`getCatalog()`) every other projection in this directory already consumes, reusing
 * `buildMcpToolRegistration` (projection_builders.ts) for the per-tool shape.
 *
 * SOURCE OF THE THREE SETS: the registry's own `projection_tags` field (D1 contract,
 * `descriptor_defaults.ts`) already declares `mcp_full` / `mcp_compact` / `mcp_consult`
 * per capability (see that file's mechanical rule: L-ORIENT traversal → all four tags
 * incl. mcp_consult; leaf tool_role → mcp_full only; everything else → chat+mcp_full+
 * mcp_compact). This builder does not invent a second classification — it SELECTS
 * within the tag the registry already declares, per profile:
 *
 *   - full:    every mcp_full-tagged tool, uncapped (the "MCP-full / expert" profile).
 *   - compact: mcp_compact-tagged tools, RANKED and CAPPED at COMPACT_MAX_TOOLS (20,
 *              per RC-1), so a non-Claude family's tools/list never exceeds the
 *              cross-vendor ≤20 target. Ranking precedence (types.ts's own documented
 *              order): (1) demand_ranking.bearing_first (true first), (2) family_rank
 *              ascending (unset sorts last), (3) static_salience descending (unset = 0),
 *              (4) name ascending (final deterministic tiebreaker). Tools cut by the cap
 *              are NOT dropped from the catalog — they remain reachable via the `full`
 *              profile and via each surfaced tool's own `drill_children` — reported
 *              honestly in `overflow_tool_names`, never silently discarded.
 *   - consult: mcp_consult-tagged tools only — the restricted "safe by default"
 *              profile (plan §6.5: "consultation profile default; raw tools scope-
 *              gated"). No `full`/`compact`-only tool is ever reachable from this set.
 *
 * F-R7 (NO-LEAKAGE, ACCEPTED ruling): `calibration_context_only` capabilities are
 * excluded from ALL THREE profiles here (this builder's own enforcement — the plan's
 * exact words are "excluded from ALL projections... + a CI canary"). Honest residual:
 * the OTHER four projections this compiler already emits (chat/mcp_full/mcp_compact
 * top-level in `projection_builders.ts`) do NOT yet apply this filter — flagged, not
 * silently fixed in place here (that touches a file this lane did not open to rewrite;
 * a natural next-wave tightening).
 *
 * `marsys_drill` dispatcher: the plan's compact-profile prose names a dispatcher tool
 * that does not exist in this catalog yet (no capability registered under that name —
 * confirmed by grep). Not fabricated here. The existing `drill_children` field on every
 * descriptor already gives the SAME "leaves reachable by drill" guarantee the dispatcher
 * would provide; this builder reports overflow tools' reachability via that existing
 * mechanism instead of inventing the dispatcher tool. A future wave may still want the
 * literal `marsys_drill` tool for a single fixed drill-call shape — out of this lane's
 * scope, recorded as a residual in the generator's report, not built here.
 */
import type { CapabilityDescriptor } from '../../src/lib/retrieval/registry/types'
import { resolveType, buildMcpToolRegistration, type McpToolRegistration } from './projection_builders'

export type McpProfileName = 'full' | 'compact' | 'consult'

/** RC-1: "≤20 umbrellas for non-Claude families." Applied to the compact profile only. */
export const COMPACT_MAX_TOOLS = 20

export interface McpSurfaceProfile {
  profile: McpProfileName
  /** null = uncapped (full profile only). */
  max_tools: number | null
  /** Count of tools actually surfaced in this profile (== tools.length). */
  total: number
  tool_names: string[]
  tools: McpToolRegistration[]
  /**
   * Eligible-but-not-surfaced tool names (compact only, when eligible count > max_tools).
   * Reachable via the `full` profile or via a surfaced sibling's `drill_children` —
   * never silently dropped from the catalog, just not in THIS profile's tools/list.
   */
  overflow_tool_names: string[]
  /** F-R7 honesty note: names excluded from this profile because calibration_context_only === true. */
  excluded_calibration_context_only: string[]
  /**
   * Real finding, this lane (not a plan-cited residual): `descriptor_defaults.ts`'s
   * mechanical projection_tags rule ("L-ORIENT → all four tags incl. mcp_consult")
   * sweeps up several capabilities whose OWN authored description explicitly says
   * "Not LLM-facing" (`maro_orchestrate`, `maro_mcp_surface`, `synergy_pipeline`,
   * `synergy_cross_layer`, `route`, `channel_mcp_wiring`, `channel_chat_dispatch` —
   * internal orchestration/introspection meta-tools consumed by the D8 eval harness
   * and D3 grounding spine, never meant for any LLM client) into the SAME L-ORIENT
   * bucket as genuine orienting tools like `get_chart_header`/`chart_snapshot`. Two of
   * these (`channel_mcp_wiring`/`channel_chat_dispatch`) are already known-excluded via
   * `projection_tags` left `undefined` (STATE.md W2 descriptor-migration note) — the
   * REST are not, and would otherwise leak into every profile including the most-
   * restricted `consult` one. This builder detects and excludes them by their own
   * descriptor text (`/not llm-facing/i` in `description`) rather than a hardcoded
   * name list, so a NEW internal meta-tool authored the same way is caught the same
   * way. Recorded here, not silently fixed at the source (`descriptor_defaults.ts`'s
   * L-ORIENT rule is out of this lane's scope to rewrite) — a real residual for
   * whoever owns that rule next.
   */
  excluded_not_llm_facing: string[]
}

interface RankableCapability {
  cap: CapabilityDescriptor
  bearingFirst: boolean
  familyRank: number
  staticSalience: number
}

function toRankable(cap: CapabilityDescriptor): RankableCapability {
  const dr = cap.demand_ranking
  return {
    cap,
    bearingFirst: dr?.bearing_first === true,
    // Unset family_rank sorts LAST (a huge ordinal), never first — an absent rank is
    // not a claim of top priority.
    familyRank: dr?.family_rank ?? Number.MAX_SAFE_INTEGER,
    staticSalience: dr?.static_salience ?? 0,
  }
}

/**
 * demand_ranking precedence per types.ts's own documented order: bearing_first,
 * then family_rank ascending, then static_salience descending, then name ascending
 * as the final deterministic tiebreaker (never leave sort order to object insertion
 * order, which getCatalog() does not itself guarantee is stable across builds).
 */
function compareRank(a: RankableCapability, b: RankableCapability): number {
  if (a.bearingFirst !== b.bearingFirst) return a.bearingFirst ? -1 : 1
  if (a.familyRank !== b.familyRank) return a.familyRank - b.familyRank
  if (a.staticSalience !== b.staticSalience) return b.staticSalience - a.staticSalience
  return a.cap.name.localeCompare(b.cap.name)
}

/** See `excluded_not_llm_facing` doc comment above — grounded in the descriptor's own authored text. */
const NOT_LLM_FACING_PATTERN = /not llm-facing/i

/**
 * Supplementary explicit exclusion, found while verifying the pattern above against the
 * live catalog: `dprofiles_registration.ts`'s MODULE-LEVEL doc comment states all three
 * MARO meta-capabilities are "NOT LLM-facing for end-user queries", but only TWO of the
 * three (`maro_orchestrate`, and `synergy_pipeline`/`synergy_cross_layer` in the sibling
 * D6 file) actually carry that phrase in their own per-capability `description` field —
 * `maro_mcp_surface`'s `description` omits it, so the pattern above does not catch it,
 * even though the same file's module comment claims it. Added explicitly by name rather
 * than silently trusting the pattern alone, since a false negative here is exactly the
 * "consult profile reaches a raw/internal tool" failure mode the V5 gate checks for.
 * Flagged as a real registry-authoring inconsistency for whoever owns
 * `dprofiles_registration.ts` next (the fix belongs in that capability's own
 * `description` text, not here) — not silently patched at the source, out of this
 * lane's scope to rewrite that file.
 */
const KNOWN_INTERNAL_NOT_IN_OWN_DESCRIPTION = new Set(['maro_mcp_surface'])

function eligibleForTag(caps: CapabilityDescriptor[], tag: 'mcp_full' | 'mcp_compact' | 'mcp_consult'): {
  eligible: CapabilityDescriptor[]
  excludedCalibrationContextOnly: string[]
  excludedNotLlmFacing: string[]
} {
  const tagged = caps.filter((c) => resolveType(c) === 'tool' && (c.projection_tags ?? []).includes(tag))
  const excludedCalibration = tagged.filter((c) => c.calibration_context_only === true)
  const afterCalibration = tagged.filter((c) => c.calibration_context_only !== true)
  const isInternal = (c: CapabilityDescriptor): boolean =>
    NOT_LLM_FACING_PATTERN.test(c.description ?? '') || KNOWN_INTERNAL_NOT_IN_OWN_DESCRIPTION.has(c.name)
  const excludedInternal = afterCalibration.filter(isInternal)
  const eligible = afterCalibration.filter((c) => !isInternal(c))
  return {
    eligible,
    excludedCalibrationContextOnly: excludedCalibration.map((c) => c.name).sort(),
    excludedNotLlmFacing: excludedInternal.map((c) => c.name).sort(),
  }
}

function buildFullProfile(caps: CapabilityDescriptor[]): McpSurfaceProfile {
  const { eligible, excludedCalibrationContextOnly, excludedNotLlmFacing } = eligibleForTag(caps, 'mcp_full')
  const sorted = [...eligible].sort((a, b) => a.name.localeCompare(b.name))
  const tools = sorted.map(buildMcpToolRegistration)
  return {
    profile: 'full',
    max_tools: null,
    total: tools.length,
    tool_names: tools.map((t) => t.tool_name),
    tools,
    overflow_tool_names: [],
    excluded_calibration_context_only: excludedCalibrationContextOnly,
    excluded_not_llm_facing: excludedNotLlmFacing,
  }
}

function buildCompactProfile(caps: CapabilityDescriptor[]): McpSurfaceProfile {
  const { eligible, excludedCalibrationContextOnly, excludedNotLlmFacing } = eligibleForTag(caps, 'mcp_compact')
  const ranked = eligible.map(toRankable).sort(compareRank)
  const surfaced = ranked.slice(0, COMPACT_MAX_TOOLS)
  const overflow = ranked.slice(COMPACT_MAX_TOOLS)
  const tools = surfaced.map((r) => buildMcpToolRegistration(r.cap)).sort((a, b) => a.tool_name.localeCompare(b.tool_name))
  return {
    profile: 'compact',
    max_tools: COMPACT_MAX_TOOLS,
    total: tools.length,
    tool_names: tools.map((t) => t.tool_name),
    tools,
    overflow_tool_names: overflow.map((r) => r.cap.name).sort(),
    excluded_calibration_context_only: excludedCalibrationContextOnly,
    excluded_not_llm_facing: excludedNotLlmFacing,
  }
}

function buildConsultProfile(caps: CapabilityDescriptor[]): McpSurfaceProfile {
  const { eligible, excludedCalibrationContextOnly, excludedNotLlmFacing } = eligibleForTag(caps, 'mcp_consult')
  const sorted = [...eligible].sort((a, b) => a.name.localeCompare(b.name))
  const tools = sorted.map(buildMcpToolRegistration)
  return {
    profile: 'consult',
    // Not RC-1-capped: the mcp_consult tag set is already the small orienting set
    // (plan: "~5 orienting tools"); if the registry ever tags more than 20 as
    // mcp_consult, that is itself a finding to surface (via `total`), not a cap to
    // silently apply — a hard cap here would be the same "invent a number" failure
    // §N.4 warns against, applied to the wrong field.
    max_tools: null,
    total: tools.length,
    tool_names: tools.map((t) => t.tool_name),
    tools,
    overflow_tool_names: [],
    excluded_calibration_context_only: excludedCalibrationContextOnly,
    excluded_not_llm_facing: excludedNotLlmFacing,
  }
}

export interface McpSurfaceProfiles {
  full: McpSurfaceProfile
  compact: McpSurfaceProfile
  consult: McpSurfaceProfile
}

export function buildMcpSurfaceProfiles(caps: CapabilityDescriptor[]): McpSurfaceProfiles {
  return {
    full: buildFullProfile(caps),
    compact: buildCompactProfile(caps),
    consult: buildConsultProfile(caps),
  }
}

/**
 * Cross-profile invariant this builder guarantees by construction (asserted in the
 * parity test, not just documented): every consult tool name is ALSO a compact tool
 * name whenever it's within the compact cap, and every compact/consult tool name is
 * ALSO present in full. Consult must never contain a name absent from full — that
 * would be a tool reachable ONLY under the most-restricted profile, which cannot
 * happen given consult ⊆ mcp_consult-tagged ⊆ mcp_full-tagged-or-not (mcp_consult is
 * one of the four tags `descriptor_defaults.ts` sets TOGETHER with mcp_full for
 * L-ORIENT capabilities) — this function computes the check so the test doesn't
 * re-derive registry internals.
 */
export function consultIsSubsetOfFull(profiles: McpSurfaceProfiles): boolean {
  const fullNames = new Set(profiles.full.tool_names)
  return profiles.consult.tool_names.every((n) => fullNames.has(n))
}
