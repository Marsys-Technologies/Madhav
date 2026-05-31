/**
 * form_schema.ts — pure validation helpers for NewClientForm
 */

// ─── derivePreferredName ──────────────────────────────────────────────────────

/**
 * Returns preferred_name if non-blank; otherwise returns the first word of
 * full_name, or full_name verbatim if it has no spaces.
 */
export function derivePreferredName(full_name: string, preferred_name: string): string {
  const trimmed = preferred_name.trim()
  if (trimmed) return trimmed
  const firstName = full_name.trim().split(/\s+/)[0] ?? ''
  return firstName
}

// ─── parseBirthDateUi ─────────────────────────────────────────────────────────

/**
 * Converts "DD MM YYYY" (space-separated, day-first) to "YYYY-MM-DD".
 * Returns null on any parse failure — caller is responsible for showing error.
 */
export function parseBirthDateUi(raw: string): string | null {
  if (!raw || !raw.trim()) return null

  const parts = raw.trim().split(/\s+/)
  if (parts.length !== 3) return null

  const day = parseInt(parts[0], 10)
  const month = parseInt(parts[1], 10)
  const year = parseInt(parts[2], 10)

  if (isNaN(day) || isNaN(month) || isNaN(year)) return null
  if (day < 1 || day > 31) return null
  if (month < 1 || month > 12) return null
  if (year < 1) return null

  const mm = String(month).padStart(2, '0')
  const dd = String(day).padStart(2, '0')
  const candidate = `${year}-${mm}-${dd}`

  const d = new Date(`${candidate}T00:00:00Z`)
  if (isNaN(d.getTime())) return null
  if (d.getUTCFullYear() !== year || d.getUTCMonth() + 1 !== month || d.getUTCDate() !== day) {
    return null
  }

  return candidate
}
