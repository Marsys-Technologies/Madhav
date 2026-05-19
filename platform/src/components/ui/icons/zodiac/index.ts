/**
 * Zodiac sign glyphs — Unicode approach (♈♉♊…♓).
 *
 * Chosen over inline SVG because the project uses text-based iconography
 * and Unicode glyphs render at any size without separate SVG assets.
 *
 * Phase: 4C-4-S2 (Item 3)
 */

/** Sanskrit rashi name → Unicode zodiac glyph */
export const ZODIAC_GLYPHS: Record<string, string> = {
  // Sanskrit names (primary keys)
  Mesha: '♈',
  Vrishabha: '♉',
  Mithuna: '♊',
  Karka: '♋',
  Simha: '♌',
  Kanya: '♍',
  Tula: '♎',
  Vrishchika: '♏',
  Dhanus: '♐',
  Makara: '♑',
  Kumbha: '♒',
  Meena: '♓',
  // English aliases (fallback for sidecar responses that use English names)
  Aries: '♈',
  Taurus: '♉',
  Gemini: '♊',
  Cancer: '♋',
  Leo: '♌',
  Virgo: '♍',
  Libra: '♎',
  Scorpio: '♏',
  Sagittarius: '♐',
  Capricorn: '♑',
  Aquarius: '♒',
  Pisces: '♓',
}

/** Sign number (1-indexed, 1=Mesha) → Sanskrit name */
export const SIGN_NAMES_SANSKRIT: string[] = [
  'Mesha',
  'Vrishabha',
  'Mithuna',
  'Karka',
  'Simha',
  'Kanya',
  'Tula',
  'Vrishchika',
  'Dhanus',
  'Makara',
  'Kumbha',
  'Meena',
]

/**
 * Return the Unicode glyph for a sign name (Sanskrit or English).
 * Returns empty string if unrecognised.
 */
export function getZodiacGlyph(signName: string | null | undefined): string {
  if (!signName) return ''
  return ZODIAC_GLYPHS[signName] ?? ''
}

/**
 * Convert a 0-indexed sign number (0=Mesha … 11=Meena) to Sanskrit name.
 */
export function signIndexToSanskrit(index: number): string {
  return SIGN_NAMES_SANSKRIT[index] ?? ''
}

/**
 * Derive sign from absolute ecliptic longitude (0–360°).
 * Returns { index, sanskrit, glyph }
 */
export function signFromLon(absoluteLon: number): { index: number; sanskrit: string; glyph: string } {
  const normalized = ((absoluteLon % 360) + 360) % 360
  const index = Math.floor(normalized / 30)
  const sanskrit = SIGN_NAMES_SANSKRIT[index] ?? ''
  const glyph = getZodiacGlyph(sanskrit)
  return { index, sanskrit, glyph }
}
