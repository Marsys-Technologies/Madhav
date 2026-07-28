/**
 * Fixture — simulates the "platform" tree copy of cr_status.ts for
 * check_reconciliation_cadence.py's --self-test. Not real code; never imported by anything.
 */

export const OPEN_CRS = [
  'FIX-2',
  'FIX-3',
  'FIX-4', // deliberately ALSO in CLOSED_CRS below — this is the FIX-4 self-contradiction fixture
] as const;

export const LOGGED_CRS = [] as const;

export const CLOSED_CRS = [
  'FIX-1', // closed in both copies; sample_register.md's FIX-1 row is still OPEN -> REGISTER_NOT_FLIPPED
  'FIX-4', // see OPEN_CRS note above
  'FIX-5', // closed here; registry_data_a.ts cites known_gap: 'FIX-5' -> KNOWN_GAP_CITES_CLOSED
  'FIX-6', // closed in both copies AND register row flipped -> the clean, non-divergent case
] as const;
