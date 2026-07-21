/**
 * no_leakage_filter.ts — NO-LEAKAGE arm-2 capability filter (doctrine ruling F-R7,
 * ACCEPTED), ported into the `platform` deployable (W6 module-placement correction).
 *
 * ── Why this lives here, not in platform-mcp ─────────────────────────────────────
 * `platform-mcp` and `platform` are separate Cloud Run deployables with no shared
 * import path. Investigation for the prashna_ask↔engine bridge (Task 4) found that
 * the engine's tool-call loop — where NO-LEAKAGE must actually be enforced before a
 * tool is dispatched — executes entirely inside `platform`'s process (driven today
 * by `/api/chat/consult/route.ts`), never inside `platform-mcp`. A filter applied
 * only on the `platform-mcp` side would be advisory, not enforcing: nothing stops
 * the engine from assembling an unfiltered tool set across the HTTP boundary. See
 * `00_ARCHITECTURE/briefs/retrieval_impl/STATE.md` for the full record.
 *
 * Because this file lives in the SAME deployable as the registry, it imports the
 * real `CapabilityDescriptor` type and the live registry lookup directly — the
 * `platform-mcp` attempt's local structural mirror type is no longer needed here.
 *
 * ── Shape ─────────────────────────────────────────────────────────────────────
 * The engine hands the route a `toolsAuthorized: string[]` (tool/capability
 * names — see `/api/chat/consult/route.ts`'s `toolsAuthorized` derivation around
 * line 561). This filter operates directly on that shape: a list of tool names in,
 * the same list back with any leaked name removed.
 *
 * Any name that does not resolve to a registered capability is passed through
 * unfiltered (fail-open on unknown names) — this filter's only job is to strip
 * capabilities affirmatively flagged `calibration_context_only: true`; it is not a
 * tool-name validator (that is `getToolByName`'s job downstream, and an unresolved
 * name will simply no-op there).
 */

import { getCapability } from '@/lib/retrieval/registry'
import { getCatalog } from '@/lib/retrieval/registry/catalog'
import { resolveToolUri } from '@/lib/retrieval/registry/tool_name_bridge'

/**
 * Returns a new array containing only tool names that are safe to dispatch — i.e.
 * every entry except those whose registered `CapabilityDescriptor` is explicitly
 * flagged `calibration_context_only: true`. Entries where the flag is absent or
 * `false`, or where the name does not resolve to any registered capability, are
 * kept. Pure function: does not mutate the input array.
 *
 * Calls `getCatalog()` first (not just the raw registry) because `calibration_
 * context_only` is one of the descriptor-default fields `getCatalog()` backfills
 * in place on first call (see `registry/catalog.ts`'s `applyDescriptorDefaults`
 * loop) — a raw `getCapability()` lookup before that backfill has run would see
 * the field as `undefined` even for a capability F-R7 flags as leaked. `getCatalog()`
 * is cheap and idempotent (it mutates the same registered objects `getCapability()`
 * reads), so calling it here does not duplicate registration work.
 */
export function filterLeakedCapabilities(toolNames: readonly string[]): string[] {
  getCatalog()
  return toolNames.filter((toolName) => {
    const uri = resolveToolUri(toolName)
    if (!uri) return true
    const cap = getCapability(uri)
    if (!cap) return true
    return cap.calibration_context_only !== true
  })
}
