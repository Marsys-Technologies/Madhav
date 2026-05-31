/**
 * form_schema.ts — pure validation helpers for NewClientForm
 *
 * UI-layer concern: birth date is entered as DD MM YYYY (day-first, space-
 * separated) and converted to ISO 8601 (YYYY-MM-DD) before submission.
 * timezone_id is an IANA zone string ("Asia/Kolkata").
 *
 * [BUILD-ORCH-D-S1]
 */

// ─── Types ────────────────────────────────────────────────────────────────────

export interface FormInput {
  full_name: string
  preferred_name: string
  gender: 'male' | 'female' | 'other' | 'not-specified'
  birth_date_ui: string     // DD MM YYYY (UI-only)
  birth_time: string        // HH:MM
  birth_place: string
  latitude: string
  longitude: string
  timezone_id: string       // IANA TZ e.g. "Asia/Kolkata"
  ayanamshas: string[]
}

export type ValidateOk = {
  ok: true
  birth_date: string        // YYYY-MM-DD (ISO, ready for API)
  preferred_name: string    // derived or provided
} & FormInput

export type ValidateErr = {
  ok: false
  errors: string[]          // field names that failed
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

  // Verify it's a real date
  const d = new Date(`${candidate}T00:00:00Z`)
  if (isNaN(d.getTime())) return null
  // Guard against day overflow (e.g. Feb 31)
  if (d.getUTCFullYear() !== year || d.getUTCMonth() + 1 !== month || d.getUTCDate() !== day) {
    return null
  }

  return candidate
}

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

// ─── validateFormSchema ───────────────────────────────────────────────────────

export function validateFormSchema(input: FormInput): ValidateOk | ValidateErr {
  const errors: string[] = []

  // birth_date_ui → birth_date (ISO)
  const birth_date = parseBirthDateUi(input.birth_date_ui)
  if (!birth_date) errors.push('birth_date_ui')

  // timezone_id required
  if (!input.timezone_id || !input.timezone_id.trim()) errors.push('timezone_id')

  // full_name required
  if (!input.full_name || !input.full_name.trim()) errors.push('full_name')

  // birth_place required
  if (!input.birth_place || !input.birth_place.trim()) errors.push('birth_place')

  // ayanamshas non-empty
  if (!input.ayanamshas || input.ayanamshas.length === 0) errors.push('ayanamshas')

  if (errors.length > 0) return { ok: false, errors }

  return {
    ok: true,
    ...input,
    birth_date: birth_date!,
    preferred_name: derivePreferredName(input.full_name, input.preferred_name),
  }
}
