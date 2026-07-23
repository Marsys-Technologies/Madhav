/**
 * Vidhi compiler — D-2 Lane V-1.
 *
 * question → scope_tuple(intent, domains, width, depth, horizon, intervention?, entitlement)
 * → contract = floor(intent) + machine_band(depth) + LLM_extensions
 * (DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3).
 *
 * Deterministic by construction: `compileContract` is a pure function of its two
 * arguments (no Date.now/Math.random/env reads) — see `compiler.test.ts`'s hash-equality
 * assertion. The scope tuple → intent classification (question text → ScopeTuple) is
 * explicitly OUT of scope here: that's LLM-owned band-3 territory routed through
 * `intent_classify` once the CR-28 engineering ruling lands (V-3). This module starts
 * from an already-produced `ScopeTuple`.
 *
 * §N.4 "no audience tier": `entitlement` is echoed on the compiled contract as metadata
 * for the serving layer (V-2) to apply at serve time — this compiler never drops floor
 * items based on entitlement. Writers/compilers emit the full contract; serve-time governs
 * access.
 */
import type {
  CompiledContract,
  CompiledFloorItem,
  CompletenessReceiptTemplate,
  FloorItem,
  IntentFloor,
  ScopeDepth,
  ScopeTuple,
  VidhiPrimitive,
} from './types';
import { VIDHI_PRIMITIVES, VIDHI_INTENT_FLOORS } from './registry_data';

// RC-14 breaking flip (2026-07-23): bumped 1.0.0 -> 2.0.0. The 43 legacy P1 tool
// names were removed from the MCP surface and 6 tools renamed; this bump (plus the
// VIDHI_PRIMITIVES live_tool/fallback repoints) moves VIDHI_CAPABILITY_VERSION so a
// tools/list_changed staleness notification fires for every client holding the old
// version (capability_version.ts / notifyIfCapabilityStale).
export const COMPILER_VERSION = '2.0.0';

export interface VidhiRegistry {
  readonly primitives: readonly VidhiPrimitive[];
  readonly floors: readonly IntentFloor[];
}

function primitiveIndex(registry: VidhiRegistry): ReadonlyMap<string, VidhiPrimitive> {
  const idx = new Map<string, VidhiPrimitive>();
  for (const p of registry.primitives) idx.set(p.primitive_id, p);
  return idx;
}

/**
 * Which bands a given `depth` compiles in. `retrieval` compiles the acharya floor's
 * structural items only (no machine band — the "minimal, single-fact" shape);
 * `structure` compiles the full acharya floor, no machine band; `deepdive` compiles
 * both bands in full. This is the one place `depth` has effect — deliberately simple
 * and total, so identical tuples always resolve identically.
 */
function bandsForDepth(depth: ScopeDepth): { includeAcharyaFloor: boolean; includeMachineBand: boolean; structuralOnly: boolean } {
  switch (depth) {
    case 'retrieval':
      return { includeAcharyaFloor: true, includeMachineBand: false, structuralOnly: true };
    case 'structure':
      return { includeAcharyaFloor: true, includeMachineBand: false, structuralOnly: false };
    case 'deepdive':
      return { includeAcharyaFloor: true, includeMachineBand: true, structuralOnly: false };
  }
}

function mergeArgs(
  base: Readonly<Record<string, unknown>>,
  override: Readonly<Record<string, unknown>> | undefined,
  chartId: string,
): Record<string, unknown> {
  const merged: Record<string, unknown> = { ...base, ...(override ?? {}) };
  for (const [k, v] of Object.entries(merged)) {
    if (v === '{chart_id}') merged[k] = chartId;
  }
  return merged;
}

function compileItem(item: FloorItem, primitive: VidhiPrimitive, chartId: string): CompiledFloorItem {
  return {
    primitive_id: primitive.primitive_id,
    band: item.band,
    live_tool: primitive.live_tool,
    tool_args: mergeArgs(primitive.tool_args, item.args_override, chartId),
    fallback_face: primitive.fallback_face,
    known_gap: primitive.known_gap,
  };
}

function buildReceiptTemplate(
  floor: readonly CompiledFloorItem[],
  machineBand: readonly CompiledFloorItem[],
): CompletenessReceiptTemplate {
  const all = [...floor, ...machineBand];
  const dark = all.filter((i) => i.known_gap !== null).map((i) => i.primitive_id);
  return { served: [], empty: [], dark };
}

/**
 * Compile a `ScopeTuple` into a `CompiledContract`. Deterministic: identical `tuple`
 * (structurally, not referentially) + identical `registry` → byte-identical output
 * (verified via JSON.stringify + sha256 in compiler.test.ts).
 *
 * Throws if `tuple.intent` has no registered floor, or a floor item references an
 * unregistered primitive_id — both are registry-completeness bugs, not runtime data
 * gaps, and must fail loudly rather than silently compile a partial contract.
 */
export function compileContract(tuple: ScopeTuple, registry: VidhiRegistry, chartId = '{chart_id}'): CompiledContract {
  const floorDef = registry.floors.find((f) => f.intent === tuple.intent);
  if (!floorDef) {
    throw new Error(`vidhi compiler: no floor registered for intent "${tuple.intent}"`);
  }
  const primitives = primitiveIndex(registry);
  const bands = bandsForDepth(tuple.depth);

  const sortedItems = [...floorDef.floor_items].sort((a, b) => a.order - b.order);

  const acharyaItems: CompiledFloorItem[] = [];
  const machineItems: CompiledFloorItem[] = [];

  for (const item of sortedItems) {
    const primitive = primitives.get(item.primitive_id);
    if (!primitive) {
      throw new Error(
        `vidhi compiler: floor "${tuple.intent}" references unregistered primitive "${item.primitive_id}"`,
      );
    }
    if (item.band === 'acharya_floor' && bands.includeAcharyaFloor) {
      if (bands.structuralOnly && primitive.category !== 'structural') continue;
      acharyaItems.push(compileItem(item, primitive, chartId));
    } else if (item.band === 'machine_band' && bands.includeMachineBand) {
      machineItems.push(compileItem(item, primitive, chartId));
    }
  }

  // intervention=false strips remedy-category items from both bands (a remedy read is
  // never useful without an intervention ask) — the one place `intervention` has effect.
  const filterIntervention = (items: CompiledFloorItem[]): CompiledFloorItem[] =>
    tuple.intervention
      ? items
      : items.filter((i) => primitives.get(i.primitive_id)?.category !== 'remedy');

  const floor = filterIntervention(acharyaItems);
  const machineBand = filterIntervention(machineItems);

  return {
    compiler_version: COMPILER_VERSION,
    scope_tuple: tuple,
    floor,
    machine_band: machineBand,
    completeness_receipt_template: buildReceiptTemplate(floor, machineBand),
    llm_extension_note:
      'Band 3 (question-specific extension) is LLM-owned: pursue beyond-floor context this ' +
      'specific question needs. The floor above is the non-skippable minimum; skipping any ' +
      'served floor item without citing its known_gap is a completeness-receipt violation.',
  };
}

/** Convenience: build a `VidhiRegistry` from the module's own canonical data (registry_data.ts). */
export function defaultRegistry(): VidhiRegistry {
  return { primitives: VIDHI_PRIMITIVES, floors: VIDHI_INTENT_FLOORS };
}
