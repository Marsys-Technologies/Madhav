// FAIL fixture — the TypeScript serving-layer shape (F-20 `freshness.stale`,
// F-23 the consult route's hardcoded planner metrics). A literal-bound status
// property claims a verification result the response never computed.
// EXPECT-VIOLATIONS: 5   (4 object_property + 1 assignment)
export function buildFreshness(rows: unknown[]) {
  return {
    row_count: rows.length,        // real value — not flagged
    stale: false,                  // (T-a) LITERAL
    verified: true,                // (T-a) LITERAL
    orientation_ok: true,          // (T-a) LITERAL
    verdict: 'PASS',               // (T-a) LITERAL
  };
}

export function annotate(result: Record<string, unknown>) {
  result.gateOpen = true;          // (T-b) LITERAL, camelCase normalised
  return result;
}
