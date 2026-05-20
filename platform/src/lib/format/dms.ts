/**
 * dms.ts — Decimal degrees → Degrees°Minutes'Seconds" formatter
 *
 * Reused by PlanetaryGrid and future Panchang components.
 * Phase: 4C-4-S2 (Item 4)
 */

export interface DMS {
  degrees: number
  minutes: number
  seconds: number
}

/**
 * Convert decimal degrees to DMS components.
 * Input is treated as absolute value — caller handles sign/direction.
 * Wraps values > 360 correctly.
 */
export function decimalToDMS(decimalDeg: number): DMS {
  // Normalize to [0, 360)
  const normalized = ((decimalDeg % 360) + 360) % 360
  const totalSeconds = Math.round(normalized * 3600)
  const degrees = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  return { degrees, minutes, seconds }
}

/**
 * Format decimal degrees as "DD°MM'SS"".
 * Examples:
 *   4.389  → "04°23'20\""
 *   0      → "00°00'00\""
 *   360    → "00°00'00\""  (wraps)
 *   -5     → "355°00'00\"" (normalized to positive)
 */
export function formatDMS(decimalDeg: number): string {
  const { degrees, minutes, seconds } = decimalToDMS(decimalDeg)
  const dd = String(degrees).padStart(2, '0')
  const mm = String(minutes).padStart(2, '0')
  const ss = String(seconds).padStart(2, '0')
  return `${dd}°${mm}'${ss}"`
}

/**
 * Format decimal degrees as short DMS — "DD°MM'" (no seconds).
 * Used in the Planetary Grid where space is tight.
 */
export function formatDMSShort(decimalDeg: number): string {
  const { degrees, minutes } = decimalToDMS(decimalDeg)
  const dd = String(degrees).padStart(2, '0')
  const mm = String(minutes).padStart(2, '0')
  return `${dd}°${mm}'`
}

/**
 * Degrees within a sign (0–29.999°) from absolute ecliptic longitude.
 * E.g. Sun at Mesha 4°23' = absolute lon 4.389 → within-sign = 4.389
 *      Moon at Vrishabha 18° = absolute lon 48° → within-sign = 18
 */
export function lonWithinSign(absoluteLon: number): number {
  const normalized = ((absoluteLon % 360) + 360) % 360
  return normalized % 30
}
