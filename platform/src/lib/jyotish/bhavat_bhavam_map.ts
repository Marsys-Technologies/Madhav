/**
 * bhavat_bhavam_map.ts — the Bhavat Bhavam 12-cell doctrinal map (D-1.5b Lane B-4, CR-97).
 *
 * Pure registry DATA — deliberately not expressed as scattered if/else logic (brief
 * BRIEF_D1_5B.md §Lane B-4: "The 12-cell doctrinal map ... as registry data").
 *
 * DOCTRINE (hard rule, not an oversight): only the six ODD houses receive a "house of the
 * house" (bhavat bhavam) derivation. EVEN houses receive NOTHING — no derived house is ever
 * computed for an even primary house. This is the TypeScript mirror of the canonical Python
 * registry (`platform/python-sidecar/bodha_writers/bhavat_bhavam_registry.py`, which the
 * bo_laksana `bhavat_bhavam_amplifier` MSR emitter reads); both sides carry the SAME map as
 * data, never re-derived from logic.
 *
 * Map (verbatim from the brief):
 *   1  -> [1, 7]
 *   3  -> [2, 8]
 *   5  -> [3, 9]
 *   7  -> [4, 10]
 *   9  -> [5, 11]
 *   11 -> [6, 12]
 *   2, 4, 6, 8, 10, 12 -> []  (even houses: no derivation, by design)
 */

export const BHAVAT_BHAVAM_MAP_VERSION = '1.0'

/** Every house 1..12 is present as a key so callers never need a fallback branch to
 *  distinguish "odd, no entry yet" from "even, deliberately empty" — both read as []. */
export const BHAVAT_BHAVAM_MAP: Readonly<Record<number, readonly number[]>> = Object.freeze({
  1: [1, 7],
  2: [],
  3: [2, 8],
  4: [],
  5: [3, 9],
  6: [],
  7: [4, 10],
  8: [],
  9: [5, 11],
  10: [],
  11: [6, 12],
  12: [],
})

export const ODD_HOUSES: readonly number[] = [1, 3, 5, 7, 9, 11]
export const EVEN_HOUSES: readonly number[] = [2, 4, 6, 8, 10, 12]

/** Return the derived ("house of the house") bhāvas for `primaryHouse`. Even houses ALWAYS
 *  return [] — the hard doctrinal rule, enforced here as code. */
export function derivedHouses(primaryHouse: number): readonly number[] {
  const derived = BHAVAT_BHAVAM_MAP[primaryHouse]
  if (derived === undefined) {
    throw new Error(`bhavat_bhavam: house ${primaryHouse} is not a valid bhava (1-12)`)
  }
  return derived
}

export function isOddHouse(house: number): boolean {
  return ODD_HOUSES.includes(house)
}
