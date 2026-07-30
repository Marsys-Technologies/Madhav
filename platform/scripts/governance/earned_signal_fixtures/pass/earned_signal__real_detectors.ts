// PASS fixture — the correct TypeScript shapes. None of these may be flagged.

// A string-literal UNION in a type position is not a value binding.
export interface Freshness {
  verdict?: 'PASS' | 'FAIL';
  stale: boolean;
  verified_fraction: number;
}

// A literal inside a comment must not match:
//   stale: false,
//   verdict: 'PASS',

export function buildFreshness(rows: unknown[], staleAfter?: number): Freshness {
  const ageMs = Date.now() - lastBuiltAt(rows);
  return {
    // Real detectors: each value depends on runtime input.
    stale: staleAfter !== undefined && ageMs > staleAfter,
    verified_fraction: rows.filter(isVerified).length / Math.max(rows.length, 1),
    verdict: gradeOf(rows),
  };
}

// The sanctioned value for a signal with no detector: null / undefined.
export const UNBUILT_FRESHNESS = {
  stale: null,
  verified: null,
  orientation_ok: undefined,
};

function lastBuiltAt(_rows: unknown[]): number {
  return 0;
}
function isVerified(_row: unknown): boolean {
  return false;
}
function gradeOf(_rows: unknown[]): 'PASS' | 'FAIL' {
  return 'FAIL';
}
