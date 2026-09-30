// A Next.js route may export only handlers and route configuration.
// Keep these messages here so runtime and tests share identical text.
export const ORPHAN_RUN_MESSAGE =
  'orphan-watchdog: run orphaned — no asset_throughput heartbeat or build_substep_progress ' +
  'commit in the last 15 minutes on a run running 30+ minutes'
export const STUCK_ASSET_MESSAGE = 'orphan-watchdog: writer never reported back'
export const UNDISPATCHED_RUN_MESSAGE = 'orphan-watchdog: run never dispatched'
