/**
 * completeness_wiring.ts — W4 "One Planner", sequential core step 4 (completeness receipts on
 * the web/consult channel).
 *
 * Bridges the deterministic vidhi contract (compiled from a plan's classifier `scope_tuple`) to
 * the consult route's ACTUAL per-tool execution outcomes, producing a truthful completeness
 * receipt via the ported `emitCompletenessReceipt` (@/lib/vidhi/completeness_receipt).
 *
 * ── The honesty problem this file exists to NOT paper over ───────────────────────────────────
 *
 * `compileContract` emits floor items whose `live_tool` is an MCP-connector tool name. The web
 * consult path executes retrieval-REGISTRY tool names, and `LIVE_TOOL_TO_RETRIEVAL`
 * (compiled_floor_adapter.ts) maps only a SMALL subset (4 live_tools today). Every other floor
 * primitive has NO web-executable equivalent — the MCP↔web namespace gap. This wiring reports
 * that reality faithfully:
 *   - a primitive whose retrieval tool actually returned rows  → served (source = retrieval tool)
 *   - a primitive whose retrieval tool ran but returned 0 rows → empty (route_empty)
 *   - a primitive whose retrieval tool errored                 → empty (route_error)
 *   - a primitive with a `known_gap` CR that was not served    → dark (cites its CR — emitter)
 *   - a primitive with NO web-executable tool (namespace gap)  → empty (web_namespace_gap: …)
 *
 * The last bucket is the dominant reality today: most floor items are `web_namespace_gap` empties
 * or `known_gap` darks, because only 4 of ~23 distinct MCP tool names map to web-executable
 * retrieval tools. The receipt's top-level `channel_note` surfaces that count so a reader can
 * never mistake a small `served` set for "the floor was fully honored on web".
 */

import { compileContract, defaultRegistry } from '@/lib/vidhi/compiler'
import {
  emitCompletenessReceipt,
  type CompletenessReceipt,
  type FloorItemObservation,
} from '@/lib/vidhi/completeness_receipt'
import type { CompiledFloorItem } from '@/lib/vidhi/types'
import type { ScopeTuple as ClassifierScopeTuple } from '@/lib/vidhi/scope_classifier'
import {
  classifierTupleToCompilerTuple,
  LIVE_TOOL_TO_RETRIEVAL,
} from './compiled_floor_adapter'

/** Per-retrieval-tool execution outcome the consult route observed (from its toolEventLog). */
export interface ToolExecutionOutcome {
  readonly name: string
  readonly status: 'done' | 'error'
  /** Rows returned when status==='done' (0 = ran-but-empty). */
  readonly ok_count: number
}

/** The web-channel completeness receipt: the faithful V-0-shaped receipt plus a channel note. */
export interface WebCompletenessReceipt extends CompletenessReceipt {
  /** Which serving channel produced this receipt — always 'web' here (vs the MCP channel). */
  readonly channel: 'web'
  /**
   * Honest one-line summary of the namespace-gap reality: how many floor items had NO
   * web-executable retrieval tool at all. Surfaced at the envelope level so a small `served`
   * count is never read as full floor coverage.
   */
  readonly channel_note: string
  /** primitive_ids with no web-executable retrieval tool (subset of empty ∪ dark). */
  readonly web_dark_primitive_ids: string[]
}

const WEB_NAMESPACE_GAP_PREFIX = 'web_namespace_gap'

/**
 * Build a truthful completeness receipt for a resolved plan on the WEB channel.
 *
 * @param scopeTuple  The plan's classifier scope_tuple (plan.scope_tuple). Total mapping to a
 *                    compiler intent via classifierTupleToCompilerTuple — never throws.
 * @param chartId     The chart the floor was compiled for (fills {chart_id} placeholders).
 * @param toolOutcomes The consult route's per-tool execution log (name/status/ok_count).
 * @returns A WebCompletenessReceipt, or null if the contract could not compile (registry bug) —
 *          the caller then simply omits the receipt (it is delivery metadata, never load-bearing).
 */
export function buildWebCompletenessReceipt(
  scopeTuple: ClassifierScopeTuple,
  chartId: string,
  toolOutcomes: readonly ToolExecutionOutcome[],
): WebCompletenessReceipt | null {
  let contract
  try {
    contract = compileContract(classifierTupleToCompilerTuple(scopeTuple), defaultRegistry(), chartId)
  } catch {
    // compileContract throws only on a registry-completeness bug. The receipt is delivery
    // metadata; degrade safely by omitting it rather than crashing the response.
    return null
  }

  // Index the route's execution outcomes by retrieval tool name (last write wins; a tool appears
  // once per authorized set).
  const outcomeByTool = new Map<string, ToolExecutionOutcome>()
  for (const o of toolOutcomes) outcomeByTool.set(o.name, o)

  const webDarkPrimitiveIds: string[] = []
  const observations: FloorItemObservation[] = []

  const uniqueItems: CompiledFloorItem[] = []
  const seen = new Set<string>()
  for (const item of [...contract.floor, ...contract.machine_band]) {
    if (seen.has(item.primitive_id)) continue
    seen.add(item.primitive_id)
    uniqueItems.push(item)
  }

  for (const item of uniqueItems) {
    const retrievalName = LIVE_TOOL_TO_RETRIEVAL[item.live_tool]
    if (!retrievalName) {
      // No web-executable equivalent — the namespace gap. Report an honest empty observation.
      // (The emitter promotes this to `dark` when the primitive ALSO has a known_gap CR — a
      // known_gap CR is the more specific truth, so it wins; otherwise it lands in `empty` with
      // the namespace-gap reason below.)
      webDarkPrimitiveIds.push(item.primitive_id)
      observations.push({
        floor_item_id: item.primitive_id,
        status: 'empty',
        empty_reason: `${WEB_NAMESPACE_GAP_PREFIX}: live_tool "${item.live_tool}" has no web retrieval-registry equivalent (MCP-native only)`,
      })
      continue
    }
    const outcome = outcomeByTool.get(retrievalName)
    if (!outcome) {
      // Mapped to a web tool, but that tool was not among the authorized/executed set for this
      // request (e.g. it was deduped away, or the plan did not surface it). Honest empty.
      observations.push({
        floor_item_id: item.primitive_id,
        status: 'empty',
        empty_reason: `route_not_invoked: retrieval tool "${retrievalName}" was not executed for this request`,
      })
      continue
    }
    if (outcome.status === 'error') {
      observations.push({ floor_item_id: item.primitive_id, status: 'empty', empty_reason: 'route_error' })
    } else if (outcome.ok_count > 0) {
      observations.push({ floor_item_id: item.primitive_id, status: 'served', source: retrievalName })
    } else {
      observations.push({ floor_item_id: item.primitive_id, status: 'empty', empty_reason: 'route_empty' })
    }
  }

  const receipt = emitCompletenessReceipt(contract, observations)
  const floorTotal = receipt.coverage.floor_item_total

  return {
    ...receipt,
    channel: 'web',
    web_dark_primitive_ids: webDarkPrimitiveIds,
    channel_note:
      `${webDarkPrimitiveIds.length} of ${floorTotal} floor items have NO web-executable ` +
      `retrieval tool (MCP↔web namespace gap); ${receipt.coverage.served} served, ` +
      `${receipt.coverage.empty} empty, ${receipt.coverage.dark} dark. A small served count ` +
      `reflects the namespace gap, not a fully-honored floor.`,
  }
}
