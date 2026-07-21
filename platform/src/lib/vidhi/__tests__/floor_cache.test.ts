import { createHash } from 'crypto';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { compileContract, defaultRegistry, type VidhiRegistry } from '@/lib/vidhi/compiler';
import {
  capabilityVersion,
  compileContractCached,
  floorCacheSize,
  floorCacheStats,
  resetFloorCache,
  warmFloorCache,
} from '@/lib/vidhi/floor_cache';
import type { ScopeTuple } from '@/lib/vidhi/types';

function hashOf(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

const CHART = '482012f1-710e-4a25-994a-93821f5871aa';

const wealthDeepdiveTuple: ScopeTuple = {
  intent: 'wealth_deepdive',
  domains: ['wealth'],
  width: 'standard',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: true,
  entitlement: 'native',
};

describe('vidhi floor_cache — correctness vs the un-cached compiler', () => {
  beforeEach(() => {
    resetFloorCache();
    warmFloorCache();
  });
  afterEach(() => resetFloorCache());

  it('cached output is byte-identical (hash-equal) to a direct compileContract call', () => {
    const registry = defaultRegistry();
    const direct = compileContract(wealthDeepdiveTuple, registry, CHART);
    const cached = compileContractCached(wealthDeepdiveTuple, registry, CHART);
    expect(hashOf(cached)).toBe(hashOf(direct));
  });

  it('matches the un-cached compiler across EVERY intent × depth × intervention combo', () => {
    const registry = defaultRegistry();
    for (const floor of registry.floors) {
      for (const depth of ['retrieval', 'structure', 'deepdive'] as const) {
        for (const intervention of [true, false]) {
          const tuple: ScopeTuple = { ...wealthDeepdiveTuple, intent: floor.intent, depth, intervention };
          const direct = compileContract(tuple, registry, CHART);
          const cached = compileContractCached(tuple, registry, CHART);
          expect(hashOf(cached)).toBe(hashOf(direct));
        }
      }
    }
  });

  it('echoes the caller\'s FULL scope_tuple (not the placeholder core tuple)', () => {
    const cached = compileContractCached(wealthDeepdiveTuple, defaultRegistry(), CHART);
    // domains/width/horizon/entitlement are cosmetic to compilation but must round-trip verbatim.
    expect(cached.scope_tuple).toEqual(wealthDeepdiveTuple);
  });

  it('substitutes the real chartId into tool_args on a cache hit', () => {
    const cached = compileContractCached(wealthDeepdiveTuple, defaultRegistry(), CHART);
    const withToken = JSON.stringify(cached).includes('{chart_id}');
    expect(withToken).toBe(false);
    // and a chart-args-bearing item actually carries the chart id
    const anyItem = [...cached.floor, ...cached.machine_band].find((i) => 'chart_id' in i.tool_args);
    expect(anyItem?.tool_args.chart_id).toBe(CHART);
  });

  it('the default placeholder chartId path also matches the un-cached compiler', () => {
    const registry = defaultRegistry();
    const direct = compileContract(wealthDeepdiveTuple, registry); // default '{chart_id}'
    const cached = compileContractCached(wealthDeepdiveTuple, registry); // default '{chart_id}'
    expect(hashOf(cached)).toBe(hashOf(direct));
  });
});

describe('vidhi floor_cache — hit / miss behavior', () => {
  beforeEach(() => resetFloorCache());
  afterEach(() => resetFloorCache());

  it('cold call is a miss; a repeat with the same effective dims is a hit', () => {
    const registry = defaultRegistry();
    const before = floorCacheStats();
    compileContractCached(wealthDeepdiveTuple, registry, CHART);
    const afterFirst = floorCacheStats();
    expect(afterFirst.misses).toBe(before.misses + 1);

    compileContractCached(wealthDeepdiveTuple, registry, CHART);
    const afterSecond = floorCacheStats();
    expect(afterSecond.hits).toBe(afterFirst.hits + 1);
    expect(afterSecond.misses).toBe(afterFirst.misses); // no new miss
  });

  it('a different chartId with the same dims is still a HIT (chart-agnostic core)', () => {
    const registry = defaultRegistry();
    compileContractCached(wealthDeepdiveTuple, registry, CHART); // miss
    const afterMiss = floorCacheStats();
    compileContractCached(wealthDeepdiveTuple, registry, 'a-different-chart'); // hit
    const afterHit = floorCacheStats();
    expect(afterHit.hits).toBe(afterMiss.hits + 1);
    expect(afterHit.misses).toBe(afterMiss.misses);
  });

  it('cosmetic-only tuple changes (width/horizon/entitlement/domains) are HITS', () => {
    const registry = defaultRegistry();
    compileContractCached(wealthDeepdiveTuple, registry, CHART); // miss
    const afterMiss = floorCacheStats();
    compileContractCached(
      { ...wealthDeepdiveTuple, width: 'panoramic', horizon: 'natal', entitlement: 'research', domains: ['x'] },
      registry,
      CHART,
    );
    const afterHit = floorCacheStats();
    expect(afterHit.hits).toBe(afterMiss.hits + 1);
    expect(afterHit.misses).toBe(afterMiss.misses);
  });

  it('distinct intent / depth / intervention each produce a distinct cache entry (a miss)', () => {
    const registry = defaultRegistry();
    compileContractCached(wealthDeepdiveTuple, registry, CHART); // miss #1
    const base = floorCacheStats();

    compileContractCached({ ...wealthDeepdiveTuple, depth: 'retrieval' }, registry, CHART); // miss #2 (depth)
    compileContractCached({ ...wealthDeepdiveTuple, intervention: false }, registry, CHART); // miss #3 (intervention)
    compileContractCached({ ...wealthDeepdiveTuple, intent: 'career_deepdive' }, registry, CHART); // miss #4 (intent)

    const after = floorCacheStats();
    expect(after.misses).toBe(base.misses + 3);
  });
});

describe('vidhi floor_cache — capability_version invalidation', () => {
  beforeEach(() => resetFloorCache());
  afterEach(() => resetFloorCache());

  it('capabilityVersion changes when the registry content changes → cache busts', () => {
    const registry = defaultRegistry();
    const v1 = capabilityVersion(registry);

    // Mutate a floor item's args_override — a real registry edit.
    const mutated: VidhiRegistry = {
      primitives: registry.primitives,
      floors: registry.floors.map((f) =>
        f.intent === 'wealth_deepdive'
          ? {
              ...f,
              floor_items: f.floor_items.map((it, idx) =>
                idx === 0 ? { ...it, args_override: { ...(it.args_override ?? {}), house: 99 } } : it,
              ),
            }
          : f,
      ),
    };
    const v2 = capabilityVersion(mutated);
    expect(v2).not.toBe(v1);

    // A call under v1 populates v1's key space; the same dims under v2 must MISS (new key).
    compileContractCached(wealthDeepdiveTuple, registry, CHART); // miss under v1
    const afterV1 = floorCacheStats();
    compileContractCached(wealthDeepdiveTuple, mutated, CHART); // miss under v2 (busted)
    const afterV2 = floorCacheStats();
    expect(afterV2.misses).toBe(afterV1.misses + 1);

    // And the busted result is correct for the mutated registry.
    const direct = compileContract(wealthDeepdiveTuple, mutated, CHART);
    const cached = compileContractCached(wealthDeepdiveTuple, mutated, CHART);
    expect(hashOf(cached)).toBe(hashOf(direct));
  });

  it('an unchanged registry keeps a stable capability_version across calls', () => {
    expect(capabilityVersion(defaultRegistry())).toBe(capabilityVersion(defaultRegistry()));
  });
});

describe('vidhi floor_cache — eager warming', () => {
  it('the cache is fully warm (48 cores) after an explicit warmFloorCache()', () => {
    resetFloorCache();
    const warmed = warmFloorCache();
    // 8 intents × 3 depths × 2 intervention = 48
    expect(warmed).toBe(48);
    expect(floorCacheSize()).toBe(48);
  });

  it('every combo is a HIT immediately after warming — zero misses on first real use', () => {
    resetFloorCache();
    warmFloorCache();
    const before = floorCacheStats();
    const registry = defaultRegistry();
    for (const floor of registry.floors) {
      for (const depth of ['retrieval', 'structure', 'deepdive'] as const) {
        for (const intervention of [true, false]) {
          compileContractCached(
            { ...wealthDeepdiveTuple, intent: floor.intent, depth, intervention },
            registry,
            CHART,
          );
        }
      }
    }
    const after = floorCacheStats();
    expect(after.misses).toBe(before.misses); // no misses — the warm cache absorbed every call
    expect(after.hits).toBe(before.hits + 48);
  });

  it('warming is idempotent — a second warm adds no new cores', () => {
    resetFloorCache();
    warmFloorCache();
    const size1 = floorCacheSize();
    warmFloorCache();
    expect(floorCacheSize()).toBe(size1);
  });
});
