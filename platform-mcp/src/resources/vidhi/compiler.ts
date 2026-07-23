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
 *
 * VIDHI-PŪRṆATĀ P-3b (2026-07-23) elevation wiring — additive, determinism-preserving:
 *   - §N.6 density: `compileItem` now carries `hard_floor` from the floor item onto the
 *     compiled item (E-0 digest lead + E-7 insight band declare it).
 *   - E-3 Anusaraṇa: `compileContract` emits `adaptive_expansions` — deterministic, one-hop,
 *     chart-AGNOSTIC follow-directives computed AFTER the floor resolves (embed no chart_id,
 *     so the floor_cache reuses them verbatim across charts and hash-equality still holds).
 *   - E-4 multi-domain: `compileMultiDomainContract` UNIONS the matched deepdive floors
 *     (dedup on primitive_id+args, primary-first stable order). Kept SEPARATE from
 *     `compileContract` (which stays strictly single-intent) so the floor_cache's
 *     "domains is cosmetic to the compiled floor" invariant — and every existing determinism
 *     test — hold unchanged; the union is opt-in at the call site (plan_builder).
 *   - E-7 insight mandate: the deepdive `llm_extension_note` is the beyond-acharya INSIGHT
 *     MANDATE (BRIEF_VIDHI_PURNATA_v1_0 §B, verbatim).
 *
 * VENDORED MIRROR (D-2 Lane V-2): 1:1 content mirror of
 * platform/src/lib/vidhi/compiler.ts — the ONLY edit applied on copy is the NodeNext-required
 * `.js` import extensions. Drift is caught by vidhi_registry_parity.test.ts (byte-identical
 * compiled output).
 */
import type {
  AdaptiveExpansion,
  CompiledContract,
  CompiledFloorItem,
  CompletenessReceiptTemplate,
  FloorItem,
  IntentClass,
  IntentFloor,
  ScopeDepth,
  ScopeTuple,
  VidhiPrimitive,
} from './types.js';
import { VIDHI_PRIMITIVES, VIDHI_INTENT_FLOORS } from './registry_data.js';

// RC-14 breaking flip (2026-07-23): bumped 1.0.0 -> 2.0.0. The 43 legacy P1 tool
// names were removed from the MCP surface and 6 tools renamed; this bump (plus the
// VIDHI_PRIMITIVES live_tool/fallback repoints) moves VIDHI_CAPABILITY_VERSION so a
// tools/list_changed staleness notification fires for every client holding the old
// version (capability_version.ts / notifyIfCapabilityStale). VIDHI-PŪRṆATĀ P-3b's
// additive output fields (hard_floor / adaptive_expansions / insight mandate) do NOT
// bump this: capability_version's content-hash suffix already busts on the registry +
// output-shape change, so clients re-fetch without a semver flip. Kept at 2.0.0.
export const COMPILER_VERSION = '2.0.0';

export interface VidhiRegistry {
  readonly primitives: readonly VidhiPrimitive[];
  readonly floors: readonly IntentFloor[];
}

/**
 * E-4 (multi-domain composition): the domain-name → deepdive-IntentClass map. Domains are the
 * classifier/scope vocabulary (`intent_classify` DOMAINS + scope_resolver keyword domains);
 * the values are the compiler's registered deepdive floors. `children` and `progeny` both map
 * to `progeny_deepdive` (P-0 (b) naming reconciliation: the classifier DOMAIN is `children`,
 * the compiler IntentClass is `progeny_deepdive`). A domain absent here (e.g. `general`,
 * `litigation`, `property`, `travel`) contributes no union intent — those have no dedicated
 * deepdive floor yet, so they never force a union. Exported for reuse + tests.
 */
export const DOMAIN_TO_INTENT: Readonly<Record<string, IntentClass>> = {
  wealth: 'wealth_deepdive',
  career: 'career_deepdive',
  health: 'health_deepdive',
  marriage: 'marriage_deepdive',
  spirituality: 'spirituality_deepdive',
  education: 'education_deepdive',
  children: 'progeny_deepdive',
  progeny: 'progeny_deepdive',
};

/** The set of registered deepdive IntentClasses (union targets + the E-7 insight-mandate gate). */
const DEEPDIVE_INTENTS: ReadonlySet<IntentClass> = new Set<IntentClass>(Object.values(DOMAIN_TO_INTENT));

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
 *
 * DEPTH-DEFAULT DOCTRINE (BINDING — BRIEF_VIDHI_PURNATA_v1_0 §0; native-directed 2026-07-23):
 * `depth` arrives here ALREADY intent-resolved — it is NOT keyword-gated. Deepdive is the
 * default state of the instrument; the scope resolver (scope_resolver.ts::defaultDepthForIntent)
 * drops below `deepdive` only for the two reduced intents (structure_read / retrieval_only), and
 * an unclassifiable question resolves to general_synthesis at `deepdive`, never trimmed. This
 * function stays a pure depth→bands map — it neither defaults nor deepens; that policy lives at
 * resolution time. Closes F5 (naive-depth trap) of STATIC_VIDHI_AUDIT_v1_0.
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
    // §N.6 density signal (VIDHI-PŪRṆATĀ P-3b): propagate the floor item's hard_floor flag
    // (E-0 digest lead, E-7 insight band) onto the compiled item so the serving-layer budget
    // trimmer protects these rows and never sacrifices them first. Default false.
    hard_floor: item.hard_floor ?? false,
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

// ─────────────────────────────────────────────────────────────────────────────────────
// E-3 — Anusaraṇa (chart-adaptive) one-hop expansion (VIDHI-PŪRṆATĀ P-3b)
// ─────────────────────────────────────────────────────────────────────────────────────

/**
 * The primitive categories whose tool responses carry a firing / contradiction / valence /
 * discovery flag worth a pre-authorized drill (E-3 rule (c)). Derived from the registry's own
 * `category` field (auditable, not a hand-curated magic list): `doctrine` (yoga/dosha/NBRY/
 * āyurdāya firings), `signal` (varga-ratification divergence, CGM mechanism, loss mechanism,
 * sudarśana, bhāvat-bhāvam, tail divergence, arudha). `contradiction_scan` (category `utility`)
 * is added explicitly — it is the discovery/contradiction surface by definition.
 */
const FLAG_BEARING_CATEGORIES: ReadonlySet<VidhiPrimitive['category']> = new Set(['doctrine', 'signal']);

function isFlagBearing(primitive: VidhiPrimitive): boolean {
  return FLAG_BEARING_CATEGORIES.has(primitive.category) || primitive.primitive_id === 'contradiction_scan';
}

/** A resolved, non-placeholder house number in a compiled item's tool_args, or null. */
function resolvedHouse(item: CompiledFloorItem): number | null {
  const h = item.tool_args.house;
  return typeof h === 'number' ? h : null;
}

/** A resolved, non-placeholder karaka name in a compiled item's tool_args, or null. */
function resolvedKaraka(item: CompiledFloorItem): string | null {
  const k = item.tool_args.karaka ?? item.tool_args.chara_karaka;
  return typeof k === 'string' && !k.startsWith('{') ? k : null;
}

/**
 * Compute the E-3 Anusaraṇa one-hop expansion RULES for a resolved floor. A PURE function of
 * (compiled floor items + registry) — it reads only static registry-derived fields (primitive
 * category, and the house/karaka an item targets via its args_override) and NEVER `chart_id`,
 * so every emitted rule is chart-AGNOSTIC: identical for every chart, reused verbatim by the
 * floor_cache, and hash-stable for the determinism test. Hard-capped at ONE hop (`hop: 1`) —
 * the compiler emits DIRECTIVES, never resolved targets (resolving a bhāveśa's occupied house or
 * a kāraka's dispositor requires live chart facts, which is the executor's job). No transitive
 * closure: each rule is a single follow, and the compiler never feeds an emitted target back in.
 *
 * Rules (BRIEF_VIDHI_PURNATA_v1_0 §B E-3):
 *   (a) bhavesha_dispositor_hop — each floor bhāveśa → its occupied house → add that bhava_condition.
 *   (b) karaka_dispositor_hop   — each domain kāraka → its dispositor → add that condition.
 *   (c) response_flag_drill     — each flag-bearing floor item → drill the flagged target IF its
 *       response carries a firing/contradiction/drill flag (executor-side, on_response_flag).
 */
function computeAdaptiveExpansions(
  compiled: readonly CompiledFloorItem[],
  primitives: ReadonlyMap<string, VidhiPrimitive>,
): AdaptiveExpansion[] {
  const expansions: AdaptiveExpansion[] = [];

  for (const item of compiled) {
    // (a) bhāveśa → occupied house.
    if (item.primitive_id === 'bhavesha_condition') {
      const house = resolvedHouse(item);
      if (house !== null) {
        expansions.push({
          rule: 'bhavesha_dispositor_hop',
          source_primitive_id: item.primitive_id,
          source_house: house,
          follow: `Resolve the lord of house ${house} to the house it occupies in the rasi chart; add a bhava_condition read of that occupied house.`,
          add_primitive_id: 'bhava_condition',
          trigger: 'always (materialize during floor execution once the house-lord placement is read)',
          hop: 1,
          note: 'E-3 anusaraṇa one-hop bhāveśa→occupied-house follow. Chart-agnostic directive; the executor resolves the target house from live facts (compiler never resolves it — that would need chart data). One hop, no transitive closure.',
        });
      }
    }

    // (b) domain kāraka → its dispositor.
    if (item.primitive_id === 'karaka_condition' || item.primitive_id === 'chara_karaka_read') {
      const karaka = resolvedKaraka(item);
      if (karaka !== null) {
        expansions.push({
          rule: 'karaka_dispositor_hop',
          source_primitive_id: item.primitive_id,
          source_karaka: karaka,
          follow: `Resolve the dispositor (sign-lord) of ${karaka}; add a karaka_condition/dignity read of that dispositor.`,
          add_primitive_id: 'karaka_condition',
          trigger: 'always (materialize during floor execution once the kāraka placement is read)',
          hop: 1,
          note: 'E-3 anusaraṇa one-hop kāraka→dispositor follow. Chart-agnostic directive; the executor resolves the dispositor from live facts. One hop, no transitive closure.',
        });
      }
    }

    // (c) flag-bearing item → pre-authorized drill on a live response flag.
    const primitive = primitives.get(item.primitive_id);
    if (primitive && isFlagBearing(primitive)) {
      expansions.push({
        rule: 'response_flag_drill',
        source_primitive_id: item.primitive_id,
        follow: `If ${item.primitive_id}'s response carries a firing / contradiction / drill flag (e.g. a fired yoga, a discovery/contradiction pole, a varga-ratification divergence, a drill_pointer), drill that flagged target on the SAME authoritative surface (re-invoke it at the detail its response names).`,
        add_primitive_id: item.primitive_id,
        trigger: 'on_response_flag (materialize only if the item\'s response actually carries a firing/contradiction/drill flag)',
        hop: 1,
        note: 'E-3 anusaraṇa one-hop response-flag drill. Pre-authorized in the plan; the executor follows the response\'s own drill pointer. One hop, no transitive closure.',
      });
    }
  }

  return expansions;
}

// ─────────────────────────────────────────────────────────────────────────────────────
// E-7 — the insight mandate (VIDHI-PŪRṆATĀ P-3b)
// ─────────────────────────────────────────────────────────────────────────────────────

/**
 * The beyond-acharya INSIGHT MANDATE, verbatim from BRIEF_VIDHI_PURNATA_v1_0 §B (E-7). Becomes
 * a deepdive plan's `llm_extension_note` — every full-read plan ENDS by directing the answerer
 * past fact-gathering to the non-obvious. Paired with the floor-discipline sentence so the
 * completeness-receipt reminder is not lost.
 */
const INSIGHT_MANDATE =
  'INSIGHT MANDATE (E-7): the floor is evidence; the deliverable is the insight an acharya ' +
  'could not reach — name the confluences, the contradictions and their resolution, the ' +
  'rarities, and what only this convergence of surfaces reveals.';

const FLOOR_DISCIPLINE_NOTE =
  'Band 3 (question-specific extension) is LLM-owned: pursue beyond-floor context this ' +
  'specific question needs. The floor above is the non-skippable minimum; skipping any ' +
  'served floor item without citing its known_gap is a completeness-receipt violation.';

/** The insight band (contradiction/tail_divergence/mechanism/statistical) is compiled only at
 *  deepdive; at deepdive the note leads with the INSIGHT MANDATE, else with floor discipline. */
function extensionNoteForDepth(depth: ScopeDepth): string {
  return depth === 'deepdive' ? `${INSIGHT_MANDATE} ${FLOOR_DISCIPLINE_NOTE}` : FLOOR_DISCIPLINE_NOTE;
}

// ─────────────────────────────────────────────────────────────────────────────────────
// Core compile
// ─────────────────────────────────────────────────────────────────────────────────────

/**
 * Compile an already-resolved floor-item set into a `CompiledContract`. Shared by
 * `compileContract` (single intent) and `compileMultiDomainContract` (E-4 union) so both
 * apply the identical band/depth/intervention/hard_floor/adaptive_expansions pipeline — the
 * single-intent path through the union is therefore byte-identical to `compileContract`.
 *
 * Throws if a floor item references an unregistered primitive_id — a registry-completeness bug,
 * which must fail loudly rather than silently compile a partial contract.
 *
 * Field insertion order is load-bearing: `JSON.stringify` hashes by insertion order, and
 * floor_cache.ts's reconstruction mirrors this exact order for cached↔direct hash parity.
 */
function compileFloorItems(
  items: readonly FloorItem[],
  tuple: ScopeTuple,
  registry: VidhiRegistry,
  chartId: string,
): CompiledContract {
  const primitives = primitiveIndex(registry);
  const bands = bandsForDepth(tuple.depth);
  const sortedItems = [...items].sort((a, b) => a.order - b.order);

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
  const filterIntervention = (its: CompiledFloorItem[]): CompiledFloorItem[] =>
    tuple.intervention
      ? its
      : its.filter((i) => primitives.get(i.primitive_id)?.category !== 'remedy');

  const floor = filterIntervention(acharyaItems);
  const machineBand = filterIntervention(machineItems);

  // E-3 Anusaraṇa: computed AFTER the floor resolves, over the surviving floor + machine band,
  // as a chart-agnostic pure function (no chart_id) — one hop, no transitive closure.
  const adaptive_expansions = computeAdaptiveExpansions([...floor, ...machineBand], primitives);

  return {
    compiler_version: COMPILER_VERSION,
    scope_tuple: tuple,
    floor,
    machine_band: machineBand,
    adaptive_expansions,
    completeness_receipt_template: buildReceiptTemplate(floor, machineBand),
    llm_extension_note: extensionNoteForDepth(tuple.depth),
  };
}

/**
 * Compile a `ScopeTuple` into a `CompiledContract`. Deterministic: identical `tuple`
 * (structurally, not referentially) + identical `registry` → byte-identical output
 * (verified via JSON.stringify + sha256 in compiler.test.ts).
 *
 * STRICTLY SINGLE-INTENT: selects the floor by `tuple.intent` alone and never reads
 * `tuple.domains` — this is what keeps the floor_cache's "domains is cosmetic to the compiled
 * floor" invariant true. Multi-domain composition is the opt-in `compileMultiDomainContract`.
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
  return compileFloorItems(floorDef.floor_items, tuple, registry, chartId);
}

/**
 * E-4 (multi-domain composition). Resolve the ORDERED, deduped set of deepdive intents implied
 * by the tuple: the primary `tuple.intent` FIRST, then — only when the primary is itself a
 * deepdive — each `tuple.domains` entry mapped through DOMAIN_TO_INTENT to a DISTINCT deepdive
 * intent, in domains order. A non-deepdive primary (structure_read / retrieval_only /
 * panoramic_breadth / general_synthesis) yields exactly `[tuple.intent]` — no domain union, so
 * the E-0 foundational fallback and the reduced intents are never silently replaced by a union.
 */
function resolveUnionIntents(tuple: ScopeTuple): IntentClass[] {
  const intents: IntentClass[] = [tuple.intent];
  if (!DEEPDIVE_INTENTS.has(tuple.intent)) return intents;
  const seen = new Set<IntentClass>(intents);
  for (const domain of tuple.domains) {
    const mapped = DOMAIN_TO_INTENT[domain];
    if (mapped && !seen.has(mapped)) {
      seen.add(mapped);
      intents.push(mapped);
    }
  }
  return intents;
}

/**
 * Union the floor_items of `intents` into one ordered set, deduped on (primitive_id + args) per
 * BRIEF §B E-4. Primary-intent items come first (in their own order), then each subsequent
 * intent's NOT-yet-seen items (in their order); `order` is re-sequenced from 1 so the merged set
 * is a well-formed floor. Deterministic: pure function of the intents list + registry.
 */
function unionFloorItems(intents: readonly IntentClass[], registry: VidhiRegistry): FloorItem[] {
  const seen = new Set<string>();
  const merged: FloorItem[] = [];
  let nextOrder = 1;
  for (const intent of intents) {
    const floorDef = registry.floors.find((f) => f.intent === intent);
    if (!floorDef) continue;
    const sorted = [...floorDef.floor_items].sort((a, b) => a.order - b.order);
    for (const item of sorted) {
      // Dedup key = primitive_id + args (band-agnostic per E-4): the first occurrence wins and
      // keeps its band + hard_floor. Distinct args (e.g. bhava_condition house 2 vs 10, or
      // standing_predictions_read domain wealth vs career) are KEPT — both are wanted.
      const key = `${item.primitive_id}|${JSON.stringify(item.args_override ?? {})}`;
      if (seen.has(key)) continue;
      seen.add(key);
      merged.push({ ...item, order: nextOrder++ });
    }
  }
  return merged;
}

/**
 * E-4 multi-domain composition. When the tuple's primary intent is a deepdive AND its
 * `domains[]` name one or more OTHER deepdive domains, UNION the matched deepdive floors (dedup
 * on primitive_id+args, primary-first stable order) and compile the merged set. Otherwise
 * (single deepdive intent, or a non-deepdive primary) it delegates to `compileContract`, so the
 * single-domain path is byte-identical to the plain compiler — the union only ever ADDS the
 * other domains' items, never mutates the single-domain output.
 *
 * Opt-in at the call site (plan_builder). `compileContract` and the floor_cache stay strictly
 * single-intent so their determinism / "domains is cosmetic" invariants are untouched.
 */
export function compileMultiDomainContract(
  tuple: ScopeTuple,
  registry: VidhiRegistry,
  chartId = '{chart_id}',
): CompiledContract {
  const intents = resolveUnionIntents(tuple);
  if (intents.length <= 1) {
    return compileContract(tuple, registry, chartId);
  }
  const items = unionFloorItems(intents, registry);
  return compileFloorItems(items, tuple, registry, chartId);
}

/** Convenience: build a `VidhiRegistry` from the module's own canonical data (registry_data.ts). */
export function defaultRegistry(): VidhiRegistry {
  return { primitives: VIDHI_PRIMITIVES, floors: VIDHI_INTENT_FLOORS };
}
