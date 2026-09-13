/**
 * bhavat_bhavam_map.ts — the Bhavat Bhavam 12-cell doctrinal map (D-1.5b Lane B-4, CR-97).
 *
 * Pure registry DATA — deliberately not expressed as scattered if/else logic (brief
 * BRIEF_D1_5B.md §Lane B-4: "The 12-cell doctrinal map ... as registry data").
 *
 * PRESERVED IMPLEMENTATION SCOPE: only the six ODD houses receive a "house of the
 * house" (bhavat bhavam) reference. EVEN houses receive NOTHING. The L0 semantic
 * package now states the crucial qualification boundary: this narrow, non-recursive
 * map is preserved but remains UNQUALIFIED_SOURCE until an exact admitted passage,
 * edition/translation and rights/use pin supports this exact scope.
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

import resourceConfigJson from "../../../python-sidecar/brahmagyan/l0_resource_config_slice_v1.json";

export const BHAVAT_BHAVAM_MAP_VERSION = "1.0";
export const BHAVAT_BHAVAM_SEMANTIC_RELEASE_ID =
  resourceConfigJson.semantic_release_id;
export const BHAVAT_BHAVAM_SEMANTIC_RELEASE_DIGEST =
  resourceConfigJson.semantic_release_digest;
export const BHAVAT_BHAVAM_SLICE_ID = resourceConfigJson.slice_id;
export const BHAVAT_BHAVAM_GENERATION_ID = resourceConfigJson.generation_id;
export const BHAVAT_BHAVAM_METHOD_ID = resourceConfigJson.method.method_id;
export const BHAVAT_BHAVAM_OPERATOR_SCOPE_ID =
  resourceConfigJson.method.operator_scope_id;
export const BHAVAT_BHAVAM_QUALIFICATION_STATE =
  resourceConfigJson.method.qualification_state;
export const BHAVAT_BHAVAM_SOURCE_PASSAGE_ID =
  resourceConfigJson.source_witness.source_passage_id;
export const BHAVAT_BHAVAM_RESTRAINTS = Object.freeze(
  resourceConfigJson.method.restraints,
);

/** Every house 1..12 is present as a key so callers never need a fallback branch to
 *  distinguish "odd, no entry yet" from "even, deliberately empty" — both read as []. */
export const BHAVAT_BHAVAM_MAP: Readonly<Record<number, readonly number[]>> =
  Object.freeze(
    Object.fromEntries(
      Object.entries(resourceConfigJson.map).map(([house, derived]) => [
        Number(house),
        Object.freeze([...derived]),
      ]),
    ),
  );

export const ODD_HOUSES: readonly number[] = [1, 3, 5, 7, 9, 11];
export const EVEN_HOUSES: readonly number[] = [2, 4, 6, 8, 10, 12];

/** Return the preserved, non-recursive reference-map entries for `primaryHouse`.
 * Even houses return []; the package remains `UNQUALIFIED_SOURCE`, so this is
 * reference data rather than authority to generate a configuration. */
export function derivedHouses(primaryHouse: number): readonly number[] {
  const derived = BHAVAT_BHAVAM_MAP[primaryHouse];
  if (derived === undefined) {
    throw new Error(
      `bhavat_bhavam: house ${primaryHouse} is not a valid bhava (1-12)`,
    );
  }
  return derived;
}

export function isOddHouse(house: number): boolean {
  return ODD_HOUSES.includes(house);
}
