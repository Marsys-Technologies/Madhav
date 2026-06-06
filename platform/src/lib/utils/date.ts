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
