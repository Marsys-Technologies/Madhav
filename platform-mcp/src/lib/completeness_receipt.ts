/**
 * completeness_receipt.ts — D-2 Lane V-2 EMITTER, BIND_D-2.md §F1.7 ledger row 17.
 *
 * "Completeness receipt on EVERY synthesis (served/empty/dark per floor item, each dark
 * citing its CR row)." (BRIEF_D2.md §F1 Lane V-2.)
 *
 * This is the PRODUCER side. The VALIDATOR (V-0, already shipped, read-only, outside this
 * lane's glob) lives at
 * `platform/scripts/audit/doctrine_harness/lib/completeness_receipt.ts` and asserts the
 * exact shape below. This emitter is written to produce PRECISELY what that validator
 * accepts — the two are a producer/consumer pair:
 *
 *   {
 *     served: [{ floor_item_id: string, source?: string }],
 *     empty:  [{ floor_item_id: string, empty_reason: string }],   // empty_reason non-empty
 *     dark:   [{ floor_item_id: string, cr_row: string }],         // cr_row matches /^CR-\d+$/
 *   }
 *
 * Invariants (enforced here, checked there):
 *   - `served ∪ empty ∪ dark` = the compiled floor's full floor-item set (TOTAL).
 *   - the three sets are pairwise DISJOINT (each floor_item_id in exactly one bucket).
 *   - every `dark` item cites its primitive's `known_gap` CR — which V-1's registry
 *     guarantees is an OPEN/LOGGED CR (never CLOSED); the validator re-checks this against
 *     the live register, so a drift surfaces as a real defect, not a silent pass.
 *
 * HONESTY (§F1.7 data-over-flags): a floor item is placed in `served` ONLY when the caller
 * reports it actually returned data; a known-gap item that was not served is `dark` with
 * its true CR reason; everything else is `empty` with a TRUTHFUL reason. At plan issuance
 * (no observations yet), non-dark items carry the reason `pending_execution: ...` — a
 * factual statement that the item's live_tool has not been invoked, NOT a false claim that
 * a route was called and returned nothing. When the synthesizing agent re-emits with
 * observations, served/empty reflect what actually happened.
 */
import type { CompiledContract, CompiledFloorItem } from '../resources/vidhi/types.js';
import { isCitableKnownGap } from '../resources/vidhi/cr_status.js';

/** Per-floor-item observation the synthesizing agent reports after executing the plan. */
export interface FloorItemObservation {
  readonly floor_item_id: string;
  readonly status: 'served' | 'empty';
  /** For served items: which tool/source actually produced the data (defaults to live_tool). */
  readonly source?: string;
  /** For empty items: honest reason the route returned nothing (route_empty/route_error/…). */
  readonly empty_reason?: string;
}

export interface ReceiptServedItem {
  readonly floor_item_id: string;
  readonly source: string;
}
export interface ReceiptEmptyItem {
  readonly floor_item_id: string;
  readonly empty_reason: string;
}
export interface ReceiptDarkItem {
  readonly floor_item_id: string;
  readonly cr_row: string;
  /** Non-load-bearing note; the validator ignores extra fields. */
  readonly note?: string;
}

export interface CompletenessReceipt {
  readonly served: ReceiptServedItem[];
  readonly empty: ReceiptEmptyItem[];
  readonly dark: ReceiptDarkItem[];
  /** Convenience coverage summary (extra field; validator ignores it). */
  readonly coverage: {
    readonly floor_item_total: number;
    readonly served: number;
    readonly empty: number;
    readonly dark: number;
  };
}

const CR_ROW_PATTERN = /^CR-\d+$/;

/**
 * De-duplicate the compiled floor + machine band into the ordered, unique floor-item set the
 * receipt accounts for. A primitive that appears in both bands is a SINGLE receipt line
 * (the receipt is about coverage of the underlying retrieval atom, and the validator
 * requires each id to appear once).
 */
function uniqueFloorItems(contract: CompiledContract): CompiledFloorItem[] {
  const seen = new Set<string>();
  const items: CompiledFloorItem[] = [];
  for (const item of [...contract.floor, ...contract.machine_band]) {
    if (seen.has(item.primitive_id)) continue;
    seen.add(item.primitive_id);
    items.push(item);
  }
  return items;
}

/**
 * Emit a completeness receipt for a compiled vidhi contract.
 *
 * @param contract      The compiled contract whose floor items the receipt accounts for.
 * @param observations  Optional per-item results from a synthesis that already executed the
 *                      plan. Omit at plan issuance — non-dark items are then reported as
 *                      `empty` with a truthful `pending_execution` reason.
 */
export function emitCompletenessReceipt(
  contract: CompiledContract,
  observations: readonly FloorItemObservation[] = [],
): CompletenessReceipt {
  const obsById = new Map<string, FloorItemObservation>();
  for (const o of observations) obsById.set(o.floor_item_id, o);

  const served: ReceiptServedItem[] = [];
  const empty: ReceiptEmptyItem[] = [];
  const dark: ReceiptDarkItem[] = [];

  for (const item of uniqueFloorItems(contract)) {
    const id = item.primitive_id;
    const obs = obsById.get(id);

    // 1. Served takes priority — an item that actually returned data is served, even if it
    //    carries a known_gap (the tool worked despite the register-tracked coverage gap).
    if (obs?.status === 'served') {
      served.push({ floor_item_id: id, source: obs.source ?? item.live_tool });
      continue;
    }

    // 2. Known-gap items that were not served are DARK by construction, citing their CR.
    if (item.known_gap !== null) {
      const cr = item.known_gap;
      const citable = CR_ROW_PATTERN.test(cr) && isCitableKnownGap(cr);
      dark.push({
        floor_item_id: id,
        cr_row: cr,
        note: citable
          ? `coverage gap tracked by ${cr} (OPEN/LOGGED)`
          : `WARNING: ${cr} is not a citable OPEN/LOGGED CR — registry defect (V-1)`,
      });
      continue;
    }

    // 3. Observed empty — honest reason from the caller (defaulting to route_empty).
    if (obs?.status === 'empty') {
      empty.push({ floor_item_id: id, empty_reason: obs.empty_reason ?? 'route_empty' });
      continue;
    }

    // 4. Not yet executed (plan issuance) — truthful pending reason, NOT a false absence claim.
    empty.push({
      floor_item_id: id,
      empty_reason: `pending_execution: live_tool "${item.live_tool}" not yet invoked — re-emit the receipt with observations after the synthesis runs the plan`,
    });
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
  };
}
