import { describe, expect, it } from 'vitest';
import { VIDHI_INTENT_FLOORS, VIDHI_PRIMITIVES } from '@/lib/vidhi/registry_data';

// NIRMANA L1 W3 F-E10: ga_vastu's serving surface (get_vastu_directions) had zero routed
// vidhi consumers. Fix: mint a `vastu_read` primitive so it is a proper, planner-citable
// vidhi face. It is deliberately NOT forced onto any life-domain deepdive floor — no
// wealth/career/health/marriage/spirituality/education/progeny floor is a natural fit for
// a directional-dwelling read, and DOMAIN_TO_INTENT (compiler.ts) already documents
// `property` as a domain with no dedicated deepdive floor yet.
describe('F-E10 vastu_read vidhi primitive', () => {
  const primitive = VIDHI_PRIMITIVES.find((p) => p.primitive_id === 'vastu_read');

  it('is defined and routes to the live ganita_vastu_get tool with chart_id', () => {
    expect(primitive).toBeDefined();
    expect(primitive?.live_tool).toBe('ganita_vastu_get');
    expect(primitive?.tool_args).toEqual({ chart_id: '{chart_id}' });
    expect(primitive?.known_gap).toBeNull();
  });

  it('is deliberately not a member of any life-domain deepdive floor (documented disposition)', () => {
    for (const floor of VIDHI_INTENT_FLOORS) {
      const memberIds = floor.floor_items.map((item) => item.primitive_id);
      expect(memberIds).not.toContain('vastu_read');
    }
  });
});
