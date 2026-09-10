/**
 * Coarse relative-time label for a sidebar row ("now", "5m", "3h", "2d").
 * Pure function of `(updatedAtMs, nowMs)` so it is trivially testable without
 * faking the system clock globally.
 */
export function formatRelativeTime(updatedAtMs: number, nowMs: number): string {
  const deltaSeconds = Math.max(0, Math.floor((nowMs - updatedAtMs) / 1000))
  if (deltaSeconds < 45) return 'now'
  const minutes = Math.floor(deltaSeconds / 60)
  if (minutes < 60) return `${minutes}m`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d`
  const months = Math.floor(days / 30)
  return `${months}mo`
}
