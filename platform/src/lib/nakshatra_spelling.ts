/**
 * nakshatra_spelling.ts -- the TypeScript table of nakshatra spellings for platform/ (Next.js app).
 *
 * Canonical spelling = the L0 lexicon's `name_en` (platform/python-sidecar/brahmagyan/
 * l0_nakshatra.py, which is also `canonical_name_en` in l0_ontology.py). Sibling copy for the
 * separate platform-mcp package: platform-mcp/src/lib/nakshatra_names.ts (identical table; both pinned
 * to the lexicon). Python mirror:
 * platform/python-sidecar/brahmagyan/nakshatra_vocabulary.py. A pin test
 * (__tests__/nakshatra_spelling.test.ts) reads l0_nakshatra.py and fails if this table drifts from it.
 *
 * Three canonical names differ from the old L1 spelling: no. 5 Mrigasira (L1 wrote Mrigashira),
 * no. 19 Moola (Mula), no. 23 Dhanishtha (Dhanishta). Stored L1 rows keep the old spellings until
 * the single rebuild, so every reader resolves BOTH (`legacy`), plus common aliases (`aliases`).
 * An unknown name resolves to null, never to a guess (CLAUDE.md §N.7 item 6).
 */

interface NakshatraSpelling {
  /** L0 lexicon `name_en`. */
  canonical: string
  /** Other spellings that exist in STORED data (old L1 name table, L0 medical seed). */
  legacy: readonly string[]
  /** Other common transliterations / regional names (resolve-only, never stored). */
  aliases: readonly string[]
}

/** Index 0 = nakshatra no. 1 (Ashwini) ... index 26 = no. 27 (Revati). */
const TABLE: readonly NakshatraSpelling[] = [
  { canonical: 'Ashwini', legacy: [], aliases: ['Aswini', 'Ashvini'] },
  { canonical: 'Bharani', legacy: [], aliases: ['Apabharani'] },
  { canonical: 'Krittika', legacy: [], aliases: ['Krithika', 'Kartika'] },
  { canonical: 'Rohini', legacy: [], aliases: [] },
  { canonical: 'Mrigasira', legacy: ['Mrigashira'], aliases: ['Mrigashirsha'] },
  { canonical: 'Ardra', legacy: [], aliases: ['Arudra', 'Thiruvathirai'] },
  { canonical: 'Punarvasu', legacy: [], aliases: [] },
  { canonical: 'Pushya', legacy: [], aliases: ['Pushyami'] },
  { canonical: 'Ashlesha', legacy: [], aliases: ['Aslesha'] },
  { canonical: 'Magha', legacy: [], aliases: [] },
  { canonical: 'Purva Phalguni', legacy: [], aliases: ['Poorva Phalguni'] },
  { canonical: 'Uttara Phalguni', legacy: [], aliases: [] },
  { canonical: 'Hasta', legacy: [], aliases: [] },
  { canonical: 'Chitra', legacy: [], aliases: ['Chithra'] },
  { canonical: 'Swati', legacy: [], aliases: ['Svati'] },
  { canonical: 'Vishakha', legacy: [], aliases: ['Visakha'] },
  { canonical: 'Anuradha', legacy: [], aliases: [] },
  { canonical: 'Jyeshtha', legacy: [], aliases: ['Jyestha'] },
  { canonical: 'Moola', legacy: ['Mula'], aliases: ['Mool'] },
  { canonical: 'Purva Ashadha', legacy: [], aliases: ['Poorva Ashadha', 'Purvashadha'] },
  { canonical: 'Uttara Ashadha', legacy: [], aliases: ['Uttarashadha'] },
  { canonical: 'Shravana', legacy: [], aliases: ['Sravana'] },
  { canonical: 'Dhanishtha', legacy: ['Dhanishta'], aliases: ['Dhanistha'] },
  { canonical: 'Shatabhisha', legacy: [], aliases: ['Satabhisha'] },
  { canonical: 'Purva Bhadrapada', legacy: [], aliases: ['Poorva Bhadrapada', 'Purvabhadra'] },
  { canonical: 'Uttara Bhadrapada', legacy: [], aliases: ['Uttarabhadra'] },
  { canonical: 'Revati', legacy: [], aliases: [] },
]

/** The 27 canonical names, index 0 -> number 1. Derived from TABLE (no second literal). */
export const CANONICAL_NAKSHATRA_NAMES: readonly string[] = TABLE.map((r) => r.canonical)

/** Case / spacing / punctuation / diacritic tolerant key; keeps the long-standing aa/sh/ph folds. */
function foldKey(s: string): string {
  return s
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z]+/g, '')
    .replace(/aa/g, 'a').replace(/sh/g, 's').replace(/ph/g, 'f')
}

const NUMBER_BY_KEY: ReadonlyMap<string, number> = (() => {
  const m = new Map<string, number>()
  TABLE.forEach((row, i) => {
    for (const spelling of [row.canonical, ...row.legacy, ...row.aliases]) {
      const key = foldKey(spelling)
      const prior = m.get(key)
      if (prior !== undefined && prior !== i + 1) {
        throw new Error(`nakshatra_spelling: spelling "${spelling}" collides across nakshatras ${prior} and ${i + 1}`)
      }
      m.set(key, i + 1)
    }
  })
  return m
})()

/** Number 1..27 of a nakshatra name (canonical, old-L1, or alias spelling), else null. */
export function nakshatraNumberOf(name: string | undefined | null): number | null {
  if (typeof name !== 'string') return null
  const key = foldKey(name)
  return key ? NUMBER_BY_KEY.get(key) ?? null : null
}

/** The canonical spelling of a name, else null. */
export function canonicalNakshatraName(name: string | undefined | null): string | null {
  const n = nakshatraNumberOf(name)
  return n === null ? null : CANONICAL_NAKSHATRA_NAMES[n - 1] ?? null
}

/** Spellings that can exist in STORED data for this nakshatra (canonical first, then legacy), else null. */
export function storedNakshatraSpellings(name: string | undefined | null): string[] | null {
  const n = nakshatraNumberOf(name)
  const row = n === null ? undefined : TABLE[n - 1]
  return row ? [row.canonical, ...row.legacy] : null
}
