/**
 * identifier_format.ts — shared humanizer + canonical-output formatter (EL-32 + EL-44)
 * ============================================================================
 * ONE formatter serving two charter items at once (ELEVATION_CAMPAIGN_CHARTER_v2_1.md §γ.E):
 *   - EL-44: assess_*'s verdict layer must humanize machine-key text
 *     (`Saturn_in_H7` → "Saturn in the 7th house") rather than echo raw tokens.
 *   - EL-32: canonical-output pass — a served identifier always carries its FULL
 *     canonical form (e.g. "SUN", not "SU" or "sun") on OUTPUT; any alias variant
 *     (2-char code, 3-char L1 fact_subject token, lowercase) is accepted on INPUT.
 *
 * Scope note: this lane's manifest is register_d8_assess_domain.ts + ranking/**.
 * This module is written so a later pass on other registry/layers files (out of
 * this lane's manifest) can import it as the ONE shared formatter rather than
 * growing a second one — the naming-governance gate this charter item asks for
 * is "one formatter used everywhere", not "one formatter per file".
 */

// ── Graha canonicalization (EL-32) ─────────────────────────────────────────────
// Every alias variant observed across L1/L2 layers resolves to ONE canonical
// UPPERCASE full name on output. Mirrors composite_ranker.ts's GRAHA_TO_CODE /
// GRAHA_TOKEN_TO_NAME tables (kept independent here — this module must not
// depend on ranking internals — but doctrinally identical).
const GRAHA_ALIAS_TO_CANONICAL: Record<string, string> = {
  SU: 'SUN', MO: 'MOON', MA: 'MARS', ME: 'MERCURY', JU: 'JUPITER', VE: 'VENUS', SA: 'SATURN',
  RA: 'RAHU', KE: 'KETU',
  SUN: 'SUN', MOON: 'MOON', MARS: 'MARS', MERCURY: 'MERCURY', JUPITER: 'JUPITER',
  VENUS: 'VENUS', SATURN: 'SATURN', RAHU: 'RAHU', KETU: 'KETU',
  MAR: 'MARS', MER: 'MERCURY', JUP: 'JUPITER', VEN: 'VENUS', SAT: 'SATURN',
  RAH_MEAN: 'RAHU', KET_MEAN: 'KETU', RAH: 'RAHU', KET: 'KETU',
}

const GRAHA_DISPLAY: Record<string, string> = {
  SUN: 'Sun', MOON: 'Moon', MARS: 'Mars', MERCURY: 'Mercury', JUPITER: 'Jupiter',
  VENUS: 'Venus', SATURN: 'Saturn', RAHU: 'Rahu', KETU: 'Ketu',
}

/** Canonical UPPERCASE full graha name for any alias input, or null if unresolvable. Never
 *  invents a graha (B.10) — returns null rather than guessing. */
export function canonicalGraha(input: string | null | undefined): string | null {
  if (!input) return null
  return GRAHA_ALIAS_TO_CANONICAL[input.toUpperCase()] ?? null
}

/** Title-case display form for prose ("Sun", not "SUN" or "SU"). Falls back to the raw
 *  input, Title-cased, if it is not a recognized graha alias. */
export function displayGraha(input: string | null | undefined): string {
  if (!input) return ''
  const canon = canonicalGraha(input)
  if (canon) return GRAHA_DISPLAY[canon] ?? canon
  return input.charAt(0).toUpperCase() + input.slice(1).toLowerCase()
}

// ── Varga display names (classical Sanskrit + D-code, per BPHS Ch.6) ──────────
// Source: the same Shodasavarga (16-fold) scheme cited in priors_config.ts
// VARGA_BASE_WEIGHT / VARGA_WEIGHT_CITATION (EL-55) — kept as a separate literal
// table here (this module must not depend on ranking internals) but naming the
// same 16 vargas.
export const VARGA_DISPLAY: Record<string, string> = {
  D1: 'Rāśi (D1)', D2: 'Horā (D2)', D3: 'Drekkāṇa (D3)', D4: 'Caturthāṃśa (D4)',
  D6: 'Ṣaṣṭhāṃśa (D6)', D7: 'Saptāṃśa (D7)', D9: 'Navāṃśa (D9)', D10: 'Daśāṃśa (D10)',
  D11: 'Rudrāṃśa / Ekādaśāṃśa (D11)', D12: 'Dvādaśāṃśa (D12)', D16: 'Ṣoḍaśāṃśa (D16)',
  D20: 'Viṃśāṃśa (D20)', D24: 'Caturviṃśāṃśa (D24)', D27: 'Saptaviṃśāṃśa / Bhāṃśa (D27)',
  D30: 'Triṃśāṃśa (D30)', D40: 'Khavedāṃśa (D40)', D45: 'Akṣavedāṃśa (D45)', D60: 'Ṣaṣṭyāṃśa (D60)',
}

/** Display form for a varga code (e.g. "D2" -> "Horā (D2)"). Falls back to the bare code. */
export function displayVarga(code: string | null | undefined): string {
  if (!code) return ''
  const up = code.toUpperCase()
  return VARGA_DISPLAY[up] ?? up
}

/** Ordinal house phrase ("H7" / 7 -> "7th house"). Never invents a house number — the caller
 *  supplies it; this only formats. */
export function ordinalHouse(house: number | string | null | undefined): string {
  if (house === null || house === undefined || house === '') return ''
  const n = typeof house === 'string' ? Number(house.replace(/^H/i, '')) : house
  if (!Number.isInteger(n) || n < 1 || n > 12) return String(house)
  const mod100 = n % 100
  const suffix = mod100 >= 11 && mod100 <= 13 ? 'th' : ['th', 'st', 'nd', 'rd'][n % 10] ?? 'th'
  return `${n}${suffix} house`
}

/**
 * Humanize a machine-key identifier into plain-language prose (EL-44).
 * Recognizes three shapes commonly served by this file's own output:
 *   1. "{GRAHA}_in_H{N}"       -> "Saturn in the 7th house"        (the charter's own example)
 *   2. "{VARGA}_{GRAHA}"       -> "Sun in Horā (D2)"                (L1 fact_subject shape, e.g. "D2_SUN")
 *   3. a bare graha alias      -> "Saturn"
 * Anything else is returned unchanged — this function never fabricates a gloss for a key
 * shape it does not recognize (B.10); an unrecognized key is served as-is, not silently altered.
 */
export function humanizeMachineKey(key: string | null | undefined): string {
  if (!key) return ''
  const inHouseMatch = key.match(/^([A-Za-z_]+)_in_H(\d{1,2})$/)
  if (inHouseMatch) {
    const graha = displayGraha(inHouseMatch[1])
    const house = ordinalHouse(Number(inHouseMatch[2]))
    if (graha && house) return `${graha} in the ${house}`
  }
  const vargaGrahaMatch = key.match(/^(D\d{1,4})_([A-Za-z_]+)$/)
  if (vargaGrahaMatch) {
    const varga = displayVarga(vargaGrahaMatch[1])
    const graha = displayGraha(vargaGrahaMatch[2])
    if (graha && varga) return `${graha} in ${varga}`
  }
  const bareGraha = canonicalGraha(key)
  if (bareGraha) return GRAHA_DISPLAY[bareGraha] ?? bareGraha
  return key
}

/**
 * Humanize a snake_case/UPPER_SNAKE machine reason/id string into a readable phrase
 * (e.g. yoga_canonical_id, always_on_reason values) — pure mechanical de-snake-casing,
 * never a re-interpretation. "GAJAKESARI_YOGA" -> "Gajakesari Yoga".
 */
export function humanizeSnakeLabel(raw: string | null | undefined): string {
  if (!raw) return ''
  return raw
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map(w => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}
