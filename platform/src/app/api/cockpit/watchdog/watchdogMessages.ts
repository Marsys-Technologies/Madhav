// Lives in a sibling module, not route.ts: a Next.js route file may export only route
// handlers/config, so exporting these constants from route.ts fails `next build`.
// Packet A2 ("Always record why it failed") — named, attributable messages shared
// between the build_runs.last_error write and the companion build_run_assets.error
// write, so both tables record the SAME text instead of one of them staying blank.
// Exported for tests that assert the propagated text without duplicating the literal.
export const ORPHAN_RUN_MESSAGE =
  'orphan-watchdog: run orphaned — no asset_throughput heartbeat or build_substep_progress ' +
  'commit in the last 15 minutes on a run running 30+ minutes'
export const STUCK_ASSET_MESSAGE = 'orphan-watchdog: writer never reported back'
export const UNDISPATCHED_RUN_MESSAGE = 'orphan-watchdog: run never dispatched'
