/**
 * completeness_receipt.ts — WEB-SIDE PORT of the MCP emitter (W4 "One Planner", core steps 4-5).
 *
 * This is a faithful 1:1 port of `platform-mcp/src/lib/completeness_receipt.ts` (D-2 Lane V-2
 * EMITTER, BIND_D-2.md §F1.7 ledger row 17) onto the web/consult channel. The ONLY edits versus
 * the MCP source are the two sibling import paths (`../resources/vidhi/{types,cr_status}.js` →
 * `./types` / `./cr_status`) — the algorithm, shape, and honesty invariants are byte-faithful.
 *
 * WHY THIS FILE EXISTS AT ALL (divergence note): the web-side vidhi package
 * (`platform/src/lib/vidhi/`) is the CANONICAL source for the compiler + registry that the MCP
 * side vendors/codegens a mirror of (see `generate_vidhi_registry_mirror.ts`). But the *emitter*
 * (`emitCompletenessReceipt`) was authored ONLY on the MCP side, in `platform-mcp/src/lib/`
 * (NOT inside the mirrored `resources/vidhi/` dir), and the codegen mirror (`codegen:vidhi`)
 * only mirrors `registry_data.ts`. So the emitter was never ported here — the canonical vidhi
 * package could compile a contract but had no way to emit a completeness receipt from it. This
 * file closes that omission for the web channel. (It is NOT wired into `codegen:vidhi:check`,
 * which by design only guards `registry_data.ts`; the two emitter copies are kept in sync by
 * hand, same as `types.ts`/`compiler.ts` — a known, flagged gap the codegen header already
 * documents.)
 *
 * The receipt shape (V-0 validator contract):
 *   {
 *     served: [{ floor_item_id: string, source?: string }],
 *     empty:  [{ floor_item_id: string, empty_reason: string }],   // empty_reason non-empty
 *     dark:   [{ floor_item_id: string, cr_row: string }],         // cr_row matches /^CR-\d+$/
 *   }
 *
 * Invariants:
 *   - `served ∪ empty ∪ dark` = the compiled floor's full floor-item set (TOTAL).
 *   - the three sets are pairwise DISJOINT (each floor_item_id in exactly one bucket).
 *   - every `dark` item cites its primitive's `known_gap` CR (an OPEN/LOGGED CR, never CLOSED).
 *
 * HONESTY (§F1.7 data-over-flags): a floor item is placed in `served` ONLY when the caller
 * reports it actually returned data; a known-gap item that was not served is `dark` with its
 * true CR reason; everything else is `empty` with a TRUTHFUL reason. At plan issuance (no
 * observations), non-dark items carry `pending_execution: ...` — a factual statement that the
 * item's live_tool has not been invoked, NOT a false claim that a route was called and returned
 * nothing.
 */
import type { CompiledContract, CompiledFloorItem } from './types'
import { isCitableKnownGap } from './cr_status'

/** Per-floor-item observation the caller reports after executing the plan. */
export interface FloorItemObservation {
  readonly floor_item_id: string
  readonly status: 'served' | 'empty'
  /** For served items: which tool/source actually produced the data (defaults to live_tool). */
  readonly source?: string
  /** For empty items: honest reason the route returned nothing (route_empty/route_error/…). */
  readonly empty_reason?: string
}

export interface ReceiptServedItem {
  readonly floor_item_id: string
  readonly source: string
}
export interface ReceiptEmptyItem {
  readonly floor_item_id: string
  readonly empty_reason: string
}
export interface ReceiptDarkItem {
  readonly floor_item_id: string
  readonly cr_row: string
  /** Non-load-bearing note; the validator ignores extra fields. */
  readonly note?: string
}

export interface CompletenessReceipt {
  readonly served: ReceiptServedItem[]
  readonly empty: ReceiptEmptyItem[]
  readonly dark: ReceiptDarkItem[]
  /** Convenience coverage summary (extra field; validator ignores it). */
  readonly coverage: {
    readonly floor_item_total: number
    readonly served: number
    readonly empty: number
    readonly dark: number
  }
}

const CR_ROW_PATTERN = /^CR-\d+$/

/**
 * De-duplicate the compiled floor + machine band into the ordered, unique floor-item set the
 * receipt accounts for. A primitive that appears in both bands is a SINGLE receipt line.
 */
function uniqueFloorItems(contract: CompiledContract): CompiledFloorItem[] {
  const seen = new Set<string>()
  const items: CompiledFloorItem[] = []
  for (const item of [...contract.floor, ...contract.machine_band]) {
    if (seen.has(item.primitive_id)) continue
    seen.add(item.primitive_id)
    items.push(item)
  }
  return items
}

/**
 * Emit a completeness receipt for a compiled vidhi contract.
 *
 * @param contract      The compiled contract whose floor items the receipt accounts for.
 * @param observations  Optional per-item results from an execution that already ran the plan.
 *                      Omit at plan issuance — non-dark items are then reported as `empty` with
 *                      a truthful `pending_execution` reason.
 */
export function emitCompletenessReceipt(
  contract: CompiledContract,
  observations: readonly FloorItemObservation[] = [],
): CompletenessReceipt {
  const obsById = new Map<string, FloorItemObservation>()
  for (const o of observations) obsById.set(o.floor_item_id, o)

  const served: ReceiptServedItem[] = []
  const empty: ReceiptEmptyItem[] = []
  const dark: ReceiptDarkItem[] = []

  for (const item of uniqueFloorItems(contract)) {
    const id = item.primitive_id
    const obs = obsById.get(id)

    // 1. Served takes priority — an item that actually returned data is served, even if it
    //    carries a known_gap (the tool worked despite the register-tracked coverage gap).
    if (obs?.status === 'served') {
      served.push({ floor_item_id: id, source: obs.source ?? item.live_tool })
      continue
    }

    // 2. Known-gap items that were not served are DARK by construction, citing their CR.
    if (item.known_gap !== null) {
      const cr = item.known_gap
      const citable = CR_ROW_PATTERN.test(cr) && isCitableKnownGap(cr)
      dark.push({
        floor_item_id: id,
        cr_row: cr,
        note: citable
          ? `coverage gap tracked by ${cr} (OPEN/LOGGED)`
          : `WARNING: ${cr} is not a citable OPEN/LOGGED CR — registry defect (V-1)`,
      })
      continue
    }

    // 3. Observed empty — honest reason from the caller (defaulting to route_empty).
    if (obs?.status === 'empty') {
      empty.push({ floor_item_id: id, empty_reason: obs.empty_reason ?? 'route_empty' })
      continue
    }

    // 4. Not yet executed (plan issuance) — truthful pending reason, NOT a false absence claim.
    empty.push({
      floor_item_id: id,
      empty_reason: `pending_execution: live_tool "${item.live_tool}" not yet invoked — re-emit the receipt with observations after the plan runs`,
    })
  }

  return {
    served,
    empty,
    dark,
    coverage: {
      floor_item_total: served.length + empty.length + dark.length,
      served: served.length,
      empty: empty.length,
      dark: dark.length,
    },
  }
}
