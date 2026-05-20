/**
 * tara_bala.ts — Tara Bala computation for Panchang personalisation.
 *
 * Tara Bala measures the strength / weakness of a nakshatra day
 * relative to the native's birth (Janma) nakshatra.
 *
 * The 9 Taras repeat cyclically across all 27 nakshatras:
 *   Count from native's birth nakshatra to the current nakshatra
 *   (wrapping modulo 27); the remainder mod 9 gives the Tara index.
 *
 * Classical source: Muhurta Chintamani §2 / Kala Prakasika Tara table.
 *
 * Phase: 4C-5 (Item 1)
 */

// ── Tara types ────────────────────────────────────────────────────────────────

export type TaraBalaName =
  | 'Janma'
  | 'Sampat'
  | 'Vipat'
  | 'Kshema'
  | 'Pratyari'
  | 'Sadhaka'
  | 'Vadha'
  | 'Mitra'
  | 'Ati Mitra'

export type TaraBalaClass = 'auspicious' | 'inauspicious' | 'mixed'

export interface TaraBalaResult {
  tara: TaraBalaName
  /** 1-indexed count from native's birth nakshatra (1 = Janma, 9 = Ati Mitra) */
  count: number
  classification: TaraBalaClass
}

// ── Static tables ─────────────────────────────────────────────────────────────

/** 9 Taras in order. Index 0 → count 1 (Janma). */
const TARA_NAMES: TaraBalaName[] = [
  'Janma',      // 1 — mixed (own star; powerful but neutral tendency)
  'Sampat',     // 2 — auspicious
  'Vipat',      // 3 — inauspicious
  'Kshema',     // 4 — auspicious
  'Pratyari',   // 5 — inauspicious
  'Sadhaka',    // 6 — auspicious
  'Vadha',      // 7 — inauspicious
  'Mitra',      // 8 — auspicious
  'Ati Mitra',  // 9 — auspicious
]

const TARA_CLASSIFICATION: Record<TaraBalaName, TaraBalaClass> = {
  'Janma':      'mixed',
  'Sampat':     'auspicious',
  'Vipat':      'inauspicious',
  'Kshema':     'auspicious',
  'Pratyari':   'inauspicious',
  'Sadhaka':    'auspicious',
  'Vadha':      'inauspicious',
  'Mitra':      'auspicious',
  'Ati Mitra':  'auspicious',
}

// ── Core function ─────────────────────────────────────────────────────────────

/**
 * computeTaraBala — returns the Tara Bala for a given (birth, current) nakshatra pair.
 *
 * @param nativeBirthNakshatraId  Native's Janma nakshatra, 1-indexed (1 = Ashwini … 27 = Revati)
 * @param currentNakshatraId      Today's nakshatra, 1-indexed (same scale)
 * @returns TaraBalaResult
 *
 * Algorithm:
 *   distance = (current − birth + 27) % 27   → 0-indexed forward count
 *   count    = distance + 1                   → 1-indexed (1 = Janma)
 *   taraIdx  = (count − 1) % 9               → 0-indexed into TARA_NAMES
 *
 * Edge case: when birth === current, distance = 0, count = 1 → Janma (own star).
 */
export function computeTaraBala(
  nativeBirthNakshatraId: number,
  currentNakshatraId: number,
): TaraBalaResult {
  if (
    !Number.isInteger(nativeBirthNakshatraId) ||
    nativeBirthNakshatraId < 1 ||
    nativeBirthNakshatraId > 27
  ) {
    throw new RangeError(
      `nativeBirthNakshatraId must be integer 1–27, got ${nativeBirthNakshatraId}`,
    )
  }
  if (
    !Number.isInteger(currentNakshatraId) ||
    currentNakshatraId < 1 ||
    currentNakshatraId > 27
  ) {
    throw new RangeError(
      `currentNakshatraId must be integer 1–27, got ${currentNakshatraId}`,
    )
  }

  // Convert to 0-indexed for modular arithmetic
  const birthIdx   = nativeBirthNakshatraId - 1  // 0..26
  const currentIdx = currentNakshatraId - 1       // 0..26

  // Forward distance (wrapping); 0 means same nakshatra
  const distance = (currentIdx - birthIdx + 27) % 27

  // 1-indexed count (1 = Janma / own star)
  const count = distance + 1  // 1..27

  // Tara index cycles every 9 nakshatras
  const taraIdx = (count - 1) % 9   // 0..8

  const tara = TARA_NAMES[taraIdx]!
  const classification = TARA_CLASSIFICATION[tara]

  return { tara, count, classification }
}
