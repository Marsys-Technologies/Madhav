const MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']

/** Canonical portal date: dd-MMM-yyyy (e.g., "05-Feb-1984"). UTC-based. */
export function formatDate(iso: string | Date | null | undefined): string {
  if (!iso) return ''
  const d = iso instanceof Date ? iso : new Date(iso)
  if (isNaN(d.getTime())) return ''
  const dd = String(d.getUTCDate()).padStart(2, '0')
  const mmm = MONTHS[d.getUTCMonth()]
  const yyyy = d.getUTCFullYear()
  return `${dd}-${mmm}-${yyyy}`
}

/** Canonical portal datetime: dd-MMM-yyyy HH:mm (UTC). */
export function formatDateTime(iso: string | Date | null | undefined): string {
  if (!iso) return ''
  const d = iso instanceof Date ? iso : new Date(iso)
  if (isNaN(d.getTime())) return ''
  const hh = String(d.getUTCHours()).padStart(2, '0')
  const mm = String(d.getUTCMinutes()).padStart(2, '0')
  return `${formatDate(d)} ${hh}:${mm}`
}

/** Human-readable relative time from now (e.g., "2h ago", "3d ago"). Returns null for null/invalid. */
export function formatRelative(iso: string | Date | null | undefined): string | null {
  if (!iso) return null
  const d = iso instanceof Date ? iso : new Date(iso)
  if (isNaN(d.getTime())) return null
  const diffMs = Date.now() - d.getTime()
  const diffSec = Math.floor(diffMs / 1000)
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 30) return `${diffDay}d ago`
  const diffMo = Math.floor(diffDay / 30)
  if (diffMo < 12) return `${diffMo}mo ago`
  return `${Math.floor(diffMo / 12)}y ago`
}
