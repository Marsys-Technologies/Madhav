/** Original saved time only; missing or invalid metadata never becomes the export time. */
export function savedReadingTimestamp(metadata: unknown): string | null {
  if (!metadata || typeof metadata !== 'object') return null
  const value = (metadata as { createdAt?: unknown }).createdAt
  // The shared DB client deliberately returns PostgreSQL timestamps as strings.
  // Require a timezone so parsing never depends on the viewer's local timezone.
  if (!(value instanceof Date)) {
    if (typeof value !== 'string') return null
    const match = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|[+-]\d{2}(?::\d{2})?)$/.exec(value)
    if (!match) return null
    const [year, month, day, hour, minute, second] = match.slice(1).map(Number)
    const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
    const days = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if (month < 1 || month > 12 || day < 1 || day > days[month - 1] ||
        hour > 23 || minute > 59 || second > 59) return null
  }
  const normalized = typeof value === 'string'
    ? value.replace(' ', 'T').replace(/([+-]\d{2})$/, '$1:00') : value
  const date = normalized instanceof Date ? normalized : new Date(normalized)
  if (Number.isNaN(date.getTime())) return null
  // Date handles timezone conversion, but only retains milliseconds. Keep the
  // saved fractional seconds verbatim so PostgreSQL microseconds survive export.
  const fraction = typeof value === 'string' ? /\.(\d+)/.exec(value)?.[1] : undefined
  return fraction
    ? date.toISOString().replace(/\.\d{3}Z$/, `.${fraction.padEnd(3, '0')}Z`)
    : date.toISOString()
}
