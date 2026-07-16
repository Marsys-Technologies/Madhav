import { describe, expect, it } from 'vitest';
import { VIDHI_INTENT_FLOORS, VIDHI_PRIMITIVES } from '@/lib/vidhi/registry_data';
import { MANDATORY_SURFACE_TAGS } from '@/lib/vidhi/types';
import type { IntentClass } from '@/lib/vidhi/types';

const ALL_INTENT_CLASSES: readonly IntentClass[] = [
  'wealth_deepdive',
  'career_deepdive',
  'health_deepdive',
  'marriage_deepdive',
  'structure_read',
  'panoramic_breadth',
  'retrieval_only',
  'general_synthesis',
];

// CR-27 register row (POST_REMEDIATION_CONSUMPTION_REGISTER_v1_0.md §A) describes four
// logged Class-9 improvisation instances in one row; this lane names them a-d for
// per-item floor-coverage tracking (see track3/CR27_MAPPING_v1_0.md for the full text).
const CR27_INSTANCES = ['CR-27a', 'CR-27b', 'CR-27c', 'CR-27d'] as const;

function primitivesConsumedBy(intent: IntentClass): Set<string> {
  const floor = VIDHI_INTENT_FLOORS.find((f) => f.intent === intent);
  if (!floor) return new Set();
  return new Set(floor.floor_items.map((i) => i.primitive_id));
}

describe('vidhi floors — coverage (D-2 Lane V-1 deliverable 2 + §F1.7 anti-vacuous)', () => {
  it('EVERY intent class has a registered floor (DONE-CHECK per BRIEF_D2.md §F1 V-1)', () => {
    const floored = new Set(VIDHI_INTENT_FLOORS.map((f) => f.intent));
    for (const intent of ALL_INTENT_CLASSES) {
      expect(floored.has(intent), `intent class "${intent}" has no floor`).toBe(true);
    }
  });

  it('every floor has at least one floor_item (no empty floors)', () => {
    for (const floor of VIDHI_INTENT_FLOORS) {
      expect(floor.floor_items.length, `floor "${floor.intent}" is empty`).toBeGreaterThan(0);
    }
  });

  it('floor(wealth_deepdive) contains every atom named in DOCTRINE_CAMPAIGN_DESIGN_v1_0.md §3\'s worked example', () => {
    const consumed = primitivesConsumedBy('wealth_deepdive');
    const designAtoms = [
      'bhava_condition',
      'bhavesha_condition',
      'karaka_condition',
      'from_moon_view',
      'varga_ratification',
      'special_lagna_read',
      'chara_karaka_read',
      'dhana_yoga_scan',
      'nbry_scan',
      'wealth_loss_mechanism_scan',
      'dasha_spine_lord_capability',
      'taranga_curve',
      'lel_retrodiction',
      'intervention_synthesis',
    ];
    for (const atom of designAtoms) {
      expect(consumed.has(atom), `floor(wealth_deepdive) is missing design-§3 atom "${atom}"`).toBe(true);
    }
  });

  it('every §B0.4 mandatory-surface tag is contractually consumed by at least one floor', () => {
    const primitivesByTag = new Map<string, string[]>();
    for (const p of VIDHI_PRIMITIVES) {
      for (const tag of p.mandatory_tags) {
        primitivesByTag.set(tag, [...(primitivesByTag.get(tag) ?? []), p.primitive_id]);
      }
    }
    // Every mandatory tag must be carried by at least one primitive...
    for (const tag of MANDATORY_SURFACE_TAGS) {
      const carriers = primitivesByTag.get(tag) ?? [];
      expect(carriers.length, `no primitive carries §B0.4 mandatory tag "${tag}"`).toBeGreaterThan(0);
    }
    // ...and at least one carrier of each tag must actually be consumed by a floor
    // (a tagged primitive that no floor ever references would be dead data, not a
    // contractually-consumed capability).
    const consumedAnywhere = new Set(VIDHI_INTENT_FLOORS.flatMap((f) => f.floor_items.map((i) => i.primitive_id)));
    for (const tag of MANDATORY_SURFACE_TAGS) {
      const carriers = primitivesByTag.get(tag) ?? [];
      const anyConsumed = carriers.some((id) => consumedAnywhere.has(id));
      expect(anyConsumed, `§B0.4 tag "${tag}" has a carrier primitive but no floor consumes it`).toBe(true);
    }
  });

  it('all four CR-27 improvisation instances are each prevented by at least one floor item', () => {
    const preventedAnywhere = new Set<string>();
    for (const floor of VIDHI_INTENT_FLOORS) {
      for (const item of floor.floor_items) {
        const primitive = VIDHI_PRIMITIVES.find((p) => p.primitive_id === item.primitive_id);
        for (const c of primitive?.cr27_prevents ?? []) preventedAnywhere.add(c);
      }
    }
    for (const instance of CR27_INSTANCES) {
      expect(preventedAnywhere.has(instance), `CR-27 instance "${instance}" is not prevented by any floor item`).toBe(true);
    }
  });

  it('the CR-36 buried-evidence specimen is prevented by at least one wealth_deepdive floor item', () => {
    const wealthFloor = VIDHI_INTENT_FLOORS.find((f) => f.intent === 'wealth_deepdive')!;
    const preventers = wealthFloor.floor_items
      .map((i) => VIDHI_PRIMITIVES.find((p) => p.primitive_id === i.primitive_id))
      .filter((p) => p?.cr27_prevents.includes('CR-36'));
    expect(preventers.length).toBeGreaterThan(0);
  });

  it('every floor declares a cr27_coverage array (possibly empty, but present) — no silently-undocumented floors', () => {
    for (const floor of VIDHI_INTENT_FLOORS) {
      expect(Array.isArray(floor.cr27_coverage)).toBe(true);
    }
  });
});
