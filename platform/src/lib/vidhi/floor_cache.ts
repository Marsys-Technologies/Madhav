/**
 * Vidhi floor precompilation cache — W-28 (planner half).
 *
 * DESIGN SOURCE: RETRIEVAL_IMPLEMENTATION_MASTER_BRIEF_v1_0.md / RETRIEVAL_PLANE_
 * ELEVATION_PLAN_v1_0.md — "Vidhi floors precompiled per intent×depth, keyed by
 * capability_version." A caching layer so `compileContract` (compiler.ts) does not redo
 * the same deterministic compilation on every request for the same scope-tuple shape.
 *
 * WHAT ACTUALLY VARIES THE COMPILED FLOOR (verified against compiler.ts):
 *   - `intent`       → selects the IntentFloor (registry.floors.find)
 *   - `depth`        → bandsForDepth() include/structural-only gates
 *   - `intervention` → strips remedy-category items from both bands
 * NOTHING ELSE in the ScopeTuple changes the compiled `floor` / `machine_band` /
 * `completeness_receipt_template`. `width`, `horizon`, `entitlement`, `domains` are ECHOED
 * verbatim in `scope_tuple` on the output but never read by the compiler. `chartId` only
 * substitutes `{chart_id}` tokens inside `tool_args` (compiler.ts `mergeArgs`) — a cheap,
 * top-level, per-call transform, NOT part of the expensive structural compilation.
 *
 * CONSEQUENCE — the precompiled unit is CHART-AGNOSTIC. We cache the compiled contract
 * built with the `{chart_id}` PLACEHOLDER, keyed on (capability_version, intent, depth,
 * intervention), then per call (a) substitute the real chartId into the item args and
 * (b) attach the caller's actual `scope_tuple`. One warm cache therefore serves every
 * chart. The result is byte-identical to calling `compileContract(tuple, registry, chartId)`
 * directly — asserted in floor_cache.test.ts by hash-equality against the un-cached path.
 *
 * KEY SHAPE: `${capability_version}|${intent}|${depth}|${intervention}`.
 *   - `capability_version` is a sha256 (first 16 hex) fingerprint of COMPILER_VERSION +
 *     the registry's primitives + floors content (stable-stringified). It changes the
 *     instant registry_data.ts (or the compiler version) changes, so the cache correctly
 *     BUSTS on any registry edit — it is NOT a hardcoded literal that would never invalidate.
 *
 * CARDINALITY / GROWTH: the input space is small and enumerable — 8 intents × 3 depths ×
 * 2 intervention = 48 chart-agnostic cores per capability_version. Across a process's life
 * the registry content changes at most a handful of times, so the Map holds low hundreds of
 * small objects worst-case. A plain unbounded Map is the simplest-correct choice; an LRU /
 * eviction policy would be over-engineering for a bounded, tiny key space (per the W-28
 * brief's "don't over-engineer eviction for a cardinality that doesn't need it").
 *
 * EAGER vs LAZY: the design language says "precompiled", so this module EAGERLY warms all
 * 48 cores for the default registry at module load (see the `warmFloorCache()` call at the
 * bottom). Warming is deterministic and cheap (48 pure compiles, no I/O). Lazy population on
 * miss is retained as a fallback so a non-default registry (e.g. the future DB-backed
 * registry the registry_data.ts header describes) still benefits without a manual warm.
 *
 * DROP-IN STATUS: `compileContractCached` has the identical signature/return type as
 * `compileContract`. The live call site (`platform/src/lib/pipeline/compiled_floor_adapter.ts`
 * / `compileFloorForPlan`, landed by a parallel W4 lane) does NOT exist on this branch, so
 * this ships as a drop-in cached wrapper AROUND `compileContract`, ready to be swapped in
 * wherever `compileContract` is called once the branches merge.
 */
import { createHash } from 'crypto';
import type { CompiledContract, CompiledFloorItem, ScopeDepth, ScopeTuple } from './types';
import { COMPILER_VERSION, compileContract, defaultRegistry, type VidhiRegistry } from './compiler';

const CHART_ID_TOKEN = '{chart_id}';

/** The three dimensions that actually vary a compiled floor's structure. */
interface FloorCacheDims {
  readonly intent: ScopeTuple['intent'];
  readonly depth: ScopeDepth;
  readonly intervention: boolean;
}

/** A cached chart-agnostic core: the placeholder-compiled contract + its capability_version. */
interface FloorCacheEntry {
  /** Compiled with `chartId = '{chart_id}'` — chart-agnostic; tool_args still hold the token. */
  readonly placeholder: CompiledContract;
}

const _cache = new Map<string, FloorCacheEntry>();
const _stats = { hits: 0, misses: 0 };

/** Stable, key-sorted JSON — identical content hashes identically regardless of key order. */
function stableStringify(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value) ?? 'null';
  if (Array.isArray(value)) return `[${value.map(stableStringify).join(',')}]`;
  const obj = value as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${stableStringify(obj[k])}`).join(',')}}`;
}

/**
 * Derive the `capability_version` fingerprint from the registry CONTENT (+ compiler version).
 * Any edit to a primitive, a floor, a floor item's args, or COMPILER_VERSION changes this
 * digest and therefore every cache key — so the cache self-invalidates on registry change.
 * Exported so the adapter / a census harness can key or assert on the same value.
 */
export function capabilityVersion(registry: VidhiRegistry): string {
  const payload = stableStringify({
    compiler_version: COMPILER_VERSION,
    primitives: registry.primitives,
    floors: registry.floors,
  });
  return createHash('sha256').update(payload).digest('hex').slice(0, 16);
}

function cacheKey(capVersion: string, dims: FloorCacheDims): string {
  return `${capVersion}|${dims.intent}|${dims.depth}|${dims.intervention}`;
}

/** A canonical ScopeTuple carrying only the compile-relevant dims; the rest are inert fillers
 *  (compiler.ts never reads width/horizon/entitlement/domains) used solely so the tuple type-checks. */
function coreTuple(dims: FloorCacheDims): ScopeTuple {
  return {
    intent: dims.intent,
    depth: dims.depth,
    intervention: dims.intervention,
    domains: [],
    width: 'standard',
    horizon: 'natal',
    entitlement: 'native',
  };
}

/** Substitute the real chartId into an item's args — mirrors compiler.ts `mergeArgs`' token
 *  pass exactly (top-level `=== '{chart_id}'` only), preserving key order so the produced
 *  object hashes identically to a direct compile. */
function substituteChartId(items: readonly CompiledFloorItem[], chartId: string): CompiledFloorItem[] {
  if (chartId === CHART_ID_TOKEN) return items.map((i) => ({ ...i, tool_args: { ...i.tool_args } }));
  return items.map((item) => {
    const tool_args: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(item.tool_args)) {
      tool_args[k] = v === CHART_ID_TOKEN ? chartId : v;
    }
    return { ...item, tool_args };
  });
}

/**
 * Compile (or fetch a precompiled) contract for `tuple`. Drop-in replacement for
 * `compileContract` — identical signature, identical (hash-equal) return value.
 *
 * On a cache hit the expensive structural compilation is skipped: only the cheap per-call
 * chartId substitution + scope_tuple echo run. On a miss it compiles the chart-agnostic core
 * once, stores it, then finalizes. Throws exactly as `compileContract` does (unregistered
 * intent / primitive) — failures are propagated, never cached.
 */
export function compileContractCached(
  tuple: ScopeTuple,
  registry: VidhiRegistry = defaultRegistry(),
  chartId = CHART_ID_TOKEN,
): CompiledContract {
  const dims: FloorCacheDims = { intent: tuple.intent, depth: tuple.depth, intervention: tuple.intervention };
  const capVersion = capabilityVersion(registry);
  const key = cacheKey(capVersion, dims);

  let entry = _cache.get(key);
  if (entry) {
    _stats.hits += 1;
  } else {
    _stats.misses += 1;
    // Compile the chart-agnostic core with the placeholder chartId, then cache it.
    const placeholder = compileContract(coreTuple(dims), registry, CHART_ID_TOKEN);
    entry = { placeholder };
    _cache.set(key, entry);
  }

  const { placeholder } = entry;
  // Finalize: substitute chartId into the item args and attach the caller's actual tuple.
  // completeness_receipt_template is chart-independent (dark = primitive_ids; served/empty = [])
  // so it is reused verbatim. Field order mirrors compiler.ts's object literal for hash parity.
  return {
    compiler_version: placeholder.compiler_version,
    scope_tuple: tuple,
    floor: substituteChartId(placeholder.floor, chartId),
    machine_band: substituteChartId(placeholder.machine_band, chartId),
    // E-3 adaptive_expansions (VIDHI-PŪRṆATĀ P-3b) are chart-AGNOSTIC — computeAdaptiveExpansions
    // embeds NO chart_id (only house/karaka/primitive_id) — so the placeholder's set is reused
    // verbatim, keeping the cached contract byte-identical to a direct compile (the hash-equality
    // floor_cache.test.ts asserts). Field position mirrors compiler.ts (after machine_band).
    adaptive_expansions: placeholder.adaptive_expansions,
    completeness_receipt_template: placeholder.completeness_receipt_template,
    llm_extension_note: placeholder.llm_extension_note,
  };
}

const ALL_DEPTHS: readonly ScopeDepth[] = ['retrieval', 'structure', 'deepdive'];
const ALL_INTERVENTION: readonly boolean[] = [true, false];

/**
 * Eagerly precompile every (intent × depth × intervention) core for `registry` — true
 * "precompilation". Idempotent (a warm entry is not recompiled). Returns the number of cores
 * now resident for this registry's capability_version. Called once at module load for the
 * default registry; callers wiring a non-default registry may call it at startup.
 */
export function warmFloorCache(registry: VidhiRegistry = defaultRegistry()): number {
  const capVersion = capabilityVersion(registry);
  let warmed = 0;
  for (const floor of registry.floors) {
    for (const depth of ALL_DEPTHS) {
      for (const intervention of ALL_INTERVENTION) {
        const dims: FloorCacheDims = { intent: floor.intent, depth, intervention };
        const key = cacheKey(capVersion, dims);
        if (!_cache.has(key)) {
          _cache.set(key, { placeholder: compileContract(coreTuple(dims), registry, CHART_ID_TOKEN) });
        }
        warmed += 1;
      }
    }
  }
  return warmed;
}

/** Number of cores resident for `registry`'s capability_version — for warm-state assertions. */
export function floorCacheSize(registry: VidhiRegistry = defaultRegistry()): number {
  const prefix = `${capabilityVersion(registry)}|`;
  let n = 0;
  for (const key of _cache.keys()) if (key.startsWith(prefix)) n += 1;
  return n;
}

/** Hit/miss counters + total resident entries — for observability and tests. */
export function floorCacheStats(): { hits: number; misses: number; size: number } {
  return { hits: _stats.hits, misses: _stats.misses, size: _cache.size };
}

/** Clear the cache and counters — test-only hygiene (never called by production paths). */
export function resetFloorCache(): void {
  _cache.clear();
  _stats.hits = 0;
  _stats.misses = 0;
}

// ── Eager warm at module load (true precompilation for the default registry) ──
warmFloorCache();
