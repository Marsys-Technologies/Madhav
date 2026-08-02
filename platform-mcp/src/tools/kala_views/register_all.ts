/**
 * register_all.ts — the ONE place kala_views tools attach to registry_bridge.ts.
 *
 * ORIGIN (post-Night-2 hygiene fix): the 8 kala_* view/capability facades were
 * originally registered as 8 separate import lines + 8 separate call lines, hand-placed
 * directly inside registry_bridge.ts's ~4500-line registerRegistryBridgeTools() function.
 * That file also carries the registration surface for every OTHER campaign's tools
 * (holistic_bundle, phala, mimamsa, chart_selection, ...), so every kala lane's PR edited
 * the same shared, high-traffic file — Night 1 alone required three separate manual
 * merge-conflict resolutions on this exact spot (see SHAD_DARSHANA_STATE.md's Phase 1b
 * log, PRs #882/#883/#884). Consolidating all 8 into this ONE dedicated, kala-owned file
 * means registry_bridge.ts changes exactly ONCE (see the bottom of this file's docstring
 * for the one-line hookup) — any future kala-tool addition touches only this file, which
 * is exclusively shad-darshana's, so a collision here is at worst shad-darshana-internal
 * (and resolves on shad-darshana/integration, not on shared main).
 *
 * ONE canonical registration site per tool still holds (brief §2): each tool's
 * `server.tool(...)` call is reached from exactly one place — inside its own
 * kala_views/<name>.ts's register function, called exactly once, from exactly here.
 */
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import type { Principal } from '../../types.js'

import { registerKalaNowGetTool } from './now.js'
import { registerKalaAheadGetTool } from './ahead.js'
import { registerKalaUpayaGet } from './upaya.js'
import { registerKalaRitualGet } from './ritual.js'
import { registerKalaPriorityTool } from './priority.js'
import { registerKalaExplainTool } from './explain.js'
import { registerKalaElectTool } from './elect.js'
import { registerKalaStoryTool } from './story.js'

/**
 * Registers all eight ṢAḌ-DARŚANA kala_* view/capability facades on `server`.
 * Called exactly once from registry_bridge.ts's registerRegistryBridgeTools().
 *
 * — now-ahead lane: kala_now_get, kala_ahead_get.
 * — upaya-ritual-stub lane: kala_upaya_get, kala_ritual_get. kala_ritual_get additionally
 *   implements the Mode-3 routing rule (KALA_SUPREME_ELEVATION_v1_0.md §8): a Mode-3-shaped
 *   call (a non-blank `undertaking` field) never reaches any Mode-1/2 logic — it returns an
 *   honest `wrong_view` naming kala_elect_get, with no passthrough/proxy/delegation.
 * — priority-explain lane: kala_priority_get (wraps the same
 *   marsys://tool/L3/call_priority_ranking capability kala_priority_ranking_get already
 *   calls), kala_explain_get (wraps the same marsys://tool/L-PACT/pact_query capability
 *   pact_query already calls) — re-served on the elevated kala_envelope.ts shape. Legacy
 *   tools are unaffected — aliases live, nothing retired.
 * — elect-story lane: kala_elect_get (VIEW 3, ELECT) wraps the existing muhurta_finder
 *   substrate and is THE SOLE SERVER OF MODE 3 — kala_ritual_get's redirect lands here.
 *   kala_story_get (VIEW 4, STORY) wraps kala_jivana_parva and fixes its known
 *   parva-duplication defect at serving (dedup by exact span + daśā level).
 */
export function registerAllKalaViews(server: McpServer, principal: Principal): void {
  registerKalaNowGetTool(server, principal)
  registerKalaAheadGetTool(server, principal)
  registerKalaUpayaGet(server, principal)
  registerKalaRitualGet(server, principal)
  registerKalaPriorityTool(server, principal)
  registerKalaExplainTool(server, principal)
  registerKalaElectTool(server, principal)
  registerKalaStoryTool(server, principal)
}
