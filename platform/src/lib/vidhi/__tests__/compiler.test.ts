import { createHash } from 'crypto';
import { describe, expect, it } from 'vitest';
import { compileContract, defaultRegistry } from '@/lib/vidhi/compiler';
import type { ScopeTuple } from '@/lib/vidhi/types';

function hashOf(value: unknown): string {
  return createHash('sha256').update(JSON.stringify(value)).digest('hex');
}

const wealthDeepdiveTuple: ScopeTuple = {
  intent: 'wealth_deepdive',
  domains: ['wealth'],
  width: 'standard',
  depth: 'deepdive',
  horizon: 'multi_year',
  intervention: true,
  entitlement: 'native',
};

describe('vidhi compiler — determinism (hash-equality)', () => {
  it('identical scope_tuple → byte-identical compiled contract (same object reference)', () => {
    const registry = defaultRegistry();
    const a = compileContract(wealthDeepdiveTuple, registry, '482012f1-710e-4a25-994a-93821f5871aa');
    const b = compileContract(wealthDeepdiveTuple, registry, '482012f1-710e-4a25-994a-93821f5871aa');
    expect(hashOf(a)).toBe(hashOf(b));
  });

  it('identical scope_tuple → byte-identical compiled contract (structurally-equal but distinct tuple object)', () => {
    const registry = defaultRegistry();
    const tupleCopy: ScopeTuple = JSON.parse(JSON.stringify(wealthDeepdiveTuple));
    const a = compileContract(wealthDeepdiveTuple, registry, 'chart-x');
    const b = compileContract(tupleCopy, registry, 'chart-x');
    expect(a).not.toBe(b); // distinct objects
    expect(hashOf(a)).toBe(hashOf(b)); // identical content
  });

  it('repeated compiles (10x) all hash-identical — no hidden nondeterminism (Date.now/Math.random/iteration order)', () => {
    const registry = defaultRegistry();
    const hashes = new Set<string>();
    for (let i = 0; i < 10; i++) {
      hashes.add(hashOf(compileContract(wealthDeepdiveTuple, registry, 'chart-x')));
    }
    expect(hashes.size).toBe(1);
  });

  it('a differing scope_tuple field (depth) produces a different hash — the test is not vacuously true', () => {
    const registry = defaultRegistry();
    const deep = compileContract(wealthDeepdiveTuple, registry, 'chart-x');
    const retrieval = compileContract({ ...wealthDeepdiveTuple, depth: 'retrieval' }, registry, 'chart-x');
    expect(hashOf(deep)).not.toBe(hashOf(retrieval));
  });

  it('intervention=false strips remedy-category floor items deterministically', () => {
    const registry = defaultRegistry();
    const withIntervention = compileContract(wealthDeepdiveTuple, registry, 'chart-x');
    const without = compileContract({ ...wealthDeepdiveTuple, intervention: false }, registry, 'chart-x');
    const remedyIdsWith = withIntervention.machine_band.filter((i) => i.primitive_id === 'intervention_synthesis');
    const remedyIdsWithout = without.machine_band.filter((i) => i.primitive_id === 'intervention_synthesis');
    expect(remedyIdsWith.length).toBe(1);
    expect(remedyIdsWithout.length).toBe(0);
    // still deterministic under the new tuple
    const again = compileContract({ ...wealthDeepdiveTuple, intervention: false }, registry, 'chart-x');
    expect(hashOf(without)).toBe(hashOf(again));
  });

  it('depth=retrieval compiles the floor to structural-only items and drops the machine band entirely', () => {
    const registry = defaultRegistry();
    const retrieval = compileContract({ ...wealthDeepdiveTuple, depth: 'retrieval' }, registry, 'chart-x');
    expect(retrieval.machine_band.length).toBe(0);
    expect(retrieval.floor.length).toBeGreaterThan(0);
  });

  it('throws loudly for an unregistered intent rather than silently compiling an empty contract', () => {
    const registry = defaultRegistry();
    const badTuple = { ...wealthDeepdiveTuple, intent: 'not_a_real_intent' } as unknown as ScopeTuple;
    expect(() => compileContract(badTuple, registry, 'chart-x')).toThrow();
  });

  it('every canonical intent class compiles without throwing', () => {
    const registry = defaultRegistry();
    for (const floor of registry.floors) {
      expect(() =>
        compileContract(
          { ...wealthDeepdiveTuple, intent: floor.intent, depth: 'deepdive' },
          registry,
          'chart-x',
        ),
      ).not.toThrow();
    }
  });
});
