/**
 * Fixture — simulates the "platform-mcp" tree copy of cr_status.ts (the copy the deployed MCP
 * server actually imports at runtime) for check_reconciliation_cadence.py's --self-test.
 * Deliberately diverges from cr_status_a.ts on FIX-2 — mirrors the real CR-24/CR-67/CR-69
 * dual-copy drift this script's author found while building it (see PR description).
 */

export const OPEN_CRS = [
  'FIX-3', // consistent with copy A -> no drift on FIX-3 itself; CODE_NOT_UPDATED still fires
           // because the REGISTER row for FIX-3 was independently flipped closed.
] as const;

export const LOGGED_CRS = [] as const;

export const CLOSED_CRS = [
  'FIX-1', // consistent with copy A
  'FIX-2', // INCONSISTENT with copy A (which has FIX-2 in OPEN_CRS) -> DUAL_COPY_DRIFT
  'FIX-6', // consistent with copy A
] as const;
