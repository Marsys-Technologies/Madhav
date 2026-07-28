/**
 * Fixture — simulates a registry_data.ts primitive citing a known_gap that its sibling
 * cr_status.ts (cr_status_a.ts, the "platform" tree copy) has already moved to CLOSED_CRS.
 * Exercises KNOWN_GAP_CITES_CLOSED in check_reconciliation_cadence.py's --self-test.
 */

export const VIDHI_PRIMITIVES = [
  {
    primitive_id: 'fixture_primitive_citing_closed_cr',
    known_gap: 'FIX-5', // FIX-5 is in cr_status_a.ts's CLOSED_CRS -> forbidden citation
  },
  {
    primitive_id: 'fixture_primitive_citing_open_cr',
    known_gap: 'FIX-3', // FIX-3 is in cr_status_a.ts's OPEN_CRS -> legitimate, no divergence
  },
] as const;
