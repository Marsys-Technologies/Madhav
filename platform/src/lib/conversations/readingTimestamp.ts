/** Original saved time only; missing or invalid metadata never becomes the export time. */
export function savedReadingTimestamp(metadata: unknown): string | null {
  if (!metadata || typeof metadata !== 'object') return null
  const value = (metadata as { createdAt?: unknown }).createdAt
  // The shared DB client deliberately returns PostgreSQL timestamps as strings.
  // Require a timezone so parsing never depends on the viewer's local timezone.
  if (!(value instanceof Date) && (typeof value !== 'string' ||
      !/^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}(?::\d{2})?)$/.test(value))) return null
  const normalized = typeof value === 'string'
    ? value.replace(' ', 'T').replace(/([+-]\d{2})$/, '$1:00') : value
  const date = normalized instanceof Date ? normalized : new Date(normalized)
  return Number.isNaN(date.getTime()) ? null : date.toISOString()
}
