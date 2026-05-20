/**
 * chandra_bala.ts — Chandra Bala (Moon strength) computation for Panchang personalisation.
 *
 * Chandra Bala evaluates the transit Moon's strength relative to the
 * native's natal Moon sign (Janma Rashi).
 *
 * House reckoning: count houses from native's natal Moon sign to the
 * current transit Moon sign (1-indexed, same sign = house 1 = Janma Rashi).
 *
 * Strength table (classical Muhurta Shastra):
 *   STRONG   : houses 1, 3, 6, 7, 10, 11
 *   MODERATE : houses 2, 5, 9
 *   WEAK     : houses 4, 8, 12   (8 = Chandrashtama — avoid major decisions)
 *
 * Source: Muhurta Chintamani §4 / Jataka Parijata Muhurta Prakarana.
 *
 * Phase: 4C-5 (Item 2)
 */

// ── Types ─────────────────────────────────────────────────────────────────────

export type ChandraBalaStrength = 'STRONG' | 'MODERATE' | 'WEAK'

export interface ChandraBalaResult {
  strength: ChandraBalaStrength
  /** House number of transit Moon from natal Moon (1–12) */
  houseFromMoon: number
  /** True when transit Moon is in house 8 from natal Moon (Chandrashtama) */
  isChandrashtama: boolean
}

// ── Static tables ─────────────────────────────────────────────────────────────

const STRONG_HOUSES   = new Set([1, 3, 6, 7, 10, 11])
const MODERATE_HOUSES = new Set([2, 5, 9])
// WEAK = houses 4, 8, 12

// ── Core function ─────────────────────────────────────────────────────────────

/**
 * computeChandraBala — returns Chandra Bala for a transit Moon sign
 *                      relative to native's natal Moon sign.
 *
 * @param nativeMoonSignId   Native's natal Moon rashi, 1-indexed (1 = Aries … 12 = Pisces)
 * @param currentMoonSignId  Transit Moon rashi, 1-indexed (same scale)
 * @returns ChandraBalaResult
 *
 * Algorithm:
 *   house = (currentIdx − nativeIdx + 12) % 12 + 1   (1-indexed, 1 = same sign)
 *
 * Where Aries=1, Taurus=2, ..., Pisces=12.
 */
export function computeChandraBala(
  nativeMoonSignId: number,
  currentMoonSignId: number,
): ChandraBalaResult {
  if (
    !Number.isInteger(nativeMoonSignId) ||
    nativeMoonSignId < 1 ||
    nativeMoonSignId > 12
  ) {
    throw new RangeError(
      `nativeMoonSignId must be integer 1–12, got ${nativeMoonSignId}`,
    )
  }
  if (
    !Number.isInteger(currentMoonSignId) ||
    currentMoonSignId < 1 ||
    currentMoonSignId > 12
  ) {
    throw new RangeError(
      `currentMoonSignId must be integer 1–12, got ${currentMoonSignId}`,
    )
  }

  // Convert to 0-indexed
  const nativeIdx  = nativeMoonSignId - 1   // 0..11
  const currentIdx = currentMoonSignId - 1  // 0..11

  // Forward house count (1-indexed; 1 = own sign)
  const houseFromMoon = (currentIdx - nativeIdx + 12) % 12 + 1

  const isChandrashtama = houseFromMoon === 8

  let strength: ChandraBalaStrength
  if (STRONG_HOUSES.has(houseFromMoon)) {
    strength = 'STRONG'
  } else if (MODERATE_HOUSES.has(houseFromMoon)) {
    strength = 'MODERATE'
  } else {
    strength = 'WEAK'
  }

  return { strength, houseFromMoon, isChandrashtama }
}
