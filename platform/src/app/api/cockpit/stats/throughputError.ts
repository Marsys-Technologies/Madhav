// Extracted from route.ts (not a route.ts file itself, so it can be unit-tested
// directly — Next's build-time route-shape check forbids any export from a
// route.ts file besides GET/POST/route-config; deriveState.ts and scalarMetric.ts
// were already pulled out of route.ts for the identical reason).
//
// Packet B1 — R-2 (review B1_rereview_20260926T190244Z.md, "THE BIG ONE"):
// `fetchAllCounts` never read `asset_throughput.last_error` at all
// (`git log -S"last_error" -- .../stats/route.ts` returns nothing, ever) — the
// `error` argument handed to `deriveState` was null on EVERY path (the
// rows_written shortcut AND the count_sql path), so `deriveState`'s `if (error)`
// branch — which holds the ENTIRE 'blocked' check Packet B1 added — was
// unreachable for a real cascade victim in any poll mode, including `?mode=live`.
// Measured against the 10 real production blocked pairs: 9 of 10 rendered 'lit'
// (green, "built"), 1 rendered 'dormant', zero rendered 'error' or 'blocked'.
//
// This function is the fix: surface `tp.last_error` as the error signal, but
// ONLY when `tp.state` itself says 'error' — never an unconditional pass-through.
// A blind pass-through was tried against live production data first and
// rejected: exactly one row (bg_transit_engine, a global asset) is state='lit'
// with a stale, never-cleared `last_error` from a much earlier attempt (the same
// "success path forgets to clear the diagnostic column" class as the 7
// anomalous BLOCKED rows / A2b-5) — passing it through unconditionally would
// have flipped a currently-healthy asset to 'error'. Gating on
// tp.state === 'error' is also the honest semantic: "does this asset's OWN
// authoritative state column say it failed", not "is there any stale text lying
// around" — the same computed-state-over-stale-text discipline runner.py's own
// STATE DIVERGENCE handling already uses (CLAUDE.md §N.8).
export interface ThroughputEntry {
  state: string
  last_built_at: string | null
  rows_written: number | null
  last_error: string | null
}

export function errorFromThroughput(tp: ThroughputEntry | undefined): string | null {
  return tp?.state === 'error' ? (tp.last_error ?? null) : null
}
